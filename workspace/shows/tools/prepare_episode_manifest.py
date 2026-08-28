from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parent))
from episode_youtube_meta import sync_youtube_json  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[3]
SHOW_CONFIG_PATH = Path(__file__).resolve().parent / "show_config.json"
VOICE_PROFILES_PATH = REPO_ROOT / "workspace" / "dialogue_podcast_research" / "voices" / "voice_profiles.json"


def voice_profiles_path() -> Path:
    if VOICE_PROFILES_PATH.exists():
        return VOICE_PROFILES_PATH
    # A Git worktree intentionally excludes the shared generated research workspace.
    # Resolve the primary checkout without copying audio/model assets into every branch.
    if REPO_ROOT.parent.name == ".worktrees":
        shared = REPO_ROOT.parent.parent / "workspace" / "dialogue_podcast_research" / "voices" / "voice_profiles.json"
        if shared.exists():
            return shared
    return VOICE_PROFILES_PATH

DELIVERY_RE = re.compile(r"^\[Delivery:\s*(.+?)\]\s*$")
SECTION_RE = re.compile(r"^\[(.+?)\]\s*$")
MARKDOWN_SECTION_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
METADATA_LINE_RE = re.compile(r"^(Title|Description|Target Level|Estimated Duration|Hosts|Show Profile|Archetype|Learner Problem|Key Phrases|T1|T2|T3):")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def target_max_len(words: int) -> int | None:
    # Match audiobook short-segment caps; long turns leave max_len unset.
    # Single-word mirror echoes (Series C Word Tour) need a tight cap — VoxCPM
    # otherwise hallucinates 5–9s clips that fail SHORT_TOO_LONG QC.
    if words <= 1:
        return 28
    if words <= 4:
        return 48
    if words <= 12:
        return 128
    return None


def pause_after_for(section: str, show_id: str) -> float:
    if section in {"Micro-Pocket", "Word Tour"}:
        return 0.42
    if section == "Close":
        return 0.32
    if show_id == "series_b" and section.startswith("Part"):
        return 0.34
    return 0.26


def parse_metadata(lines: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in lines:
        if METADATA_LINE_RE.match(line.strip()):
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta


def parse_turns(text: str, show: dict[str, Any]) -> list[dict[str, Any]]:
    host_pattern = re.compile(show["hostLinePattern"])
    hosts = show["hosts"]
    skip_sections = {"Teaching Plan", "Structure Map", "Publish Packaging", "Episode Contract"}
    turns: list[dict[str, Any]] = []
    section = ""
    delivery_cue = ""
    in_script = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "---":
            in_script = True
            continue
        delivery_match = DELIVERY_RE.match(stripped)
        if delivery_match:
            delivery_cue = delivery_match.group(1)
            continue
        section_match = SECTION_RE.match(stripped)
        if not section_match:
            section_match = MARKDOWN_SECTION_RE.match(stripped)
        if section_match:
            section = section_match.group(1)
            in_script = section not in skip_sections
            continue
        host_match = host_pattern.match(stripped)
        if not host_match or not in_script:
            continue
        speaker = host_match.group(1)
        if speaker not in hosts:
            continue
        spoken_text = stripped.split(":", 1)[1].strip()
        order = len(turns) + 1
        words = word_count(spoken_text)
        turn: dict[str, Any] = {
            "id": f"p{order:03d}",
            "order": order,
            "section": section,
            "speaker": speaker,
            "text": spoken_text,
            "wordCount": words,
            "filename": f"turn_{order:03d}.wav",
            "deliveryCue": delivery_cue,
            "pauseAfterSec": pause_after_for(section, show["showId"]),
        }
        max_len = target_max_len(words)
        if max_len is not None:
            turn["maxLen"] = max_len
        turns.append(turn)
    return turns


def source_spoken_word_count(text: str, show: dict[str, Any]) -> int:
    """Count every host line that belongs to a spoken section in the draft."""
    host_pattern = re.compile(show["hostLinePattern"])
    hosts = set(show["hosts"])
    skip_sections = {"Teaching Plan", "Structure Map", "Publish Packaging", "Episode Contract"}
    section = ""
    in_script = False
    total = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            in_script = True
            continue
        section_match = SECTION_RE.match(stripped)
        if not section_match:
            section_match = MARKDOWN_SECTION_RE.match(stripped)
        if section_match:
            section = section_match.group(1)
            in_script = section not in skip_sections
            continue
        if not in_script or section in skip_sections:
            continue
        host_match = host_pattern.match(stripped)
        if host_match and host_match.group(1) in hosts:
            total += word_count(stripped.split(":", 1)[1].strip())
    return total


def manifest_coverage(text: str, show: dict[str, Any], turns: list[dict[str, Any]]) -> dict[str, float | int]:
    source_words = source_spoken_word_count(text, show)
    manifest_words = sum(int(turn.get("wordCount") or 0) for turn in turns)
    ratio = 1.0 if source_words == 0 else manifest_words / source_words
    return {"sourceWords": source_words, "manifestWords": manifest_words, "ratio": ratio}


def infer_show_id(draft_path: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    text = draft_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.lower().startswith("show profile:"):
            profile = line.split(":", 1)[1].strip()
            if profile in {"series_a", "series_b", "series_c", "polished_english"}:
                return "series_c" if profile == "polished_english" else profile
    parts = draft_path.as_posix().split("/")
    for part in parts:
        if part in {"series_a", "series_b", "series_c"}:
            return part
    raise ValueError("Could not infer show id; pass --show series_a|series_b|series_c")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build episode_manifest.json from a show draft.")
    parser.add_argument("--draft", required=True, help="Path to 000_episode_XXX.draft.md")
    parser.add_argument("--show", choices=["series_a", "series_b", "series_c"], help="Show id override.")
    parser.add_argument("--output", help="Output manifest path; default beside draft.")
    args = parser.parse_args()

    draft_path = Path(args.draft).resolve()
    repo_root = REPO_ROOT.resolve()
    show_id = infer_show_id(draft_path, args.show)
    config = load_json(SHOW_CONFIG_PATH)
    show = config["shows"][show_id]
    voices = load_json(voice_profiles_path())["profiles"]
    text = draft_path.read_text(encoding="utf-8")
    meta = parse_metadata(text.splitlines())
    turns = parse_turns(text, show)
    if not turns:
        raise ValueError(f"No host turns parsed from {draft_path}")
    coverage = manifest_coverage(text, show, turns)
    if float(coverage["ratio"]) < 0.98:
        raise ValueError(
            "Manifest covers only "
            f"{float(coverage['ratio']) * 100:.1f}% of spoken draft words "
            f"({coverage['manifestWords']}/{coverage['sourceWords']}); fix section parsing before rendering."
        )

    episode_dir = draft_path.parent
    episode_id = episode_dir.name
    manifest_path = Path(args.output) if args.output else episode_dir / f"000_{episode_id}.episode_manifest.json"

    hosts_block: dict[str, Any] = {}
    for host in show["hosts"]:
        profile = voices[host]
        hosts_block[host] = {
            "role": profile.get("role", "host"),
            "referenceAudioClean": profile["referenceAudioClean"],
            "referenceText": profile["referenceText"],
        }

    manifest = {
        "schema": "dialogue-podcast-episode-v1",
        "episodeId": episode_id,
        "showId": show_id,
        "showProfile": show["showProfile"],
        "title": meta.get("Title", ""),
        "description": meta.get("Description", ""),
        "targetLevel": meta.get("Target Level", show["levelBand"]),
        "estimatedDuration": meta.get("Estimated Duration", "15-20 minutes"),
        "sourceDraft": str(draft_path.relative_to(repo_root)).replace("\\", "/"),
        "hosts": hosts_block,
        "renderSettings": {
            "modelId": "pretrained_models/VoxCPM2",
            "device": "cuda",
            **show["renderSettings"],
            "outputAudio": f"000_{episode_id}.raw.wav",
            "renderReport": f"000_{episode_id}.render_report.json",
        },
        "turns": turns,
        "sourceCoverage": coverage,
    }
    write_json(manifest_path, manifest)
    sync = sync_youtube_json(episode_dir, episode_id, manifest=manifest, write=True)
    print(f"manifest={manifest_path}")
    print(f"show={show_id} turns={len(turns)} words={sum(int(t['wordCount']) for t in turns)}")
    print(f"coverage={float(coverage['ratio']) * 100:.1f}%")
    if sync.get("changed"):
        print(f"youtube.json synced hookText={sync.get('hookText')!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
