"""Reproducible, sample-free ELR sonic identity. No GPU or model downloads."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def tine(t: np.ndarray, frequency: float) -> np.ndarray:
    """Soft struck tine with inharmonic partials, attack and a decaying body."""
    attack = 1 - np.exp(-t * 500)
    return attack * (
        np.sin(2 * math.pi * frequency * t) * np.exp(-t * 2.9)
        + .22 * np.sin(2 * math.pi * frequency * 2.006 * t) * np.exp(-t * 5)
        + .08 * np.sin(2 * math.pi * frequency * 3.97 * t) * np.exp(-t * 10)
    )


def synthesize(config: dict, kind: str) -> tuple[np.ndarray, list[dict]]:
    rate, fps = config['sampleRate'], config['fps']
    frames = config['introFrames'] if kind == 'intro' else config['outroFrames']
    count = round(frames / fps * rate)
    mix = np.zeros((count, 2), dtype=np.float64)
    rng = np.random.default_rng(config['seed'])
    events: list[dict] = []

    def add(signal: np.ndarray, frame: int, gain: float, pan: float, name: str) -> None:
        start = round(frame / fps * rate)
        stop = min(count, start + len(signal))
        if stop <= start:
            return
        gains = np.array([math.sqrt((1 - pan) / 2), math.sqrt((1 + pan) / 2)])
        mix[start:stop] += signal[:stop - start, None] * gains * gain
        events.append({'name': name, 'frame': frame, 'gain': gain, 'pan': pan})

    # Soft filtered air rather than a loud broadband microphone-like burst.
    sweep_count = round(config['impactFrame'] / fps * rate)
    noise = rng.standard_normal(sweep_count)
    smooth = np.convolve(noise, np.hanning(129) / np.hanning(129).sum(), mode='same')
    u = np.linspace(0, 1, sweep_count)
    air = smooth * np.sin(math.pi * u) ** 2 * (.2 + .8 * u)
    add(air, 0, .055 if kind == 'intro' else .035, -.35, 'air-build')

    t = np.arange(round(rate * 2.3)) / rate
    # No instantaneous cosine onset: that caused a 0.50-full-scale click in v1.
    # A raised-cosine 18ms attack starts at zero and keeps the onset continuous.
    attack = .5 - .5 * np.cos(math.pi * np.minimum(t / .018, 1))
    hit = tine(t, 392) * attack * np.exp(-t * 3)
    add(hit, config['impactFrame'], .15, 0, 'soft-reveal-chime')
    notes = [523.251, 659.255, 783.991] if kind == 'intro' else [783.991, 659.255, 523.251]
    for index, (frame, note) in enumerate(zip(config['noteFrames'], notes)):
        signal = tine(t, note)
        add(signal, frame, .20 - index * .015, -.3 + index * .3, 'tine')
        for delay, gain in [(4, .055), (9, .025)]:
            add(signal, frame + delay, gain, .3 - index * .3, 'early-reflection')

    if kind == 'outro':
        # Sparse harmonic air, not a looping beat competing with end-screen choice.
        bed_t = np.arange(count) / rate
        envelope = np.minimum(1, bed_t / 1.5) * np.minimum(1, (count / rate - bed_t) / 4)
        for index, note in enumerate([130.813, 195.998, 261.626, 329.628]):
            phase = .3 * np.sin(2 * math.pi * .09 * bed_t + index)
            bed = np.sin(2 * math.pi * note * bed_t + phase) * envelope
            add(bed, 0, .012, -.5 + index / 3, 'harmonic-bed')

    if kind in ('intro', 'outro'):
        # One quiet rounded press cue, no hard step or broadband pop.
        tap_t = np.arange(round(rate * .065)) / rate
        tap = np.sin(2 * math.pi * 360 * tap_t) * np.sin(math.pi * tap_t / .065) ** 2
        add(tap, config['ctaPressFrame'], .045, .15, 'subscribe-press')

    # Finite, gentle tail with no discontinuity at the splice.
    fade_in = np.minimum(1, np.arange(count) / (rate * .005))
    fade_out = np.minimum(1, (count - 1 - np.arange(count)) / (rate * .45))
    mix *= (fade_in * fade_out)[:, None]
    peak = float(np.max(np.abs(mix)))
    mix *= 10 ** (config['peakDbfs'] / 20) / max(peak, 1e-12)
    return mix, events


def measure(audio: np.ndarray, rate: int) -> dict:
    peak = float(np.max(np.abs(audio)))
    tail = audio[-round(rate * .05):]
    return {
        'durationSeconds': len(audio) / rate,
        'channels': audio.shape[1],
        'peakDbfs': 20 * math.log10(max(peak, 1e-12)),
        'tailRmsDbfs': 20 * math.log10(max(float(np.sqrt(np.mean(tail ** 2))), 1e-12)),
        'peakFrameAt30fps': int(np.argmax(np.max(np.abs(audio), axis=1))) / rate * 30,
        'maxSampleStep': float(np.max(np.abs(np.diff(audio, axis=0)))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'public/branding/v4')
    args = parser.parse_args()
    config_path = ROOT / 'configs/branding/motion-v4.json'
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trace = {'version': config['version'], 'provider': 'original-procedural-synthesis',
             'externalSamples': [], 'modelWeights': [], 'seed': config['seed'],
             'configSha256': hashlib.sha256(config_bytes).hexdigest(),
             'generatorSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'artifacts': []}
    for kind in ['intro', 'outro']:
        audio, events = synthesize(config, kind)
        path = args.output_dir / f'{kind}.wav'
        pcm = np.round(audio * 32767).astype('<i2')
        with wave.open(str(path), 'wb') as output:
            output.setnchannels(2)
            output.setsampwidth(2)
            output.setframerate(config['sampleRate'])
            output.writeframes(pcm.tobytes())
        # Measure actual quantized samples, not just the pre-encode floats.
        trace['artifacts'].append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                   'events': events, **measure(pcm.astype(np.float64) / 32768, config['sampleRate'])})
    (args.output_dir / 'trace.json').write_text(json.dumps(trace, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(trace['artifacts'], indent=2))


if __name__ == '__main__':
    main()
