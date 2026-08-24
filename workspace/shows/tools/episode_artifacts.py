from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def episode_prefix(episode_id: str) -> str:
    return f"000_{episode_id}"


def artifact_paths(workspace: Path, episode_id: str) -> dict[str, Path]:
    """Resolve every episode artifact to a structured subdirectory layout.

    Layout (episode root = workspace):
      <episode_id>/
        000_<episode_id>.draft.md                 # script stage (root, easy to find)
        000_<episode_id>.youtube.json              # script metadata (root)
        000_<episode_id>.episode_manifest.json     # render plan (root, control center)
        audio/
          turns/                                    # per-turn rendered WAVs (VoxCPM output)
            turn_001.wav
          _master_turns/                            # per-turn mastered WAVs
            p001_turn_001.wav
          000_<episode_id>.raw.wav                 # concatenated raw
          000_<episode_id>.master.wav              # mastered program
          000_<episode_id>.preloudnorm.wav          # intermediate
        video/
          000_<episode_id>.cover_source.png         # generated cover (text baked in)
          000_<episode_id>.video_bg_source.png      # generated no-text bg
          000_<episode_id>.thumbnail.png            # final thumbnail
          000_<episode_id>.video_bg.jpg             # final video bg
          000_<episode_id>.barwave.mov              # waveform overlay
          000_<episode_id>.mp4                      # final composed video
        subtitles/
          000_<episode_id>.words.json              # aligned words
          000_<episode_id>.karaoke.ass               # karaoke ASS
          000_<episode_id>.srt                      # SRT
        reports/
          000_<episode_id>.render_report.json
          000_<episode_id>.qc.json
          000_<episode_id>.master_report.json
          000_<episode_id>.subtitle_report.json
          000_<episode_id>.video_report.json
          000_<episode_id>.thumbnail_report.json
          000_<episode_id>.youtube_description.txt
          000_<episode_id>.meta.json
          000_<episode_id>._prompts.json
    """
    prefix = episode_prefix(episode_id)
    audio_dir = workspace / "audio"
    video_dir = workspace / "video"
    subs_dir = workspace / "subtitles"
    reports_dir = workspace / "reports"
    return {
        "workspace": workspace,
        # directories
        "audioDir": audio_dir,
        "videoDir": video_dir,
        "subtitlesDir": subs_dir,
        "reportsDir": reports_dir,
        "turnsDir": audio_dir / "turns",
        "masterTurnsDir": audio_dir / "_master_turns",
        # script stage (root)
        "draft": workspace / f"{prefix}.draft.md",
        "youtube": workspace / f"{prefix}.youtube.json",
        "manifest": workspace / f"{prefix}.episode_manifest.json",
        # audio stage
        "rawWav": audio_dir / f"{prefix}.raw.wav",
        "masterWav": audio_dir / f"{prefix}.master.wav",
        "preloudnormWav": audio_dir / f"{prefix}.preloudnorm.wav",
        # video stage
        "coverSource": video_dir / f"{prefix}.cover_source.png",
        "coverBakedScene": video_dir / f"{prefix}.cover_baked_16x9.png",
        "videoBgSource": video_dir / f"{prefix}.video_bg_source.png",
        "videoBgSource16x9": video_dir / f"{prefix}.video_bg_source_16x9.png",
        "thumbnailPng": video_dir / f"{prefix}.thumbnail.png",
        "videoBgJpg": video_dir / f"{prefix}.video_bg.jpg",
        "barwaveMov": video_dir / f"{prefix}.barwave.mov",
        "mp4": video_dir / f"{prefix}.mp4",
        # subtitles stage
        "wordsJson": subs_dir / f"{prefix}.words.json",
        "karaokeAss": subs_dir / f"{prefix}.karaoke.ass",
        "srt": subs_dir / f"{prefix}.srt",
        # reports stage
        "renderReport": reports_dir / f"{prefix}.render_report.json",
        "qcReport": reports_dir / f"{prefix}.qc.json",
        "masterReport": reports_dir / f"{prefix}.master_report.json",
        "subtitleReport": reports_dir / f"{prefix}.subtitle_report.json",
        "videoReport": reports_dir / f"{prefix}.video_report.json",
        "thumbnailReport": reports_dir / f"{prefix}.thumbnail_report.json",
        "youtubeDescription": reports_dir / f"{prefix}.youtube_description.txt",
        "meta": reports_dir / f"{prefix}.meta.json",
        "manifestScript": reports_dir / f"{prefix}.episode_manifest.script.json",
        "prompts": reports_dir / f"{prefix}._prompts.json",
    }


def turn_wav_path(workspace: Path, turn_filename: str) -> Path:
    """Resolve a turn's rendered WAV inside the episode audio/turns/ dir.

    turn_filename is stored bare in the manifest (e.g. "turn_001.wav"); we place
    the rendered file under audio/turns/ to keep the episode root clean.
    """
    return workspace / "audio" / "turns" / Path(turn_filename).name


def master_turn_wav_path(workspace: Path, turn_id: str, turn_filename: str) -> Path:
    """Resolve a mastered turn WAV inside audio/_master_turns/."""
    return workspace / "audio" / "_master_turns" / f"{turn_id}_{Path(turn_filename).name}"


def resolve_episode_audio(workspace: Path, episode_id: str, override: Path | None = None) -> Path:
    """Prefer mastered WAV for formal packs; fall back to raw for pilots."""
    if override is not None:
        return override
    paths = artifact_paths(workspace, episode_id)
    if paths["masterWav"].is_file():
        return paths["masterWav"]
    return paths["rawWav"]
