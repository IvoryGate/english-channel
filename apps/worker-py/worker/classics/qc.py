from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from .config import BookConfig
from .io import atomic_write_json, read_json, sha256_file
from .paths import ClassicPaths, chapter_id


class ChapterQcError(RuntimeError):
    pass


def qc_chapter(repo_root: Path, config: BookConfig, chapter: int) -> dict[str, Any]:
    paths = ClassicPaths(repo_root, config.slug)
    manifest = read_json(paths.segments(chapter))
    expected = [str(segment["filename"]) for segment in manifest["segments"]]
    segment_dir = paths.segment_audio_dir(chapter)
    actual = sorted(path.name for path in segment_dir.glob("*.wav"))
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        raise ChapterQcError(f"Missing narration segments: {missing}")

    target_rate = int(config.render["sampleRate"])
    silence = float(config.render["interSegmentSilenceSec"])
    segment_reports: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    total_duration = 0.0
    for segment in manifest["segments"]:
        path = segment_dir / str(segment["filename"])
        audio, rate = sf.read(path, dtype="float32")
        channels = 1 if audio.ndim == 1 else int(audio.shape[1])
        mono = audio if audio.ndim == 1 else audio.mean(axis=1)
        duration = float(len(mono) / rate)
        peak = float(np.max(np.abs(mono)))
        word_count = max(1, len(str(segment["spokenText"]).split()))
        seconds_per_word = duration / word_count
        flags: list[str] = []
        if int(rate) != target_rate:
            flags.append("sample-rate")
        if channels != 1:
            flags.append("channels")
        if duration <= 0.2:
            flags.append("too-short")
        # Pace is not statistically meaningful for one- or two-word literary
        # fragments (for example "support." or "Wentworth?"). Content ASR is
        # the appropriate guard for those clips.
        if word_count >= 3:
            if seconds_per_word < 0.16:
                flags.append("speech-too-fast")
            if seconds_per_word > 1.35:
                flags.append("speech-too-slow-or-repeated")
        if peak >= 0.999:
            flags.append("clipping")
        if flags:
            warnings.append({"segment": segment["id"], "flags": flags})
        segment_reports.append(
            {
                "id": segment["id"],
                "path": path.relative_to(repo_root).as_posix(),
                "durationSec": round(duration, 3),
                "secondsPerWord": round(seconds_per_word, 3),
                "peak": round(peak, 6),
                "sha256": sha256_file(path),
                "flags": flags,
            }
        )
        total_duration += duration
    total_duration += silence * max(0, len(expected) - 1)

    raw = paths.raw_audio(chapter)
    if not raw.is_file():
        raise ChapterQcError(f"Raw chapter audio is missing: {raw}")
    raw_info = sf.info(raw)
    raw_duration = float(raw_info.frames / raw_info.samplerate)
    compose_drift = abs(raw_duration - total_duration)
    if compose_drift > 0.05:
        warnings.append({"segment": None, "flags": ["compose-duration-drift"]})

    report = {
        "schema": "classic-listening-qc-v1",
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "bookSlug": config.slug,
        "chapter": chapter,
        "expectedSegmentCount": len(expected),
        "actualSegmentCount": len(actual),
        "missing": missing,
        "extra": extra,
        "rawDurationSec": round(raw_duration, 3),
        "expectedDurationSec": round(total_duration, 3),
        "composeDriftSec": round(compose_drift, 4),
        "warnings": warnings,
        "segments": segment_reports,
        "status": "PASS" if not warnings and not extra else "REVIEW",
    }
    report_path = paths.reports_dir(chapter) / f"000_{chapter_id(chapter)}.qc.json"
    atomic_write_json(report_path, report)
    report["reportPath"] = report_path.relative_to(repo_root).as_posix()
    return report
