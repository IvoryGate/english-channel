from __future__ import annotations

import json
import re
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import soundfile as sf

from .config import BookConfig
from .io import atomic_write_json, atomic_write_text, read_json, sha256_file
from .paths import ClassicPaths, chapter_id
from .qc import qc_chapter


class ChapterPackageError(RuntimeError):
    pass


CHAPTER_COPY = {
    1: {
        "hook": "A Family of Pride",
        "summary": "Meet Sir Walter Elliot, whose devotion to rank and appearance leaves the thoughtful Anne almost invisible inside her own family.",
        "keywords": ["Sir Walter Elliot", "Anne Elliot", "Kellynch Hall", "family pride"],
    },
    2: {
        "hook": "The Price of Pride",
        "summary": "Debt forces the Elliots to consider leaving Kellynch Hall, while Anne's sensible counsel is heard—and quietly set aside.",
        "keywords": ["Kellynch Hall", "Lady Russell", "Bath", "family debt"],
    },
    3: {
        "hook": "A Name Returns",
        "summary": "A possible naval tenant brings Admiral Croft into view and one long-remembered name back into Anne Elliot's world.",
        "keywords": ["Admiral Croft", "Captain Wentworth", "Royal Navy", "Kellynch Hall"],
    },
}


def channel_description_footer(repo_root: Path) -> str:
    programming_path = repo_root / "configs" / "channel" / "programming.json"
    try:
        programming = json.loads(programming_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ChapterPackageError(f"Channel programming config is unavailable: {programming_path}") from exc
    rows = programming.get("descriptionFooter")
    if not isinstance(rows, list) or not rows or any(
        not isinstance(row, str) or not row.strip() for row in rows
    ):
        raise ChapterPackageError("Channel programming descriptionFooter must contain non-empty strings")
    return "📅 New episodes on a fixed schedule:\n" + "\n".join(row.strip() for row in rows)


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise ChapterPackageError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr[-4000:]}")
    return result


def _timestamp(seconds: float, *, srt: bool = False) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    separator = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def _youtube_timestamp(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _subtitle_chunks(text: str, duration: float) -> list[tuple[str, float]]:
    lines = textwrap.wrap(text, width=58, break_long_words=False, break_on_hyphens=False) or [text]
    cues = ["\n".join(lines[index : index + 2]) for index in range(0, len(lines), 2)]
    weights = [max(1, len(re.sub(r"\s+", "", cue))) for cue in cues]
    total = sum(weights)
    return [(cue, duration * weight / total) for cue, weight in zip(cues, weights, strict=True)]


def write_subtitles(repo_root: Path, config: BookConfig, chapter: int) -> dict[str, Any]:
    paths = ClassicPaths(repo_root, config.slug)
    manifest = read_json(paths.segments(chapter))
    silence = float(config.render["interSegmentSilenceSec"])
    cursor = 0.0
    cues: list[dict[str, Any]] = []
    for index, segment in enumerate(manifest["segments"]):
        audio_path = paths.segment_audio_dir(chapter) / str(segment["filename"])
        if not audio_path.is_file():
            raise ChapterPackageError(f"Missing segment audio: {audio_path}")
        info = sf.info(audio_path)
        duration = float(info.frames / info.samplerate)
        for text, cue_duration in _subtitle_chunks(str(segment["displayText"]), duration):
            cues.append({"start": cursor, "end": cursor + cue_duration, "text": text})
            cursor += cue_duration
        if index < len(manifest["segments"]) - 1:
            cursor += silence

    srt_path = paths.subtitle_srt(chapter)
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_blocks = [
        f"{index}\n{_timestamp(cue['start'], srt=True)} --> {_timestamp(cue['end'], srt=True)}\n{cue['text']}"
        for index, cue in enumerate(cues, start=1)
    ]
    srt_path.write_text("\n\n".join(srt_blocks) + "\n", encoding="utf-8")

    ass_path = srt_path.with_suffix(".ass")
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 2560
PlayResY: 1440
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Georgia,62,&H00FFF9E9,&H00FFF9E9,&H002A1D17,&H76000000,-1,0,0,0,100,100,0,0,3,3,0,2,150,150,105,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for cue in cues:
        text = str(cue["text"]).replace("\n", r"\N").replace("{", r"\{").replace("}", r"\}")
        events.append(f"Dialogue: 0,{_timestamp(cue['start'])},{_timestamp(cue['end'])},Default,,0,0,0,,{text}")
    ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8-sig")
    return {"srt": srt_path, "ass": ass_path, "durationSec": cursor, "cueCount": len(cues)}


def master_audio(repo_root: Path, config: BookConfig, chapter: int, *, force: bool = False) -> Path:
    paths = ClassicPaths(repo_root, config.slug)
    raw_path = paths.raw_audio(chapter)
    output = paths.master_audio(chapter)
    if not raw_path.is_file():
        raise ChapterPackageError(f"Raw chapter audio is missing: {raw_path}")
    if output.is_file() and not force:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    target_lufs = float(config.mastering.get("integratedLufs", -16.0))
    target_peak = float(config.mastering.get("truePeakDb", -1.5))
    target_lra = float(config.mastering.get("loudnessRange", 11.0))
    _run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw_path),
            "-af", f"loudnorm=I={target_lufs}:TP={target_peak}:LRA={target_lra}",
            "-ar", str(config.render["sampleRate"]), "-ac", "1", "-c:a", "pcm_s24le", str(output),
        ],
        cwd=repo_root,
    )
    return output


def render_body_video(repo_root: Path, config: BookConfig, chapter: int, *, force: bool = False) -> Path:
    paths = ClassicPaths(repo_root, config.slug)
    output = paths.body_video(chapter)
    if output.is_file() and not force:
        return output
    backgrounds = config.visual.get("chapterBackgrounds")
    if not isinstance(backgrounds, dict) or str(chapter) not in backgrounds:
        raise ChapterPackageError(f"No visual.chapterBackgrounds entry for chapter {chapter}")
    background = config.repo_path(repo_root, str(backgrounds[str(chapter)]))
    master = paths.master_audio(chapter)
    ass_path = paths.subtitle_srt(chapter).with_suffix(".ass")
    if not background.is_file() or not master.is_file() or not ass_path.is_file():
        raise ChapterPackageError("Body video inputs are incomplete")
    output.parent.mkdir(parents=True, exist_ok=True)
    ass_filter_path = ass_path.relative_to(repo_root).as_posix().replace(":", r"\:")
    video_filter = (
        "scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,"
        "drawbox=x=0:y=1030:w=2560:h=410:color=0x2b1c16@0.18:t=fill,"
        f"ass='{ass_filter_path}'"
    )
    _run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-i", str(background),
            "-i", str(master), "-vf", video_filter, "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-ac", "2", "-shortest", "-movflags", "+faststart", str(output),
        ],
        cwd=repo_root,
    )
    return output


def _probe(repo_root: Path, path: Path) -> dict[str, Any]:
    result = _run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-show_entries", "stream=codec_name,codec_type,width,height,sample_rate,channels", "-of", "json", str(path)],
        cwd=repo_root,
    )
    return json.loads(result.stdout)


def compose_final_video(repo_root: Path, config: BookConfig, chapter: int, *, force: bool = False) -> Path:
    paths = ClassicPaths(repo_root, config.slug)
    output = paths.final_video(chapter)
    if output.is_file() and not force:
        return output
    inputs = [paths.intro_video(chapter), paths.body_video(chapter), paths.outro_video(chapter)]
    if not all(path.is_file() for path in inputs):
        raise ChapterPackageError(f"Intro/body/outro inputs are incomplete for chapter {chapter}")
    list_path = paths.video_dir(chapter) / f".{chapter_id(chapter)}.concat.txt"
    list_path.write_text("\n".join(f"file '{path.resolve().as_posix()}'" for path in inputs) + "\n", encoding="utf-8")
    try:
        _run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", "-movflags", "+faststart", str(output)],
            cwd=repo_root,
        )
    finally:
        list_path.unlink(missing_ok=True)
    return output


def write_youtube_package(repo_root: Path, config: BookConfig, chapter: int) -> dict[str, Any]:
    if chapter not in CHAPTER_COPY:
        raise ChapterPackageError(f"No reviewed YouTube copy for chapter {chapter}")
    paths = ClassicPaths(repo_root, config.slug)
    copy = CHAPTER_COPY[chapter]
    video_probe = _probe(repo_root, paths.final_video(chapter))
    duration = float(video_probe["format"]["duration"])
    body_duration = float(_probe(repo_root, paths.body_video(chapter))["format"]["duration"])
    intro_duration = float(_probe(repo_root, paths.intro_video(chapter))["format"]["duration"])
    outro_start = intro_duration + body_duration
    title = f"Persuasion Chapter {chapter}: {copy['hook']} | Jane Austen Full Audiobook"
    if len(title) > 100:
        raise ChapterPackageError(f"YouTube title exceeds 100 characters: {title}")
    timestamps = [
        {"time": "0:00", "label": "Classic Listening introduction"},
        {"time": _youtube_timestamp(intro_duration), "label": f"Persuasion — Chapter {chapter}"},
        {"time": _youtube_timestamp(outro_start), "label": "Continue the story"},
    ]
    timestamp_text = "\n".join(f"{item['time']} {item['label']}" for item in timestamps)
    schedule_footer = channel_description_footer(repo_root)
    description = f"""Settle in for Chapter {chapter} of Jane Austen's Persuasion, warmly narrated in clear English by the English Listening Room.

{copy['summary']}

This complete chapter includes synchronized English subtitles, making it suitable for relaxed listening, reading along, and thoughtful English practice.

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
        "Persuasion audiobook", "Jane Austen audiobook", f"Persuasion chapter {chapter}", "full audiobook",
        "classic audiobook", "English audiobook", "English listening practice", "audiobook with subtitles",
        "public domain audiobook", "British literature", "Regency novel", "English Listening Room", *copy["keywords"],
    ]
    report = {
        "schema": "classic-listening-youtube-package-v1",
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
        "durationSec": duration,
        "video": paths.final_video(chapter).relative_to(repo_root).as_posix(),
        "thumbnail": paths.thumbnail(chapter).relative_to(repo_root).as_posix(),
        "captions": paths.subtitle_srt(chapter).relative_to(repo_root).as_posix(),
    }
    atomic_write_json(paths.youtube_report(chapter), report)

    export_dir = repo_root / "exports" / "youtube" / config.slug / f"chapter-{chapter:02d}"
    export_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths.final_video(chapter), export_dir / f"persuasion-chapter-{chapter:02d}.mp4")
    shutil.copy2(paths.thumbnail(chapter), export_dir / f"persuasion-chapter-{chapter:02d}-thumbnail.png")
    shutil.copy2(paths.subtitle_srt(chapter), export_dir / f"persuasion-chapter-{chapter:02d}.srt")
    atomic_write_text(export_dir / "title.txt", title)
    atomic_write_text(export_dir / "description.txt", description)
    atomic_write_text(export_dir / "tags.txt", ", ".join(tags))
    checklist = f"""# YouTube upload checklist — Persuasion Chapter {chapter}

- [ ] Upload `persuasion-chapter-{chapter:02d}.mp4`
- [ ] Apply `title.txt` and `description.txt`
- [ ] Add `persuasion-chapter-{chapter:02d}-thumbnail.png`
- [ ] Upload English captions from `persuasion-chapter-{chapter:02d}.srt`
- [ ] Confirm language: English
- [ ] Confirm category: Education
- [ ] Confirm not made for kids
- [ ] Review timestamps and end-screen placement
- [ ] Publish or schedule manually
"""
    atomic_write_text(export_dir / "upload-checklist.md", checklist)
    shutil.copy2(paths.youtube_report(chapter), export_dir / "youtube-package.json")

    verification = {
        "schema": "classic-listening-verification-v1",
        "verifiedAt": datetime.now(timezone.utc).isoformat(),
        "chapter": chapter,
        "sourceSha256": sha256_file(paths.source_text(chapter)),
        "videoSha256": sha256_file(paths.final_video(chapter)),
        "thumbnailSha256": sha256_file(paths.thumbnail(chapter)),
        "captionsSha256": sha256_file(paths.subtitle_srt(chapter)),
        "videoProbe": video_probe,
        "titleLength": len(title),
        "exportDirectory": export_dir.relative_to(repo_root).as_posix(),
        "status": "EXPORTED",
    }
    atomic_write_json(paths.verification_report(chapter), verification)
    return {"youtube": report, "verification": verification, "exportDirectory": export_dir}


def package_chapter(repo_root: Path, config: BookConfig, chapter: int, *, force: bool = False) -> dict[str, Any]:
    paths = ClassicPaths(repo_root, config.slug)
    qc = qc_chapter(repo_root, config, chapter)
    master = master_audio(repo_root, config, chapter, force=force)
    subtitles = write_subtitles(repo_root, config, chapter)
    body = render_body_video(repo_root, config, chapter, force=force)
    final = compose_final_video(repo_root, config, chapter, force=force)
    youtube = write_youtube_package(repo_root, config, chapter)
    return {
        "chapter": chapter,
        "qcStatus": qc["status"],
        "qcWarnings": qc["warnings"],
        "master": master.relative_to(repo_root).as_posix(),
        "subtitles": {key: value.relative_to(repo_root).as_posix() if isinstance(value, Path) else value for key, value in subtitles.items()},
        "body": body.relative_to(repo_root).as_posix(),
        "video": final.relative_to(repo_root).as_posix(),
        "exportDirectory": youtube["exportDirectory"].relative_to(repo_root).as_posix(),
    }
