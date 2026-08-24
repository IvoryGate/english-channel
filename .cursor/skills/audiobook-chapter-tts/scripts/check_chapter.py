from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path
from typing import Any

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from audiobook_workspace import (
    QC_WARN_TRAILING_SILENCE_SEC,
    build_chapter_qc_report,
    chapter_qc_path,
    ensure_segment_defaults,
    load_json,
    manifest_path,
    write_json,
)

CONTENT_REVIEW_FLAGS = frozenset(
    {
        "ASR_MISMATCH",
        "ASR_LONGER",
        "ASR_SHORTER",
        "CHECK_LONG",
        "CHECK_FAST",
        "SHORT_TOO_LONG",
        "TOO_QUIET",
        "MISSING",
        "CLIPPING",
    }
)


def load_asr_backend(device: str) -> tuple[str, Any]:
    from faster_whisper import WhisperModel

    compute_type = "float16" if device == "cuda" else "int8"
    print(f"Loading faster-whisper base on {device} ({compute_type})...", flush=True)
    return ("faster-whisper", WhisperModel("base", device=device, compute_type=compute_type))


def create_asr_backend(device: str) -> tuple[str, Any, str]:
    candidates = ["cuda", "cpu"] if device in {"auto", "cuda"} else [device]
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            name, model = load_asr_backend(candidate)
            return name, model, candidate
        except Exception as exc:
            last_error = exc
            print(f"ASR device {candidate} unavailable: {exc}", flush=True)
    raise RuntimeError(
        "Could not initialize faster-whisper on any device. "
        "Install with: .\\.conda-env\\python.exe -m pip install faster-whisper"
    ) from last_error


def transcribe_segment(path: Path, backend: tuple[str, Any]) -> str:
    name, model = backend
    if name == "faster-whisper":
        segments, _info = model.transcribe(str(path), language="en", vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()
    raise RuntimeError(f"Unsupported ASR backend: {name}")


def run_asr(
    workspace: Path,
    manifest: dict[str, Any],
    segment_ids: set[str],
    device: str,
    *,
    verbose: bool = True,
) -> dict[str, str]:
    if not segment_ids:
        return {}

    try:
        from faster_whisper import WhisperModel  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is required for chapter QC layer 2. "
            "Install with: .\\.conda-env\\python.exe -m pip install faster-whisper"
        ) from exc

    backend_name, backend_model, active_device = create_asr_backend(device)
    backend: tuple[str, Any] = (backend_name, backend_model)
    transcripts: dict[str, str] = {}

    for segment in manifest["segments"]:
        segment_id = str(segment["id"])
        if segment_id not in segment_ids:
            continue
        path = workspace / str(segment["filename"])
        if not path.is_file():
            continue
        if verbose:
            print(f"ASR {segment_id} -> {segment['filename']} ({active_device})", flush=True)
        try:
            transcripts[segment_id] = transcribe_segment(path, backend)
        except RuntimeError as exc:
            if active_device == "cpu":
                raise
            if verbose:
                print(f"ASR failed on {active_device}: {exc}", flush=True)
                print("Retrying ASR on cpu...", flush=True)
            backend_name, backend_model, active_device = create_asr_backend("cpu")
            backend = (backend_name, backend_model)
            transcripts[segment_id] = transcribe_segment(path, backend)
    return transcripts


def review_segment_ids(report: dict[str, Any]) -> set[str]:
    return {str(segment["id"]) for segment in report["segments"] if segment["status"] == "review"}


def _segment_display_text(segment: dict[str, Any]) -> str:
    return str(segment.get("displayText") or segment.get("text", "")).strip()


def _format_segment_block(segment: dict[str, Any], *, show_asr: bool) -> list[str]:
    flags = ", ".join(segment["flags"])
    lines = [
        f"- **{segment['id']}** `{segment['filename']}` ({segment.get('durationSec')}s, {flags})",
        f"  原文: {_segment_display_text(segment)}",
    ]
    if show_asr and segment.get("asrText"):
        lines.append(f"  ASR: {str(segment['asrText']).strip()}")
        lines.append(f"  匹配度: {segment.get('asrMatchRatio')}")
    if segment.get("trailingSilenceSec") is not None:
        lines.append(f"  尾部静音: {segment['trailingSilenceSec']}s")
    return lines


def format_qc_conversation_summary(report: dict[str, Any]) -> str:
    chapter = report["chapter"]
    lines = [
        f"自检结果: {chapter['reviewCount']}/{chapter['segmentCount']} 个片段需关注。",
    ]
    if chapter["flags"]:
        lines.append(f"章节级: {', '.join(chapter['flags'])}")
    if chapter.get("composeDriftSec") is not None:
        lines.append(
            f"合成时长: raw {chapter.get('rawDurationSec')}s / 预期 {chapter.get('expectedDurationSec')}s "
            f"(偏差 {chapter.get('composeDriftSec')}s)"
        )

    review_segments = [segment for segment in report["segments"] if segment["status"] == "review"]
    if not review_segments:
        lines.append("未发现异常，可直接试听确认。")
        return "\n".join(lines)

    content_issues = [
        segment
        for segment in review_segments
        if any(flag in CONTENT_REVIEW_FLAGS for flag in segment["flags"])
    ]
    tail_issues = [
        segment
        for segment in review_segments
        if segment not in content_issues and "TRAILING_SILENCE" in segment["flags"]
    ]
    other_issues = [segment for segment in review_segments if segment not in content_issues and segment not in tail_issues]

    if content_issues:
        lines.append("")
        lines.append("内容异常（建议试听；尾部乱读/多读优先重渲染或裁剪）:")
        for segment in content_issues:
            show_asr = any(
                flag in segment["flags"] for flag in ("ASR_MISMATCH", "ASR_LONGER", "ASR_SHORTER", "CHECK_LONG")
            )
            lines.extend(_format_segment_block(segment, show_asr=show_asr))

    if tail_issues:
        lines.append("")
        lines.append("尾部静音 >1s（可选裁剪，一般问题不大）:")
        for segment in tail_issues:
            lines.extend(_format_segment_block(segment, show_asr=False))

    if other_issues:
        lines.append("")
        lines.append("其他:")
        for segment in other_issues:
            lines.extend(_format_segment_block(segment, show_asr=bool(segment.get("asrText"))))

    lines.append("")
    lines.append("请确认后再处理（重渲染 / 裁剪 / 跳过）。未确认前不要自动修改片段。")
    return "\n".join(lines)


def print_summary(report: dict[str, Any]) -> None:
    print(format_qc_conversation_summary(report), flush=True)


def run_chapter_check(
    workspace: Path,
    *,
    write_report: bool = False,
    run_asr_layer: bool = True,
    asr_all: bool = False,
    asr_device: str = "auto",
    warn_sec_per_word: float = 0.7,
    warn_trailing_silence: float = QC_WARN_TRAILING_SILENCE_SEC,
    verbose: bool = True,
) -> dict[str, Any]:
    manifest = ensure_segment_defaults(load_json(manifest_path(workspace)))
    thresholds = {
        "warnSecPerWordHigh": warn_sec_per_word,
        "warnTrailingSilenceSec": warn_trailing_silence,
    }

    layer1 = build_chapter_qc_report(workspace, manifest, thresholds=thresholds)
    asr_by_segment_id: dict[str, str] | None = None

    if run_asr_layer:
        if asr_all:
            target_ids = {str(segment["id"]) for segment in manifest["segments"]}
        else:
            target_ids = review_segment_ids(layer1)
        if verbose and target_ids:
            print(f"ASR targets={len(target_ids)} segments", flush=True)
        if target_ids:
            asr_by_segment_id = run_asr(
                workspace,
                manifest,
                target_ids,
                asr_device,
                verbose=verbose,
            )

    report = build_chapter_qc_report(
        workspace,
        manifest,
        asr_by_segment_id=asr_by_segment_id,
        thresholds=thresholds,
    )
    if write_report:
        output = chapter_qc_path(workspace)
        write_json(output, report)
        if verbose:
            print(f"output={output.as_posix()}", flush=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run automated QC checks on an audiobook chapter workspace.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--warn-sec-per-word", type=float, default=0.7)
    parser.add_argument("--warn-trailing-silence", type=float, default=QC_WARN_TRAILING_SILENCE_SEC)
    parser.add_argument(
        "--no-asr",
        action="store_true",
        help="Skip Whisper transcription on flagged segments (layer 1 only).",
    )
    parser.add_argument(
        "--asr-all",
        action="store_true",
        help="Transcribe every segment, not just flagged ones (slow).",
    )
    parser.add_argument("--asr-device", default="auto", help="Device for faster-whisper: auto, cuda, or cpu.")
    parser.add_argument("--write-report", action="store_true", help="Write 000_chapter_XXX.qc.json to disk.")
    parser.add_argument("--strict", action="store_true", help="Exit code 1 when any segment needs review.")
    args = parser.parse_args()

    report = run_chapter_check(
        Path(args.workspace),
        write_report=args.write_report,
        run_asr_layer=not args.no_asr,
        asr_all=args.asr_all,
        asr_device=args.asr_device,
        warn_sec_per_word=args.warn_sec_per_word,
        warn_trailing_silence=args.warn_trailing_silence,
        verbose=True,
    )
    print_summary(report)

    if args.strict and report["chapter"]["status"] == "review":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
