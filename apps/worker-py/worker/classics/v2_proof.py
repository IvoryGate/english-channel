from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import soundfile as sf

from .aligned_subtitles import align_segment_files
from .config import BookConfig
from .io import atomic_write_json, atomic_write_text, read_json, sha256_file
from .paths import ClassicPaths


class V2ProofError(RuntimeError):
    pass


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise V2ProofError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr[-4000:]}")
    return result


def _timestamp(seconds: float, *, srt: bool = False) -> str:
    centiseconds = max(0, round(seconds * (1000 if srt else 100)))
    divisor = 1000 if srt else 100
    hours, remainder = divmod(centiseconds, 3600 * divisor)
    minutes, remainder = divmod(remainder, 60 * divisor)
    secs, fraction = divmod(remainder, divisor)
    if srt:
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{fraction:03d}"
    return f"{hours}:{minutes:02d}:{secs:02d}.{fraction:02d}"


def write_aligned_subtitles(
    output_dir: Path,
    cues: list[dict[str, Any]],
    *,
    base_name: str = "persuasion-chapter-01-v2-proof",
) -> tuple[Path, Path]:
    srt_path = output_dir / f"{base_name}.srt"
    ass_path = output_dir / f"{base_name}.ass"
    srt_blocks = [
        f"{index}\n{_timestamp(float(cue['start']), srt=True)} --> {_timestamp(float(cue['end']), srt=True)}\n{cue['text']}"
        for index, cue in enumerate(cues, start=1)
    ]
    atomic_write_text(srt_path, "\n\n".join(srt_blocks))
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 2560
PlayResY: 1440
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Georgia,62,&H00FFF9E9,&H00FFF9E9,&H002A1D17,&H84000000,-1,0,0,0,100,100,0,0,3,3,0,2,170,170,105,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    for cue in cues:
        text = str(cue["text"]).replace("\n", r"\N").replace("{", r"\{").replace("}", r"\}")
        events.append(
            f"Dialogue: 0,{_timestamp(float(cue['start']))},{_timestamp(float(cue['end']))},Default,,0,0,0,,{text}"
        )
    atomic_write_text(ass_path, header + "\n".join(events))
    return srt_path, ass_path


def scene_timeline(
    manifest: dict[str, Any],
    segment_dir: Path,
    selected_ids: list[str],
    scene_end_ids: list[str],
    silence_sec: float,
) -> tuple[float, list[float]]:
    if not scene_end_ids or scene_end_ids[-1] != selected_ids[-1]:
        raise V2ProofError("The final scene must end at the final selected segment")
    if any(segment_id not in selected_ids for segment_id in scene_end_ids):
        raise V2ProofError("Every scene end id must be a selected segment")
    by_id = {str(segment["id"]): segment for segment in manifest["segments"]}
    elapsed = 0.0
    boundaries: list[float] = []
    for index, segment_id in enumerate(selected_ids):
        path = segment_dir / str(by_id[segment_id]["filename"])
        info = sf.info(path)
        elapsed += float(info.frames / info.samplerate)
        if segment_id in scene_end_ids[:-1]:
            boundaries.append(elapsed + silence_sec / 2.0)
        if index < len(selected_ids) - 1:
            elapsed += silence_sec
    return elapsed, boundaries


def _master_audio(repo_root: Path, config: BookConfig, source: Path, output: Path) -> None:
    target_lufs = float(config.mastering.get("integratedLufs", -16.0))
    target_peak = float(config.mastering.get("truePeakDb", -1.5))
    target_lra = float(config.mastering.get("loudnessRange", 11.0))
    _run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
            "-af", f"loudnorm=I={target_lufs}:TP={target_peak}:LRA={target_lra}",
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", str(output),
        ],
        cwd=repo_root,
    )


def _render_video(
    repo_root: Path,
    images: list[Path],
    master_audio: Path,
    ass_path: Path,
    output: Path,
    total_duration: float,
    boundaries: list[float],
    transition_sec: float,
) -> None:
    if len(images) < 2 or len(boundaries) != len(images) - 1:
        raise V2ProofError("Scene images and transition boundaries do not match")
    durations = [boundaries[0] + transition_sec / 2.0]
    durations.extend(
        boundaries[index] - boundaries[index - 1] + transition_sec
        for index in range(1, len(boundaries))
    )
    durations.append(total_duration - boundaries[-1] + transition_sec / 2.0)
    if min(durations) <= transition_sec:
        raise V2ProofError("Scene duration is too short for the requested transition")
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for image, duration in zip(images, durations, strict=True):
        command.extend(["-loop", "1", "-framerate", "30", "-t", f"{duration:.6f}", "-i", str(image)])
    command.extend(["-i", str(master_audio)])
    ass_filter_path = ass_path.relative_to(repo_root).as_posix().replace(":", r"\:")
    x_positions = ["iw/2-(iw/zoom/2)", "iw-(iw/zoom)", "0"]
    filters: list[str] = []
    for index in range(len(images)):
        zoom_step = 0.000020 + (index % 4) * 0.000002
        zoom_limit = 1.030 + (index % 3) * 0.002
        filters.append(
            f"[{index}:v]scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,"
            f"zoompan=z='min(zoom+{zoom_step:.6f},{zoom_limit:.3f})':"
            f"x='{x_positions[index % len(x_positions)]}':y='ih/2-(ih/zoom/2)':"
            f"d=1:s=2560x1440:fps=30,setsar=1,format=yuv420p[v{index}]"
        )
    previous = "v0"
    for index, boundary in enumerate(boundaries, start=1):
        output_label = f"x{index}"
        filters.append(
            f"[{previous}][v{index}]xfade=transition=fade:duration={transition_sec:.3f}:"
            f"offset={boundary-transition_sec/2.0:.6f}[{output_label}]"
        )
        previous = output_label
    filters.append(f"[{previous}]ass='{ass_filter_path}'[vout]")
    command.extend(
        [
            "-filter_complex", ";".join(filters), "-map", "[vout]", "-map", f"{len(images)}:a:0",
            "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
            "-t", f"{total_duration:.6f}", "-movflags", "+faststart", str(output),
        ]
    )
    _run(command, cwd=repo_root)


def build_v2_proof(
    repo_root: Path,
    config: BookConfig,
    chapter: int,
    preview_name: str,
    selected_ids: list[str],
    scenes: list[tuple[str, Path]],
    *,
    transition_sec: float = 1.5,
    model_name: str = "base",
) -> dict[str, Any]:
    if chapter != 1:
        raise V2ProofError("The current review proof is intentionally limited to chapter 1")
    paths = ClassicPaths(repo_root, config.slug)
    output_dir = paths.workspace / "v2-proof"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(paths.segments(chapter))
    segment_dir = paths.audio_dir(chapter) / "previews" / preview_name / "segments"
    raw_audio = paths.audio_dir(chapter) / "previews" / f"{preview_name}.wav"
    images = [path if path.is_absolute() else repo_root / path for _, path in scenes]
    required = [raw_audio, *images]
    if any(not path.is_file() for path in required):
        missing = [str(path) for path in required if not path.is_file()]
        raise V2ProofError(f"Missing V2 proof input(s): {missing}")

    silence = float(config.render["interSegmentSilenceSec"])
    alignment = align_segment_files(
        manifest,
        segment_dir,
        selected_ids,
        silence_sec=silence,
        model_name=model_name,
    )
    srt_path, ass_path = write_aligned_subtitles(output_dir, alignment["cues"])
    total_duration, boundaries = scene_timeline(
        manifest, segment_dir, selected_ids, [end_id for end_id, _ in scenes], silence
    )
    master_path = output_dir / "persuasion-chapter-01-v2-proof.master.wav"
    _master_audio(repo_root, config, raw_audio, master_path)
    output_video = output_dir / "persuasion-chapter-01-v2-proof.mp4"
    _render_video(
        repo_root, images, master_path, ass_path, output_video, total_duration, boundaries, transition_sec
    )
    preview_copy = output_dir / "persuasion-chapter-01-v2-proof.raw.wav"
    shutil.copy2(raw_audio, preview_copy)

    alignment_report = {
        "schema": "classic-listening-aligned-subtitles-v2",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "model": model_name,
        "selectedSegmentIds": selected_ids,
        **alignment,
    }
    alignment_path = output_dir / "alignment-report.json"
    atomic_write_json(alignment_path, alignment_report)
    probe = json.loads(
        _run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
                "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
                "-of", "json", str(output_video),
            ],
            cwd=repo_root,
        ).stdout
    )
    report = {
        "schema": "classic-listening-v2-proof-v1",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "chapter": chapter,
        "voiceVariant": {"name": preview_name, "cfgValue": 1.9, "inferenceTimesteps": 16},
        "selectedSegmentIds": selected_ids,
        "durationSec": round(total_duration, 3),
        "subtitleCueCount": len(alignment["cues"]),
        "subtitleMethod": "faster-whisper word timestamps mapped to exact source display text",
        "transitionSec": transition_sec,
        "sceneBoundariesSec": [round(value, 3) for value in boundaries],
        "scenes": [
            {
                "endSegmentId": end_id,
                "path": image.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(image),
            }
            for (end_id, _), image in zip(scenes, images, strict=True)
        ],
        "audio": {
            "raw": preview_copy.relative_to(repo_root).as_posix(),
            "master": master_path.relative_to(repo_root).as_posix(),
            "rawSha256": sha256_file(preview_copy),
            "masterSha256": sha256_file(master_path),
        },
        "subtitles": {
            "srt": srt_path.relative_to(repo_root).as_posix(),
            "ass": ass_path.relative_to(repo_root).as_posix(),
        },
        "video": output_video.relative_to(repo_root).as_posix(),
        "videoSha256": sha256_file(output_video),
        "probe": probe,
    }
    report_path = output_dir / "v2-proof-report.json"
    atomic_write_json(report_path, report)
    report["reportPath"] = report_path.relative_to(repo_root).as_posix()
    return report
