from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.workspace import word_count, write_json


HOST_LINE_RE = re.compile(r"^\s*(?P<host>[A-Za-z][A-Za-z0-9 _-]{0,30})\s*:\s*(?P<text>.+?)\s*$")
MARKDOWN_HOST_LINE_RE = re.compile(
    r"^\s*\*{0,2}(?P<host>[A-Za-z][A-Za-z0-9 _-]{0,30})\*{0,2}\s+(?:-|--|—)\s+(?P<text>.+?)\s*$"
)
METADATA_LABELS = {
    "archetype",
    "alternate title",
    "act 1",
    "act 2",
    "act 3",
    "close",
    "cold open",
    "cta",
    "description",
    "episode engine",
    "early contract",
    "episode contract",
    "estimated duration",
    "hosts",
    "host intro",
    "key phrases",
    "learner problem",
    "lexis teaser",
    "micro pocket",
    "micro-pocket",
    "one-line promise",
    "outcomes",
    "part 1",
    "part 2",
    "part 3",
    "recycle",
    "show profile",
    "structure map",
    "t1",
    "t2",
    "t3",
    "tags",
    "teaching plan",
    "target level",
    "title",
    "word tour",
}
POLISHED_REQUIRED_MARKERS = {
    "Teaching Plan": ("[teaching plan]", "## teaching plan", "teaching plan"),
    "Structure Map": ("[structure map]", "## structure map", "structure map"),
    "Early Contract": ("[early contract]", "early contract"),
    "Host Intro": ("[host intro]", "host intro"),
    "Micro-Pocket": ("[micro-pocket]", "micro-pocket", "micro pocket"),
    "Recycle": ("[recycle]", "recycle"),
    "Word Tour": ("[word tour]", "word tour"),
}
SERIES_B_REQUIRED_MARKERS = {
    "Teaching Plan": ("[teaching plan]", "## teaching plan", "teaching plan"),
    "Episode Contract": ("[episode contract]", "episode contract", "by the end"),
}

PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "general": {"min_words": 700, "max_words": 1800, "spoken_only": False},
    "polished_english": {"min_words": 1900, "max_words": 2800, "spoken_only": True, "structure": "polished"},
    "series_a": {"min_words": 1800, "max_words": 2400, "spoken_only": True, "structure": "polished"},
    "series_b": {"min_words": 1400, "max_words": 1900, "spoken_only": True, "structure": "series_b"},
    "series_c": {"min_words": 2000, "max_words": 2800, "spoken_only": True, "structure": "polished"},
}

FROZEN_COLD_OPEN_PHRASES = (
    "hey, hey, english learners. welcome back to daily talk",
    "welcome back to polished english, where two people talk about real life",
)


def _host_line_match(line: str) -> re.Match[str] | None:
    return HOST_LINE_RE.match(line) or MARKDOWN_HOST_LINE_RE.match(line)


def _has_any_marker(text_lower: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text_lower for marker in markers)


def validate_script_text(
    text: str,
    min_words: int,
    max_words: int,
    profile: str = "general",
) -> dict[str, Any]:
    lines = text.splitlines()
    host_turns: Counter[str] = Counter()
    spoken_text_parts: list[str] = []
    spoken_turns: list[str] = []
    issues: list[dict[str, str]] = []
    title_present = any(line.lower().startswith("title:") for line in lines)
    description_present = any(line.lower().startswith("description:") for line in lines)
    cta_present = bool(re.search(r"\b(comment|subscribe|practice|repeat|download|share|follow|save)\b", text, re.I))
    text_lower = text.lower()
    profile_config = PROFILE_DEFAULTS.get(profile, PROFILE_DEFAULTS["general"])
    spoken_only = bool(profile_config.get("spoken_only"))

    for line in lines:
        match = _host_line_match(line)
        if match:
            host = match.group("host").strip()
            if host.lower() not in METADATA_LABELS:
                host_turns[host] += 1
                spoken_turn = match.group("text").strip()
                spoken_text_parts.append(spoken_turn)
                spoken_turns.append(spoken_turn)

    total_words = word_count(" ".join(spoken_text_parts)) if spoken_only else word_count(text)
    if not title_present:
        issues.append({"code": "MISSING_TITLE", "message": "Add a `Title:` line."})
    if not description_present:
        issues.append({"code": "MISSING_DESCRIPTION", "message": "Add a `Description:` line."})
    if len(host_turns) != 2:
        issues.append({"code": "HOST_COUNT", "message": f"Expected exactly two hosts, found {len(host_turns)}."})
    if host_turns:
        most = max(host_turns.values())
        least = min(host_turns.values())
        if least and most / least > 1.8:
            issues.append({"code": "TURN_IMBALANCE", "message": f"Host turns are imbalanced: {dict(host_turns)}."})
    if total_words < min_words:
        issues.append({"code": "TOO_SHORT", "message": f"Script has {total_words} words, below minimum {min_words}."})
    if total_words > max_words:
        issues.append({"code": "TOO_LONG", "message": f"Script has {total_words} words, above maximum {max_words}."})
    if not cta_present:
        issues.append({"code": "MISSING_CTA", "message": "End with one learner action or CTA."})

    if profile in {"polished_english", "series_a", "series_b", "series_c"}:
        opening = " ".join(spoken_turns[:2]).lower()
        if any(phrase in text_lower for phrase in FROZEN_COLD_OPEN_PHRASES):
            issues.append(
                {
                    "code": "FROZEN_COLD_OPEN",
                    "message": "Replace the inherited greeting chassis with a specific situation, failed moment, or social tension.",
                }
            )
        elif re.search(r"\bwelcome\s+(back|to)\b|\benglish learners\b", opening):
            issues.append(
                {
                    "code": "GREETING_FIRST_OPEN",
                    "message": "Open with the learner's situation before the welcome or show name.",
                }
            )

        repeated_turns = [
            turn
            for turn, count in Counter(re.sub(r"\s+", " ", item.lower()) for item in spoken_turns).items()
            if count >= 5 and word_count(turn) >= 4
        ]
        if repeated_turns:
            issues.append(
                {
                    "code": "EXCESSIVE_EXACT_REPETITION",
                    "message": "Reduce a verbatim learner phrase repeated five or more times in the same script.",
                }
            )

    structure = profile_config.get("structure")
    if structure == "polished":
        for label, markers in POLISHED_REQUIRED_MARKERS.items():
            if not _has_any_marker(text_lower, markers):
                issues.append({"code": "POLISHED_STRUCTURE", "message": f"Add a `{label}` block or marker."})
        if "delivery:" not in text_lower and '"emotion"' not in text_lower and "emotion:" not in text_lower:
            issues.append(
                {
                    "code": "MISSING_DELIVERY",
                    "message": "Add section-level delivery notes or render-handoff emotion/delivery fields.",
                }
            )
    elif structure == "series_b":
        for label, markers in SERIES_B_REQUIRED_MARKERS.items():
            if not _has_any_marker(text_lower, markers):
                issues.append({"code": "SERIES_B_STRUCTURE", "message": f"Add a `{label}` block or marker."})

    if profile in {"polished_english", "series_a", "series_b", "series_c"} and "speed" in text_lower:
        issues.append({"code": "OLD_SPEED_CONTROL", "message": "Remove old `speed` controls; all series use speed=1.0."})

    return {
        "ok": not issues,
        "profile": profile,
        "word_count": total_words,
        "host_turns": dict(host_turns),
        "issues": issues,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a two-person dialogue podcast script draft.")
    parser.add_argument("script", help="Markdown/text script file.")
    parser.add_argument("--min-words", type=int)
    parser.add_argument("--max-words", type=int)
    parser.add_argument(
        "--profile",
        choices=["general", "polished_english", "series_a", "series_b", "series_c"],
        default="general",
    )
    parser.add_argument("--write-report", help="Optional JSON report path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    defaults = PROFILE_DEFAULTS[args.profile]
    min_words = args.min_words if args.min_words is not None else int(defaults["min_words"])
    max_words = args.max_words if args.max_words is not None else int(defaults["max_words"])
    text = Path(args.script).read_text(encoding="utf-8")
    result = validate_script_text(text, min_words=min_words, max_words=max_words, profile=args.profile)
    if args.write_report:
        write_json(Path(args.write_report), result)
    for issue in result["issues"]:
        print(f"{issue['code']}: {issue['message']}")
    print(f"ok={str(result['ok']).lower()} words={result['word_count']} hosts={len(result['host_turns'])} profile={args.profile}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
