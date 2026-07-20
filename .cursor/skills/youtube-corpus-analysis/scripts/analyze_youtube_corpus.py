from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.workspace import (
    DEFAULT_CHANNELS,
    DEFAULT_CORPUS_ROOT,
    analysis_path,
    clean_text,
    iter_video_records,
    keyword_counts,
    sentence_count,
    word_count,
    words,
    write_json,
)


TITLE_PATTERNS = {
    "question": re.compile(r"\?|\b(why|what|how|when|where|which|do|does|did|can|should)\b", re.I),
    "how_to": re.compile(r"\bhow to\b|\blearn\b|\bpractice\b|\bimprove\b", re.I),
    "list": re.compile(r"\b\d+\b|\b(common|phrases|ways|tips|things|rules)\b", re.I),
    "conversation": re.compile(r"\b(conversation|dialogue|podcast|talk|speaking|speak)\b", re.I),
    "story": re.compile(r"\b(story|life|day|experience|mistake|secret)\b", re.I),
    "pronunciation": re.compile(r"\b(pronunciation|accent|sound|intonation|stress)\b", re.I),
    "vocabulary": re.compile(r"\b(vocabulary|words|phrases|idioms|expressions)\b", re.I),
}

CTA_PATTERNS = {
    "subscribe": re.compile(r"\b(subscribe|channel|notification|bell)\b", re.I),
    "comment": re.compile(r"\b(comment|tell me|let me know|question below)\b", re.I),
    "download": re.compile(r"\b(download|pdf|worksheet|transcript|notes)\b", re.I),
    "course": re.compile(r"\b(course|class|program|membership|lesson)\b", re.I),
    "social": re.compile(r"\b(instagram|tiktok|facebook|website|link)\b", re.I),
}

HOOK_PATTERNS = (
    re.compile(r"\b(stop saying|don't say|native speakers|sound natural|real english)\b", re.I),
    re.compile(r"\b(common mistakes?|mistakes? you make|avoid)\b", re.I),
    re.compile(r"\b(you need to know|must know|everyday english)\b", re.I),
    re.compile(r"\b(secret|easy way|fast|quick)\b", re.I),
)


def classify_title(title: str) -> list[str]:
    labels = [label for label, pattern in TITLE_PATTERNS.items() if pattern.search(title)]
    return labels or ["general"]


def classify_ctas(description: str) -> list[str]:
    labels = [label for label, pattern in CTA_PATTERNS.items() if pattern.search(description)]
    return labels or ["none_detected"]


def hook_score(title: str) -> int:
    return sum(1 for pattern in HOOK_PATTERNS if pattern.search(title))


def estimated_level(text: str) -> str:
    tokens = words(text)
    if not tokens:
        return "unknown"
    avg_len = mean(len(token) for token in tokens)
    long_word_ratio = sum(1 for token in tokens if len(token) >= 8) / len(tokens)
    if avg_len <= 4.3 and long_word_ratio < 0.12:
        return "beginner"
    if avg_len <= 5.1 and long_word_ratio < 0.2:
        return "intermediate"
    return "upper_intermediate"


def paragraph_count(text: str) -> int:
    paragraphs = [part for part in re.split(r"\n{2,}|\r\n{2,}", text) if part.strip()]
    if paragraphs:
        return len(paragraphs)
    lines = [line for line in text.splitlines() if line.strip()]
    return len(lines)


def analyze_record(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record["metadata"]
    title = str(metadata.get("title") or "")
    description = record["description"]
    transcript = record["transcript"]
    transcript_words = word_count(transcript)
    return {
        "video_id": metadata.get("id"),
        "url": metadata.get("webpage_url"),
        "title": title,
        "channel_slug": record["channel"]["slug"],
        "channel_name": record["channel"]["name"],
        "view_count": int(metadata.get("view_count") or 0),
        "duration": metadata.get("duration"),
        "upload_date": metadata.get("upload_date"),
        "title_word_count": word_count(title),
        "title_patterns": classify_title(title),
        "hook_score": hook_score(title),
        "description_word_count": word_count(description),
        "description_ctas": classify_ctas(description),
        "has_transcript": bool(transcript.strip()),
        "transcript_word_count": transcript_words,
        "transcript_sentence_count": sentence_count(transcript),
        "transcript_paragraph_count": paragraph_count(transcript),
        "estimated_level": estimated_level(transcript or description or title),
    }


def summarize_channel(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "video_count": 0,
            "transcript_coverage": 0.0,
            "top_videos": [],
            "title_patterns": {},
            "description_ctas": {},
            "keywords": [],
        }
    views = [int(record["view_count"]) for record in records]
    transcript_count = sum(1 for record in records if record["has_transcript"])
    title_counter: Counter[str] = Counter()
    cta_counter: Counter[str] = Counter()
    level_counter: Counter[str] = Counter(record["estimated_level"] for record in records)
    for record in records:
        title_counter.update(record["title_patterns"])
        cta_counter.update(record["description_ctas"])
    return {
        "video_count": len(records),
        "transcript_coverage": round(transcript_count / len(records), 3),
        "view_count": {
            "average": round(mean(views), 1),
            "median": median(views),
            "max": max(views),
        },
        "top_videos": [
            {
                "title": record["title"],
                "view_count": record["view_count"],
                "url": record["url"],
                "patterns": record["title_patterns"],
            }
            for record in sorted(records, key=lambda item: int(item["view_count"]), reverse=True)[:5]
        ],
        "title_patterns": dict(title_counter.most_common()),
        "description_ctas": dict(cta_counter.most_common()),
        "estimated_levels": dict(level_counter.most_common()),
        "keywords": keyword_counts((record["title"] for record in records), limit=20),
        "average_title_words": round(mean(record["title_word_count"] for record in records), 1),
        "average_transcript_words": round(mean(record["transcript_word_count"] for record in records if record["has_transcript"]), 1)
        if transcript_count
        else 0,
    }


def build_recommendations(video_records: list[dict[str, Any]], channel_summaries: dict[str, Any]) -> list[str]:
    pattern_counter: Counter[str] = Counter()
    cta_counter: Counter[str] = Counter()
    for record in video_records:
        pattern_counter.update(record["title_patterns"])
        cta_counter.update(record["description_ctas"])

    recommendations = [
        "Open each script with a concrete learner problem before hosts introduce themselves.",
        "Use two stable host roles: one curious learner/proxy and one concise coach who models natural phrasing.",
        "Keep title promises narrow: one situation, one mistake type, or one phrase family per episode.",
        "Build recurring beats: hook, mini-dialogue, explanation, guided repetition, variation, recap, and CTA.",
    ]
    if pattern_counter.get("conversation", 0) >= pattern_counter.get("vocabulary", 0):
        recommendations.append("Favor scenario-based dialogue titles and episode structures over isolated word lists.")
    if cta_counter.get("comment", 0) or cta_counter.get("download", 0):
        recommendations.append("End with one learner action: comment an answer, repeat a prompt, or download notes.")
    if any(summary.get("average_transcript_words", 0) > 1200 for summary in channel_summaries.values()):
        recommendations.append("For long episodes, insert recap checkpoints every 3-5 minutes so the dialogue remains teachable.")
    return recommendations


def analyze_corpus(corpus_root: Path) -> dict[str, Any]:
    analyzed = [analyze_record(record) for record in iter_video_records(corpus_root)]
    by_channel: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in analyzed:
        by_channel[record["channel_slug"]].append(record)

    channel_summaries = {
        channel["slug"]: summarize_channel(by_channel.get(channel["slug"], []))
        for channel in DEFAULT_CHANNELS
    }
    return {
        "schema": "dialogue-podcast-youtube-analysis-v1",
        "corpus_root": str(corpus_root.as_posix()),
        "video_count": len(analyzed),
        "transcript_count": sum(1 for record in analyzed if record["has_transcript"]),
        "channels": channel_summaries,
        "cross_channel": {
            "title_keywords": keyword_counts((record["title"] for record in analyzed), limit=30),
            "description_keywords": keyword_counts((record["title"] + " " + record["description_ctas"][0] for record in analyzed), limit=20),
            "top_hook_titles": [
                {
                    "title": record["title"],
                    "channel": record["channel_name"],
                    "view_count": record["view_count"],
                    "url": record["url"],
                }
                for record in sorted(analyzed, key=lambda item: (int(item["hook_score"]), int(item["view_count"])), reverse=True)[:10]
            ],
        },
        "recommendations": build_recommendations(analyzed, channel_summaries),
        "videos": analyzed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze archived YouTube corpus for dialogue podcast scriptwriting.")
    parser.add_argument("--workspace-root", default=str(DEFAULT_CORPUS_ROOT), help="Corpus root directory.")
    parser.add_argument("--output", help="Output analysis JSON path. Defaults to analysis/corpus_analysis.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    output = Path(args.output) if args.output else analysis_path(corpus_root)
    analysis = analyze_corpus(corpus_root)
    write_json(output, analysis)
    print(f"analysis={output}")
    print(f"videos={analysis['video_count']} transcripts={analysis['transcript_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
