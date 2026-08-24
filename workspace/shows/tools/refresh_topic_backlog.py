"""Refresh an ELR series topic backlog from LOCAL research artifacts (no scraping).

Reads:
  - analysis/episode_brief_suggestions.json   (curated topic clusters + show profiles)
  - analysis/corpus_analysis.json              (top_hook_titles, cross-channel keywords, per-channel top videos)
  - analysis/trending_videos.json             (optional fresher trending titles)
  - workspace/shows/<series>/topic_backlog.json (existing backlog — preserved)
  - workspace/shows/<series>/episode_*/000_*.youtube.json (produced titles — excluded)

Generates candidate topics, dedups against existing backlog + produced episodes, and
merges new candidates (status `planned`) into the backlog. Existing topics are never
overwritten; only appended. This script NEVER scrapes.

Usage:
    python workspace/shows/tools/refresh_topic_backlog.py --show series_a
    python workspace/shows/tools/refresh_topic_backlog.py --all
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
ANALYSIS_DIR = REPO / "workspace" / "dialogue_podcast_research" / "youtube_corpus" / "analysis"
BRIEFS_PATH = ANALYSIS_DIR / "episode_brief_suggestions.json"
CORPUS_ANALYSIS = ANALYSIS_DIR / "corpus_analysis.json"
TRENDING_VIDEOS = ANALYSIS_DIR / "trending_videos.json"

ARCHETYPE_TO_SERIES = {"A": "series_a", "B": "series_b", "C": "series_c"}
SERIES_BAND = {"series_a": "B1-B2", "series_b": "A2-B1", "series_c": "B2-C1"}

# Channel -> preferred ELR series. Authoritative when the channel's CEFR band is
# knowable from its brand; falls back to spine-keyword heuristics below. This is the
# primary anti-homogeneity lever: without it, one high-view "Easy English" channel
# floods series_b with clones of its own playbook.
CHANNEL_LEVEL_HINT = {
    # A2-B1 / easy / beginner channels -> series_b
    "speak english with class": "series_b",
    "speakenglishwithclass": "series_b",
    "english with hope": "series_b",
    "englishwithhopeee": "series_b",
    "speak english with david & alice": "series_b",
    "davidandaliceenglish": "series_b",
    "go english podcast": "series_b",
    "goenglishpodcast": "series_b",
    # B1-B2 / everyday conversational channels -> series_a
    "j and may podcast": "series_a",
    "jandmaypodcast": "series_a",
    "max & mia podcast": "series_a",
    "maxandmiapodcast": "series_a",
    "english conversation pod": "series_a",
    "englishconversationpod": "series_a",
    "english goal podcast": "series_a",
    "englishgoalpodcast": "series_a",
    "bbc learning english": "series_a",
    "bbclearningenglish": "series_a",
    # B2-C1 / advanced / professional channels -> series_c
    "high level listening advanced english podcast": "series_c",
    "highlevellistening": "series_c",
    "english unleashed: the podcast": "series_c",
    "englishpodcastunleashed": "series_c",
}

# Max candidates drawn from a single competitor channel per series per refresh.
# Prevents one high-view channel from dominating a series' backlog.
MAX_PER_CHANNEL_PER_SERIES = 3


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", value.lower().strip())
    return re.sub(r"_+", "_", value).strip("_") or "topic"


# Stop words for dedup. Includes ELR title boilerplate ("english", "podcast", "learn",
# "daily", "talk", "life", ...) so that the shared wrapper "English Podcast For <X> |
# Learn English" does NOT make every candidate collide with every existing topic.
# Without this filter, hot-title candidates are silently dropped as false duplicates
# and fresh research data never reaches the backlog.
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "do", "does", "for",
    "from", "get", "has", "have", "how", "i", "if", "in", "into", "is", "it",
    "me", "more", "my", "of", "on", "or", "our", "so", "that", "the", "their",
    "this", "to", "up", "use", "was", "we", "what", "when", "with", "you", "your",
    "not", "still", "actually", "without", "sounding", "sound", "every", "day",
    "only", "minutes", "fast", "real", "easy", "slow", "everyday", "intermediate",
    "beginner", "practice", "listening", "speak", "speaking", "fluent", "fluency",
    "level", "improve", "learn", "learning", "english", "podcast", "conversation",
    "talk", "daily", "life", "lesson", "lessons", "class", "course", "language",
    "b1", "b2", "c1", "a2", "people", "really", "very", "much", "lot", "things",
    "thing", "make", "made", "going", "gone", "been", "being", "had", "having",
    "did", "done", "doing", "say", "said", "says", "said", "tell", "told",
    "know", "knew", "known", "think", "thought", "want", "wanted", "need",
    "needed", "feel", "felt", "look", "looked", "seem", "seemed", "find", "found",
    "give", "gave", "given", "take", "took", "taken", "come", "came", "go",
    "went", "let", "lets", "let's", "now", "then", "here", "there", "where",
    "why", "who", "whom", "whose", "which", "all", "any", "some", "no", "yes",
    "don", "doesn", "didn", "won", "wouldn", "shouldn", "couldn", "isn", "aren",
    "wasn", "weren", "hasn", "haven", "hadn", "mightn", "mustn", "needn",
    "shouldn", "ll", "ve", "re", "s", "t", "d", "m",
    "first", "step", "steps", "simple", "simply", "just", "about", "around",
    "through", "over", "under", "again", "back", "out", "off", "away", "down",
}


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z'-]*", text.lower()) if len(w) >= 3}


def content_words(text: str) -> set[str]:
    return {w for w in words(text) if w not in STOP_WORDS}


def title_overlap(a: str, b: str) -> bool:
    """True if two titles share enough CONTENT words to be 'the same topic'.

    Stop-word filtered so the shared ELR wrapper ('English Podcast For ... | Learn
    English') does not produce false collisions between genuinely different topics.
    """
    wa, wb = content_words(a), content_words(b)
    if not wa or not wb:
        return False
    overlap = len(wa & wb)
    # require a meaningful share of the smaller topic's content words
    return overlap >= max(2, min(len(wa), len(wb)) // 2)


def produced_titles(series_dir: Path) -> list[str]:
    out: list[str] = []
    if not series_dir.is_dir():
        return out
    for ep_dir in sorted(series_dir.iterdir()):
        if not ep_dir.is_dir() or not ep_dir.name.startswith("episode_"):
            continue
        yj = next(ep_dir.glob("000_*.youtube.json"), None)
        if not yj or not yj.is_file():
            continue
        try:
            out.append(str(load_json(yj).get("title") or ""))
        except Exception:
            continue
    return out


def working_title_from_problem(problem: str, series: str) -> str:
    """Turn a learner-problem prompt into a working ELR-style title (agent refines later)."""
    p = problem.strip().rstrip(".")
    name = {"series_a": "Daily Talk", "series_b": "First Steps", "series_c": "Polished English"}[series]
    # take the first ~8 words of the problem as the topic spine
    spine = " ".join(p.split()[:10])
    return f"English Podcast For {name} | {spine} | Learn English"


def candidates_from_briefs() -> list[dict[str, Any]]:
    """Curated candidates from episode_brief_suggestions.json."""
    if not BRIEFS_PATH.is_file():
        return []
    briefs = load_json(BRIEFS_PATH)
    out: list[dict[str, Any]] = []
    for brief in briefs.get("briefs", []):
        series = ARCHETYPE_TO_SERIES.get(str(brief.get("recommended_archetype") or "").upper())
        if not series:
            continue
        problem = str(brief.get("learner_problem_prompt") or "").strip()
        if not problem:
            continue
        cluster = str(brief.get("topic_cluster") or "topic")
        out.append({
            "series": series,
            "slug": slugify(cluster),
            "publicTitle": working_title_from_problem(problem, series),
            "learnerProblem": problem,
            "hookAngle": str(brief.get("hook_angle") or brief.get("topic_cluster") or cluster),
            "source": "episode_brief_suggestions",
            "topic_cluster": cluster,
        })
    return out


def candidates_from_hot_titles() -> list[dict[str, Any]]:
    """Supplementary candidates from high-view competitor titles (topic segment extracted).

    Anti-homogeneity: each candidate records the source competitor channel + exact source
    title + a differentiationAngle prompt, so the scriptwriter deliberately takes a
    different angle instead of cloning the competitor's video.
    """
    titles: list[dict[str, Any]] = []
    if CORPUS_ANALYSIS.is_file():
        for item in load_json(CORPUS_ANALYSIS).get("cross_channel", {}).get("top_hook_titles", []):
            titles.append({
                "title": str(item.get("title", "")),
                "view_count": int(item.get("view_count", 0) or 0),
                "channel": str(item.get("channel", "")),
                "url": str(item.get("url", "")),
            })
    if TRENDING_VIDEOS.is_file():
        for vid in load_json(TRENDING_VIDEOS).get("videos", []):
            titles.append({
                "title": str(vid.get("title", "")),
                "view_count": int(vid.get("view_count", 0) or 0),
                "channel": str(vid.get("channel_name") or vid.get("channel_slug") or ""),
                "url": str(vid.get("url", "")),
            })
    out: list[dict[str, Any]] = []
    seen_spines: set[str] = set()
    # anti-homogeneity cap: at most MAX_PER_CHANNEL_PER_SERIES candidates per
    # (channel, series) so one high-view channel cannot flood a single series.
    per_channel_series: dict[tuple[str, str], int] = {}
    for hot in titles:
        title = hot["title"]
        # Class-style titles: "English Podcast for X | <Topic> | Learn English Fast"
        parts = [p.strip() for p in re.split(r"\||–|—", title) if p.strip()]
        spine = parts[1] if len(parts) >= 3 else title
        spine = re.sub(r"\b(learn english( fast)?|english podcast( for .*)?)\b", "", spine, flags=re.I).strip(" |-")
        if not spine or len(spine) < 8:
            continue
        key = slugify(spine)
        if key in seen_spines:
            continue
        seen_spines.add(key)
        competitor = hot.get("channel") or "competitor"
        # level mapping: prefer the authoritative channel hint; fall back to spine keywords
        series = CHANNEL_LEVEL_HINT.get(competitor.lower())
        if not series:
            lower = (spine + " " + title).lower()
            if re.search(r"\b(slow|easy|beginner|first step|simple)\b", lower):
                series = "series_b"
            elif re.search(r"\b(work|professional|polished|feedback|email|meeting|career)\b", lower):
                series = "series_c"
            else:
                series = "series_a"
        cap_key = (competitor.lower(), series)
        if per_channel_series.get(cap_key, 0) >= MAX_PER_CHANNEL_PER_SERIES:
            continue
        per_channel_series[cap_key] = per_channel_series.get(cap_key, 0) + 1
        out.append({
            "series": series,
            "slug": key,
            "publicTitle": working_title_from_problem(spine, series),
            "learnerProblem": f"Learners struggle with: {spine}.",
            "hookAngle": spine,
            "source": f"competitor_hot_title ({hot['view_count']:,} views)",
            "sourceCompetitor": competitor,
            "sourceTitle": title,
            "sourceUrl": hot.get("url", ""),
            "differentiationAngle": (
                f"Differentiate from {competitor}'s '{title}': use the two-host dialogue treatment "
                f"and a different hook/angle — do NOT clone their title, structure, or phrasing."
            ),
            "topic_cluster": spine,
        })
    return out


def refresh(series: str) -> dict[str, Any]:
    series_dir = SHOWS_ROOT / series
    backlog_path = series_dir / "topic_backlog.json"
    backlog = load_json(backlog_path) if backlog_path.is_file() else {
        "schema": "elr-topic-backlog-v1", "showId": series,
        "levelBand": SERIES_BAND.get(series, ""), "note": "Auto-refreshed from local research.",
        "topics": [],
    }

    existing_slugs = {str(t.get("slug", "")) for t in backlog.get("topics", [])}
    existing_titles = [str(t.get("publicTitle", "")) for t in backlog.get("topics", [])]
    produced = produced_titles(series_dir)

    candidates = [c for c in candidates_from_briefs() if c["series"] == series]
    candidates += [c for c in candidates_from_hot_titles() if c["series"] == series]

    added: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for c in candidates:
        slug = c["slug"]
        title = c["publicTitle"]
        if slug in existing_slugs:
            skipped.append({"slug": slug, "reason": "slug already in backlog"})
            continue
        if any(title_overlap(title, t) for t in existing_titles):
            skipped.append({"slug": slug, "reason": "title overlaps existing backlog topic"})
            continue
        if any(title_overlap(title, p) for p in produced if p):
            skipped.append({"slug": slug, "reason": "title overlaps a produced episode"})
            continue
        # assign next id
        existing_ids = [t.get("id", "") for t in backlog.get("topics", [])]
        prefix = series[-1]  # a/b/c
        nums = [int(m.group(1)) for i in existing_ids if (m := re.match(rf"^{prefix}(\d+)$", i))]
        next_num = (max(nums) + 1) if nums else (len(backlog.get("topics", [])) + 1)
        new_id = f"{prefix}{next_num:02d}"
        entry = {
            "id": new_id, "slug": slug, "status": "planned",
            "publicTitle": title, "learnerProblem": c["learnerProblem"],
            "hookAngle": c["hookAngle"], "source": c["source"],
        }
        # anti-homogeneity: persist source competitor + differentiation angle so the
        # scriptwriter deliberately diverges instead of cloning the competitor video
        if c.get("sourceCompetitor"):
            entry["sourceCompetitor"] = c["sourceCompetitor"]
            entry["sourceTitle"] = c.get("sourceTitle", "")
            entry["sourceUrl"] = c.get("sourceUrl", "")
            entry["differentiationAngle"] = c.get("differentiationAngle", "")
        backlog["topics"].append(entry)
        existing_slugs.add(slug)
        existing_titles.append(title)
        added.append({"id": new_id, "slug": slug, "publicTitle": title})

    backlog["lastRefreshed"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    write_json(backlog_path, backlog)
    return {
        "schema": "elr-topic-backlog-refresh-v1",
        "showId": series,
        "backlog": backlog_path.as_posix(),
        "addedCount": len(added),
        "skippedCount": len(skipped),
        "added": added,
        "skipped": skipped[:10],
        "totalTopics": len(backlog.get("topics", [])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh ELR topic backlog(s) from LOCAL research (no scraping).")
    parser.add_argument("--show", choices=["series_a", "series_b", "series_c"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not args.show and not args.all:
        parser.error("provide --show or --all")
    targets = ["series_a", "series_b", "series_c"] if args.all else [args.show]
    results = [refresh(s) for s in targets]
    print(json.dumps(results if args.all else results[0], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
