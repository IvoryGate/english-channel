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
VERY_SHORT_WORD_LIMIT = 4
VERY_SHORT_MAX_LEN = 56
DEFAULT_PACE_CUE = "unhurried pace"
DEFAULT_REFERENCE_TEMPO_RATIO = 1.0
SHORT_CONTROL = "same cloned narrator, slightly slower"
LONG_DIALOGUE_WORD_LIMIT = 35
SEGMENT_PEAK_NORMALIZE_TARGET = 0.88
SEGMENT_PEAK_BOOST_BELOW = 0.45


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
    return workspace / f"000_{chapter}_raw.wav"


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


def normalize_segment_peak(
    y: np.ndarray,
    target_peak: float = SEGMENT_PEAK_NORMALIZE_TARGET,
    boost_if_peak_below: float = SEGMENT_PEAK_BOOST_BELOW,
) -> np.ndarray:
    """Peak-normalize quiet segments only (not time-stretch)."""
    if len(y) == 0:
        return y
    peak = float(np.max(np.abs(y)))
    if peak <= 0 or peak >= boost_if_peak_below:
        return y
    return (y / peak * target_peak).astype(np.float32, copy=False)


def short_segment_max_len(segment: dict[str, Any], words: int) -> int | None:
    override = segment.get("maxLen")
    if override is not None:
        return int(override)
    if words <= VERY_SHORT_WORD_LIMIT:
        return VERY_SHORT_MAX_LEN
    if words <= SHORT_SEGMENT_WORD_LIMIT:
        return SHORT_SEGMENT_MAX_LEN
    return None


def compose_control(
    segment: dict[str, Any],
    global_control: str,
    pace_cue: str | None = None,
    character_profiles: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build TTS prompt. global_control is manifest metadata only; do not inject it into ttsText.

    character_profiles gives one stable cue per speaker for dialogue consistency.
    pace_cue is opt-in via manifest paceCue only.
    """
    _ = global_control
    profiles = character_profiles or {}
    speaker = str(segment.get("speaker", "narrator"))
    character = str(profiles.get(speaker, "")).strip()
    delivery_cue = str(segment.get("deliveryCue", "plain understated narration"))
    text = str(segment["text"])
    words = int(segment.get("wordCount") or word_count(text))
    kind = str(segment.get("kind", "narration"))
    pace = pace_cue.strip() if pace_cue else ""

    def join_control(*parts: str) -> str:
        return ", ".join(part.strip() for part in parts if part and part.strip())

    render_policy = str(segment.get("renderPolicy", ""))
    force_delivery = render_policy == "include_delivery_cue"
    max_len = short_segment_max_len(segment, words) if kind == "dialogue" or words <= SHORT_SEGMENT_WORD_LIMIT else None

    if kind == "dialogue":
        if character and words > LONG_DIALOGUE_WORD_LIMIT and not force_delivery:
            control = character
            policy = "character-only-long-dialogue"
        elif character:
            control = join_control(character, delivery_cue)
            policy = "character-dialogue-cue" if not force_delivery else "character-long-with-delivery"
        else:
            control = join_control(pace, delivery_cue) if pace else delivery_cue
            policy = "compact-dialogue-cue"
        return {
            "ttsText": f"({control}) {text}",
            "control": control,
            "maxLen": max_len,
            "policy": "character-short-dialogue"
            if words <= SHORT_SEGMENT_WORD_LIMIT and character
            else policy,
        }

    if words <= SHORT_SEGMENT_WORD_LIMIT:
        control = join_control(SHORT_CONTROL, pace, delivery_cue)
        return {
            "ttsText": f"({control}) {text}",
            "control": control,
            "maxLen": max_len or SHORT_SEGMENT_MAX_LEN,
            "policy": "compact-short-segment-control",
        }
    control = join_control("same cloned narrator", pace, delivery_cue)
    return {
        "ttsText": f"({control}) {text}",
        "control": control,
        "maxLen": None,
        "policy": "compact-narration-cue",
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


def subtitle_text(raw: str) -> str:
    text = str(raw).strip()
    for left, right in (('"', '"'), ('"', '"'), ("'", "'"), ("「", "」")):
        if text.startswith(left) and text.endswith(right):
            return text[len(left) : -len(right)].strip()
    return text


def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def chapter_srt_path(workspace: Path) -> Path:
    chapter = workspace.name
    return workspace / f"000_{chapter}.srt"


def inter_segment_silence_sec(manifest: dict[str, Any], workspace: Path) -> float:
    run_path = run_manifest_path(workspace)
    if run_path.is_file():
        run = load_json(run_path)
        value = run.get("interSegmentSilenceSec")
        if value is not None:
            return float(value)
    value = manifest.get("interSegmentSilenceSec")
    if value is not None:
        return float(value)
    return DEFAULT_INTER_SEGMENT_SILENCE_SEC


def chapter_timeline(
    workspace: Path,
    manifest: dict[str, Any] | None = None,
    silence_sec: float | None = None,
) -> list[dict[str, Any]]:
    manifest = ensure_segment_defaults(manifest or load_json(manifest_path(workspace)))
    silence = float(silence_sec) if silence_sec is not None else inter_segment_silence_sec(manifest, workspace)
    cursor = 0.0
    timeline: list[dict[str, Any]] = []
    for segment in manifest["segments"]:
        path = workspace / str(segment["filename"])
        if not path.is_file():
            raise FileNotFoundError(f"Missing segment audio: {path}")
        wav, _sr = read_mono(path)
        duration = float(len(wav) / _sr)
        start = cursor
        end = start + duration
        timeline.append(
            {
                "id": segment["id"],
                "order": segment["order"],
                "filename": segment["filename"],
                "speaker": segment["speaker"],
                "text": subtitle_text(str(segment["text"])),
                "startSec": round(start, 3),
                "endSec": round(end, 3),
                "durationSec": round(duration, 3),
            }
        )
        cursor = end + silence
    return timeline
