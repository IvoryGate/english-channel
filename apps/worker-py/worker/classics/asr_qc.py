from __future__ import annotations

import difflib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import BookConfig
from .io import atomic_write_json, read_json
from .paths import ClassicPaths, chapter_id


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def asr_qc_chapter(
    repo_root: Path,
    config: BookConfig,
    chapter: int,
    *,
    selected_ids: set[str] | None = None,
    model_name: str = "base",
) -> dict[str, Any]:
    from faster_whisper import WhisperModel

    paths = ClassicPaths(repo_root, config.slug)
    manifest = read_json(paths.segments(chapter))
    segments = [
        segment
        for segment in manifest["segments"]
        if not selected_ids or str(segment["id"]) in selected_ids
    ]
    model = WhisperModel(model_name, device="cpu", compute_type="int8", local_files_only=True, cpu_threads=4)
    results: list[dict[str, Any]] = []
    for segment in segments:
        audio_path = paths.segment_audio_dir(chapter) / str(segment["filename"])
        if not audio_path.is_file():
            continue
        transcription, _ = model.transcribe(str(audio_path), beam_size=3, vad_filter=True)
        heard = " ".join(item.text.strip() for item in transcription).strip()
        expected = str(segment["spokenText"])
        ratio = difflib.SequenceMatcher(None, _normalized(expected), _normalized(heard)).ratio()
        results.append(
            {
                "id": segment["id"],
                "expected": expected,
                "transcript": heard,
                "similarity": round(ratio, 4),
                "status": "PASS" if ratio >= 0.78 else "REVIEW",
            }
        )
    report = {
        "schema": "classic-listening-asr-qc-v1",
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "bookSlug": config.slug,
        "chapter": chapter,
        "model": model_name,
        "checkedSegmentCount": len(results),
        "reviewSegmentIds": [item["id"] for item in results if item["status"] == "REVIEW"],
        "meanSimilarity": round(sum(item["similarity"] for item in results) / len(results), 4) if results else 0,
        "segments": results,
    }
    report_path = paths.reports_dir(chapter) / f"000_{chapter_id(chapter)}.asr-qc.json"
    atomic_write_json(report_path, report)
    report["reportPath"] = report_path.relative_to(repo_root).as_posix()
    return report
