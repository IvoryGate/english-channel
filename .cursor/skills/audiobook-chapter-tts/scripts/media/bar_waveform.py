from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

DEFAULT_WIDTH = 560
DEFAULT_HEIGHT = 88
DEFAULT_FPS = 30
DEFAULT_BAR_COUNT = 40
DEFAULT_GAP = 4
DEFAULT_BOTTOM_PAD = 2
SMOOTHING = 0.45
MIN_FFT_SIZE = 512
MAX_FFT_SIZE = 2048


def _hz_to_mel(hz: float) -> float:
    return 2595.0 * np.log10(1.0 + hz / 700.0)


def _mel_to_hz(mel: float) -> float:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def _mel_band_ranges(bar_count: int, sample_rate: int, fft_size: int) -> list[tuple[int, int]]:
    bin_hz = sample_rate / fft_size
    mel_min = _hz_to_mel(80.0)
    mel_max = _hz_to_mel(min(7600.0, sample_rate * 0.5))
    mel_edges = np.linspace(mel_min, mel_max, bar_count + 1)
    ranges: list[tuple[int, int]] = []
    for index in range(bar_count):
        low_hz = _mel_to_hz(float(mel_edges[index]))
        high_hz = _mel_to_hz(float(mel_edges[index + 1]))
        low_bin = max(1, int(low_hz / bin_hz))
        high_bin = max(low_bin + 1, int(high_hz / bin_hz))
        ranges.append((low_bin, high_bin))
    return ranges


def _spread_band_peaks(peaks: np.ndarray) -> np.ndarray:
    floor = float(np.percentile(peaks, 18))
    spread = np.maximum(peaks - floor, 0.0)
    tilt = np.linspace(0.9, 1.4, len(spread), dtype=np.float32)
    spread = spread * tilt
    kernel = np.array([0.18, 0.64, 0.18], dtype=np.float32)
    padded = np.pad(spread, (1, 1), mode="edge")
    spread = np.convolve(padded, kernel, mode="valid")
    peak_max = float(np.max(spread)) or 1.0
    return (spread / peak_max).astype(np.float32)


def _frame_bar_peaks(chunk: np.ndarray, bar_count: int, sample_rate: int) -> np.ndarray:
    if len(chunk) < 32:
        return np.zeros(bar_count, dtype=np.float32)

    fft_size = 1 << max(9, min(len(chunk), MAX_FFT_SIZE) - 1).bit_length()
    fft_size = int(np.clip(fft_size, MIN_FFT_SIZE, MAX_FFT_SIZE))
    if len(chunk) > fft_size:
        chunk = chunk[-fft_size:]
    padded = np.zeros(fft_size, dtype=np.float32)
    padded[: len(chunk)] = chunk
    windowed = padded * np.hanning(fft_size)
    spectrum = np.abs(np.fft.rfft(windowed))
    if len(spectrum) <= 1:
        return np.zeros(bar_count, dtype=np.float32)

    peaks: list[float] = []
    for low_bin, high_bin in _mel_band_ranges(bar_count, sample_rate, fft_size):
        band = spectrum[low_bin:high_bin]
        if len(band) == 0:
            peaks.append(0.0)
            continue
        peaks.append(float(np.sqrt(np.mean(np.square(band)))))

    peaks_arr = np.array(peaks, dtype=np.float32)
    if float(np.max(peaks_arr)) < 1e-5:
        return np.zeros(bar_count, dtype=np.float32)

    peaks_arr = np.log1p(peaks_arr * 18.0)
    return _spread_band_peaks(peaks_arr)


def render_bar_waveform_video(
    audio_path: Path,
    output_path: Path,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    fps: int = DEFAULT_FPS,
    bar_count: int = DEFAULT_BAR_COUNT,
    gap: int = DEFAULT_GAP,
    bar_rgb: tuple[int, int, int],
    transparent_background: bool = True,
) -> Path:
    audio, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=False)
    if getattr(audio, "ndim", 1) > 1:
        audio = audio.mean(axis=1)

    duration = len(audio) / float(sample_rate)
    frame_count = max(1, int(np.ceil(duration * fps)))
    bar_width = max(4, (width - (bar_count + 1) * gap) // bar_count)
    radius = max(2, bar_width // 2)

    output_path = output_path.with_suffix(".mov")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgba",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-c:v",
        "ffv1",
        "-pix_fmt",
        "yuva420p",
        str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    assert process.stdin is not None
    window_samples = int(0.12 * sample_rate)
    smoothed: np.ndarray | None = None

    for frame_index in range(frame_count):
        center_time = frame_index / fps
        center_sample = int(center_time * sample_rate)
        start = max(0, center_sample - window_samples)
        end = min(len(audio), center_sample)
        chunk = audio[start:end]

        peaks = _frame_bar_peaks(chunk, bar_count, sample_rate)
        if smoothed is None:
            smoothed = peaks
        else:
            smoothed = SMOOTHING * peaks + (1.0 - SMOOTHING) * smoothed

        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        bottom_y = height - DEFAULT_BOTTOM_PAD
        max_bar_height = height - DEFAULT_BOTTOM_PAD - 4
        min_bar_height = 4
        x = gap
        for peak in smoothed:
            bar_height = int(min_bar_height + float(peak) * (max_bar_height - min_bar_height))
            y_top = bottom_y - bar_height
            draw.rounded_rectangle(
                [(x, y_top), (x + bar_width, bottom_y)],
                radius=radius,
                fill=(*bar_rgb, 255),
            )
            x += bar_width + gap

        process.stdin.write(image.tobytes())

    process.stdin.close()
    return_code = process.wait()
    if return_code != 0:
        stderr = (process.stderr.read() if process.stderr else b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"bar waveform ffmpeg failed: {stderr}")
    return output_path
