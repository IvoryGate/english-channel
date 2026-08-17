from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.workspace import DEFAULT_CORPUS_ROOT, analysis_path, read_json, report_path, write_text


def fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def fmt_pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.0f}%"
    except (TypeError, ValueError):
        return "0%"


def render_keywords(items: list[dict[str, Any]], limit: int = 10) -> str:
    if not items:
        return "No local data yet."
    return ", ".join(f"{item['term']} ({item['count']})" for item in items[:limit])


def render_report(analysis: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Dialogue Podcast YouTube Research Report",
        "",
        "## Executive Summary",
        "",
        f"- Archived videos analyzed: {analysis.get('video_count', 0)}",
        f"- Videos with usable transcript text: {analysis.get('transcript_count', 0)}",
        "- Artifact policy: metadata, descriptions, and transcript text only; no video or audio downloads.",
        "",
        "## Cross-Channel Signals",
        "",
        f"- Common title keywords: {render_keywords(analysis.get('cross_channel', {}).get('title_keywords', []))}",
        "- High-performing educational formats usually make a narrow promise: fix one mistake, practice one situation, or learn one phrase family.",
        "- The reusable podcast format should convert that promise into a two-host teaching conversation instead of a monologue.",
        "",
        "## Channel Findings",
        "",
    ]

    for slug, summary in analysis.get("channels", {}).items():
        lines.extend(
            [
                f"### {slug}",
                "",
                f"- Videos analyzed: {summary.get('video_count', 0)}",
                f"- Transcript coverage: {fmt_pct(summary.get('transcript_coverage'))}",
                f"- Average views: {fmt_int(summary.get('view_count', {}).get('average'))}",
                f"- Average title length: {summary.get('average_title_words', 0)} words",
                f"- Average transcript length: {summary.get('average_transcript_words', 0)} words",
                f"- Strong title patterns: {summary.get('title_patterns', {})}",
                f"- Description CTA patterns: {summary.get('description_ctas', {})}",
                f"- Top title keywords: {render_keywords(summary.get('keywords', []), limit=8)}",
                "",
                "Top archived videos:",
                "",
            ]
        )
        top_videos = summary.get("top_videos") or []
        if not top_videos:
            lines.append("- No videos archived yet.")
        for video in top_videos:
            lines.append(f"- {video.get('title')} ({fmt_int(video.get('view_count'))} views) - {video.get('url')}")
        lines.append("")

    lines.extend(
        [
            "## Scriptwriting Recommendations",
            "",
        ]
    )
    for recommendation in analysis.get("recommendations", []):
        lines.append(f"- {recommendation}")

    lines.extend(
        [
            "",
            "## Skill Guidance",
            "",
            "- Use aggregate findings as style and structure guidance.",
            "- Do not copy transcript passages into generated scripts.",
            "- For each new episode, produce an original title, description, and two-host script aligned to one learner problem.",
            "- Keep host roles stable across episodes so later TTS voice work can map each speaker consistently.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Markdown report from dialogue podcast YouTube analysis JSON.")
    parser.add_argument("--workspace-root", default=str(DEFAULT_CORPUS_ROOT), help="Corpus root directory.")
    parser.add_argument("--analysis", help="Input analysis JSON. Defaults to analysis/corpus_analysis.json.")
    parser.add_argument("--output", help="Output report path. Defaults to analysis/youtube_research_report.md.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    input_path = Path(args.analysis) if args.analysis else analysis_path(corpus_root)
    output_path = Path(args.output) if args.output else report_path(corpus_root)
    report = render_report(read_json(input_path))
    write_text(output_path, report)
    print(f"report={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
