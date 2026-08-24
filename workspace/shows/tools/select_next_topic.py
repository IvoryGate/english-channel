"""Select the next episode topic for an ELR series from the local topic backlog.

This script NEVER scrapes. It only reads local artifacts:
  - workspace/shows/<series>/topic_backlog.json   (candidate topics)
  - workspace/shows/<series>/episode_*/000_*.youtube.json  (already-produced titles → exclude)
  - workspace/dialogue_podcast_research/youtube_corpus/analysis/corpus_analysis.json  (trend signals)
  - .../analysis/trending_videos.json  (optional, fresher trend signals)

It scores each `planned` topic by trend signal + series fit + freshness, picks the
highest-scoring topic not yet produced, and writes a dated selection record so the
scriptwriting stage has a single source of truth for "what episode to write next".

Usage:
    python workspace/shows/tools/select_next_topic.py --show series_a
    python workspace/shows/tools/select_next_topic.py --show series_a --apply
        # --apply also flips the chosen topic's backlog status to "selected"
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
SHOWS_ROOT = REPO / "workspace" / "shows"
CORPUS_ANALYSIS = REPO / "workspace" / "dialogue_podcast_research" / "youtube_corpus" / "analysis" / "corpus_analysis.json"
TRENDING_VIDEOS = REPO / "workspace" / "dialogue_podcast_research" / "youtube_corpus" / "analysis" / "trending_videos.json"

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "do", "does", "for",
    "from", "get", "has", "have", "how", "i", "if", "in", "into", "is", "it",
    "learn", "like", "me", "more", "my", "of", "on", "or", "our", "so", "that",
    "the", "their", "this", "to", "up", "use", "was", "we", "what", "when",
    "with", "you", "your", "not", "but", "still", "actually", "without",
    "sounding", "sound", "every", "day", "only", "minutes", "english", "podcast",
    "conversation", "talk", "easy", "daily", "life", "fast", "learnenglish",
    "englishpodcast", "learnenglishpodcast",
}

LEVEL_BAND = {
    "series_a": "B1-B2",
    "series_b": "A2-B1",
    "series_c": "B2-C1",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text.lower())


def content_words(text: str) -> set[str]:
    return {w for w in words(text) if w not in STOP_WORDS and len(w) >= 3}


def produced_titles(series_dir: Path) -> list[dict[str, str]]:
    """Scan episode_*/youtube.json to learn which titles/slugs are already produced."""
    out: list[dict[str, str]] = []
    if not series_dir.is_dir():
        return out
    for ep_dir in sorted(series_dir.iterdir()):
        if not ep_dir.is_dir() or not ep_dir.name.startswith("episode_"):
            continue
        yj = next(ep_dir.glob("000_*.youtube.json"), None)
        if not yj or not yj.is_file():
            continue
        try:
            data = load_json(yj)
        except Exception:
            continue
        title = str(data.get("title") or data.get("hookText") or "").strip()
        slug = str(data.get("slug") or "")
        out.append({"episode": ep_dir.name, "title": title, "slug": slug})
    return out


def load_trend_signals() -> dict[str, Any]:
    """Read local research artifacts. Returns dict with keyword weights + hot titles."""
    signals: dict[str, Any] = {"keywords": {}, "hot_titles": [], "research_date": None}
    if CORPUS_ANALYSIS.is_file():
        analysis = load_json(CORPUS_ANALYSIS)
        for kw in analysis.get("cross_channel", {}).get("title_keywords", []):
            signals["keywords"][kw.get("term", "")] = int(kw.get("count", 0))
        for item in analysis.get("cross_channel", {}).get("top_hook_titles", []):
            signals["hot_titles"].append({
                "title": str(item.get("title", "")),
                "view_count": int(item.get("view_count", 0) or 0),
            })
    # trending_videos.json is fresher (post-scrape); prefer it when present
    if TRENDING_VIDEOS.is_file():
        trending = load_json(TRENDING_VIDEOS)
        for vid in trending.get("videos", []):
            signals["hot_titles"].append({
                "title": str(vid.get("title", "")),
                "view_count": int(vid.get("view_count", 0) or 0),
            })
        signals["research_date"] = trending.get("generated_at") or signals.get("research_date")
    return signals


def trend_signal(topic: dict[str, Any], signals: dict[str, Any]) -> dict[str, Any]:
    """How strongly a backlog topic matches real competitor trend signals (0..1)."""
    blob = " ".join([
        str(topic.get("publicTitle", "")),
        str(topic.get("learnerProblem", "")),
        str(topic.get("hookAngle", "")),
    ])
    tw = content_words(blob)
    if not tw:
        return {"score": 0.0, "matched_keywords": [], "matched_titles": []}
    # keyword frequency weight (capped)
    kw_weight = 0.0
    matched_kw: list[str] = []
    for term, count in signals.get("keywords", {}).items():
        if term in tw:
            kw_weight += min(count, 30)
            matched_kw.append(term)
    kw_norm = min(kw_weight / 120.0, 1.0)
    # hot-title match: does the topic share content words with a high-view title?
    title_weight = 0.0
    matched_titles: list[str] = []
    for hot in signals.get("hot_titles", []):
        hot_words = content_words(hot["title"])
        overlap = len(tw & hot_words)
        if overlap >= 2:
            view_norm = min(hot["view_count"] / 200_000.0, 1.0)
            title_weight += view_norm * (overlap / max(len(tw), 1))
            matched_titles.append(hot["title"])
    title_norm = min(title_weight / 3.0, 1.0)
    score = min(kw_norm * 0.45 + title_norm * 0.55, 1.0)
    return {"score": round(score, 4), "matched_keywords": matched_kw[:8], "matched_titles": matched_titles[:3]}


def title_overlap(a: str, b: str) -> bool:
    """True if two titles share enough content words to be 'the same topic'."""
    wa = content_words(a)
    wb = content_words(b)
    if not wa or not wb:
        return False
    overlap = len(wa & wb)
    return overlap >= max(2, min(len(wa), len(wb)) // 2)


def is_used(topic: dict[str, Any], produced: list[dict[str, str]]) -> str | None:
    """Return the episode id that already used this topic, or None."""
    topic_title = str(topic.get("publicTitle", ""))
    topic_slug = str(topic.get("slug", ""))
    for ep in produced:
        if topic_slug and ep["slug"] and topic_slug == ep["slug"]:
            return ep["episode"]
        if topic_title and ep["title"] and title_overlap(topic_title, ep["title"]):
            return ep["episode"]
    return None


def _recent_competitors(backlog: dict[str, Any], limit: int = 3) -> set[str]:
    """Competitor channels used by the most recently produced episodes (anti-clustering)."""
    done = [t for t in backlog.get("topics", []) if t.get("status") == "done" and t.get("producedEpisode")]
    done.sort(key=lambda t: str(t.get("producedEpisode", "")), reverse=True)
    return {str(t.get("sourceCompetitor", "")) for t in done[:limit] if t.get("sourceCompetitor")}


def score_topic(topic: dict[str, Any], signals: dict[str, Any], *, recent_competitors: set[str] | None = None) -> dict[str, Any]:
    ts = trend_signal(topic, signals)
    # small freshness proxy: topics with a hookAngle that names a concrete situation score a touch higher
    situational = 0.05 if re.search(r"\b(work|email|meeting|small talk|weekend|intro|no|feedback|mistake|silence)\b",
                                    str(topic.get("hookAngle", "")) + str(topic.get("learnerProblem", "")), re.I) else 0.0
    # anti-homogeneity: reward topics sourced from a DIFFERENT competitor than the last
    # few produced episodes, so we don't cluster on one channel's playbook.
    src = str(topic.get("sourceCompetitor", ""))
    diversity = 0.0
    if recent_competitors and src:
        diversity = 0.06 if src not in recent_competitors else -0.04
    total = max(0.0, min(ts["score"] + situational + diversity, 1.0))
    return {
        "trendSignal": ts["score"], "situationalBonus": situational,
        "sourceDiversityBonus": round(diversity, 4), "total": round(total, 4),
        "matched_keywords": ts["matched_keywords"], "matched_titles": ts["matched_titles"],
        "sourceCompetitor": src or None,
        "differentiationAngle": str(topic.get("differentiationAngle", "")) or None,
    }


def select_next(series: str, *, apply: bool = False) -> dict[str, Any]:
    series_dir = SHOWS_ROOT / series
    backlog_path = series_dir / "topic_backlog.json"
    if not backlog_path.is_file():
        raise FileNotFoundError(f"Missing backlog: {backlog_path}. Run refresh_topic_backlog.py first.")
    backlog = load_json(backlog_path)
    produced = produced_titles(series_dir)
    produced_eps = [p["episode"] for p in produced]
    signals = load_trend_signals()
    recent_competitors = _recent_competitors(backlog)

    candidates: list[dict[str, Any]] = []
    for topic in backlog.get("topics", []):
        status = str(topic.get("status", "planned"))
        used_by = is_used(topic, produced)
        if used_by:
            # auto-writeback: mark done if backlog still says planned/draft
            if status not in ("done", "used"):
                topic["status"] = "done"
                topic["producedEpisode"] = used_by
            continue
        if status == "done":
            continue
        sc = score_topic(topic, signals, recent_competitors=recent_competitors)
        candidates.append({"topic": topic, "score": sc, "status": status})

    if not candidates:
        # persist any auto-writebacks
        if apply:
            write_json(backlog_path, backlog)
        return {
            "schema": "elr-topic-selection-v1",
            "showId": series,
            "selectedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "selectedTopic": None,
            "reason": "no planned topics remain (all produced or done); run refresh_topic_backlog.py to add candidates",
            "producedEpisodes": produced_eps,
            "considered": [],
        }

    candidates.sort(key=lambda c: c["score"]["total"], reverse=True)
    chosen = candidates[0]

    record = {
        "schema": "elr-topic-selection-v1",
        "showId": series,
        "levelBand": LEVEL_BAND.get(series, ""),
        "selectedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "researchSource": {
            "corpus_analysis": CORPUS_ANALYSIS.is_file(),
            "trending_videos": TRENDING_VIDEOS.is_file(),
            "research_date": signals.get("research_date"),
        },
        "producedEpisodes": produced_eps,
        "antiHomogeneity": {
            "recentCompetitors": sorted(recent_competitors),
            "policy": "Trend signal informs demand; the scriptwriter must diverge in hook/angle/phrasing per differentiationAngle. Selection rotates across competitor sources to avoid clustering on one channel's playbook.",
        },
        "selectedTopic": {
            "id": chosen["topic"].get("id"),
            "slug": chosen["topic"].get("slug"),
            "publicTitle": chosen["topic"].get("publicTitle"),
            "learnerProblem": chosen["topic"].get("learnerProblem"),
            "hookAngle": chosen["topic"].get("hookAngle"),
            "status": chosen["topic"].get("status"),
            "sourceCompetitor": chosen["topic"].get("sourceCompetitor"),
            "sourceTitle": chosen["topic"].get("sourceTitle"),
            "sourceUrl": chosen["topic"].get("sourceUrl"),
            "differentiationAngle": chosen["topic"].get("differentiationAngle"),
        },
        "score": chosen["score"],
        "considered": [
            {"id": c["topic"].get("id"), "slug": c["topic"].get("slug"),
             "publicTitle": c["topic"].get("publicTitle"), "total": c["score"]["total"]}
            for c in candidates[:6]
        ],
    }

    if apply:
        chosen["topic"]["status"] = "selected"
        write_json(backlog_path, backlog)
        sel_path = series_dir / f"topic_selection_{record['selectedAt']}.json"
        write_json(sel_path, record)
        record["selectionRecord"] = sel_path.as_posix()

    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Pick the next episode topic for an ELR series from the local backlog (no scraping).")
    parser.add_argument("--show", required=True, choices=["series_a", "series_b", "series_c"])
    parser.add_argument("--apply", action="store_true", help="Flip the chosen topic to 'selected' and write a dated selection record.")
    args = parser.parse_args()
    record = select_next(args.show, apply=args.apply)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if record.get("selectedTopic"):
        return 0
    return 1  # nothing to select — caller should refresh backlog first


if __name__ == "__main__":
    raise SystemExit(main())
