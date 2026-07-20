from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CORPUS_ROOT = Path("workspace") / "dialogue_podcast_research" / "youtube_corpus"

DEFAULT_SEARCH_QUERIES: tuple[str, ...] = (
    "english podcast two hosts learn english",
    "english conversation podcast for learners",
    "learn english daily talk podcast",
    "b1 b2 english podcast dialogue",
    "english learning podcast natural conversation",
)

DUAL_HOST_PATTERNS = (
    re.compile(r"\b(two hosts?|co-?host|podcast|dialogue|conversation between)\b", re.I),
    re.compile(r"\b(host|guest|interview|chat with|talk with)\b", re.I),
    re.compile(r"\b(we talk|let's talk|join us|between us)\b", re.I),
)

DUAL_HOST_NAME_PATTERNS = (
    re.compile(r"\b(and|&|with)\s+[A-Z][a-z]+\b"),
    re.compile(r"\b[A-Z][a-z]+\s+(and|&)\s+[A-Z][a-z]+\b"),
)

TRANSCRIPT_TURN_PATTERNS = (
    re.compile(r"^(host|speaker|person)\s*[12ab]:", re.I | re.M),
    re.compile(r"^[A-Z][a-z]+:\s", re.M),
)

DEFAULT_CHANNELS: tuple[dict[str, str], ...] = (
    # --- original 3 (user-supplied) ---
    {
        "slug": "englishwithhopeee",
        "name": "English With HOPE",
        "url": "https://www.youtube.com/@englishwithHOPEEE",
    },
    {
        "slug": "jandmaypodcast",
        "name": "J and May Podcast",
        "url": "https://www.youtube.com/@JandMayPodcast",
    },
    {
        "slug": "speakenglishwithclass",
        "name": "Speak English With Class",
        "url": "https://www.youtube.com/@SpeakEnglishWithClass",
    },
    # --- expanded set: dual-host English learning podcasts (direct competitors) ---
    # surfaced by discover_youtube_podcasts.py; added to broaden trend signals and
    # reduce homogeneity risk from tracking only the original 3. Collect one at a time
    # via run_research_refresh.py --channel <slug> (anti-ban: never all at once).
    {
        "slug": "maxandmiapodcast",
        "name": "Max & Mia Podcast",
        "url": "https://www.youtube.com/@MaxandMiaPodcast",
    },
    {
        "slug": "davidandaliceenglish",
        "name": "Speak English with David & Alice",
        "url": "https://www.youtube.com/@English.Academy.plus-o",
    },
    {
        "slug": "goenglishpodcast",
        "name": "Go English - The Podcast",
        "url": "https://www.youtube.com/@Goenglishpodcast",
    },
    {
        "slug": "englishpodcastunleashed",
        "name": "English Unleashed: The Podcast",
        "url": "https://www.youtube.com/@EnglishPodcastUnleashed",
    },
    {
        "slug": "englishconversationpod",
        "name": "English Conversation Podcast",
        "url": "https://www.youtube.com/@EnglishConversationPod",
    },
    {
        "slug": "highlevellistening",
        "name": "High Level Listening Advanced English Podcast",
        "url": "https://www.youtube.com/@highlevellistening",
    },
    # --- trend reference (institutional, not a direct competitor but a demand signal) ---
    {
        "slug": "bbclearningenglish",
        "name": "BBC Learning English",
        "url": "https://www.youtube.com/@bbclearningenglish",
    },
)

STOP_WORDS = {
    "a",
    "about",
    "after",
    "again",
    "all",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "but",
    "by",
    "can",
    "for",
    "from",
    "get",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "learn",
    "like",
    "me",
    "more",
    "my",
    "of",
    "on",
    "or",
    "our",
    "so",
    "that",
    "the",
    "their",
    "this",
    "to",
    "up",
    "use",
    "was",
    "we",
    "what",
    "when",
    "with",
    "you",
    "your",
}


def slugify(value: str, fallback: str = "item") -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or fallback


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def channel_by_slug(slug: str) -> dict[str, str]:
    normalized = slugify(slug)
    for channel in DEFAULT_CHANNELS:
        if channel["slug"] == normalized:
            return dict(channel)
    raise ValueError(f"Unknown channel slug: {slug}")


def channel_dir(corpus_root: Path, channel_slug: str) -> Path:
    return corpus_root / channel_slug


def videos_dir(corpus_root: Path, channel_slug: str) -> Path:
    return channel_dir(corpus_root, channel_slug) / "videos"


def selected_videos_path(corpus_root: Path, channel_slug: str) -> Path:
    return channel_dir(corpus_root, channel_slug) / "selected_videos.json"


def video_dir(corpus_root: Path, channel_slug: str, video_id: str) -> Path:
    return videos_dir(corpus_root, channel_slug) / slugify(video_id, "video")


def analysis_dir(corpus_root: Path) -> Path:
    return corpus_root / "analysis"


def analysis_path(corpus_root: Path) -> Path:
    return analysis_dir(corpus_root) / "corpus_analysis.json"


def report_path(corpus_root: Path) -> Path:
    return analysis_dir(corpus_root) / "youtube_research_report.md"


def discovery_dir(corpus_root: Path) -> Path:
    return corpus_root / "discovery"


def trending_path(corpus_root: Path) -> Path:
    return analysis_dir(corpus_root) / "trending_videos.json"


def transcript_structure_path(corpus_root: Path) -> Path:
    return analysis_dir(corpus_root) / "transcript_structure.json"


def episode_briefs_path(corpus_root: Path) -> Path:
    return analysis_dir(corpus_root) / "episode_brief_suggestions.json"


def browser_profile_dir(corpus_root: Path) -> Path:
    return corpus_root / "browser_profile"


def chrome_user_data_dir(corpus_root: Path) -> Path:
    return browser_profile_dir(corpus_root) / "chrome_user_data"


def has_chrome_user_profile(corpus_root: Path) -> bool:
    root = chrome_user_data_dir(corpus_root)
    if not root.exists():
        return False
    return any(root.iterdir())


def normalize_video_id(raw: str | None) -> str:
    if not raw:
        return ""
    value = raw.strip()
    match = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{6,})", value)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{6,}", value):
        return value
    return ""


def video_url(video_id_or_url: str) -> str:
    video_id = normalize_video_id(video_id_or_url)
    if not video_id:
        return video_id_or_url
    return f"https://www.youtube.com/watch?v={video_id}"


def clean_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text.lower())


def word_count(text: str) -> int:
    return len(words(text))


def sentence_count(text: str) -> int:
    sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]
    return len(sentences)


def keyword_counts(texts: Iterable[str], limit: int = 30) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for text in texts:
        for token in words(text):
            if token in STOP_WORDS or len(token) < 3:
                continue
            counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"term": term, "count": count} for term, count in ranked[:limit]]


def strip_vtt_to_text(raw: str) -> str:
    lines: list[str] = []
    previous = ""
    for line in raw.splitlines():
        value = line.strip()
        if not value:
            continue
        if value.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in value:
            continue
        if re.fullmatch(r"\d+", value):
            continue
        value = re.sub(r"<[^>]+>", "", value)
        value = re.sub(r"&nbsp;", " ", value)
        value = clean_text(value)
        if value and value != previous:
            lines.append(value)
            previous = value
    return "\n".join(lines).strip()


def transcript_files(folder: Path) -> list[Path]:
    candidates: list[Path] = []
    for suffix in ("*.vtt", "*.srt", "*.ttml", "*.srv3", "*.txt"):
        candidates.extend(folder.glob(suffix))
    excluded = {"transcript.txt", "description.txt", "collection_status.json", "metadata.json"}
    return sorted({path for path in candidates if path.name not in excluded})


def load_transcript_text(folder: Path) -> str:
    for path in transcript_files(folder):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix.lower() in {".vtt", ".srt", ".ttml", ".srv3"}:
            text = strip_vtt_to_text(raw)
        else:
            text = raw.strip()
        if text:
            return text
    status_path = folder / "collection_status.json"
    if status_path.exists():
        status = read_json(status_path).get("transcript", {})
        if status.get("source_file") == "description.txt":
            return ""
    transcript = folder / "transcript.txt"
    if transcript.exists():
        return transcript.read_text(encoding="utf-8")
    return ""


def parse_upload_date(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return datetime.strptime(text, "%Y%m%d").replace(tzinfo=timezone.utc)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return None


def days_since_upload(upload_date: str | None, *, now: datetime | None = None) -> int | None:
    parsed = parse_upload_date(upload_date)
    if not parsed:
        return None
    reference = now or datetime.now(timezone.utc)
    delta = reference - parsed
    return max(delta.days, 1)


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def engagement_rate(metadata: dict[str, Any]) -> float:
    views = float(metadata.get("view_count") or 0)
    likes = float(metadata.get("like_count") or 0)
    comments = float(metadata.get("comment_count") or 0)
    if views <= 0:
        return 0.0
    return (likes + comments * 2.0) / views


def view_velocity(metadata: dict[str, Any], *, now: datetime | None = None) -> float | None:
    views = float(metadata.get("view_count") or 0)
    days = days_since_upload(str(metadata.get("upload_date") or ""), now=now)
    if days is None:
        return None
    return views / days


def dual_host_signals(title: str, description: str, transcript: str = "") -> dict[str, Any]:
    combined = f"{title}\n{description}\n{transcript[:4000]}"
    pattern_hits = sum(1 for pattern in DUAL_HOST_PATTERNS if pattern.search(combined))
    name_hits = sum(1 for pattern in DUAL_HOST_NAME_PATTERNS if pattern.search(f"{title}\n{description}"))
    turn_hits = sum(1 for pattern in TRANSCRIPT_TURN_PATTERNS if pattern.search(transcript[:8000]))
    score = pattern_hits * 2 + name_hits + min(turn_hits, 3)
    return {
        "score": score,
        "pattern_hits": pattern_hits,
        "name_hits": name_hits,
        "turn_hits": turn_hits,
        "likely_dual_host": score >= 3,
    }


def composite_trend_score(
    metadata: dict[str, Any],
    *,
    title: str = "",
    description: str = "",
    transcript: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    views = int(metadata.get("view_count") or 0)
    likes = int(metadata.get("like_count") or 0)
    velocity = view_velocity(metadata, now=now)
    engagement = engagement_rate(metadata)
    dual_host = dual_host_signals(title or str(metadata.get("title") or ""), description, transcript)

    velocity_norm = min((velocity or 0.0) / 5000.0, 1.0)
    engagement_norm = min(engagement * 100.0, 1.0)
    views_norm = min(views / 1_000_000.0, 1.0)
    likes_norm = min(likes / 50_000.0, 1.0)
    dual_host_norm = min(dual_host["score"] / 8.0, 1.0)

    composite = (
        velocity_norm * 0.35
        + engagement_norm * 0.25
        + views_norm * 0.20
        + likes_norm * 0.10
        + dual_host_norm * 0.10
    )
    return {
        "view_count": views,
        "like_count": likes,
        "engagement_rate": round(engagement, 6),
        "view_velocity_per_day": round(velocity, 2) if velocity is not None else None,
        "days_since_upload": days_since_upload(str(metadata.get("upload_date") or ""), now=now),
        "dual_host": dual_host,
        "components": {
            "velocity_norm": round(velocity_norm, 4),
            "engagement_norm": round(engagement_norm, 4),
            "views_norm": round(views_norm, 4),
            "likes_norm": round(likes_norm, 4),
            "dual_host_norm": round(dual_host_norm, 4),
        },
        "trend_score": round(composite, 4),
    }


def iter_video_records(corpus_root: Path) -> Iterable[dict[str, Any]]:
    for channel in DEFAULT_CHANNELS:
        root = videos_dir(corpus_root, channel["slug"])
        if not root.exists():
            continue
        selected_path = selected_videos_path(corpus_root, channel["slug"])
        if selected_path.exists():
            selected = read_json(selected_path).get("video_ids", [])
            folders = [root / slugify(str(video_id), "video") for video_id in selected]
        else:
            folders = sorted(path for path in root.iterdir() if path.is_dir())
        for folder in folders:
            if not folder.is_dir():
                continue
            metadata_path = folder / "metadata.json"
            if not metadata_path.exists():
                continue
            metadata = read_json(metadata_path)
            description_path = folder / "description.txt"
            description = description_path.read_text(encoding="utf-8") if description_path.exists() else ""
            transcript = load_transcript_text(folder)
            yield {
                "channel": channel,
                "folder": str(folder.as_posix()),
                "metadata": metadata,
                "description": description,
                "transcript": transcript,
            }
