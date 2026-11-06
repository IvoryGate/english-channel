from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.cursor/skills/audiobook-chapter-tts/scripts'))
sys.path.insert(0, str(ROOT / 'workspace/shows/tools'))
from media.radial_waveform import (radial_frame, spectrum_targets, smooth_motion,
    advance_particles, inner_ring_radii, LightParticle, particle_opacity)
from media.generate_karaoke_ass import generate_karaoke_ass, _ass_timestamp
from media.thumbnail_tokens import DEFAULT_TOKENS
from compose_episode_video import branding_assets_for


def test_radial_geometry_transparency_and_audio_change():
    quiet = np.asarray(radial_frame(np.zeros(96)))
    loud = np.asarray(radial_frame(np.ones(96)))
    assert quiet.shape == (800, 800, 4)
    assert quiet[0, 0, 3] == 0
    assert np.count_nonzero(loud[:, :, 3]) > np.count_nonzero(quiet[:, :, 3])
    assert np.array_equal(np.asarray(radial_frame(np.ones(96))), loud)
    visible_bars = loud[100:160, 385:415]
    bright = visible_bars[:, :, 3] > 230
    assert np.any(bright)
    assert np.all(visible_bars[:, :, 1][bright] > visible_bars[:, :, 0][bright])
    halo = loud[:190]
    assert np.any((halo[:, :, 3] > 5) & (halo[:, :, 3] < 120))
    # Outside the avatar/core, visible pixels retain gradient color, not black borders.
    visible = halo[:, :, 3] > 20
    assert np.all(halo[:, :, :3][visible].sum(axis=1) > 350)
    lower_light = loud[620:710]
    assert np.any((lower_light[:, :, 2] > lower_light[:, :, 1]) & (lower_light[:, :, 3] > 120))


def test_cached_static_artwork_is_reused_without_frame_mutation():
    from media.radial_waveform import _static_core, _band_directions
    _static_core.cache_clear()
    _band_directions.cache_clear()
    first = np.asarray(radial_frame(np.zeros(96))).copy()
    radial_frame(np.ones(96))
    again = np.asarray(radial_frame(np.zeros(96)))
    assert np.array_equal(first, again)
    assert _static_core.cache_info().misses == 1
    assert _static_core.cache_info().hits == 2
    assert _band_directions.cache_info().misses == 1
    assert _band_directions.cache_info().hits == 2


def test_light_beams_attack_quickly_and_release_to_silence():
    position, velocity = np.zeros(24), np.zeros(24)
    target = spectrum_targets(np.full(24, .6))
    position, velocity = smooth_motion(position, velocity, target, 1/60)
    assert np.all((position > 0) & (position < .04))
    for _ in range(60):
        position, velocity = smooth_motion(position, velocity, np.zeros(24), 1/60)
    assert np.all(position < .001)


def test_smoothing_is_time_based_and_particle_birth_is_soft():
    end = []
    for fps in (30, 60):
        p, v = np.zeros(1), np.zeros(1)
        for _ in range(fps//5):
            p, v = smooth_motion(p, v, np.ones(1), 1/fps)
        end.append(p)
    assert np.allclose(end[0], end[1], atol=1e-8)
    assert particle_opacity(LightParticle(0, 250, 100, .8)) == 0
    assert 0 < particle_opacity(LightParticle(0, 250, 100, .8, age=.03)) < .5
    assert particle_opacity(LightParticle(0, 250, 100, .8, age=.6)) == 0


def test_reference_ring_keeps_short_local_pulses():
    peaks = np.zeros(96)
    peaks[10:15] = 1
    frame = np.asarray(radial_frame(peaks))
    y, x = np.where(frame[:, :, 3] > 120)
    assert np.max(np.hypot(x-400, y-400)) < 305
    assert spectrum_targets(np.array([.1]))[0] == 0


def test_inner_thread_separates_from_fixed_bar_roots():
    radii = inner_ring_radii(np.array([0., .5, 1.]), 800)
    assert np.allclose(radii, [248, 233, 218])
    # Thread can remain contracted when the bar has already dropped.
    settled = np.asarray(radial_frame(np.zeros(96)))
    contracted = np.asarray(radial_frame(np.zeros(96), inner_peaks=np.ones(96)))
    assert not np.array_equal(settled, contracted)


def test_peak_particles_emit_fly_outward_and_expire():
    peaks = np.zeros(96)
    peaks[12] = .8
    emitted_at = np.full(96, -1.)
    initial = advance_particles([], peaks, np.zeros(96), emitted_at, 0, 1/30, 720)
    assert len(initial) == 1
    later = advance_particles(initial, peaks, peaks, emitted_at, .1, .1, 720)
    assert len(later) == 1
    assert later[0].radius > initial[0].radius+10
    assert later[0].age > initial[0].age
    assert advance_particles(later, peaks*0, peaks, emitted_at, 1, 1, 720) == []


def test_caption_two_lines_stable_position_gaps_and_escaping():
    words = [{'word': text, 'start': i*.4, 'end': i*.4+.2, 'speaker': 'Nora'}
             for i, text in enumerate('A clear short sentence stays still while each spoken word changes'.split())]
    ass = generate_karaoke_ass(words, DEFAULT_TOKENS['series_a'])
    captions = [line for line in ass.splitlines() if line.startswith('Dialogue: 2')]
    assert captions
    assert all(line.count('\\N') <= 1 for line in captions)
    assert all('\\pos(1280,1010)' in line for line in captions)
    assert any('0:00:00.20,0:00:00.40' in line and '\\c' not in line for line in captions)
    assert 'NORA' in ass
    assert _ass_timestamp(59.999) == '0:01:00.00'


def test_approved_plates_are_canonical_without_copy():
    intro, outro = branding_assets_for('episode_040', disabled=False)
    assert intro == ROOT / 'workspace/branding/v4/intro-r4.mp4'
    assert outro == ROOT / 'workspace/branding/v4/outro-complete.mp4'
    assert branding_assets_for('episode_040', disabled=True) == (None, None)
    assert branding_assets_for('episode_001', disabled=False) == (intro, outro)


def test_non_shorts_policy_and_cue_only_cards():
    import json
    from media.generate_karaoke_ass import generate_phrase_cue_ass
    from media.media_layout import FPS, WAVE_WIDTH
    from worker.classics.providers.branding import uses_approved_body
    policy = json.loads((ROOT / 'configs/branding/approved-longform.json').read_text(encoding='utf-8'))
    assert policy['scope'] == 'all_future_non_shorts'
    assert policy['body']['fps'] == FPS == 30
    assert policy['body']['spectrumSize'] == WAVE_WIDTH == 800
    assert uses_approved_body(ROOT, 'new-book', 1)
    assert uses_approved_body(ROOT, 'persuasion', 12)
    assert not uses_approved_body(ROOT, 'persuasion', 11)
    ass = generate_phrase_cue_ass([{'text': 'Anne listened carefully to every word.', 'start': 0, 'end': 4}], DEFAULT_TOKENS['series_a'])
    captions = [line for line in ass.splitlines() if line.startswith('Dialogue: 2')]
    assert captions and all('\\pos(1280,1010)' in line for line in captions)
    assert all('\\c&H008AD5FF&' not in line for line in captions)


def test_classic_future_branding_preserves_old_chapters():
    sys.path.insert(0, str(ROOT / 'apps/worker-py'))
    from worker.classics.paths import ClassicPaths
    paths = ClassicPaths(ROOT, 'persuasion')
    assert paths.intro_video(11).parent == paths.video_dir(11)
    assert paths.intro_video(12) == ROOT / 'workspace/branding/v4/intro-r4.mp4'
    assert paths.outro_video(12) == ROOT / 'workspace/branding/v4/outro-complete.mp4'
