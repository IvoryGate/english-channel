from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.workspace import (
    DEFAULT_CORPUS_ROOT,
    episode_briefs_path,
    ensure_dir,
    iter_video_records,
    keyword_counts,
    read_json,
    sentence_count,
    transcript_structure_path,
    trending_path,
    word_count,
    words,
    write_json,
)


BEAT_PATTERNS = {
    "hook": re.compile(r"\b(today|in this episode|welcome|let's talk|we're going to|stop saying|did you know)\b", re.I),
    "practice": re.compile(r"\b(repeat|practice|try|say it|your turn|listen and|shadow)\b", re.I),
    "recap": re.compile(r"\b(recap|summary|remember|takeaway|key phrase|before we go|word tour|slow down)\b", re.I),
    "cta": re.compile(r"\b(subscribe|comment|download|worksheet|follow|like this video|notification)\b", re.I),
    "dialogue": re.compile(r"\b(host|guest|person a|person b|let me ask|what about you|right\?|exactly)\b", re.I),
}

TOPIC_PATTERNS = {
    "workplace": re.compile(r"\b(work|office|meeting|email|boss|colleague|interview|resume)\b", re.I),
    "social": re.compile(r"\b(friend|party|coffee|small talk|dating|family|neighbor)\b", re.I),
    "travel": re.compile(r"\b(travel|airport|hotel|restaurant|order|directions|trip)\b", re.I),
    "mindset": re.compile(r"\b(confidence|motivation|plateau|habit|mindset|fear|anxiety)\b", re.I),
    "grammar_style": re.compile(r"\b(grammar|tense|formal|informal|native|accent|pronunciation)\b", re.I),
    "phrases": re.compile(r"\b(phrase|expression|idiom|chunk|vocabulary|word)\b", re.I),
}


def split_sections(transcript: str) -> dict[str, str]:
    text = transcript.strip()
    if not text:
        return {"opening": "", "middle": "", "closing": ""}
    total_words = word_count(text)
    if total_words < 120:
        return {"opening": text, "middle": "", "closing": ""}
    tokens = text.split()
    open_end = max(int(total_words * 0.12), 40)
    close_start = max(int(total_words * 0.82), open_end + 20)
    opening = " ".join(tokens[:open_end])
    middle = " ".join(tokens[open_end:close_start])
    closing = " ".join(tokens[close_start:])
    return {"opening": opening, "middle": middle, "closing": closing}


def beat_hits(text: str) -> dict[str, int]:
    return {label: len(pattern.findall(text)) for label, pattern in BEAT_PATTERNS.items()}


def topic_hits(title: str, description: str, transcript: str) -> list[str]:
    combined = f"{title}\n{description}\n{transcript[:6000]}"
    labels = [label for label, pattern in TOPIC_PATTERNS.items() if pattern.search(combined)]
    return labels or ["general"]


def question_density(text: str) -> float:
    if not text.strip():
        return 0.0
    return sentence_count(text) and text.count("?") / max(word_count(text) / 100.0, 1.0)


def analyze_transcript_record(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record["metadata"]
    title = str(metadata.get("title") or "")
    description = record["description"]
    transcript = record["transcript"]
    sections = split_sections(transcript)
    opening_hits = beat_hits(sections["opening"])
    closing_hits = beat_hits(sections["closing"])
    topics = topic_hits(title, description, transcript)
    return {
        "video_id": metadata.get("id"),
        "title": title,
        "url": metadata.get("webpage_url"),
        "channel_slug": record["channel"]["slug"],
        "channel_name": record["channel"]["name"],
        "view_count": int(metadata.get("view_count") or 0),
        "has_transcript": bool(transcript.strip()),
        "transcript_word_count": word_count(transcript),
        "topics": topics,
        "question_density": round(question_density(transcript), 3),
        "opening_beats": opening_hits,
        "closing_beats": closing_hits,
        "keywords": keyword_counts([title, description, transcript[:3000]], limit=12),
        "structure_notes": build_structure_notes(opening_hits, closing_hits, topics, transcript),
    }


def build_structure_notes(
    opening_hits: dict[str, int],
    closing_hits: dict[str, int],
    topics: list[str],
    transcript: str,
) -> list[str]:
    notes: list[str] = []
    if opening_hits.get("hook", 0):
        notes.append("Opens with a direct episode promise or learner pain point.")
    if opening_hits.get("dialogue", 0) or closing_hits.get("dialogue", 0):
        notes.append("Uses conversational back-and-forth rather than monologue-only delivery.")
    if closing_hits.get("recap", 0):
        notes.append("Ends with recap or slow phrase review.")
    if closing_hits.get("cta", 0):
        notes.append("Includes an explicit platform or learner action CTA near the close.")
    if closing_hits.get("practice", 0):
        notes.append("Contains guided practice or repeat-after-me beats.")
    if "mindset" in topics:
        notes.append("Topic mixes language learning with confidence or habit framing.")
    if not transcript.strip():
        notes.append("Transcript missing locally; structure inference is title/description only.")
    return notes


def build_episode_briefs(analyzed: list[dict[str, Any]], trending: dict[str, Any] | None) -> list[dict[str, Any]]:
    topic_counter: Counter[str] = Counter()
    beat_counter: Counter[str] = Counter()
    for record in analyzed:
        topic_counter.update(record["topics"])
        for label, count in record["opening_beats"].items():
            if count:
                beat_counter[label] += 1
        for label, count in record["closing_beats"].items():
            if count:
                beat_counter[label] += 1

    hot_topics = [topic for topic, _ in topic_counter.most_common(6) if topic != "general"]
    briefs: list[dict[str, Any]] = []
    for topic in hot_topics[:4]:
        briefs.append(
            {
                "topic_cluster": topic,
                "show_profile": "polished_english",
                "learner_problem_prompt": learner_problem_for_topic(topic),
                "recommended_archetype": archetype_for_topic(topic),
                "structure_checklist": [
                    "Cold open with a concrete stake in the first 30-45 seconds.",
                    "One early contract line promising a slow end recap.",
                    "2-3 threads only; use question-flow transitions.",
                    "One micro-pocket after the first major thread.",
                    "Conflict recycle with resistance, not a dry weekly schedule.",
                    "Word tour with 2-4 pre-heard phrases and an honest stay line.",
                ],
                "signals_from_corpus": {
                    "topic_frequency": topic_counter[topic],
                    "common_opening_beats": dict(beat_counter.most_common(5)),
                },
            }
        )

    if trending and trending.get("videos"):
        for video in trending["videos"][:3]:
            briefs.append(
                {
                    "topic_cluster": "trending_signal",
                    "show_profile": "polished_english",
                    "seed_title": video.get("title"),
                    "seed_url": video.get("url"),
                    "trend_score": video.get("trend_score"),
                    "learner_problem_prompt": f"Invent an original episode inspired by the promise shape of: {video.get('title')}",
                    "recommended_archetype": "A",
                    "structure_checklist": [
                        "Do not copy the seed title, hook, or anecdotes.",
                        "Keep Leo/Mia daily-talk voice.",
                        "Extract only the learner problem and episode shape.",
                    ],
                }
            )
    return briefs


def learner_problem_for_topic(topic: str) -> str:
    prompts = {
        "workplace": "Sound professional in English without sounding stiff or overly formal at work.",
        "social": "Keep casual conversation going without freezing after the first sentence.",
        "travel": "Handle real travel situations with polite, natural English under time pressure.",
        "mindset": "Stay motivated when English practice feels slow, awkward, or embarrassing.",
        "grammar_style": "Choose the register that fits the moment instead of sounding textbook-perfect.",
        "phrases": "Upgrade one phrase family you already use so it sounds more natural in context.",
        "general": "Turn one narrow English frustration into a useful two-host daily-talk episode.",
    }
    return prompts.get(topic, prompts["general"])


def archetype_for_topic(topic: str) -> str:
    if topic in {"mindset", "grammar_style"}:
        return "C"
    if topic in {"phrases"}:
        return "B"
    return "A"


def analyze_transcript_corpus(corpus_root: Path) -> dict[str, Any]:
    analyzed = [analyze_transcript_record(record) for record in iter_video_records(corpus_root)]
    trending_file = trending_path(corpus_root)
    trending = read_json(trending_file) if trending_file.exists() else None
    topic_counter: Counter[str] = Counter()
    for record in analyzed:
        topic_counter.update(record["topics"])
    transcript_lengths = [record["transcript_word_count"] for record in analyzed if record["has_transcript"]]
    return {
        "schema": "dialogue-podcast-transcript-structure-v1",
        "corpus_root": str(corpus_root.as_posix()),
        "video_count": len(analyzed),
        "transcript_count": sum(1 for record in analyzed if record["has_transcript"]),
        "average_transcript_words": round(mean(transcript_lengths), 1) if transcript_lengths else 0,
        "topic_distribution": dict(topic_counter.most_common()),
        "videos": analyzed,
        "episode_briefs": build_episode_briefs(analyzed, trending),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze transcript structure and generate polished_english episode briefs.")
    parser.add_argument("--workspace-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--output", help="Structure analysis JSON path.")
    parser.add_argument("--briefs-output", help="Episode brief suggestions JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    ensure_dir(corpus_root / "analysis")
    analysis = analyze_transcript_corpus(corpus_root)
    structure_output = Path(args.output) if args.output else transcript_structure_path(corpus_root)
    briefs_output = Path(args.briefs_output) if args.briefs_output else episode_briefs_path(corpus_root)
    write_json(structure_output, analysis)
    write_json(
        briefs_output,
        {
            "schema": "dialogue-podcast-episode-briefs-v1",
            "corpus_root": str(corpus_root.as_posix()),
            "brief_count": len(analysis["episode_briefs"]),
            "briefs": analysis["episode_briefs"],
        },
    )
    print(f"structure={structure_output}")
    print(f"briefs={briefs_output}")
    print(f"videos={analysis['video_count']} briefs={len(analysis['episode_briefs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
