"""Measured turn/pause clock shared by episode mastering and its consumers."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from episode_artifacts import artifact_paths, load_json, master_turn_wav_path, turn_wav_path

TIMELINE_SCHEMA = "elr-measured-turn-timeline-v1"
TIMING_TOLERANCE_SEC = 0.05


def validated_gaps(count: int, default: float, gaps_sec: list[float] | None = None) -> list[float]:
    gaps = [default] * max(0, count - 1) if gaps_sec is None else list(gaps_sec)
    if len(gaps) != max(0, count - 1):
        raise ValueError("Expected one gap between each pair of turns")
    if isinstance(default, bool) or not math.isfinite(float(default)) or float(default) < 0:
        raise ValueError("Default gap must be finite and nonnegative")
    if any(isinstance(gap, bool) or not math.isfinite(float(gap)) or float(gap) < 0 for gap in gaps):
        raise ValueError("Turn gaps must be finite and nonnegative")
    return [float(gap) for gap in gaps]


def manifest_gaps(manifest: dict[str, Any], default: float | None = None) -> list[float]:
    turns = manifest["turns"]
    fallback = manifest.get("renderSettings", {}).get("interTurnSilenceSec", 0.3) if default is None else default
    return validated_gaps(len(turns), fallback, [turn.get("pauseAfterSec", fallback) for turn in turns[:-1]])


def wav_duration(path: Path) -> float:
    import soundfile as sf
    info = sf.info(str(path))
    if info.samplerate <= 0 or info.frames <= 0:
        raise ValueError(f"Empty or invalid turn audio: {path}")
    return float(info.frames / info.samplerate)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def timing_input_sha256(manifest: dict[str, Any]) -> str:
    payload = {"episodeId": manifest["episodeId"], "gapsSec": manifest_gaps(manifest),
               "turns": [{key: turn.get(key) for key in ("id", "filename", "speaker", "text")}
                         for turn in manifest["turns"]]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def measured_timeline(manifest: dict[str, Any], clips: list[Path], gaps_sec: list[float]) -> dict[str, Any]:
    turns = manifest["turns"]
    if not turns or len(turns) != len(clips):
        raise ValueError("Timeline requires one clip for each nonempty manifest turn")
    gaps = validated_gaps(len(clips), 0.0, gaps_sec)
    rows = []
    cursor = 0.0
    for index, (turn, clip) in enumerate(zip(turns, clips)):
        duration = wav_duration(clip)
        end = cursor + duration
        rows.append({"id": str(turn["id"]), "order": int(turn.get("order", index + 1)),
                     "filename": str(turn["filename"]), "speaker": str(turn.get("speaker", "")),
                     "section": str(turn.get("section", "")), "text": str(turn.get("text", "")),
                     "startSec": cursor, "endSec": end, "durationSec": duration,
                     "pauseAfterSec": gaps[index] if index < len(gaps) else 0.0})
        cursor = end + (gaps[index] if index < len(gaps) else 0.0)
    return {"schema": TIMELINE_SCHEMA, "gapsSec": gaps, "turns": rows, "durationSec": cursor}


def assert_program_duration(timeline: dict[str, Any], audio: Path) -> float:
    duration = wav_duration(audio)
    if abs(duration - float(timeline["durationSec"])) > TIMING_TOLERANCE_SEC:
        raise ValueError(f"Turn timeline does not match program audio: {timeline['durationSec']:.3f}s vs {duration:.3f}s")
    return duration


def master_timeline_record(manifest: dict[str, Any], clips: list[Path], audio: Path) -> dict[str, Any]:
    timeline = measured_timeline(manifest, clips, manifest_gaps(manifest))
    timeline["programDurationSec"] = assert_program_duration(timeline, audio)
    timeline.update(source="mastered-turns", timingInputSha256=timing_input_sha256(manifest),
                    programSha256=file_sha256(audio), turnSha256=[file_sha256(clip) for clip in clips])
    return timeline


def resolve_episode_timeline(workspace: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], list[Path]]:
    """Prefer actual mastered media; never substitute raw durations for a master.

    Legacy reports attest only uniform gaps and duration, not full provenance.
    New reports bind manifest timing/text and audio hashes; stale inputs fail.
    """
    paths = artifact_paths(workspace, str(manifest["episodeId"]))
    turns = manifest["turns"]
    if paths["masterWav"].is_file() or paths["masterReport"].is_file():
        if not paths["masterReport"].is_file() or not paths["masterWav"].is_file():
            raise FileNotFoundError("Master audio and its report are both required to resolve timing")
        report = load_json(paths["masterReport"])
        if report.get("episodeId") != manifest["episodeId"] or report.get("sourceTurns") != len(turns):
            raise ValueError("Master report episode/turn identity does not match manifest")
        clips = [master_turn_wav_path(workspace, str(turn["id"]), str(turn["filename"])) for turn in turns]
        recorded = report.get("timeline")
        if recorded is not None:
            if not isinstance(recorded, dict) or recorded.get("schema") != TIMELINE_SCHEMA:
                raise ValueError("Unsupported master timeline contract")
            if recorded.get("timingInputSha256") != timing_input_sha256(manifest):
                raise ValueError("Master timeline is stale: manifest timing or text changed")
            if recorded.get("programSha256") != file_sha256(paths["masterWav"]):
                raise ValueError("Master timeline is stale: program audio changed")
            if recorded.get("turnSha256") != [file_sha256(clip) for clip in clips]:
                raise ValueError("Master timeline is stale: mastered turn audio changed")
            gaps = manifest_gaps(manifest)
            if recorded.get("gapsSec") != gaps:
                raise ValueError("Master timeline gap record disagrees with manifest")
            source = "mastered-turns-hash-verified"
        else:
            if "gapSec" not in report:
                raise ValueError("Legacy master report has no recorded gap; cannot infer timing")
            gaps = validated_gaps(len(turns), report["gapSec"])
            source = "legacy-mastered-turns-duration-validated"
        timeline = measured_timeline(manifest, clips, gaps)
        actual = assert_program_duration(timeline, paths["masterWav"])
        reported_duration = float(report.get("durationSec", float("nan")))
        if not math.isfinite(reported_duration) or abs(reported_duration - actual) > TIMING_TOLERANCE_SEC:
            raise ValueError("Master report duration does not match program audio")
        timeline.update(source=source, programDurationSec=actual)
        return timeline, clips
    clips = [turn_wav_path(workspace, str(turn["filename"])) for turn in turns]
    timeline = measured_timeline(manifest, clips, manifest_gaps(manifest))
    timeline["source"] = "raw-turns-manifest-gaps"
    if paths["rawWav"].is_file():
        timeline["programDurationSec"] = assert_program_duration(timeline, paths["rawWav"])
    return timeline, clips
