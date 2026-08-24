"""Master ELR dialogue episode audio after turn QC approval.

Pipeline (see docs/shows/AUDIO_MASTERING.md):
  per-turn: highpass + mild afftdn + soft compress + limiter
  concat with inter-turn gaps
  two-pass EBU R128 loudnorm → master.wav + report.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from episode_artifacts import turn_wav_path, master_turn_wav_path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _run_capture(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return (proc.stderr or "") + (proc.stdout or "")


def probe_duration_sec(path: Path) -> float:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(out.stdout.strip())


def measure_loudness(path: Path) -> dict[str, float]:
    """Single-pass loudnorm print format to read integrated / true peak / LRA."""
    text = _run_capture(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ]
    )
    match = re.search(r"\{\s*\"input_i\".*?\}", text, flags=re.S)
    if not match:
        # ffmpeg prints JSON after a summary line; take last JSON object
        matches = list(re.finditer(r"\{[^{}]*\"input_i\"[^{}]*\}", text, flags=re.S))
        if not matches:
            raise RuntimeError(f"loudnorm measurement failed for {path}\n{text[-2000:]}")
        match = matches[-1]
    payload = json.loads(match.group(0))
    return {
        "integratedLufs": float(payload["input_i"]),
        "truePeakDb": float(payload["input_tp"]),
        "lra": float(payload["input_lra"]),
        "threshold": float(payload["input_thresh"]),
    }


def loudnorm_two_pass(src: Path, dest: Path, *, integrated: float = -16.0, true_peak: float = -1.5, lra: float = 11.0) -> dict[str, Any]:
    measure_text = _run_capture(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(src),
            "-af",
            f"loudnorm=I={integrated}:TP={true_peak}:LRA={lra}:print_format=json",
            "-f",
            "null",
            "-",
        ]
    )
    matches = list(re.finditer(r"\{[^{}]*\"input_i\"[^{}]*\}", measure_text, flags=re.S))
    if not matches:
        raise RuntimeError(f"loudnorm pass-1 failed\n{measure_text[-2000:]}")
    stats = json.loads(matches[-1].group(0))
    filt = (
        f"loudnorm=I={integrated}:TP={true_peak}:LRA={lra}:"
        f"measured_I={stats['input_i']}:"
        f"measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:"
        f"measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:"
        f"linear=true:print_format=summary"
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-af",
            filt,
            "-ar",
            "48000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )
    return {
        "targetIntegratedLufs": integrated,
        "targetTruePeakDb": true_peak,
        "targetLra": lra,
        "measured": {
            "integratedLufs": float(stats["input_i"]),
            "truePeakDb": float(stats["input_tp"]),
            "lra": float(stats["input_lra"]),
            "threshold": float(stats["input_thresh"]),
            "offset": float(stats["target_offset"]),
        },
    }


def per_turn_filter(*, denoise_nr: float, denoise_nf: float) -> str:
    # Conservative speech chain — see AUDIO_MASTERING.md
    return (
        "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,"
        "highpass=f=80,"
        f"afftdn=nr={denoise_nr}:nf={denoise_nf},"
        "acompressor=threshold=-18dB:ratio=2.5:attack=15:release=120:makeup=2,"
        "alimiter=limit=0.89:attack=5:release=50"
    )


def master_turn(src: Path, dest: Path, *, denoise_nr: float, denoise_nf: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-af",
            per_turn_filter(denoise_nr=denoise_nr, denoise_nf=denoise_nf),
            "-ar",
            "48000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )


def concat_turns(clips: list[Path], output: Path, *, gap_sec: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="elr_master_concat_") as tmp:
        tmp_dir = Path(tmp)
        list_file = tmp_dir / "concat.txt"
        lines: list[str] = []
        silence = tmp_dir / "gap.wav"
        if gap_sec > 0 and len(clips) > 1:
            _run(
                [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    f"anullsrc=r=48000:cl=mono",
                    "-t",
                    str(gap_sec),
                    "-c:a",
                    "pcm_s16le",
                    str(silence),
                ]
            )
        for index, clip in enumerate(clips):
            lines.append(f"file '{clip.resolve().as_posix()}'")
            if gap_sec > 0 and index < len(clips) - 1:
                lines.append(f"file '{silence.resolve().as_posix()}'")
        list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                str(output),
            ]
        )


def master_episode(
    *,
    manifest_path: Path,
    denoise_strength: float = 6.0,
    integrated_lufs: float = -16.0,
    true_peak_db: float = -1.5,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    workspace = manifest_path.parent
    episode_id = str(manifest["episodeId"])
    gap = float(manifest.get("renderSettings", {}).get("interTurnSilenceSec", 0.3))
    turns = list(manifest["turns"])
    clips = [turn_wav_path(workspace, str(t["filename"])) for t in turns]
    missing = [str(c) for c in clips if not c.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing turn WAVs: {missing[:5]}")

    # afftdn nr ~6 mild; map --denoise-strength 0..20
    denoise_nr = max(0.0, min(20.0, float(denoise_strength)))
    denoise_nf = -25.0

    master_dir = workspace / "audio" / "_master_turns"
    master_dir.mkdir(parents=True, exist_ok=True)
    cleaned: list[Path] = []
    for turn, clip in zip(turns, clips):
        out = master_turn_wav_path(workspace, str(turn["id"]), str(turn["filename"]))
        print(f"master turn {turn['id']} -> {out.name}", flush=True)
        master_turn(clip, out, denoise_nr=denoise_nr, denoise_nf=denoise_nf)
        cleaned.append(out)

    audio_dir = workspace / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    concat_path = audio_dir / f"000_{episode_id}.preloudnorm.wav"
    print(f"concat -> {concat_path.name} gap={gap}", flush=True)
    concat_turns(cleaned, concat_path, gap_sec=gap)

    raw_path = audio_dir / f"000_{episode_id}.raw.wav"
    master_path = audio_dir / f"000_{episode_id}.master.wav"
    print(f"loudnorm -> {master_path.name}", flush=True)
    ln = loudnorm_two_pass(
        concat_path,
        master_path,
        integrated=integrated_lufs,
        true_peak=true_peak_db,
    )

    before = measure_loudness(concat_path)
    after = measure_loudness(master_path)
    report = {
        "schema": "elr-episode-audio-master-v1",
        "episodeId": episode_id,
        "showId": manifest.get("showId"),
        "sourceTurns": len(clips),
        "gapSec": gap,
        "denoiseNr": denoise_nr,
        "denoiseNf": denoise_nf,
        "rawWav": str(raw_path).replace("\\", "/") if raw_path.is_file() else None,
        "preloudnormWav": str(concat_path).replace("\\", "/"),
        "masterWav": str(master_path).replace("\\", "/"),
        "durationSec": round(probe_duration_sec(master_path), 3),
        "loudnorm": ln,
        "measuredBeforeProgram": before,
        "measuredAfterProgram": after,
        "targets": {
            "integratedLufs": integrated_lufs,
            "truePeakDb": true_peak_db,
        },
    }
    report_path = workspace / "reports" / f"000_{episode_id}.master_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(report_path, report)
    print(f"report={report_path.as_posix()}", flush=True)
    print(
        f"LUFS {before['integratedLufs']:.2f} -> {after['integratedLufs']:.2f} | "
        f"TP {before['truePeakDb']:.2f} -> {after['truePeakDb']:.2f} dB",
        flush=True,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Master ELR episode turn WAVs to program loudness.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument(
        "--denoise-strength",
        type=float,
        default=6.0,
        help="afftdn nr (0–20). Default 6 = mild anti-metallic; raise only after listening.",
    )
    parser.add_argument("--integrated-lufs", type=float, default=-16.0)
    parser.add_argument("--true-peak-db", type=float, default=-1.5)
    args = parser.parse_args()
    master_episode(
        manifest_path=Path(args.manifest),
        denoise_strength=args.denoise_strength,
        integrated_lufs=args.integrated_lufs,
        true_peak_db=args.true_peak_db,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
