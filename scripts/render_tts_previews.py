from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

REPO = Path(__file__).resolve().parents[1]
WORKER = REPO / "apps" / "worker-py"
TOOLS = REPO / "workspace" / "shows" / "tools"
for value in (WORKER, TOOLS):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

from master_episode_audio import loudnorm_two_pass, measure_loudness, probe_duration_sec  # noqa: E402
from worker.classics.asr_qc import asr_qc_chapter  # noqa: E402
from worker.classics.audio_render import render_audio  # noqa: E402
from worker.classics.config import load_book_config  # noqa: E402
from worker.classics.io import atomic_write_json  # noqa: E402
from worker.classics.paths import ClassicPaths  # noqa: E402


PYTHON = REPO / ".conda-env" / "python.exe"
PREVIEW_ROOT = REPO / "workspace" / "runtime" / "tts-audition" / "previews"
SHOW_CONFIG = TOOLS / "show_config.json"
PREVIEW_SEED_OFFSETS = {("chatterbox-500m-dialogue", "p004"): 1000}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def word_count(item: dict[str, Any]) -> int:
    value = item.get("wordCount")
    if isinstance(value, int):
        return value
    text = str(item.get("text") or item.get("spokenText") or "")
    return len(re.findall(r"\b[\w'-]+\b", text))


def select_three_zone_sample(items: list[dict[str, Any]], target_words: int = 520) -> list[dict[str, Any]]:
    if len(items) < 3:
        return list(items)
    per_zone = max(1, target_words // 3)
    starts = [0, len(items) // 2, max(0, (len(items) * 4) // 5)]
    selected: dict[str, dict[str, Any]] = {}
    for start in starts:
        words = 0
        for item in items[start:]:
            key = str(item["id"])
            if key in selected:
                continue
            selected[key] = item
            words += word_count(item)
            if words >= per_zone:
                break
    return sorted(selected.values(), key=lambda item: int(item["order"]))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dialogue_manifest(show_id: str, source_episode: str, preview_id: str) -> Path:
    source_path = (
        REPO
        / "workspace"
        / "shows"
        / show_id
        / source_episode
        / f"000_{source_episode}.episode_manifest.json"
    )
    source = read_json(source_path)
    show = read_json(SHOW_CONFIG)["shows"][show_id]
    turns = select_three_zone_sample(list(source["turns"]))
    for turn in turns:
        offset = PREVIEW_SEED_OFFSETS.get((preview_id, str(turn["id"])))
        if offset is not None:
            turn["ttsSeedOffset"] = offset
    hosts = dict(source["hosts"])
    for name, host_value in hosts.items():
        host = dict(host_value)
        if show["renderSettings"]["ttsProvider"] == "kokoro":
            host["voice"] = {"kind": "preset", "voiceId": show["presetVoices"][name]}
        else:
            reference = str(host["referenceAudioClean"])
            host["voice"] = {
                "kind": "clone",
                "referencePath": reference,
                "referenceSha256": sha256_file(REPO / reference),
            }
        hosts[name] = host
    root = PREVIEW_ROOT / preview_id
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / f"000_{preview_id}.episode_manifest.json"
    render_settings = {
        **show["renderSettings"],
        "outputAudio": f"000_{preview_id}.raw.wav",
        "renderReport": f"000_{preview_id}.render_report.json",
    }
    manifest = {
        **source,
        "episodeId": preview_id,
        "title": f"TTS preview: {source.get('title', source_episode)}",
        "hosts": hosts,
        "renderSettings": render_settings,
        "turns": turns,
        "previewSelection": {
            "sourceManifest": source_path.relative_to(REPO).as_posix(),
            "method": "ordered excerpts from opening, middle, and final emotional zone",
            "words": sum(word_count(item) for item in turns),
        },
    }
    atomic_write_json(manifest_path, manifest)
    return manifest_path


def run_dialogue(show_id: str, source_episode: str, preview_id: str) -> dict[str, Any]:
    manifest = dialogue_manifest(show_id, source_episode, preview_id)
    commands = [
        [str(PYTHON), "-u", str(TOOLS / "render_episode.py"), "--manifest", str(manifest), "--no-self-check", "--skip-existing"],
        # Provider-native clips can be quieter than delivery audio. Record all
        # raw-turn findings, then let mastering normalize the listening copy.
        [str(PYTHON), "-u", str(TOOLS / "check_episode.py"), "--manifest", str(manifest), "--write-report", "--asr-all", "--asr-device", "cpu"],
        [str(PYTHON), "-u", str(TOOLS / "master_episode_audio.py"), "--manifest", str(manifest)],
    ]
    for command in commands:
        subprocess.run(command, cwd=REPO, check=True)
    qc = read_json(manifest.parent / "reports" / f"000_{preview_id}.qc.json")
    content_flags = {"ASR_LONGER", "SHORT_TOO_LONG", "CLIPPING", "MISSING"}
    number_words = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "twenty": "20", "thirty": "30", "forty": "40",
        "fifty": "50", "sixty": "60",
    }

    def asr_ratio(row: dict[str, Any]) -> float:
        def tokens(value: str) -> list[str]:
            return [number_words.get(token, token) for token in re.findall(r"[a-z]+|\d+", value.lower())]

        return SequenceMatcher(None, tokens(str(row.get("text") or "")), tokens(str(row.get("asrText") or ""))).ratio()

    blocked = [
        str(row["id"])
        for row in qc.get("segments", [])
        if content_flags.intersection(row.get("flags", []))
        or ("ASR_MISMATCH" in row.get("flags", []) and asr_ratio(row) < 0.82)
    ]
    if blocked:
        raise RuntimeError(f"{preview_id} content QC review required: {blocked}")
    report = read_json(manifest.parent / "reports" / f"000_{preview_id}.master_report.json")
    duration = float(report["durationSec"])
    if not 180 <= duration <= 300:
        raise RuntimeError(f"{preview_id} duration {duration:.1f}s is outside the 3–5 minute gate")
    return {
        "id": preview_id,
        "provider": read_json(manifest)["renderSettings"]["ttsProvider"],
        "listenPath": report["masterWav"],
        "durationSec": duration,
        "manifestPath": manifest.relative_to(REPO).as_posix(),
        "qcPath": (manifest.parent / "reports" / f"000_{preview_id}.qc.json").relative_to(REPO).as_posix(),
    }


def run_classic() -> dict[str, Any]:
    config = load_book_config(REPO, "persuasion")
    paths = ClassicPaths(REPO, config.slug)
    chapter = 5
    segments = read_json(paths.segments(chapter))["segments"]
    # Isolated one-word interjections are a segmentation stress case rather
    # than a useful voice-quality comparison. Full chapters still retain and
    # gate them; the owner audition samples substantive phrases.
    eligible = [item for item in segments if word_count(item) >= 2]
    selected = select_three_zone_sample(eligible)
    selected_ids = {str(item["id"]) for item in selected}
    name = "chatterbox-500m-classic"
    trace = render_audio(
        REPO,
        config,
        chapter,
        selected_ids,
        preview_name=name,
        isolated_preview=True,
        force=False,
        seed_offsets={"104": 1000},
    )
    preview = REPO / str(trace["previewPath"])
    listen = preview.with_name(f"{name}.listen.wav")
    loudnorm_two_pass(preview, listen, integrated=-16.0, true_peak=-1.5)
    duration = probe_duration_sec(listen)
    if not 180 <= duration <= 300:
        raise RuntimeError(f"{name} duration {duration:.1f}s is outside the 3–5 minute gate")
    asr = asr_qc_chapter(
        REPO,
        config,
        chapter,
        selected_ids=selected_ids,
        model_name="base",
        preview_name=name,
    )
    if asr["reviewSegmentIds"]:
        raise RuntimeError(f"Classic ASR review required: {asr['reviewSegmentIds']}")
    metrics = measure_loudness(listen)
    return {
        "id": name,
        "provider": config.render["ttsProvider"],
        "listenPath": listen.relative_to(REPO).as_posix(),
        "durationSec": round(duration, 3),
        "tracePath": trace["tracePath"],
        "qcPath": asr["reportPath"],
        "loudness": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the three owner-gated TTS migration previews.")
    parser.add_argument(
        "--only",
        choices=["all", "kokoro-dialogue", "chatterbox-dialogue", "chatterbox-classic"],
        default="all",
    )
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    if args.only in {"all", "kokoro-dialogue"}:
        results.append(run_dialogue("series_b", "episode_025", "kokoro-dialogue"))
    if args.only in {"all", "chatterbox-dialogue"}:
        results.append(run_dialogue("series_a", "episode_024", "chatterbox-500m-dialogue"))
    if args.only in {"all", "chatterbox-classic"}:
        results.append(run_classic())
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    review_path = PREVIEW_ROOT / "review.json"
    if args.only != "all" and review_path.is_file():
        existing = read_json(review_path).get("previews", [])
        by_id = {str(item["id"]): item for item in existing}
        by_id.update({str(item["id"]): item for item in results})
        results = list(by_id.values())
    report = {
        "schema": "elr-tts-migration-previews-v1",
        "status": "awaiting_owner_listening",
        "previews": results,
    }
    atomic_write_json(review_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
