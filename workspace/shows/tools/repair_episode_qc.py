"""Repair blocking QC turns without manual GPU re-render in agent shell.

Series C Word Tour mirror turns (single-word echoes like "Tangent.") often fail
SHORT_TOO_LONG. This tool:
  1. Runs layer-1 QC
  2. Trims trailing silence when that alone fixes SHORT_TOO_LONG
  3. Re-renders blocking turns one subprocess at a time (monitor parity)
  4. Re-composes raw.wav and re-checks (up to --max-rounds)

Use from pack_episode (auto) or manually:

  python workspace/shows/tools/repair_episode_qc.py \\
    --manifest workspace/shows/series_c/episode_013/000_episode_013.episode_manifest.json
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
DEFAULT_PYTHON = REPO / ".conda-env" / "python.exe"
RENDER_SCRIPT = TOOLS / "render_episode.py"

sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"))
sys.path.insert(0, str(REPO / "apps" / "worker-py"))

from audiobook_workspace import (  # noqa: E402
    QC_SHORT_TOO_LONG_SEC,
    QC_SHORT_WORD_LIMIT,
    SINGLE_WORD_MAX_LEN,
    analyze_segment_qc,
    normalize_segment_peak,
    read_mono,
    trailing_silence_sec,
)
from check_episode import (  # noqa: E402
    blocking_segment_ids,
    has_blocking_qc_issues,
    run_episode_check,
)
from episode_artifacts import turn_wav_path  # noqa: E402
from gpu_production_lock import GpuProductionLock  # noqa: E402
from prepare_reference_concat_audio import build_concat_audio  # noqa: E402
from worker.tts.trace import atomic_write_json, sha256_file, turn_trace_path  # noqa: E402


def compose_raw_wav(manifest_path: Path) -> Path:
    episode = load_json(manifest_path)
    workspace = manifest_path.parent
    settings = episode.get("renderSettings") or {}
    episode_id = str(episode["episodeId"])
    audio_dir = workspace / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    raw_path = audio_dir / f"000_{episode_id}.raw.wav"
    clips = [turn_wav_path(workspace, str(t["filename"])) for t in episode["turns"]]
    missing = [c.name for c in clips if not c.is_file()]
    if missing:
        raise FileNotFoundError(f"missing turn wavs: {missing[:5]}")
    gap = float(settings.get("interTurnSilenceSec", 0.3))
    build_concat_audio(clips, raw_path, gap_sec=gap)
    print(f"raw={raw_path.as_posix()} gap={gap}", flush=True)
    return raw_path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def segment_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in report.get("segments") or []}


def advance_seed_offsets(manifest: dict[str, Any], turn_ids: list[str], *, step: int = 1000) -> None:
    """Move blocking turns to a new deterministic sample before re-rendering."""
    selected = set(turn_ids)
    for turn in manifest.get("turns") or []:
        if str(turn.get("id")) not in selected:
            continue
        current = turn.get("ttsSeedOffset", 0)
        if not isinstance(current, int) or isinstance(current, bool):
            current = 0
        turn["ttsSeedOffset"] = current + step


def tighten_short_turn_caps(manifest: dict[str, Any]) -> int:
    """Ensure manifest maxLen caps match current policy (esp. single-word mirrors)."""
    updated = 0
    for turn in manifest.get("turns") or []:
        words = int(turn.get("wordCount") or 0)
        if words <= 0:
            continue
        if words == 1:
            cap = SINGLE_WORD_MAX_LEN
        elif words <= 4:
            cap = 48
        elif words <= 12:
            cap = 128
        else:
            continue
        if int(turn.get("maxLen") or cap) != cap:
            turn["maxLen"] = cap
            updated += 1
    return updated


def trim_trailing_silence(path: Path, *, tail_pad_sec: float = 0.12) -> bool:
    audio, sr = read_mono(path)
    if len(audio) == 0:
        return False
    peak = float(np.max(np.abs(audio)))
    if peak <= 0:
        return False
    threshold = peak * 0.02
    frame = max(1, int(sr * 0.02))
    end = len(audio)
    for start in range(len(audio) - frame, -1, -frame):
        chunk = audio[start : start + frame]
        if float(np.max(np.abs(chunk))) >= threshold:
            end = start + frame
            break
    pad = int(sr * tail_pad_sec)
    trimmed = audio[: min(len(audio), end + pad)]
    if len(trimmed) >= len(audio):
        return False
    # Turn WAVs are float PCM. Changing one repaired clip to PCM_16 makes the
    # concat demuxer interpret its packet size using the first clip's codec,
    # which can halve that clip in the composed raw track.
    _atomic_float_wav(path, trimmed, sr)
    return True


def try_trim_repair(
    workspace: Path,
    segment: dict[str, Any],
    manifest: dict[str, Any],
) -> bool:
    flags = set(segment.get("flags") or [])
    if "SHORT_TOO_LONG" not in flags and "TRAILING_SILENCE" not in flags:
        return False
    words = int(segment.get("wordCount") or 0)
    if words > QC_SHORT_WORD_LIMIT:
        return False
    path = turn_wav_path(workspace, str(segment["filename"]))
    if not path.is_file():
        return False
    before, sr = read_mono(path)
    if not trim_trailing_silence(path):
        return False
    after, _sr = read_mono(path)
    qc = analyze_segment_qc(segment, after, sr)
    ok = "SHORT_TOO_LONG" not in qc.get("flags", [])
    if ok:
        output_hash = sha256_file(path)
        trace_path = turn_trace_path(path)
        if trace_path.is_file():
            trace = load_json(trace_path)
            trace["durationSec"] = round(float(len(after) / sr), 3)
            trace["peak"] = round(float(np.max(np.abs(after))), 6)
            trace["outputSha256"] = output_hash
            transforms = list(trace.get("postProcessing") or [])
            transforms.append(
                {
                    "kind": "trailing-silence-trim",
                    "beforeDurationSec": round(float(len(before) / sr), 3),
                    "afterDurationSec": round(float(len(after) / sr), 3),
                }
            )
            trace["postProcessing"] = transforms
            atomic_write_json(trace_path, trace)
        turn_id = str(segment["id"])
        for rendered in manifest.get("rendered") or []:
            if str(rendered.get("id")) == turn_id:
                rendered["durationSec"] = round(float(len(after) / sr), 3)
                rendered["peak"] = round(float(np.max(np.abs(after))), 6)
                rendered["outputSha256"] = output_hash
                break
    print(
        f"trim {segment['id']} {len(before)/sr:.2f}s -> {len(after)/sr:.2f}s flags={qc.get('flags')} ok={ok}",
        flush=True,
    )
    return ok


def _atomic_float_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".wav", dir=path.parent)
    os.close(fd)
    try:
        sf.write(temp_name, audio.astype(np.float32, copy=False), sample_rate, subtype="FLOAT")
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def try_quiet_repair(
    workspace: Path,
    segment: dict[str, Any],
    manifest: dict[str, Any],
) -> bool:
    """Normalize valid but abnormally quiet speech without another TTS render."""
    if "TOO_QUIET" not in set(segment.get("flags") or []):
        return False
    path = turn_wav_path(workspace, str(segment["filename"]))
    trace_path = turn_trace_path(path)
    if not path.is_file() or not trace_path.is_file():
        return False
    audio, sr = read_mono(path)
    if len(audio) == 0:
        return False
    before_peak = float(np.max(np.abs(audio)))
    repaired = normalize_segment_peak(audio)
    after_peak = float(np.max(np.abs(repaired)))
    if after_peak <= before_peak:
        return False
    qc = analyze_segment_qc(segment, repaired, sr)
    if "TOO_QUIET" in qc.get("flags", []) or "CLIPPING" in qc.get("flags", []):
        return False

    _atomic_float_wav(path, repaired, sr)
    output_hash = sha256_file(path)
    trace = load_json(trace_path)
    trace["peak"] = round(after_peak, 6)
    trace["outputSha256"] = output_hash
    transforms = list(trace.get("postProcessing") or [])
    transforms.append(
        {
            "kind": "quiet-peak-normalization",
            "beforePeak": round(before_peak, 6),
            "afterPeak": round(after_peak, 6),
        }
    )
    trace["postProcessing"] = transforms
    atomic_write_json(trace_path, trace)

    turn_id = str(segment["id"])
    for rendered in manifest.get("rendered") or []:
        if str(rendered.get("id")) == turn_id:
            rendered["peak"] = round(after_peak, 6)
            rendered["outputSha256"] = output_hash
            break
    print(f"normalize {turn_id} peak={before_peak:.3f} -> {after_peak:.3f}", flush=True)
    return True


def repair_turn_encodings(workspace: Path, manifest: dict[str, Any]) -> int:
    """Restore legacy/non-float turn WAVs to the pipeline's float PCM contract."""
    repaired_count = 0
    for turn in manifest.get("turns") or []:
        path = turn_wav_path(workspace, str(turn["filename"]))
        if not path.is_file() or sf.info(path).subtype == "FLOAT":
            continue
        audio, sr = read_mono(path)
        _atomic_float_wav(path, audio, sr)
        output_hash = sha256_file(path)
        trace_path = turn_trace_path(path)
        if trace_path.is_file():
            trace = load_json(trace_path)
            trace["outputSha256"] = output_hash
            transforms = list(trace.get("postProcessing") or [])
            transforms.append({"kind": "restore-float-pcm"})
            trace["postProcessing"] = transforms
            atomic_write_json(trace_path, trace)
        turn_id = str(turn["id"])
        for rendered in manifest.get("rendered") or []:
            if str(rendered.get("id")) == turn_id:
                rendered["outputSha256"] = output_hash
                break
        repaired_count += 1
        print(f"encoding {turn_id} -> FLOAT", flush=True)
    return repaired_count


def rerender_turns(
    *,
    manifest_path: Path,
    turn_ids: list[str],
    python: Path,
    device: str,
    retry_on_failure: int,
) -> int:
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    env.pop("PYTORCH_CUDA_ALLOC_CONF", None)

    for turn_id in turn_ids:
        attempts = 1 + max(retry_on_failure, 0)
        for attempt in range(1, attempts + 1):
            cmd = [
                str(python),
                "-u",
                str(RENDER_SCRIPT),
                "--manifest",
                str(manifest_path.resolve()),
                "--segments",
                turn_id,
                "--device",
                device,
                "--no-compose",
                "--no-self-check",
            ]
            print(f"rerender {turn_id} attempt {attempt}/{attempts}", flush=True)
            proc = subprocess.run(cmd, cwd=str(REPO), env=env, text=True, capture_output=True)
            if proc.stdout:
                for line in proc.stdout.rstrip().splitlines()[-8:]:
                    print(f"  {line}", flush=True)
            if proc.stderr:
                for line in proc.stderr.rstrip().splitlines()[-8:]:
                    print(f"  err: {line}", flush=True)
            if proc.returncode == 0:
                break
            if attempt < attempts:
                print(f"  cooldown 20s before retry", flush=True)
                time.sleep(20)
                gc.collect()
            else:
                return int(proc.returncode)

    print("recompose raw.wav", flush=True)
    try:
        compose_raw_wav(manifest_path)
    except Exception as exc:
        print(f"compose failed: {exc}", flush=True)
        return 1
    return 0


def repair_episode_qc(
    manifest_path: Path,
    *,
    max_rounds: int = 3,
    device: str = "cuda",
    python: Path = DEFAULT_PYTHON,
    qc_no_asr: bool = True,
    retry_on_failure: int = 2,
    write_report: bool = True,
) -> tuple[int, dict[str, Any]]:
    workspace = manifest_path.parent
    episode = load_json(manifest_path)
    tighten_short_turn_caps(episode)
    encoding_repairs = repair_turn_encodings(workspace, episode)
    write_json(manifest_path, episode)
    if encoding_repairs:
        compose_raw_wav(manifest_path)

    report: dict[str, Any] = {}
    for round_idx in range(1, max_rounds + 1):
        report = run_episode_check(
            manifest_path,
            write_report=False,
            run_asr_layer=not qc_no_asr,
        )
        if not has_blocking_qc_issues(report):
            if write_report:
                out = workspace / "reports" / f"000_{episode['episodeId']}.qc.json"
                write_json(out, report)
            print(f"qc repair ok after round {round_idx - 1 if round_idx > 1 else 0}", flush=True)
            return 0, report

        ids = blocking_segment_ids(report)
        by_id = segment_by_id(report)
        print(f"qc repair round {round_idx}/{max_rounds} blocking={ids}", flush=True)

        still_blocking: list[str] = []
        manifest_changed = False
        audio_changed = False
        for turn_id in ids:
            seg = by_id.get(turn_id)
            if seg and try_quiet_repair(workspace, seg, episode):
                manifest_changed = True
                audio_changed = True
                continue
            if seg and try_trim_repair(workspace, seg, episode):
                audio_changed = True
                manifest_changed = True
                continue
            still_blocking.append(turn_id)

        if manifest_changed:
            write_json(manifest_path, episode)

        if audio_changed and not still_blocking:
            compose_raw_wav(manifest_path)

        if still_blocking:
            advance_seed_offsets(episode, still_blocking)
            write_json(manifest_path, episode)
            for turn_id in still_blocking:
                turn = next(t for t in episode["turns"] if str(t["id"]) == turn_id)
                wav = turn_wav_path(workspace, str(turn["filename"]))
                if wav.is_file():
                    wav.unlink()
            code = rerender_turns(
                manifest_path=manifest_path,
                turn_ids=still_blocking,
                python=python,
                device=device,
                retry_on_failure=retry_on_failure,
            )
            if code != 0:
                print(f"rerender failed exit={code}", flush=True)
                return code, report

    report = run_episode_check(manifest_path, write_report=False, run_asr_layer=not qc_no_asr)
    if write_report:
        out = workspace / "reports" / f"000_{episode['episodeId']}.qc.json"
        write_json(out, report)
    if has_blocking_qc_issues(report):
        print(f"qc repair exhausted rounds; still blocking: {blocking_segment_ids(report)}", flush=True)
        return 1, report
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-repair blocking episode QC turns (GPU-safe subprocess rerender).")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--with-asr", action="store_true", help="Run Whisper ASR during QC (slow).")
    parser.add_argument("--retry-on-failure", type=int, default=2)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument(
        "--no-gpu-lock",
        action="store_true",
        help="Caller already holds gpu_production.lock (e.g. pack_episode subprocess).",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    def _run() -> tuple[int, dict[str, Any]]:
        return repair_episode_qc(
            manifest_path,
            max_rounds=args.max_rounds,
            device=args.device,
            python=args.python,
            qc_no_asr=not args.with_asr,
            retry_on_failure=args.retry_on_failure,
            write_report=args.write_report,
        )

    if args.no_gpu_lock:
        code, _report = _run()
    else:
        with GpuProductionLock("repair_episode_qc"):
            code, _report = _run()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
