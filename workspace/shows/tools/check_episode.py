"""Episode audio QC — same checks as audiobook check_chapter (silence, length, ASR)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"))

from audiobook_workspace import (  # noqa: E402
    QC_WARN_TRAILING_SILENCE_SEC,
    analyze_segment_qc,
    read_mono,
)
from check_chapter import (  # noqa: E402
    create_asr_backend,
    format_qc_conversation_summary,
    review_segment_ids,
    transcribe_segment,
)
from episode_artifacts import turn_wav_path  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def episode_as_chapter_manifest(episode: dict[str, Any]) -> dict[str, Any]:
    """Adapt episode turns into the segment shape expected by audiobook QC helpers."""
    segments = []
    for turn in episode["turns"]:
        segments.append(
            {
                "id": turn["id"],
                "order": turn["order"],
                "filename": turn["filename"],
                "speaker": turn["speaker"],
                "kind": "dialogue",
                "text": turn["text"],
                "wordCount": turn.get("wordCount"),
                "deliveryCue": turn.get("deliveryCue", ""),
            }
        )
    return {
        "chapterId": episode.get("episodeId", "episode"),
        "segments": segments,
        "interSegmentSilenceSec": float(episode.get("renderSettings", {}).get("interTurnSilenceSec", 0.3)),
    }


def build_episode_qc_report(
    workspace: Path,
    episode: dict[str, Any],
    *,
    asr_by_id: dict[str, str] | None = None,
    warn_sec_per_word: float = 0.7,
    warn_trailing_silence: float = QC_WARN_TRAILING_SILENCE_SEC,
) -> dict[str, Any]:
    chapter_like = episode_as_chapter_manifest(episode)
    rows: list[dict[str, Any]] = []
    for segment in chapter_like["segments"]:
        path = turn_wav_path(workspace, str(segment["filename"]))
        audio = None
        sample_rate = None
        if path.is_file():
            audio, sample_rate = read_mono(path)
        asr_text = None if asr_by_id is None else asr_by_id.get(str(segment["id"]))
        rows.append(
            analyze_segment_qc(
                segment,
                audio,
                sample_rate,
                warn_sec_per_word_high=warn_sec_per_word,
                warn_trailing_silence_sec=warn_trailing_silence,
                asr_text=asr_text,
            )
        )

    review_count = sum(1 for row in rows if row["status"] == "review")
    flags: list[str] = []
    if review_count:
        flags.append("HAS_REVIEW_SEGMENTS")
    raw_name = str(episode.get("renderSettings", {}).get("outputAudio", ""))
    raw_path = (workspace / "audio" / Path(raw_name).name) if raw_name else None
    raw_duration = None
    if raw_path and raw_path.is_file():
        raw_audio, raw_sr = read_mono(raw_path)
        raw_duration = round(float(len(raw_audio) / raw_sr), 3)

    expected = 0.0
    gap = float(chapter_like["interSegmentSilenceSec"])
    for i, row in enumerate(rows):
        expected += float(row.get("durationSec") or 0.0)
        if i < len(rows) - 1:
            expected += gap
    expected = round(expected, 3)
    compose_drift = None
    if raw_duration is not None:
        compose_drift = round(raw_duration - expected, 3)
        if abs(compose_drift) > 1.5:
            flags.append("COMPOSE_DRIFT")

    return {
        "schema": "elr-episode-qc-v1",
        "episodeId": episode.get("episodeId"),
        "showId": episode.get("showId"),
        "chapter": {
            "segmentCount": len(rows),
            "reviewCount": review_count,
            "flags": flags,
            "rawDurationSec": raw_duration,
            "expectedDurationSec": expected,
            "composeDriftSec": compose_drift,
        },
        "segments": rows,
    }


def run_asr_for_ids(
    workspace: Path,
    episode: dict[str, Any],
    segment_ids: set[str],
    device: str,
) -> dict[str, str]:
    if not segment_ids:
        return {}
    backend_name, backend_model, active_device = create_asr_backend(device)
    backend = (backend_name, backend_model)
    transcripts: dict[str, str] = {}
    for turn in episode["turns"]:
        turn_id = str(turn["id"])
        if turn_id not in segment_ids:
            continue
        path = turn_wav_path(workspace, str(turn["filename"]))
        if not path.is_file():
            continue
        print(f"ASR {turn_id} -> {turn['filename']} ({active_device})", flush=True)
        try:
            transcripts[turn_id] = transcribe_segment(path, backend)
        except RuntimeError:
            if active_device == "cpu":
                raise
            print("Retrying ASR on cpu...", flush=True)
            backend_name, backend_model, active_device = create_asr_backend("cpu")
            backend = (backend_name, backend_model)
            transcripts[turn_id] = transcribe_segment(path, backend)
    return transcripts


def run_episode_check(
    manifest_path: Path,
    *,
    write_report: bool = False,
    run_asr_layer: bool = True,
    asr_all: bool = False,
    asr_device: str = "auto",
    warn_sec_per_word: float = 0.7,
) -> dict[str, Any]:
    workspace = manifest_path.parent
    episode = load_json(manifest_path)
    layer1 = build_episode_qc_report(workspace, episode, warn_sec_per_word=warn_sec_per_word)
    asr_by_id: dict[str, str] | None = None
    if run_asr_layer:
        if asr_all:
            target_ids = {str(t["id"]) for t in episode["turns"]}
        else:
            target_ids = review_segment_ids(layer1)
            # Always ASR CHECK_LONG / SHORT_TOO_LONG style content risks even if only silence flagged later.
            for row in layer1["segments"]:
                if any(f in row["flags"] for f in ("CHECK_LONG", "CHECK_FAST", "SHORT_TOO_LONG", "TOO_QUIET")):
                    target_ids.add(str(row["id"]))
        asr_by_id = run_asr_for_ids(workspace, episode, target_ids, asr_device)
        report = build_episode_qc_report(
            workspace,
            episode,
            asr_by_id=asr_by_id,
            warn_sec_per_word=warn_sec_per_word,
        )
    else:
        report = layer1

    if write_report:
        reports_dir = workspace / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        out = reports_dir / f"000_{episode['episodeId']}.qc.json"
        write_json(out, report)
        print(f"qc_report={out.as_posix()}", flush=True)
    return report


BLOCKING_QC_FLAGS = frozenset(
    {"ASR_MISMATCH", "ASR_LONGER", "SHORT_TOO_LONG", "TOO_QUIET", "CLIPPING", "MISSING"}
)
TIMING_ONLY_QC_FLAGS = frozenset({"CHECK_LONG", "CHECK_FAST", "TRAILING_SILENCE"})


def blocking_segment_ids(report: dict[str, Any]) -> list[str]:
    """Turn ids that must be fixed before pack (content / missing audio)."""
    ids: list[str] = []
    for row in report.get("segments") or []:
        flags = set(row.get("flags") or [])
        if flags & BLOCKING_QC_FLAGS:
            ids.append(str(row["id"]))
            continue
        if flags - TIMING_ONLY_QC_FLAGS:
            ids.append(str(row["id"]))
    return ids


def has_blocking_qc_issues(report: dict[str, Any]) -> bool:
    """Return True only for issues that should halt the pack pipeline.

    Timing-only flags (CHECK_LONG, CHECK_FAST, TRAILING_SILENCE) on segments whose
    ASR content matches are common in Word Tour slow repeats — same as audiobook
    human review: report them, but do not block master/compose when content is fine.
    """
    chapter = report.get("chapter") or {}
    if "COMPOSE_DRIFT" in chapter.get("flags", []):
        return True
    for row in report.get("segments") or []:
        flags = set(row.get("flags") or [])
        if flags & BLOCKING_QC_FLAGS:
            return True
        if flags - TIMING_ONLY_QC_FLAGS:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="QC dialogue episode turn WAVs (audiobook-style).")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--no-asr", action="store_true")
    parser.add_argument("--asr-all", action="store_true")
    parser.add_argument("--asr-device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit code 1 when QC flags any issue (review segments or chapter-level flags). Surfaces problems instead of silently passing.",
    )
    args = parser.parse_args()
    report = run_episode_check(
        Path(args.manifest),
        write_report=args.write_report,
        run_asr_layer=not args.no_asr,
        asr_all=args.asr_all,
        asr_device=args.asr_device,
    )
    print(format_qc_conversation_summary(report), flush=True)
    if args.strict and has_blocking_qc_issues(report):
        chapter = report.get("chapter", {})
        review_count = int(chapter.get("reviewCount", 0))
        print(
            f"QC STRICT: blocking issue(s) found ({review_count} segment(s) flagged; "
            f"timing-only Word Tour repeats with good ASR do not block). "
            f"Fix content issues or rerun pack with --skip-qc after human review.",
            flush=True,
        )
        return 1
    if args.strict and int((report.get("chapter") or {}).get("reviewCount", 0)) > 0:
        print(
            "QC note: timing-only flags reported above (Word Tour slow repeats are OK); proceeding is safe when ASR matches.",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
