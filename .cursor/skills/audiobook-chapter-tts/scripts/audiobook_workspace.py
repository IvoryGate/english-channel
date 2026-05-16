from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal


DEFAULT_MODEL_ID = "pretrained_models/VoxCPM2"
DEFAULT_GLOBAL_CONTROL = (
    "one consistent cloned audiobook narrator, same voice throughout, calm literary narration, "
    "restrained expression, no character voice change"
)
DEFAULT_CFG_VALUE = 2.25
DEFAULT_INFERENCE_TIMESTEPS = 10
DEFAULT_INTER_SEGMENT_SILENCE_SEC = 0.34
SHORT_SEGMENT_WORD_LIMIT = 12
SHORT_SEGMENT_MAX_LEN = 128
SHORT_CONTROL = "same cloned narrator, slightly slower"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "book"


def chapter_id(chapter: int) -> str:
    return f"chapter_{chapter:03d}"


def workspace_path(book: str, chapter: int, root: str = "workspace") -> Path:
    return Path(root) / slugify(book) / chapter_id(chapter)


def manifest_path(workspace: Path) -> Path:
    chapter = workspace.name
    return workspace / f"000_{chapter}.segments.json"


def source_text_path(workspace: Path) -> Path:
    chapter = workspace.name
    return workspace / f"000_{chapter}.source.txt"


def final_audio_path(workspace: Path) -> Path:
    chapter = workspace.name
    return workspace / f"000_{chapter}.raw.wav"


def run_manifest_path(workspace: Path) -> Path:
    chapter = workspace.name
    return workspace / f"000_{chapter}.run.json"


def clean_reference_path(workspace: Path) -> Path:
    return workspace / "000_reference_clean.wav"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def speaker_slug(speaker: str) -> str:
    return slugify(speaker.replace(".", ""))


def segment_filename(order: int, speaker: str) -> str:
    return f"{order:03d}_{speaker_slug(speaker)}.wav"


def normalize_segment_id(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("Empty segment id")
    if value.isdigit():
        return f"{int(value):03d}"
    match = re.search(r"(\d{1,4})$", value)
    if match:
        return f"{int(match.group(1)):03d}"
    return value


def parse_segment_ids(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {normalize_segment_id(value) for value in raw.split(",") if value.strip()}


def ensure_segment_defaults(manifest: dict[str, Any]) -> dict[str, Any]:
    for index, segment in enumerate(manifest.get("segments", []), start=1):
        order = int(segment.get("order", index))
        segment["order"] = order
        segment["id"] = normalize_segment_id(str(segment.get("id", f"{order:03d}")))
        segment.setdefault("kind", "narration")
        segment.setdefault("speaker", "narrator")
        segment.setdefault("deliveryCue", "plain understated narration")
        segment["wordCount"] = int(segment.get("wordCount") or word_count(str(segment.get("text", ""))))
        segment.setdefault("filename", segment_filename(order, str(segment["speaker"])))
    return manifest


def compose_control(segment: dict[str, Any], global_control: str) -> dict[str, Any]:
    delivery_cue = str(segment.get("deliveryCue", "plain understated narration"))
    text = str(segment["text"])
    words = int(segment.get("wordCount") or word_count(text))
    if words <= SHORT_SEGMENT_WORD_LIMIT:
        control = f"{SHORT_CONTROL}, {delivery_cue}"
        return {
            "ttsText": f"({control}) {text}",
            "control": control,
            "maxLen": SHORT_SEGMENT_MAX_LEN,
            "policy": "compact-short-segment-control",
        }
    global_suffix = "slightly slower and unhurried pacing"
    control = f"{global_control}, {global_suffix}, {delivery_cue}"
    return {
        "ttsText": f"({control}) {text}",
        "control": control,
        "maxLen": None,
        "policy": "full-global-control",
    }


def light_master_raw(y: np.ndarray, sr: int) -> np.ndarray:
    if len(y) == 0:
        return y
    y = y - float(np.mean(y))
    highpass = signal.butter(2, 70, btype="highpass", fs=sr, output="sos")
    y = signal.sosfiltfilt(highpass, y).astype(np.float32)
    peak = float(np.max(np.abs(y)))
    if peak > 0:
        y = (y / peak * 0.90).astype(np.float32)
    return y


def read_mono(path: Path) -> tuple[np.ndarray, int]:
    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio.astype(np.float32, copy=False), sr
