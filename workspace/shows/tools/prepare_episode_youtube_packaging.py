"""Resolve YouTube chapter timestamps from rendered turn durations and assemble
the upload description + title for an ELR dialogue episode.

Audiobook analogue: ``prepare_youtube_packaging.py`` + ``audiobook_workspace.py``
timeline/markers helpers. This is the episode-side equivalent.

Runs **after audio render** (turn WAVs exist) so chapter timestamps reflect the
real spoken timeline. The final video adds a short intro (default 3s), so every
timestamp is offset by ``intro_offset_sec`` — matching the audiobook convention.

Marker sources (first non-empty wins):
1. ``youtube.json`` ``chapterMarkers``: ``[{"turnId": "p001", "label": "Intro"}, ...]``
2. Auto-derived from the draft's ``## `` section headers (起承转合 beats), each
   mapped to the first dialogue turn that follows it in the draft.

Outputs (under ``reports/``):
- ``000_episode_XXX.youtube_description.txt``  (consumed by export step)
- ``000_episode_XXX.youtube_title.txt``        (human reference; export also writes its own)
- ``000_episode_XXX.youtube_packaging.json``  (resolved markers + timeline, for audit)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
sys.path.insert(0, str(TOOLS))

from episode_artifacts import artifact_paths, load_json, turn_wav_path, write_json  # noqa: E402

# Legacy body-only videos previously reserved a three-second opening. Branded
# episodes derive their real offset from the composed intro asset instead.
DEFAULT_INTRO_OFFSET_SEC = 3.0

YOUTUBE_TITLE_MAX = 100


def _enforce_title_limit(title: str) -> None:
    """Fail loudly if a YouTube title exceeds the 100-character upload limit.

    YouTube silently truncates or rejects titles over 100 chars; better to halt
    the pack step with an actionable message than ship a title that gets mangled.
    """
    if len(title) > YOUTUBE_TITLE_MAX:
        raise ValueError(
            f"YouTube title is {len(title)} chars (max {YOUTUBE_TITLE_MAX}). "
            f"Shorten the `title` field in youtube.json — drop the optional "
            f"'| Learn English' suffix first, or trim the hook. Title: {title!r}"
        )


def _read_wav_duration(path: Path) -> float:
    import soundfile as sf

    info = sf.info(str(path))
    return float(info.frames / info.samplerate)


def _probe_media_duration(path: Path) -> float:
    """Read a media duration without relying on a Python video binding."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        result = subprocess.run(
            [
                ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=nokey=1:noprint_wrappers=1",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(result.stdout.strip())
        if duration > 0:
            return duration
    raise RuntimeError(f"Could not read a positive media duration for {path}")


def resolve_video_intro_offset(
    paths: dict[str, Path],
    *,
    explicit_offset_sec: float | None = None,
) -> tuple[float, str]:
    """Return the chapter offset and its audit source.

    Branding is decided by the compose report because packaging runs after
    composition. A branded episode must use the actual intro clip duration;
    silently falling back to the legacy three-second value would misplace every
    chapter timestamp.
    """
    if explicit_offset_sec is not None:
        return float(explicit_offset_sec), "explicit-cli"

    report_path = paths["videoReport"]
    if not report_path.is_file():
        return DEFAULT_INTRO_OFFSET_SEC, "legacy-default"
    report = load_json(report_path)
    branding = dict(report.get("branding") or {})
    if not branding.get("enabled"):
        return DEFAULT_INTRO_OFFSET_SEC, "legacy-default"

    intro_value = str(branding.get("introMp4") or "").strip()
    intro_path = Path(intro_value)
    if not intro_value or not intro_path.is_file():
        raise FileNotFoundError(
            "Branding is enabled in the compose report, but its intro asset is unavailable: "
            f"{intro_value or '(missing introMp4)'}"
        )
    return _probe_media_duration(intro_path), "branding-intro-media"


def episode_timeline(
    workspace: Path,
    manifest: dict[str, Any],
    *,
    silence_sec: float | None = None,
) -> list[dict[str, Any]]:
    """Build a cumulative timeline (startSec/endSec) for every turn in order.

    Durations come from the rendered turn WAVs (audio must exist). Inter-turn
    silence is ``renderSettings.interTurnSilenceSec`` (or per-turn
    ``pauseAfterSec`` if present).
    """
    gap = float(
        silence_sec
        if silence_sec is not None
        else manifest.get("renderSettings", {}).get("interTurnSilenceSec", 0.3)
    )
    cursor = 0.0
    timeline: list[dict[str, Any]] = []
    for turn in manifest["turns"]:
        wav_path = turn_wav_path(workspace, str(turn["filename"]))
        if not wav_path.is_file():
            raise FileNotFoundError(
                f"Missing turn audio for timeline: {wav_path}. Run render first."
            )
        duration = _read_wav_duration(wav_path)
        start = cursor
        end = start + duration
        timeline.append(
            {
                "id": str(turn["id"]),
                "order": int(turn["order"]),
                "filename": str(turn["filename"]),
                "speaker": str(turn["speaker"]),
                "section": str(turn.get("section", "")),
                "text": str(turn["text"]),
                "startSec": round(start, 3),
                "endSec": round(end, 3),
                "durationSec": round(duration, 3),
            }
        )
        pause = float(turn.get("pauseAfterSec", gap))
        cursor = end + pause
    return timeline


def _format_timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _clean_header_label(header: str) -> str:
    """'## Intro Hook — 起' -> 'Intro Hook'."""
    label = header.lstrip("#").strip()
    # drop trailing 起承转合 suffix after an em-dash/en-dash (NOT ascii hyphen,
    # so "Micro-Pocket" stays intact).
    label = re.split(r"\s*[—–]\s*", label)[0].strip()
    # drop parenthetical continuations like "(continued)" or "(partial)".
    label = re.sub(r"\s*\([^)]*\)\s*$", "", label).strip()
    return label or "Section"


def _shorten_label(text: str, *, max_len: int = 72) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "").strip())
    if not cleaned:
        return ""
    if len(cleaned) <= max_len:
        return cleaned
    cut = cleaned[: max_len - 1].rsplit(" ", 1)[0]
    return (cut or cleaned[: max_len - 1]).rstrip(",;—–- ") + "…"


def _parse_bracket_block(draft_text: str, block_name: str) -> str:
    pattern = rf"^\[{re.escape(block_name)}\]\s*\n(.*?)(?=^\[|\n---|\n## |\Z)"
    match = re.search(pattern, draft_text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1).strip())


def _parse_teaching_plan_threads(draft_text: str) -> list[str]:
    plan = _parse_bracket_block(draft_text, "Teaching Plan")
    if not plan:
        return []
    threads: list[str] = []
    for match in re.finditer(r"Thread\s+\d+\s*,\s*([^,\n.]+)", plan, flags=re.IGNORECASE):
        label = match.group(1).strip()
        if label:
            threads.append(label)
    if threads:
        return threads
    for match in re.finditer(r"Part\s+\d+\s*,\s*([^,\n.]+)", plan, flags=re.IGNORECASE):
        label = match.group(1).strip()
        if label:
            threads.append(label)
    return threads


def _classify_section(header: str) -> str:
    label = _clean_header_label(header).lower()
    if "intro" in label or label.endswith("hook"):
        return "intro"
    if "teaching" in label or label.startswith("part ") or label == "body":
        return "teaching"
    if "micro-pocket" in label or "micro pocket" in label:
        return "micro_pocket"
    if "recycle" in label or "pattern interrupt" in label:
        return "recycle"
    if "meta pivot" in label:
        return "meta_pivot"
    if "word tour" in label:
        return "word_tour"
    if "recap" in label or "close" in label or "cta" in label:
        return "close"
    return "other"


def _micro_pocket_label(block: str) -> str:
    if not block:
        return "Slow replay: key phrases"
    text = block.strip()
    if "replayed" in text.lower():
        phrase_part = re.split(r"\breplayed\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
        phrase_part = re.sub(r"^After[^,]*,\s*", "", phrase_part, flags=re.IGNORECASE).strip(" .")
        if phrase_part:
            return _shorten_label(f"Slow replay: {phrase_part}")
    return _shorten_label(f"Slow replay: {text}")


def _parse_key_phrases(draft_text: str) -> str:
    for line in draft_text.splitlines():
        if line.strip().lower().startswith("key phrases:"):
            return line.split(":", 1)[1].strip()
    return ""


def _plan_teaching_labels(draft_text: str, threads: list[str]) -> list[str]:
    """Spread Teaching Plan threads across however many teaching sections exist."""
    if not threads:
        return []
    teaching_count = sum(
        1
        for line in draft_text.splitlines()
        if line.strip().startswith("## ") and _classify_section(line.strip()) == "teaching"
    )
    if teaching_count <= 0:
        return []
    labels: list[str] = []
    for i in range(teaching_count):
        idx = min(int(i * len(threads) / teaching_count), len(threads) - 1)
        labels.append(threads[idx])
    return labels


def _word_tour_label(block: str, key_phrases: str = "") -> str:
    generic = block.strip().lower() in {
        "nine phrases replayed at the end.",
        "four phrases, all pre-heard, honest payoff line before the tour.",
    }
    if key_phrases and (not block or generic or "phrases replayed" in block.lower()):
        phrases = [p.strip() for p in key_phrases.split(",") if p.strip()]
        if phrases:
            preview = ", ".join(phrases[:3])
            if len(phrases) > 3:
                preview += ", …"
            return _shorten_label(f"Word tour: {preview}")
    if not block:
        return "Word tour: key phrases"
    first_line = block.splitlines()[0].strip()
    if first_line.lower().startswith("four phrases"):
        return "Word tour: key phrases from today"
    phrases = [p.strip() for p in re.split(r",|\band\b", first_line) if p.strip()]
    if phrases and not generic:
        preview = ", ".join(phrases[:3])
        if len(phrases) > 3:
            preview += ", …"
        return _shorten_label(f"Word tour: {preview}")
    if key_phrases:
        return _word_tour_label("", key_phrases)
    return "Word tour: key phrases"


def _recycle_label(block: str, header: str) -> str:
    if block:
        sentence = re.split(r"[.;]", block.strip())[0].strip()
        sentence = re.sub(
            r"^(Ethan|Nora|Sam|Riley|Leo|Mia)\s+(worries|resists|thought)\s+",
            "",
            sentence,
            flags=re.IGNORECASE,
        )
        return _shorten_label(sentence)
    if "pattern interrupt" in header.lower():
        return "Pushback & a cleaner read"
    return "Common worry & pushback"


class _ViewerChapterLabelBuilder:
    """Turn internal ## section headers into viewer-facing YouTube chapter titles."""

    def __init__(
        self,
        *,
        draft_text: str,
        youtube: dict[str, Any],
        manifest: dict[str, Any],
    ) -> None:
        self._threads = _parse_teaching_plan_threads(draft_text)
        self._teaching_labels = _plan_teaching_labels(draft_text, self._threads)
        self._teaching_idx = 0
        self._key_phrases = _parse_key_phrases(draft_text)
        self._hook = str(youtube.get("hookText") or "").strip()
        self._learner_problem = str(manifest.get("description") or youtube.get("description") or "").strip()
        meta = {
            "Micro-Pocket": _parse_bracket_block(draft_text, "Micro-Pocket"),
            "Recycle": _parse_bracket_block(draft_text, "Recycle"),
            "Word Tour": _parse_bracket_block(draft_text, "Word Tour"),
            "Meta Pivot": _parse_bracket_block(draft_text, "Meta Pivot"),
        }
        self._micro_pocket = meta["Micro-Pocket"]
        self._recycle = meta["Recycle"]
        self._word_tour = meta["Word Tour"]
        self._meta_pivot = meta["Meta Pivot"]

    def label_for(self, header: str) -> str:
        kind = _classify_section(header)
        if kind == "intro":
            return _shorten_label(self._hook or "What this episode covers")
        if kind == "teaching":
            if self._teaching_idx < len(self._teaching_labels):
                label = self._teaching_labels[self._teaching_idx]
                self._teaching_idx += 1
                return _shorten_label(label)
            if self._learner_problem:
                return _shorten_label(self._learner_problem)
            return _shorten_label(_clean_header_label(header))
        if kind == "micro_pocket":
            return _micro_pocket_label(self._micro_pocket)
        if kind == "recycle":
            return _recycle_label(self._recycle, header)
        if kind == "meta_pivot":
            if self._meta_pivot:
                return _shorten_label(self._meta_pivot)
            return "Practice: say your line out loud"
        if kind == "word_tour":
            base = _word_tour_label(self._word_tour, self._key_phrases)
            if "close" in header.lower():
                return _shorten_label(f"{base} & close")
            return base
        if kind == "close":
            return "Recap & your practice"
        return _shorten_label(_clean_header_label(header))


def auto_derive_markers_from_draft(
    draft_path: Path,
    manifest: dict[str, Any],
    *,
    youtube: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Map each ``## `` header in the draft to the first dialogue turn after it.

    Labels are **viewer-facing** (Teaching Plan threads, hookText, Micro-Pocket /
    Recycle / Word Tour metadata) — never raw production headers like
    ``Teaching Dialogue`` or ``Meta Pivot``.
    """
    if not draft_path.is_file():
        return []
    draft_text = draft_path.read_text(encoding="utf-8")
    host_pattern = re.compile(r"^(Ethan|Nora|Riley|Sam|Leo|Mia)\s*:")
    turns = manifest["turns"]
    label_builder = _ViewerChapterLabelBuilder(
        draft_text=draft_text,
        youtube=youtube or {},
        manifest=manifest,
    )
    markers: list[dict[str, str]] = []
    turn_index = 0
    pending_header: str | None = None

    for line in draft_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            pending_header = stripped
            continue
        if pending_header is not None and host_pattern.match(stripped):
            if turn_index < len(turns):
                markers.append(
                    {
                        "turnId": str(turns[turn_index]["id"]),
                        "label": label_builder.label_for(pending_header),
                    }
                )
            pending_header = None
        if host_pattern.match(stripped):
            turn_index += 1

    return markers


def resolve_markers(
    timeline: list[dict[str, Any]],
    markers: list[dict[str, str]],
    *,
    intro_offset_sec: float = DEFAULT_INTRO_OFFSET_SEC,
) -> list[dict[str, Any]]:
    by_id = {str(item["id"]): item for item in timeline}
    resolved: list[dict[str, Any]] = []
    for marker in markers:
        turn_id = str(marker["turnId"])
        if turn_id not in by_id:
            raise KeyError(f"Unknown turn id for YouTube marker: {turn_id}")
        entry = by_id[turn_id]
        audio_start = float(entry["startSec"])
        video_start = audio_start + intro_offset_sec
        resolved.append(
            {
                "turnId": turn_id,
                "label": str(marker["label"]).strip(),
                "audioStartSec": round(audio_start, 3),
                "videoTimestampSec": round(video_start, 3),
                "videoTimestamp": _format_timestamp(video_start),
                "speaker": entry.get("speaker"),
                "textPreview": str(entry.get("text", ""))[:120],
            }
        )
    resolved.sort(key=lambda item: float(item["videoTimestampSec"]))
    return resolved


def _format_timestamps_block(markers: list[dict[str, Any]]) -> str:
    return "\n".join(f"{m['videoTimestamp']} {m['label']}" for m in markers)


def _default_hashtags(tags: list[str]) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for tag in tags:
        t = str(tag).strip().replace(" ", "")
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(f"#{t}")
    return " ".join(out)


def _programming_footer(repo_root: Path = REPO) -> list[str]:
    path = repo_root / "configs" / "channel" / "programming.json"
    if not path.is_file():
        return []
    payload = load_json(path)
    if payload.get("schema") != "youtube-channel-programming-v1":
        raise ValueError(f"Unsupported channel programming schema: {payload.get('schema')!r}")
    lines = payload.get("descriptionFooter")
    if not isinstance(lines, list) or not all(isinstance(line, str) and line.strip() for line in lines):
        raise ValueError("Channel programming descriptionFooter must be a non-empty string list")
    return [line.strip() for line in lines]


def assemble_description(
    *,
    youtube: dict[str, Any],
    markers: list[dict[str, Any]],
    show_name: str,
    level_band: str,
    schedule_lines: list[str] | None = None,
) -> str:
    timestamps_block = _format_timestamps_block(markers)
    blocks: list[str] = []

    opening = str(youtube.get("openingHook") or youtube.get("description") or "").strip()
    if opening:
        blocks.append(opening)

    summary = str(youtube.get("chapterSummary") or "").strip()
    if summary:
        blocks.append(summary)

    if timestamps_block:
        blocks.append("🎧 Chapter timestamps:\n" + timestamps_block)

    highlights = youtube.get("chapterHighlights") or []
    if highlights:
        blocks.append("📖 In this episode:\n" + "\n".join(f"– {str(h).strip()}" for h in highlights if str(h).strip()))

    question = str(youtube.get("engagementQuestion") or "").strip()
    if question:
        blocks.append("💬 " + question)

    cta = str(youtube.get("subscribeCta") or "").strip()
    if not cta:
        cta = (
            f"Subscribe to {show_name} for more {level_band} English listening practice. "
            "New episodes every week."
        )
    blocks.append(cta)

    if schedule_lines:
        blocks.append("📅 New episodes on a fixed schedule:\n" + "\n".join(schedule_lines))

    hashtags = str(youtube.get("hashtags") or "").strip()
    if not hashtags:
        hashtags = _default_hashtags(list(youtube.get("tags") or []))
    if hashtags:
        blocks.append(hashtags)

    return "\n\n".join(b for b in blocks if b)


def prepare_episode_youtube_packaging(
    workspace: Path,
    *,
    episode: str,
    intro_offset_sec: float | None = None,
    write_files: bool = True,
) -> dict[str, Any]:
    paths = artifact_paths(workspace, episode)
    manifest_path = paths["manifest"]
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    manifest = load_json(manifest_path)

    youtube_path = paths["youtube"]
    if not youtube_path.is_file():
        raise FileNotFoundError(f"Missing youtube.json: {youtube_path}")
    youtube = load_json(youtube_path)

    timeline = episode_timeline(workspace, manifest)
    resolved_intro_offset_sec, offset_source = resolve_video_intro_offset(
        paths,
        explicit_offset_sec=intro_offset_sec,
    )

    markers_in = youtube.get("chapterMarkers") or []
    if markers_in:
        markers = [{"turnId": str(m["turnId"]), "label": str(m["label"])} for m in markers_in]
    else:
        markers = auto_derive_markers_from_draft(paths["draft"], manifest, youtube=youtube)
        if not markers:
            # Fallback: one marker at the start.
            markers = [{"turnId": str(manifest["turns"][0]["id"]), "label": "Episode start"}]

    resolved = resolve_markers(timeline, markers, intro_offset_sec=resolved_intro_offset_sec)
    timestamps_block = _format_timestamps_block(resolved)

    show_name = str(youtube.get("showName") or manifest.get("title", "")).strip()
    level_band = str(manifest.get("targetLevel", ""))
    description = assemble_description(
        youtube=youtube,
        markers=resolved,
        show_name=show_name,
        level_band=level_band,
        schedule_lines=_programming_footer(),
    )
    title = str(youtube.get("title") or youtube.get("hookText") or "").strip()
    _enforce_title_limit(title)

    packaging = {
        "schema": "elr-episode-youtube-packaging-v1",
        "episodeId": episode,
        "showId": str(manifest.get("showId", "")),
        "videoIntroOffsetSec": round(resolved_intro_offset_sec, 3),
        "videoIntroOffsetSource": offset_source,
        "title": title,
        "description": description,
        "descriptionTimestampsBlock": timestamps_block,
        "chapterMarkers": resolved,
        "timelineTurns": len(timeline),
        "totalDurationSec": round(float(timeline[-1]["endSec"]) if timeline else 0.0, 3),
    }

    if write_files:
        paths["reportsDir"].mkdir(parents=True, exist_ok=True)
        paths["youtubeDescription"].write_text(description + "\n", encoding="utf-8", newline="\n")
        title_path = paths["reportsDir"] / f"000_{episode}.youtube_title.txt"
        title_path.write_text(title + "\n", encoding="utf-8", newline="\n")
        packaging_path = paths["reportsDir"] / f"000_{episode}.youtube_packaging.json"
        write_json(packaging_path, packaging)

    return packaging


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve YouTube chapter timestamps from rendered turn durations and assemble the upload description."
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--episode", required=True, help="Episode id, e.g. episode_001")
    parser.add_argument(
        "--intro-offset",
        type=float,
        default=None,
        help=(
            "Explicit seconds added to every timestamp. By default, branded episodes use the "
            "measured intro media duration; legacy body-only episodes use "
            f"{DEFAULT_INTRO_OFFSET_SEC} seconds."
        ),
    )
    parser.add_argument("--no-files", action="store_true", help="Do not write description/title/packaging files.")
    args = parser.parse_args()

    packaging = prepare_episode_youtube_packaging(
        Path(args.workspace),
        episode=args.episode,
        intro_offset_sec=args.intro_offset,
        write_files=not args.no_files,
    )
    print(f"episode={packaging['episodeId']} show={packaging['showId']}", flush=True)
    print(f"markers={len(packaging.get('chapterMarkers') or [])}", flush=True)
    print(f"totalDurationSec={packaging.get('totalDurationSec')}", flush=True)
    print(f"title={packaging['title']}", flush=True)
    print("\n" + packaging["description"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
