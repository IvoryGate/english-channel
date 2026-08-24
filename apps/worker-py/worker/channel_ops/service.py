from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from .repo import JsonPublicationRepository, LocalEpisodeRepository
from .schema import normalize_episode_id
from .types import (
    ArtifactFingerprint,
    PreflightResult,
    PublicationCandidate,
    ReleaseSlot,
    ShowPolicy,
)


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def fingerprint(kind: str, path: Path) -> ArtifactFingerprint:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return ArtifactFingerprint(kind, path, path.stat().st_size, digest.hexdigest())


class PublicationPreflightService:
    def __init__(
        self,
        episodes: LocalEpisodeRepository,
        publications: JsonPublicationRepository,
        policies: dict[str, ShowPolicy],
    ) -> None:
        self.episodes = episodes
        self.publications = publications
        self.policies = policies

    def build_candidate(self, show_id: str, episode: str | int) -> PublicationCandidate:
        if show_id not in self.policies:
            raise ValueError(f"Unknown show {show_id!r}")
        policy = self.policies[show_id]
        episode_id = normalize_episode_id(episode)
        workspace = self.episodes.workspace(show_id, episode_id)
        stem = f"000_{episode_id}"
        metadata = self.episodes.youtube_metadata(workspace, episode_id)
        report = self.episodes.video_report(workspace, episode_id)
        title_path = workspace / "reports" / f"{stem}.youtube_title.txt"
        description_path = workspace / "reports" / f"{stem}.youtube_description.txt"
        paths = {
            "mp4": workspace / "video" / f"{stem}.mp4",
            "thumbnail": workspace / "video" / f"{stem}.thumbnail.png",
            "subtitles": workspace / "subtitles" / f"{stem}.srt",
            "title": title_path,
            "description": description_path,
            "youtube_metadata": workspace / f"{stem}.youtube.json",
        }
        missing = [str(path) for path in paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError("Missing publication artifacts: " + ", ".join(missing))
        title = title_path.read_text(encoding="utf-8").strip()
        description = description_path.read_text(encoding="utf-8").strip()
        if CJK_RE.search(title):
            raise ValueError(f"Title contains CJK characters: {title}")
        if CJK_RE.search(description):
            raise ValueError("Description contains CJK characters")
        if metadata.get("showId") != show_id:
            raise ValueError(
                f"youtube.json showId {metadata.get('showId')!r} does not match {show_id!r}"
            )
        if metadata.get("title") != title:
            raise ValueError("youtube.json title does not match the packaged title file")
        metadata_description = str(metadata.get("description", "")).strip()
        if not metadata_description or description.split("\n\n", 1)[0] != metadata_description:
            raise ValueError("youtube.json description does not match the packaged description")
        if policy.level_band not in title:
            raise ValueError(
                f"Title does not contain the expected CEFR band {policy.level_band}: {title}"
            )
        verification = report.get("verification")
        if not isinstance(verification, dict) or float(verification.get("durationSec", 0)) <= 0:
            raise ValueError("Video report has no positive verified duration")
        if int(verification.get("width", 0)) < 2560 or int(verification.get("height", 0)) < 1440:
            raise ValueError("Video report does not verify a minimum 2560x1440 frame")
        artifacts = tuple(fingerprint(kind, path) for kind, path in paths.items())
        return PublicationCandidate(
            show_id=show_id,
            episode_id=episode_id,
            title=title,
            description=description,
            level_band=policy.level_band,
            playlist_id=policy.playlist_id,
            duration_sec=float(verification["durationSec"]),
            artifacts=artifacts,
        )

    def preflight(self, show_id: str, episode: str | int) -> PreflightResult:
        candidate = self.build_candidate(show_id, episode)
        errors: list[str] = []
        warnings: list[str] = []
        existing_video_id: str | None = None
        mp4_hash = candidate.fingerprint("mp4").sha256
        for record in self.publications.list():
            same_episode = (
                record.show_id == candidate.show_id
                and record.episode_id == candidate.episode_id
            )
            if record.title.casefold() == candidate.title.casefold() and not same_episode:
                errors.append(
                    f"Title is already mapped to {record.show_id}/{record.episode_id} ({record.video_id})"
                )
            if record.mp4_sha256 == mp4_hash and not same_episode:
                errors.append(
                    f"MP4 fingerprint is already mapped to {record.show_id}/{record.episode_id} ({record.video_id})"
                )
            if same_episode:
                existing_video_id = record.video_id
                if record.mp4_sha256 != mp4_hash:
                    errors.append(
                        f"Canonical episode is mapped to {record.video_id} with a different MP4 fingerprint"
                    )
                elif record.playlist_id != candidate.playlist_id:
                    errors.append(
                        f"Canonical episode is mapped to the wrong playlist {record.playlist_id}"
                    )
                else:
                    warnings.append(
                        f"Idempotent resume: use existing video {record.video_id}; do not upload again"
                    )
        return PreflightResult(
            candidate=candidate,
            errors=tuple(errors),
            warnings=tuple(warnings),
            existing_video_id=existing_video_id,
        )


def validate_release_plan(
    slots: tuple[ReleaseSlot, ...],
    *,
    min_channel_spacing_hours: int,
    min_same_series_spacing_hours: int,
) -> tuple[str, ...]:
    errors: list[str] = []
    parsed: list[tuple[ReleaseSlot, datetime]] = []
    identities: set[tuple[str, str]] = set()
    for slot in slots:
        identity = (slot.show_id, slot.episode_id)
        if identity in identities:
            errors.append(f"Duplicate release slot for {slot.show_id}/{slot.episode_id}")
        identities.add(identity)
        try:
            parsed.append((slot, datetime.fromisoformat(slot.scheduled_at)))
        except ValueError:
            errors.append(f"Invalid ISO-8601 scheduledAt: {slot.scheduled_at}")
    parsed.sort(key=lambda item: item[1])
    for index, (slot, when) in enumerate(parsed):
        if index:
            previous_slot, previous_when = parsed[index - 1]
            hours = (when - previous_when).total_seconds() / 3600
            if hours < min_channel_spacing_hours:
                errors.append(
                    f"Only {hours:.1f}h between {previous_slot.show_id}/{previous_slot.episode_id} "
                    f"and {slot.show_id}/{slot.episode_id}; minimum is {min_channel_spacing_hours}h"
                )
        for earlier_slot, earlier_when in parsed[:index]:
            if earlier_slot.show_id == slot.show_id:
                hours = (when - earlier_when).total_seconds() / 3600
                if hours < min_same_series_spacing_hours:
                    errors.append(
                        f"Only {hours:.1f}h between releases for {slot.show_id}; "
                        f"minimum is {min_same_series_spacing_hours}h"
                    )
    return tuple(errors)
