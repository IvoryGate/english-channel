"""Mark a backlog topic as done after an episode is produced.

Writeback step: once an episode has been rendered/packed, flip the topic's status
to `done` and record which episode consumed it. This keeps the backlog a true source
of truth for "what's been produced" so select_next_topic.py never re-picks a used topic.

Usage:
    python workspace/shows/tools/mark_topic_done.py --show series_a --episode episode_003 --slug coasting_without_improving
    python workspace/shows/tools/mark_topic_done.py --show series_a --episode episode_003 --auto
        # --auto: infer the slug/title from the episode's youtube.json and match it to a backlog topic
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
SHOWS_ROOT = REPO / "workspace" / "shows"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _episode_youtube(series_dir: Path, episode: str) -> dict[str, Any]:
    yj = next((series_dir / episode).glob("000_*.youtube.json"), None)
    if not yj or not yj.is_file():
        raise FileNotFoundError(f"Missing youtube.json for {episode} in {series_dir}")
    return load_json(yj)


def mark_done(series: str, episode: str, *, slug: str | None = None, auto: bool = False) -> dict[str, Any]:
    series_dir = SHOWS_ROOT / series
    backlog_path = series_dir / "topic_backlog.json"
    if not backlog_path.is_file():
        raise FileNotFoundError(f"Missing backlog: {backlog_path}")
    backlog = load_json(backlog_path)

    target_slug = slug
    target_title: str | None = None
    if auto or not slug:
        yj = _episode_youtube(series_dir, episode)
        target_slug = target_slug or str(yj.get("slug") or "")
        target_title = str(yj.get("title") or yj.get("hookText") or "")

    matched: dict[str, Any] | None = None
    for topic in backlog.get("topics", []):
        t_slug = str(topic.get("slug", ""))
        if target_slug and t_slug and t_slug == target_slug:
            matched = topic
            break
    if matched is None and target_title:
        # fallback: content-word overlap (stop-word filtered so ELR title boilerplate
        # like "english podcast daily life conversation learn" does not match everything)
        import re
        STOP = {
            "a", "an", "and", "are", "as", "at", "be", "but", "by", "do", "does", "for",
            "from", "has", "have", "how", "i", "if", "in", "into", "is", "it", "learn",
            "like", "me", "more", "my", "of", "on", "or", "our", "so", "that", "the",
            "their", "this", "to", "up", "use", "was", "we", "what", "when", "with",
            "you", "your", "not", "but", "still", "actually", "without", "sounding",
            "sound", "every", "day", "only", "minutes", "english", "podcast",
            "conversation", "talk", "easy", "daily", "life", "fast", "learnenglish",
            "englishpodcast", "learnenglishpodcast", "everything", "people", "nervous",
        }
        def cwords(s: str) -> set[str]:
            return {w for w in re.findall(r"[a-z][a-z'-]*", s.lower()) if w not in STOP and len(w) >= 3}
        tw = cwords(target_title)
        best: tuple[int, dict[str, Any]] | None = None
        for topic in backlog.get("topics", []):
            bt = cwords(str(topic.get("publicTitle", ""))) | cwords(str(topic.get("learnerProblem", ""))) | cwords(str(topic.get("hookAngle", "")))
            overlap = len(tw & bt)
            if overlap >= 2 and (best is None or overlap > best[0]):
                best = (overlap, topic)
        if best:
            matched = best[1]

    if matched is None:
        return {
            "schema": "elr-topic-mark-done-v1",
            "showId": series,
            "episode": episode,
            "requestedSlug": target_slug,
            "matched": False,
            "reason": "no backlog topic matched slug/title; add it manually or run refresh_topic_backlog.py",
        }

    matched["status"] = "done"
    matched["producedEpisode"] = episode
    write_json(backlog_path, backlog)
    return {
        "schema": "elr-topic-done-v1",
        "showId": series,
        "episode": episode,
        "matched": True,
        "topic": {k: matched.get(k) for k in ("id", "slug", "publicTitle")},
        "backlog": backlog_path.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Mark a backlog topic done after an episode is produced.")
    parser.add_argument("--show", required=True, choices=["series_a", "series_b", "series_c"])
    parser.add_argument("--episode", required=True, help="Episode dir id, e.g. episode_003")
    parser.add_argument("--slug", help="Backlog topic slug to mark done")
    parser.add_argument("--auto", action="store_true", help="Infer slug/title from the episode youtube.json")
    args = parser.parse_args()
    if not args.slug and not args.auto:
        parser.error("provide --slug or --auto")
    result = mark_done(args.show, args.episode, slug=args.slug, auto=args.auto)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("matched") else 2


if __name__ == "__main__":
    raise SystemExit(main())
