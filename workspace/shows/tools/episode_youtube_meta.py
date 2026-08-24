"""Single source of truth for episode YouTube title + hookText.

Draft frontmatter ``Title:`` is authoritative. ``youtube.json`` ``title`` and
``hookText`` are derived from it — agents should only hand-author cover scene /
outfit / tags fields, not duplicate the public title in a second wording.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from episode_artifacts import artifact_paths, load_json, write_json


def extract_draft_title(draft_path: Path) -> str:
    if not draft_path.is_file():
        return ""
    for line in draft_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("title:"):
            return stripped.split(":", 1)[1].strip().strip("\"'")
        if lower.startswith("title："):
            return stripped.split("：", 1)[1].strip().strip("\"'")
    return ""


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum() or ch.isspace()).strip()


def hook_text_matches_title(hook_text: str, title: str) -> bool:
    """True when hookText is a substring of title (pack gate, case/punct insensitive)."""
    n_hook = _norm(hook_text)
    n_title = _norm(title)
    if not n_hook or not n_title:
        return False
    return n_hook in n_title or n_title in n_hook


def derive_hook_text(title: str, show_id: str | None = None) -> str:
    """Extract the thumbnail / chapter intro hook from a full YouTube title.

    Series conventions (see docs/shows/series_*/bible.md):
    - series_a: ``Brand | Hook | Learn English`` → middle segment
    - series_b: ``Prefix — Hook | Easy English Podcast …`` → clause after em dash
    - series_c: ``Hook | Polished English Podcast …`` → first segment (may contain em dash)
    """
    title = title.strip()
    if not title:
        return ""

    parts = [p.strip() for p in title.split("|") if p.strip()]
    sid = (show_id or "").strip().lower()

    if sid == "series_a":
        if len(parts) >= 3:
            return parts[1]
        if len(parts) == 2:
            return parts[0]
        return title

    if sid == "series_c":
        return parts[0] if parts else title

    if sid == "series_b":
        head = parts[0] if parts else title
        for sep in (" — ", " – ", " - "):
            if sep in head:
                return head.split(sep, 1)[1].strip()
        return head

    # Generic fallback when show_id unknown.
    if len(parts) >= 3 and re.search(r"learn english", parts[-1], re.I):
        return parts[1]
    if len(parts) >= 2 and re.search(r"polished english podcast", parts[-1], re.I):
        return parts[0]
    head = parts[0] if parts else title
    for sep in (" — ", " – ", " - "):
        if sep in head:
            return head.split(sep, 1)[1].strip()
    return head


def sync_youtube_json(
    workspace: Path,
    episode_id: str,
    *,
    manifest: dict[str, Any] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Align youtube.json ``title`` + ``hookText`` with draft/manifest Title.

    Returns a report dict with keys: changed, title, hookText, path.
    """
    paths = artifact_paths(workspace, episode_id)
    youtube_path = paths["youtube"]
    youtube = load_json(youtube_path) if youtube_path.is_file() else {}
    created = not youtube_path.is_file()
    show_id = str((manifest or {}).get("showId") or youtube.get("showId") or "").strip()

    title = str((manifest or {}).get("title") or "").strip()
    if not title:
        title = extract_draft_title(paths["draft"])
    if not title:
        return {"changed": False, "reason": "missing_title", "path": str(youtube_path)}

    hook = derive_hook_text(title, show_id or None)
    if created:
        youtube = {
            "schema": "elr-youtube-episode-v1",
            "showId": show_id,
            "title": title,
            "hookText": hook,
            "description": str((manifest or {}).get("description") or "").strip(),
            "tags": [],
        }

    changed = created
    if str(youtube.get("title") or "").strip() != title:
        youtube["title"] = title
        changed = True
    if str(youtube.get("hookText") or "").strip() != hook:
        youtube["hookText"] = hook
        changed = True

    if changed and write:
        youtube_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(youtube_path, youtube)

    return {
        "changed": changed,
        "created": created,
        "title": title,
        "hookText": hook,
        "showId": show_id,
        "path": str(youtube_path),
    }
