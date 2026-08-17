from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import parse_publication_records, read_json
from .types import PublicationRecord


class LocalEpisodeRepository:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def workspace(self, show_id: str, episode_id: str) -> Path:
        path = (
            self.repo_root / "workspace" / "shows" / show_id / episode_id
        ).resolve()
        expected_root = (self.repo_root / "workspace" / "shows").resolve()
        if expected_root not in path.parents:
            raise ValueError(f"Episode workspace escaped the repository: {path}")
        if not path.is_dir():
            raise FileNotFoundError(f"Episode workspace does not exist: {path}")
        return path

    def youtube_metadata(self, workspace: Path, episode_id: str) -> dict[str, Any]:
        return read_json(workspace / f"000_{episode_id}.youtube.json")

    def video_report(self, workspace: Path, episode_id: str) -> dict[str, Any]:
        return read_json(workspace / "reports" / f"000_{episode_id}.video_report.json")


class JsonPublicationRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> tuple[PublicationRecord, ...]:
        if not self.path.exists():
            return ()
        return parse_publication_records(read_json(self.path))

    def save(self, records: tuple[PublicationRecord, ...]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "elr-publication-ledger-v1",
            "publications": [
                {
                    "showId": item.show_id,
                    "episodeId": item.episode_id,
                    "title": item.title,
                    "playlistId": item.playlist_id,
                    "mp4Sha256": item.mp4_sha256,
                    "videoId": item.video_id,
                    "status": item.status,
                    "scheduledAt": item.scheduled_at,
                }
                for item in records
            ],
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        temporary.replace(self.path)

