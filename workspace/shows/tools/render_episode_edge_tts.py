"""Interim episode TTS via edge-tts when VoxCPM cannot load."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_reference_concat_audio import build_concat_audio  # noqa: E402

VOICES = {
    "series_a": {"Nora": "en-US-JennyNeural", "Ethan": "en-US-GuyNeural"},
    "series_b": {"Riley": "en-US-JennyNeural", "Sam": "en-US-GuyNeural"},
    "series_c": {"Mia": "en-US-JennyNeural", "Leo": "en-US-GuyNeural"},
}


async def _synth(text: str, voice: str, out: Path) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--gap-sec", type=float, default=0.32)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    workspace = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    show_id = manifest["showId"]
    voices = VOICES[show_id]
    clips: list[Path] = []

    for turn in manifest["turns"]:
        speaker = turn["speaker"]
        out = workspace / str(turn["filename"])
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"edge-tts {turn['id']} {speaker} -> {out.name}", flush=True)
        asyncio.run(_synth(str(turn["text"]), voices[speaker], out))
        clips.append(out)

    raw = workspace / f"000_{manifest['episodeId']}.raw.wav"
    build_concat_audio(clips, raw, gap_sec=args.gap_sec)
    print(f"raw={raw.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
