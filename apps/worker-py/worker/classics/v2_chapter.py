from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from .aligned_subtitles import align_segment_files
from .audio_metrics import audio_texture_metrics
from .chapter_package import (
    CHAPTER_COPY,
    _normalized_concat_command,
    _validate_composed_video,
    channel_description_footer,
)
from .config import BookConfig
from .io import atomic_write_json, atomic_write_text, read_json, sha256_file
from .paths import ClassicPaths
from .v2_proof import (
    V2ProofError,
    _master_audio,
    _render_video,
    _run,
    scene_timeline,
    write_aligned_subtitles,
)


def _probe(repo_root: Path, path: Path) -> dict[str, Any]:
    return json.loads(
        _run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
                "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels",
                "-of", "json", str(path),
            ],
            cwd=repo_root,
        ).stdout
    )


def _youtube_timestamp(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _chapter_audio_source(
    paths: ClassicPaths, chapter: int, source_name: str
) -> tuple[Path, Path]:
    """Resolve canonical production audio or an isolated preview audio set."""
    if source_name == "production":
        return paths.segment_audio_dir(chapter), paths.raw_audio(chapter)
    return (
        paths.audio_dir(chapter) / "previews" / source_name / "segments",
        paths.audio_dir(chapter) / "previews" / f"{source_name}.wav",
    )


def _voice_variant_metadata(config: BookConfig, source_name: str) -> dict[str, Any]:
    """Describe the selected voice without inventing parameters for legacy previews."""
    metadata: dict[str, Any] = {"name": source_name}
    if source_name != "production":
        metadata["parametersSource"] = "preview-generation-trace"
        return metadata
    metadata.update(
        {
            "profileId": str(config.voice["profileId"]),
            "referenceSha256": str(config.voice["referenceSha256"]),
            "cfgValue": float(config.voice["cfgValue"]),
            "inferenceTimesteps": int(config.voice["inferenceTimesteps"]),
        }
    )
    return metadata


def _compose_final(repo_root: Path, inputs: list[Path], output: Path) -> None:
    if len(inputs) != 3:
        raise V2ProofError("Final V2 composition requires intro, body, and outro")
    _run(_normalized_concat_command(inputs, output), cwd=repo_root)
    _validate_composed_video(repo_root, inputs, output)


def recompose_v2_final(repo_root: Path, config: BookConfig, chapter: int) -> dict[str, Any]:
    paths = ClassicPaths(repo_root, config.slug)
    output_dir = paths.chapter(chapter) / "v2"
    base = f"000_chapter_{chapter:03d}.v2"
    body_video = output_dir / f"{base}.body.mp4"
    final_video = output_dir / f"{base}.mp4"
    required = [paths.intro_video(chapter), body_video, paths.outro_video(chapter)]
    if any(not path.is_file() for path in required):
        raise V2ProofError("V2 recompose inputs are incomplete")
    _compose_final(repo_root, required, final_video)
    export_dir = repo_root / "exports" / "youtube" / config.slug / f"chapter-{chapter:02d}-v2"
    export_video = export_dir / f"persuasion-chapter-{chapter:02d}-v2.mp4"
    shutil.copy2(final_video, export_video)
    verification_path = output_dir / "verification.json"
    verification = read_json(verification_path)
    verification["verifiedAt"] = datetime.now(timezone.utc).isoformat()
    verification["videoSha256"] = sha256_file(final_video)
    verification["videoProbe"] = _probe(repo_root, final_video)
    verification["timelineValidation"] = _validate_composed_video(
        repo_root, required, final_video
    )
    verification["status"] = "EXPORTED_FOR_REVIEW"
    verification["compositionMethod"] = "timestamp-reset filter concat with full H.264/AAC re-encode"
    atomic_write_json(verification_path, verification)
    shutil.copy2(verification_path, export_dir / "verification.json")
    return verification


def _qc_variant_audio(
    repo_root: Path,
    config: BookConfig,
    manifest: dict[str, Any],
    segment_dir: Path,
    raw_audio: Path,
) -> dict[str, Any]:
    expected = [str(segment["filename"]) for segment in manifest["segments"]]
    actual = sorted(path.name for path in segment_dir.glob("*.wav"))
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    target_rate = int(config.render["sampleRate"])
    silence = float(config.render["interSegmentSilenceSec"])
    warnings: list[dict[str, Any]] = []
    segment_reports: list[dict[str, Any]] = []
    expected_duration = silence * max(0, len(expected) - 1)
    for segment in manifest["segments"]:
        path = segment_dir / str(segment["filename"])
        if not path.is_file():
            continue
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
        if word_count >= 3 and seconds_per_word < 0.16:
            flags.append("speech-too-fast")
        if word_count >= 3 and seconds_per_word > 1.35:
            flags.append("speech-too-slow-or-repeated")
        if peak >= 0.999:
            flags.append("clipping")
        if flags:
            warnings.append({"segment": str(segment["id"]), "flags": flags})
        expected_duration += duration
        segment_reports.append(
            {
                "id": str(segment["id"]),
                "durationSec": round(duration, 3),
                "secondsPerWord": round(seconds_per_word, 3),
                "peak": round(peak, 6),
                "sha256": sha256_file(path),
                "flags": flags,
            }
        )
    raw_info = sf.info(raw_audio)
    raw_duration = float(raw_info.frames / raw_info.samplerate)
    drift = abs(raw_duration - expected_duration)
    if drift > 0.05:
        warnings.append({"segment": None, "flags": ["compose-duration-drift"]})
    return {
        "schema": "classic-listening-variant-qc-v2",
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "expectedSegmentCount": len(expected),
        "actualSegmentCount": len(actual),
        "missing": missing,
        "extra": extra,
        "rawDurationSec": round(raw_duration, 3),
        "expectedDurationSec": round(expected_duration, 3),
        "composeDriftSec": round(drift, 4),
        "warnings": warnings,
        "segments": segment_reports,
        "status": "PASS" if not missing and not extra and not warnings else "REVIEW",
    }


def _write_youtube_package(
    repo_root: Path,
    config: BookConfig,
    chapter: int,
    final_video: Path,
    captions: Path,
    thumbnail: Path,
    intro_duration: float,
    body_duration: float,
) -> dict[str, Any]:
    copy = CHAPTER_COPY[chapter]
    outro_start = intro_duration + body_duration
    title = f"Persuasion Chapter {chapter}: {copy['hook']} | Jane Austen Full Audiobook"
    timestamps = [
        {"time": "0:00", "label": "Classic Listening introduction"},
        {"time": _youtube_timestamp(intro_duration), "label": f"Persuasion — Chapter {chapter}"},
        {"time": _youtube_timestamp(outro_start), "label": "Continue the story"},
    ]
    timestamp_text = "\n".join(f"{item['time']} {item['label']}" for item in timestamps)
    schedule_footer = channel_description_footer(repo_root)
    description = f"""Settle in for Chapter {chapter} of Jane Austen's Persuasion, warmly narrated in clear English by the English Listening Room.

{copy['summary']}

This complete chapter includes synchronized English subtitles and warm, story-led Regency scenes, making it suitable for relaxed listening and reading along.

TIMESTAMPS
{timestamp_text}

BOOK
Persuasion by Jane Austen
First published in 1817
Source text: Project Gutenberg eBook 105
The source text is public domain in the USA. Viewers outside the USA should check the laws of their country before downloading or redistributing the text.

Subscribe to the English Listening Room and continue the story with the next chapter.

{schedule_footer}

#JaneAusten #Persuasion #Audiobook #ClassicLiterature #EnglishListening"""
    tags = [
        "Persuasion audiobook", "Jane Austen audiobook", f"Persuasion chapter {chapter}",
        "full audiobook", "classic audiobook", "English audiobook", "English listening practice",
        "audiobook with subtitles", "public domain audiobook", "British literature", "Regency novel",
        "English Listening Room", *copy["keywords"],
    ]
    export_dir = repo_root / "exports" / "youtube" / config.slug / f"chapter-{chapter:02d}-v2"
    export_dir.mkdir(parents=True, exist_ok=True)
    video_name = f"persuasion-chapter-{chapter:02d}-v2.mp4"
    caption_name = f"persuasion-chapter-{chapter:02d}-v2.srt"
    thumbnail_name = f"persuasion-chapter-{chapter:02d}-thumbnail.png"
    shutil.copy2(final_video, export_dir / video_name)
    shutil.copy2(captions, export_dir / caption_name)
    shutil.copy2(thumbnail, export_dir / thumbnail_name)
    atomic_write_text(export_dir / "title.txt", title)
    atomic_write_text(export_dir / "description.txt", description)
    atomic_write_text(export_dir / "tags.txt", ", ".join(tags))
    atomic_write_text(
        export_dir / "upload-checklist.md",
        f"""# YouTube upload checklist — Persuasion Chapter {chapter} V2

- [ ] Upload `{video_name}`
- [ ] Apply `title.txt` and `description.txt`
- [ ] Add `{thumbnail_name}`
- [ ] Upload English captions from `{caption_name}`
- [ ] Confirm language: English
- [ ] Confirm category: Education
- [ ] Confirm not made for kids
- [ ] Review timestamps, transitions, and end-screen placement
- [ ] Publish or schedule manually
""",
    )
    package = {
        "schema": "classic-listening-youtube-package-v2",
        "book": config.title,
        "author": config.author,
        "chapter": chapter,
        "title": title,
        "description": description,
        "tags": tags,
        "timestamps": timestamps,
        "language": "en",
        "category": "Education",
        "visibility": "private",
        "madeForKids": False,
        "video": video_name,
        "thumbnail": thumbnail_name,
        "captions": caption_name,
    }
    atomic_write_json(export_dir / "youtube-package.json", package)
    return {"directory": export_dir, "package": package}


def build_v2_chapter(
    repo_root: Path,
    config: BookConfig,
    chapter: int,
    preview_name: str,
    scene_manifest_path: Path,
    *,
    transition_sec: float = 1.5,
    model_name: str = "base",
) -> dict[str, Any]:
    if chapter not in CHAPTER_COPY:
        raise V2ProofError(f"No reviewed YouTube copy for chapter {chapter}")
    paths = ClassicPaths(repo_root, config.slug)
    output_dir = paths.chapter(chapter) / "v2"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(paths.segments(chapter))
    selected_ids = [str(segment["id"]) for segment in manifest["segments"]]
    segment_dir, raw_audio = _chapter_audio_source(paths, chapter, preview_name)
    if not raw_audio.is_file():
        raise V2ProofError(f"Selected chapter audio is missing: {raw_audio}")
    scene_manifest = read_json(scene_manifest_path)
    scene_rows = scene_manifest.get("scenes")
    if not isinstance(scene_rows, list) or len(scene_rows) < 2:
        raise V2ProofError("Scene manifest must contain at least two scenes")
    scenes = [(str(row["endSegmentId"]), repo_root / str(row["path"])) for row in scene_rows]
    if any(not image.is_file() for _, image in scenes):
        raise V2ProofError("One or more scene images are missing")

    audio_qc = _qc_variant_audio(repo_root, config, manifest, segment_dir, raw_audio)
    audio_qc_path = output_dir / "audio-qc.json"
    atomic_write_json(audio_qc_path, audio_qc)
    if audio_qc["missing"] or audio_qc["extra"]:
        raise V2ProofError("Selected audio set is incomplete or contains orphan files")

    silence = float(config.render["interSegmentSilenceSec"])
    alignment = align_segment_files(
        manifest, segment_dir, selected_ids, silence_sec=silence, model_name=model_name
    )
    base = f"000_chapter_{chapter:03d}.v2"
    body_srt, body_ass = write_aligned_subtitles(
        output_dir, alignment["cues"], base_name=f"{base}.body"
    )
    total_duration, boundaries = scene_timeline(
        manifest, segment_dir, selected_ids, [end_id for end_id, _ in scenes], silence
    )
    master_path = output_dir / f"{base}.master.wav"
    _master_audio(repo_root, config, raw_audio, master_path)
    body_video = output_dir / f"{base}.body.mp4"
    _render_video(
        repo_root,
        [image for _, image in scenes],
        master_path,
        body_ass,
        body_video,
        total_duration,
        boundaries,
        transition_sec,
    )

    intro = paths.intro_video(chapter)
    outro = paths.outro_video(chapter)
    if not intro.is_file() or not outro.is_file():
        raise V2ProofError("Approved chapter intro/outro files are missing")
    final_video = output_dir / f"{base}.mp4"
    final_inputs = [intro, body_video, outro]
    _compose_final(repo_root, final_inputs, final_video)
    timeline_validation = _validate_composed_video(repo_root, final_inputs, final_video)
    intro_duration = float(_probe(repo_root, intro)["format"]["duration"])
    shifted_cues = [
        {**cue, "start": float(cue["start"]) + intro_duration, "end": float(cue["end"]) + intro_duration}
        for cue in alignment["cues"]
    ]
    youtube_srt, _ = write_aligned_subtitles(
        output_dir, shifted_cues, base_name=f"{base}.youtube"
    )
    youtube = _write_youtube_package(
        repo_root,
        config,
        chapter,
        final_video,
        youtube_srt,
        paths.thumbnail(chapter),
        intro_duration,
        total_duration,
    )
    alignment_path = output_dir / "alignment-report.json"
    atomic_write_json(
        alignment_path,
        {
            "schema": "classic-listening-aligned-subtitles-v2",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "model": model_name,
            "introOffsetSec": intro_duration,
            "selectedSegmentIds": selected_ids,
            **alignment,
        },
    )
    final_probe = _probe(repo_root, final_video)
    verification = {
        "schema": "classic-listening-verification-v2",
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "chapter": chapter,
        "voiceVariant": _voice_variant_metadata(config, preview_name),
        "audioQcStatus": audio_qc["status"],
        "audioQcWarnings": audio_qc["warnings"],
        "audioTextureMetrics": audio_texture_metrics(master_path),
        "bodyDurationSec": round(total_duration, 3),
        "introDurationSec": round(intro_duration, 3),
        "subtitleCueCount": len(alignment["cues"]),
        "asrMeanSimilarity": round(
            sum(float(row["similarity"]) for row in alignment["segments"]) / len(alignment["segments"]), 4
        ),
        "asrReviewSegmentIds": [row["id"] for row in alignment["segments"] if row["status"] == "REVIEW"],
        "sceneCount": len(scenes),
        "sceneBoundariesSec": [round(value, 3) for value in boundaries],
        "transitionSec": transition_sec,
        "sourceSha256": sha256_file(paths.source_text(chapter)),
        "audioSha256": sha256_file(master_path),
        "videoSha256": sha256_file(final_video),
        "captionsSha256": sha256_file(youtube_srt),
        "thumbnailSha256": sha256_file(paths.thumbnail(chapter)),
        "sceneManifestSha256": sha256_file(scene_manifest_path),
        "videoProbe": final_probe,
        "timelineValidation": timeline_validation,
        "bodyVideo": body_video.relative_to(repo_root).as_posix(),
        "finalVideo": final_video.relative_to(repo_root).as_posix(),
        "bodyCaptions": body_srt.relative_to(repo_root).as_posix(),
        "youtubeCaptions": youtube_srt.relative_to(repo_root).as_posix(),
        "youtubeExport": youtube["directory"].relative_to(repo_root).as_posix(),
        "status": "EXPORTED_FOR_REVIEW",
    }
    verification_path = output_dir / "verification.json"
    atomic_write_json(verification_path, verification)
    shutil.copy2(verification_path, youtube["directory"] / "verification.json")
    verification["verificationPath"] = verification_path.relative_to(repo_root).as_posix()
    return verification
