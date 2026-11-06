import json
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.cursor/skills/audiobook-chapter-tts/scripts'))
from media import radial_waveform as radial
from media import resumable_frames
from media.resumable_frames import render_resumable_frames, valid_media


pytestmark = pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
                               reason='media integration requires existing ffmpeg')


def test_encoder_pipe_error_preserves_diagnostic_and_verified_cache(tmp_path, monkeypatch):
    class BrokenInput:
        closed = False

        def write(self, data):
            raise OSError(22, 'Invalid argument')

        def close(self):
            self.closed = True
            raise OSError(22, 'close pipe')

    class FailedEncoder:
        returncode = 1
        stdin = BrokenInput()

        def poll(self):
            return 1

        def wait(self):
            return 1

    def failed_encoder(command, **kwargs):
        assert command[command.index('-threads') + 1] == '1'
        kwargs['stderr'].write(b'encoder allocation failed')
        return FailedEncoder()

    monkeypatch.setattr(resumable_frames.subprocess, 'Popen', failed_encoder)
    with pytest.raises(RuntimeError, match='chunk 0; exit=1; encoder allocation failed'):
        render_resumable_frames(output=tmp_path / 'overlay.mov', total_frames=2,
            width=32, height=32, fps=10, identity={'test': 'pipe-failure'},
            draw_frame=lambda frame: Image.new('RGBA', (32, 32)),
            save_state=lambda: {}, restore_state=lambda state: None)
    checkpoint = json.loads((tmp_path / 'overlay.render.json').read_text())
    assert checkpoint['chunks'] == {}
    assert checkpoint['complete'] is False


def test_resume_keeps_verified_chunk_and_restores_motion(tmp_path):
    output = tmp_path / 'overlay.mov'
    state = {'n': 0}
    drawn = []
    fail = True
    def draw(frame):
        nonlocal fail
        if fail and frame == 4:
            raise RuntimeError('simulated interruption')
        state['n'] += 1
        drawn.append((frame, state['n']))
        return Image.new('RGBA', (32, 32), (state['n'], 30, 90, 255))
    kwargs = dict(output=output, total_frames=9, width=32, height=32, fps=10,
        identity={'audio': 'same', 'style': 'same'}, draw_frame=draw,
        save_state=lambda: dict(state), restore_state=lambda data: state.update(data),
        chunk_seconds=.3)
    with pytest.raises(RuntimeError, match='simulated'):
        render_resumable_frames(**kwargs)
    checkpoint = json.loads(output.with_suffix('.render.json').read_text())
    assert checkpoint['chunks']['0']['end'] == 3
    fail = False
    state['n'] = 0
    drawn.clear()
    render_resumable_frames(**kwargs)
    assert drawn == [(frame, frame+1) for frame in range(3, 9)]
    assert valid_media(output, 9, 32, 32, 10)
    assert not list(tmp_path.rglob('00000.mov'))  # Verified final replaces chunk media.
    drawn.clear()
    render_resumable_frames(**kwargs)
    assert drawn == []  # No frame generation on an authoritative cache hit.
    kwargs['identity'] = {'audio': 'changed', 'style': 'same'}
    state['n'] = 0
    render_resumable_frames(**kwargs)
    assert len(drawn) == 9


def test_palette_cache_is_not_mutable_by_frame_alpha():
    one = radial.spectrum_palette(32)
    expected = np.asarray(one).copy()
    one.putalpha(0)
    assert np.array_equal(np.asarray(radial.spectrum_palette(32)), expected)


def test_radial_resume_preserves_exact_frame_pixels(tmp_path, monkeypatch):
    samples = np.arange(4800) / 8000
    audio = tmp_path / 'speech.wav'
    sf.write(audio, .03 * np.sin(2*np.pi*350*samples), 8000)
    real_engine = radial.resumable_frames.render_resumable_frames
    real_frame = radial.radial_frame
    pixels = []
    def capture(*args, **kwargs):
        image = real_frame(*args, **kwargs)
        pixels.append(image.tobytes())
        return image
    monkeypatch.setattr(radial, 'radial_frame', capture)
    def small_chunks(**kwargs):
        return real_engine(**kwargs, chunk_seconds=.2)
    monkeypatch.setattr(radial.resumable_frames, 'render_resumable_frames', small_chunks)
    radial.render_radial_waveform_video(audio, tmp_path / 'reference.mov',
        width=64, height=64, fps=10, bar_rgb=(255, 255, 255))
    expected = pixels.copy()
    def interrupt(**kwargs):
        original = kwargs['draw_frame']
        def draw(frame):
            if frame == 3:
                raise RuntimeError('pause')
            return original(frame)
        kwargs['draw_frame'] = draw
        return real_engine(**kwargs, chunk_seconds=.2)
    monkeypatch.setattr(radial.resumable_frames, 'render_resumable_frames', interrupt)
    with pytest.raises(RuntimeError, match='pause'):
        radial.render_radial_waveform_video(audio, tmp_path / 'resumed.mov',
            width=64, height=64, fps=10, bar_rgb=(255, 255, 255))
    pixels.clear()
    monkeypatch.setattr(radial.resumable_frames, 'render_resumable_frames', small_chunks)
    radial.render_radial_waveform_video(audio, tmp_path / 'resumed.mov',
        width=64, height=64, fps=10, bar_rgb=(255, 255, 255))
    assert pixels == expected[2:]
