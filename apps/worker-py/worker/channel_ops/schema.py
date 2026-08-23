from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .types import PublicationRecord, ReleaseSlot, ShowPolicy


EPISODE_RE = re.compile(r"^(?:episode[_-]?)?(\d{1,3})$", re.IGNORECASE)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def normalize_episode_id(value: str | int) -> str:
    match = EPISODE_RE.fullmatch(str(value).strip())
    if not match:
        raise ValueError(f"Invalid episode {value!r}; expected a number or episode_NNN")
    number = int(match.group(1))
    if not 1 <= number <= 999:
        raise ValueError(f"Episode number must be between 1 and 999, got {number}")
    return f"episode_{number:03d}"


def load_policy(path: Path) -> tuple[dict[str, ShowPolicy], int, int]:
    raw = read_json(path)
    shows = raw.get("shows")
    if not isinstance(shows, dict) or not shows:
        raise ValueError(f"Policy has no shows: {path}")
    policies: dict[str, ShowPolicy] = {}
    for show_id, value in shows.items():
        if not isinstance(value, dict):
            raise ValueError(f"Invalid policy for {show_id}")
        policies[show_id] = ShowPolicy(
            show_id=show_id,
            public_name=str(value["publicName"]),
            level_band=str(value["levelBand"]),
            playlist_id=str(value["playlistId"]),
        )
    return (
        policies,
        int(raw.get("minChannelSpacingHours", 48)),
        int(raw.get("minSameSeriesSpacingHours", 168)),
    )

def parse_publication_records(raw: dict[str, Any]) -> tuple[PublicationRecord, ...]:
    records = raw.get("publications", [])
    if not isinstance(records, list):
        raise ValueError("Publication ledger field 'publications' must be a list")
    return tuple(
        PublicationRecord(
            show_id=str(item["showId"]),
            episode_id=normalize_episode_id(item["episodeId"]),
            title=str(item["title"]),
            playlist_id=str(item["playlistId"]),
            mp4_sha256=str(item["mp4Sha256"]).lower(),
            video_id=str(item["videoId"]),
            status=str(item["status"]),
            scheduled_at=item.get("scheduledAt"),
        )
        for item in records
    )


def parse_release_slots(raw: dict[str, Any]) -> tuple[ReleaseSlot, ...]:
    slots = raw.get("slots")
    if not isinstance(slots, list) or not slots:
        raise ValueError("Release plan field 'slots' must be a non-empty list")
    return tuple(
        ReleaseSlot(
            show_id=str(item["showId"]),
            episode_id=normalize_episode_id(item["episodeId"]),
            scheduled_at=str(item["scheduledAt"]),
        )
        for item in slots
    )
