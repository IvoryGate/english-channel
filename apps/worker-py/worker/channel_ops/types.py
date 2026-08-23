from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShowPolicy:
    show_id: str
    public_name: str
    level_band: str
    playlist_id: str


@dataclass(frozen=True)
class ArtifactFingerprint:
    kind: str
    path: Path
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class PublicationCandidate:
    show_id: str
    episode_id: str
    title: str
    description: str
    level_band: str
    playlist_id: str
    duration_sec: float
    artifacts: tuple[ArtifactFingerprint, ...]

    def fingerprint(self, kind: str) -> ArtifactFingerprint:
        for artifact in self.artifacts:
            if artifact.kind == kind:
                return artifact
        raise KeyError(kind)


@dataclass(frozen=True)
class PublicationRecord:
    show_id: str
    episode_id: str
    title: str
    playlist_id: str
    mp4_sha256: str
    video_id: str
    status: str
    scheduled_at: str | None = None


@dataclass(frozen=True)
class ReleaseSlot:
    show_id: str
    episode_id: str
    scheduled_at: str


@dataclass(frozen=True)
class PreflightResult:
    candidate: PublicationCandidate
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    existing_video_id: str | None = None

    @property
    def ok(self) -> bool:
        return not self.errors
