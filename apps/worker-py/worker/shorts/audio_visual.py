"""Offline, bounded audio analysis for deterministic horizontal light spectra."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import sys

import numpy as np
import soundfile as sf


def analyze_short_audio(audio: Path, *, fps: int = 60) -> dict:
    root = Path(__file__).resolve().parents[4]
    media = str(root / '.cursor/skills/audiobook-chapter-tts/scripts')
    if media not in sys.path:
        sys.path.insert(0, media)
    from media.bar_waveform import _frame_bar_peaks
    from media.radial_waveform import smooth_motion, spectrum_targets

    if fps <= 0:
        raise ValueError('Spectrum sample rate must be positive')
    frames, threads, particles = [], [], []
    position, velocity = np.zeros(32), np.zeros(32)
    inner, inner_velocity = np.zeros(64), np.zeros(64)
    previous = np.zeros(64)
    cooldown = np.full(64, -1.)
    active: list[list[float]] = []
    with sf.SoundFile(audio) as source:
        rate = source.samplerate
        duration = len(source)/rate
        if duration > 90:
            raise ValueError('Trim audio to a Short before spectrum analysis (maximum 90 seconds)')
        for frame in range(math.ceil(duration*fps)):
            now = frame/fps
            end = min(len(source), round(now*rate))
            start = max(0, end-round(.07*rate))
            source.seek(start)
            chunk = source.read(end-start, dtype='float32', always_2d=True).mean(axis=1)
            rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) else 0.
            target = _frame_bar_peaks(chunk, 32, rate)*min(1., rms/.035)
            position, velocity = smooth_motion(position, velocity, spectrum_targets(target), 1/fps)
            values = np.concatenate((position[::-1], position))
            inner, inner_velocity = smooth_motion(inner, inner_velocity, np.sqrt(values), 1/fps, omega=22.)
            active = [[x, y-speed/fps, speed, age+1/fps, energy]
                      for x, y, speed, age, energy in active if age+1/fps < .6]
            local = (values >= np.roll(values, 1)) & (values >= np.roll(values, -1))
            eligible = np.flatnonzero((values > .32) & ((values-previous)*fps > 1.2)
                                      & local & (now-cooldown > .18))
            for index in sorted(eligible, key=lambda i: float(values[i]), reverse=True)[:4]:
                energy = float(values[index])
                active.append([index/63, -(4+energy*64), 90+energy*70, 0., energy])
                cooldown[index] = now
            rendered = []
            for x, y, speed, age, energy in active:
                t = min(1., age/.065)
                alpha = t*t*(3-2*t)*max(0., 1-age/.6)**1.4
                rendered.append([round(x, 4), round(y, 2), round(alpha, 3), round(2+energy, 2)])
            frames.append(np.round(values, 4).tolist())
            threads.append(np.round(inner, 4).tolist())
            particles.append(rendered)
            previous = values.copy()
    with audio.open('rb') as stream:
        fingerprint = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'schema': 'horizontal-light-spectrum-v1', 'fps': fps, 'durationSec': duration,
            'sourceSha256': fingerprint,
            'frames': frames, 'threads': threads, 'particles': particles}
