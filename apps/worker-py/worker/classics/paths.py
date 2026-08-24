from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import SLUG_PATTERN, ConfigError


def chapter_id(chapter: int) -> str:
    if chapter < 1:
        raise ValueError("chapter must be >= 1")
    return f"chapter_{chapter:03d}"


@dataclass(frozen=True)
class ClassicPaths:
    repo_root: Path
    slug: str

    def __post_init__(self) -> None:
        if not SLUG_PATTERN.fullmatch(self.slug):
            raise ConfigError(f"Invalid book slug: {self.slug!r}")

    @property
    def workspace(self) -> Path:
        return self.repo_root / "workspace" / "classics" / self.slug

    @property
    def inventory(self) -> Path:
        return self.workspace / "000_book.inventory.json"

    @property
    def production(self) -> Path:
        return self.workspace / "000_book.production.json"

    @property
    def state(self) -> Path:
        return self.repo_root / "logs" / "classics_runs" / f"{self.slug}.json"

    def chapter(self, number: int) -> Path:
        return self.workspace / chapter_id(number)

    def source_text(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.chapter(number) / f"000_{cid}.source.txt"

    def segments(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.chapter(number) / f"000_{cid}.segments.json"

    def audio_dir(self, number: int) -> Path:
        return self.chapter(number) / "audio"

    def segment_audio_dir(self, number: int) -> Path:
        return self.audio_dir(number) / "segments"

    def raw_audio(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.audio_dir(number) / f"000_{cid}.raw.wav"

    def master_audio(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.audio_dir(number) / f"000_{cid}.master.wav"

    def reports_dir(self, number: int) -> Path:
        return self.chapter(number) / "reports"

    def subtitles_dir(self, number: int) -> Path:
        return self.chapter(number) / "subtitles"

    def video_dir(self, number: int) -> Path:
        return self.chapter(number) / "video"

    def subtitle_srt(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.subtitles_dir(number) / f"000_{cid}.srt"

    def body_video(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.video_dir(number) / f"000_{cid}.body.mp4"

    def final_video(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.video_dir(number) / f"000_{cid}.mp4"

    def thumbnail(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.video_dir(number) / f"000_{cid}.thumbnail.png"

    def intro_video(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.video_dir(number) / f"000_{cid}.intro.mp4"

    def outro_video(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.video_dir(number) / f"000_{cid}.outro.mp4"

    def youtube_report(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.reports_dir(number) / f"000_{cid}.youtube.json"

    def verification_report(self, number: int) -> Path:
        cid = chapter_id(number)
        return self.reports_dir(number) / f"000_{cid}.verification.json"
