from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_media(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required for Shorts media quality checks")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,codec_name,width,height,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


def audio_max_volume_db(path: Path) -> float | None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for Shorts audio quality checks")
    result = subprocess.run(
        [ffmpeg, "-v", "info", "-i", str(path), "-af", "volumedetect", "-f", "null", os.devnull],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"max_volume:\s+(-?\d+(?:\.\d+)?)\s+dB", result.stderr)
    if match:
        return float(match.group(1))
    if "max_volume: -inf dB" in result.stderr:
        return float("-inf")
    return None


def analyze_mains_hum(path: Path) -> dict[str, Any]:
    """Measure stationary 50/60 Hz families against their local spectral floor."""
    audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    samples = np.asarray(audio, dtype=np.float64)
    if samples.size < sample_rate:
        raise ValueError("At least one second of audio is required for mains-hum analysis")
    samples -= float(np.mean(samples))
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(samples.size))) ** 2 + 1e-30
    frequencies = np.fft.rfftfreq(samples.size, 1.0 / float(sample_rate))
    families: list[dict[str, Any]] = []
    for base_hz in (50, 60):
        harmonics: list[dict[str, float]] = []
        for multiple in range(1, 6):
            target_hz = float(base_hz * multiple)
            signal_mask = np.abs(frequencies - target_hz) < 0.35
            noise_distance = np.abs(frequencies - target_hz)
            noise_mask = (noise_distance > 1.5) & (noise_distance < 6.0)
            signal_power = float(np.median(spectrum[signal_mask]))
            noise_power = float(np.median(spectrum[noise_mask]))
            prominence_db = 10.0 * np.log10(signal_power / noise_power)
            harmonics.append({"frequencyHz": target_hz, "prominenceDb": round(float(prominence_db), 2)})
        strongest = sorted(item["prominenceDb"] for item in harmonics)[-2:]
        family_score = float(np.median(strongest))
        families.append(
            {
                "baseFrequencyHz": base_hz,
                "scoreDb": round(family_score, 2),
                "harmonics": harmonics,
            }
        )
    return {
        "schema": "elr-short-mains-hum-v1",
        "sampleRate": int(sample_rate),
        "durationSec": round(samples.size / float(sample_rate), 3),
        "families": families,
        "maxScoreDb": max(item["scoreDb"] for item in families),
    }


def check_audio(path: Path, product: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {
            "schema": "elr-short-audio-qc-v1",
            "shortId": manifest.get("shortId"),
            "status": "fail",
            "errors": ["MASTER_AUDIO_MISSING"],
            "warnings": [],
        }
    hum = analyze_mains_hum(path)
    score = float(hum["maxScoreDb"])
    quality = product["quality"]
    if score > float(quality["mainsHumHardMaxDb"]):
        errors.append("ELECTRICAL_HUM_DETECTED")
    elif score > float(quality["mainsHumWarningDb"]):
        warnings.append("ELECTRICAL_HUM_REVIEW")
    return {
        "schema": "elr-short-audio-qc-v1",
        "shortId": manifest.get("shortId"),
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "mainsHum": hum,
    }


def check_manifest(manifest: dict[str, Any], product: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    quality = product["quality"]
    duration = float(manifest.get("durationSec", 0.0))
    if duration < float(quality["durationMinSec"]) or duration > float(quality["durationHardMaxSec"]):
        errors.append("DURATION_OUT_OF_RANGE")
    if duration > float(quality["durationTargetMaxSec"]):
        warnings.append("DURATION_ABOVE_TARGET")
    title = str(manifest.get("title", ""))
    if not title or len(title) > int(quality["titleHardMaxChars"]):
        errors.append("TITLE_INVALID")
    elif len(title) > int(quality["titleTargetMaxChars"]):
        warnings.append("TITLE_ABOVE_TARGET")
    if not manifest.get("hook"):
        errors.append("HOOK_MISSING")
    if not manifest.get("turns"):
        errors.append("TURNS_MISSING")
    visual = manifest.get("visual") or {}
    if product.get("visual", {}).get("backgroundRequired") and not visual.get("backgroundImage"):
        errors.append("GENERATED_BACKGROUND_MISSING")
    if not visual.get("brandLogo"):
        errors.append("BRAND_LOGO_MISSING")
    cta = str(manifest.get("cta", ""))
    if not cta or len(cta) > int(product["cta"]["maxChars"]):
        errors.append("CTA_INVALID")
    if product["publishing"].get("requireRelatedVideo") and not manifest.get("relatedVideoId"):
        warnings.append("RELATED_VIDEO_PENDING")
    if manifest.get("publication", {}).get("privacy") != "private":
        errors.append("PILOT_PRIVACY_MUST_BE_PRIVATE")
    return {
        "schema": "elr-short-content-qc-v1",
        "shortId": manifest.get("shortId"),
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
    }


def check_video(path: Path, manifest: dict[str, Any], *, require_audio: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {
            "schema": "elr-short-video-qc-v1",
            "shortId": manifest.get("shortId"),
            "status": "fail",
            "errors": ["VIDEO_MISSING"],
            "warnings": [],
        }
    probe = probe_media(path)
    streams = list(probe.get("streams") or [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if video is None:
        errors.append("VIDEO_STREAM_MISSING")
    else:
        if int(video.get("width", 0)) != int(manifest["width"]):
            errors.append("VIDEO_WIDTH_INVALID")
        if int(video.get("height", 0)) != int(manifest["height"]):
            errors.append("VIDEO_HEIGHT_INVALID")
        if video.get("codec_name") != "h264":
            warnings.append("VIDEO_CODEC_NOT_H264")
    if require_audio and audio is None:
        errors.append("AUDIO_STREAM_MISSING")
    audio_peak = None
    if require_audio and audio is not None:
        audio_peak = audio_max_volume_db(path)
        if audio_peak is None:
            errors.append("AUDIO_LEVEL_UNREADABLE")
        elif audio_peak < -55.0:
            errors.append("AUDIO_EFFECTIVELY_SILENT")
    if audio is not None and audio.get("codec_name") != "aac":
        warnings.append("AUDIO_CODEC_NOT_AAC")
    actual_duration = float(probe.get("format", {}).get("duration") or 0.0)
    expected_duration = float(manifest["durationSec"])
    if abs(actual_duration - expected_duration) > 0.75:
        errors.append("VIDEO_DURATION_DRIFT")
    return {
        "schema": "elr-short-video-qc-v1",
        "shortId": manifest.get("shortId"),
        "status": "fail" if errors else "pass",
        "errors": errors,
        "warnings": warnings,
        "probe": probe,
        "audioMaxVolumeDb": audio_peak,
        "sha256": sha256_file(path),
    }
