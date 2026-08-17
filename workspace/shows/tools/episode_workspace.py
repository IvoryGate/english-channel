from __future__ import annotations

import re
from pathlib import Path


SERIES_ORDER = ("series_a", "series_b", "series_c")
_EPISODE_RE = re.compile(r"^(?:episode[_-]?)?(\d{1,3})$", re.IGNORECASE)


def normalize_episode_id(value: str | int) -> str:
    raw = str(value).strip()
    match = _EPISODE_RE.fullmatch(raw)
    if not match:
        raise ValueError(
            f"Invalid episode {value!r}; use a number or episode_NNN (for example 16 or episode_016)."
        )
    number = int(match.group(1))
    if number < 1 or number > 999:
        raise ValueError(f"Episode number must be between 1 and 999, got {number}.")
    return f"episode_{number:03d}"


def episode_number(value: str | int) -> int:
    return int(normalize_episode_id(value).rsplit("_", 1)[1])


def validate_show_id(show_id: str) -> str:
    normalized = show_id.strip().lower()
    if normalized not in SERIES_ORDER:
        raise ValueError(f"Unknown show {show_id!r}; expected one of {', '.join(SERIES_ORDER)}.")
    return normalized


def canonical_episode_workspace(repo_root: Path, show_id: str, episode: str | int) -> Path:
    show = validate_show_id(show_id)
    episode_id = normalize_episode_id(episode)
    return (repo_root.resolve() / "workspace" / "shows" / show / episode_id).resolve()


def assert_canonical_workspace(
    repo_root: Path,
    show_id: str,
    episode: str | int,
    workspace: Path,
) -> Path:
    expected = canonical_episode_workspace(repo_root, show_id, episode)
    actual = workspace.resolve()
    if actual != expected:
        raise ValueError(f"Non-canonical workspace: {actual}. Expected: {expected}.")
    return expected


def resolve_series(value: str) -> tuple[str, ...]:
    normalized = value.strip().lower()
    if normalized == "all":
        return SERIES_ORDER
    return (validate_show_id(normalized),)
