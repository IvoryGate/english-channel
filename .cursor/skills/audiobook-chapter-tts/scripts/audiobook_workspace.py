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
DEFAULT_MAX_SUBTITLE_SEC = 20.0
DEFAULT_MAX_SUBTITLE_CHARS = 84
SHORT_SEGMENT_WORD_LIMIT = 12
SHORT_SEGMENT_MAX_LEN = 128
VERY_SHORT_WORD_LIMIT = 4
VERY_SHORT_MAX_LEN = 56
DEFAULT_PACE_CUE = "unhurried pace"
DEFAULT_REFERENCE_TEMPO_RATIO = 1.0
SHORT_CONTROL = "same cloned narrator, slightly slower"
SEGMENT_PEAK_NORMALIZE_TARGET = 0.88
SEGMENT_PEAK_BOOST_BELOW = 0.45
QC_WARN_SEC_PER_WORD_HIGH = 0.7
QC_WARN_SEC_PER_WORD_LOW = 0.14
QC_WARN_TRAILING_SILENCE_SEC = 1.0
QC_SHORT_WORD_LIMIT = 4
QC_SHORT_TOO_LONG_SEC = 5.0
QC_CLIP_PEAK = 1.0
QC_COMPOSE_DRIFT_SEC = 0.5
QC_ASR_MATCH_RATIO = 0.75


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

    max_len = short_segment_max_len(segment, words) if kind == "dialogue" or words <= SHORT_SEGMENT_WORD_LIMIT else None

    if kind == "dialogue":
        if character:
            control = join_control(character, delivery_cue)
            policy = "character-dialogue-cue"
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


_PROTECTED_ABBREVS = (
    ("Mrs.", "\uf000"),
    ("Mr.", "\uf001"),
    ("Ms.", "\uf002"),
    ("Dr.", "\uf003"),
    ("Prof.", "\uf004"),
    ("St.", "\uf005"),
    ("Col.", "\uf006"),
    ("Gen.", "\uf007"),
    ("Capt.", "\uf008"),
    ("Lt.", "\uf009"),
)
_SUBTITLE_BREAK_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'])|(?<=[;:])\s+|(?<=\s)—\s+")


def _protect_abbreviations(text: str) -> str:
    for abbr, token in _PROTECTED_ABBREVS:
        text = text.replace(abbr, token)
    return text


def _restore_abbreviations(text: str) -> str:
    for abbr, token in _PROTECTED_ABBREVS:
        text = text.replace(token, abbr)
    return text


def _word_wrap_subtitle(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if len(candidate) <= max_chars:
            current.append(word)
            continue
        if current:
            lines.append(" ".join(current))
        current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _subtitle_phrase_parts(text: str) -> list[str]:
    protected = _protect_abbreviations(text.strip())
    parts = [part.strip() for part in _SUBTITLE_BREAK_RE.split(protected) if part.strip()]
    return [_restore_abbreviations(part) for part in parts]


def split_subtitle_chunks_for_duration(
    text: str,
    duration_sec: float,
    max_sec: float = DEFAULT_MAX_SUBTITLE_SEC,
    max_chars: int = DEFAULT_MAX_SUBTITLE_CHARS,
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if duration_sec <= max_sec:
        return [text]

    parts = _subtitle_phrase_parts(text)
    if not parts:
        return [text]

    total_words = max(len(text.split()), 1)
    chunks: list[str] = []
    current_parts: list[str] = []
    current_words = 0

    def estimated_duration(word_count: int) -> float:
        return duration_sec * (word_count / total_words)

    def flush_current() -> None:
        nonlocal current_parts, current_words
        if current_parts:
            chunks.append(" ".join(current_parts))
            current_parts = []
            current_words = 0

    for part in parts:
        part_words = len(part.split())
        candidate_parts = current_parts + [part]
        candidate_text = " ".join(candidate_parts)
        candidate_words = current_words + part_words
        part_alone_duration = estimated_duration(part_words)

        if part_alone_duration > max_sec or len(part) > max_chars:
            flush_current()
            if part_alone_duration > max_sec:
                wrapped = _word_wrap_subtitle(part, max_chars)
                for piece in wrapped:
                    if chunks and len(chunks[-1]) + 1 + len(piece) <= max_chars:
                        merged = f"{chunks[-1]} {piece}"
                        if estimated_duration(len(merged.split())) <= max_sec:
                            chunks[-1] = merged
                            continue
                    chunks.append(piece)
            else:
                chunks.append(part)
            continue

        if current_parts and (
            estimated_duration(candidate_words) > max_sec or len(candidate_text) > max_chars
        ):
            flush_current()
            current_parts = [part]
            current_words = part_words
            continue

        current_parts = candidate_parts
        current_words = candidate_words

    flush_current()
    return chunks if chunks else [text]


def expand_subtitle_timeline(
    timeline: list[dict[str, Any]],
    max_sec: float = DEFAULT_MAX_SUBTITLE_SEC,
    max_chars: int = DEFAULT_MAX_SUBTITLE_CHARS,
) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for entry in timeline:
        text = str(entry["text"]).strip()
        duration = float(entry["durationSec"])
        chunks = split_subtitle_chunks_for_duration(
            text,
            duration,
            max_sec=max_sec,
            max_chars=max_chars,
        )
        if len(chunks) <= 1:
            expanded.append(entry)
            continue

        start = float(entry["startSec"])
        end = float(entry["endSec"])
        weights = [max(len(chunk.split()), 1) for chunk in chunks]
        total_weight = float(sum(weights))
        cursor = start
        for index, chunk in enumerate(chunks):
            chunk_end = end if index == len(chunks) - 1 else cursor + duration * (weights[index] / total_weight)
            expanded.append(
                {
                    **entry,
                    "text": chunk,
                    "startSec": round(cursor, 3),
                    "endSec": round(chunk_end, 3),
                    "durationSec": round(chunk_end - cursor, 3),
                    "subtitlePart": index + 1,
                    "subtitleParts": len(chunks),
                }
            )
            cursor = chunk_end
    return expanded


def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


DEFAULT_VIDEO_INTRO_OFFSET_SEC = 3.0


def format_youtube_chapter_timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def chapter_youtube_path(workspace: Path) -> Path:
    chapter = workspace.name
    return workspace / f"000_{chapter}.youtube.json"


def resolve_youtube_markers(
    timeline: list[dict[str, Any]],
    markers: list[dict[str, Any]],
    *,
    intro_offset_sec: float = DEFAULT_VIDEO_INTRO_OFFSET_SEC,
) -> list[dict[str, Any]]:
    by_id = {str(item["id"]): item for item in timeline}
    resolved: list[dict[str, Any]] = []
    for marker in markers:
        segment_id = str(marker["segmentId"])
        if segment_id not in by_id:
            raise KeyError(f"Unknown segment id for YouTube marker: {segment_id}")
        entry = by_id[segment_id]
        audio_start = float(entry["startSec"])
        video_start = audio_start + intro_offset_sec
        resolved.append(
            {
                "segmentId": segment_id,
                "label": str(marker["label"]).strip(),
                "audioStartSec": round(audio_start, 3),
                "videoTimestampSec": round(video_start, 3),
                "videoTimestamp": format_youtube_chapter_timestamp(video_start),
                "speaker": entry.get("speaker"),
                "textPreview": str(entry.get("text", ""))[:120],
            }
        )
    resolved.sort(key=lambda item: float(item["videoTimestampSec"]))
    return resolved


def format_youtube_timestamps_block(markers: list[dict[str, Any]]) -> str:
    return "\n".join(f"{item['videoTimestamp']} {item['label']}" for item in markers)


def assemble_youtube_description(packaging: dict[str, Any]) -> str:
    highlights = packaging.get("chapterHighlights") or []
    highlight_lines = "\n".join(f"– {str(item).strip()}" for item in highlights if str(item).strip())
    blocks = [
        str(packaging.get("openingHook") or "").strip(),
        str(packaging.get("chapterSummary") or "").strip(),
    ]
    timestamps_block = str(packaging.get("descriptionTimestampsBlock") or "").strip()
    if timestamps_block:
        blocks.append("🎧 Chapter timestamps:\n" + timestamps_block)
    if highlight_lines:
        blocks.append("📖 In this chapter:\n" + highlight_lines)
    series = str(packaging.get("seriesBoilerplate") or "").strip()
    if series:
        blocks.append(series)
    playlist = str(packaging.get("playlistLabel") or "").strip()
    if playlist:
        blocks.append("🎧 Playlist:\n" + playlist)
    question = str(packaging.get("engagementQuestion") or "").strip()
    if question:
        blocks.append("💬 " + question)
    cta = str(packaging.get("subscribeCta") or "").strip()
    if cta:
        blocks.append(cta)
    hashtags = str(packaging.get("hashtags") or "").strip()
    if hashtags:
        blocks.append(hashtags)
    return "\n\n".join(block for block in blocks if block)


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


def chapter_qc_path(workspace: Path) -> Path:
    chapter = workspace.name
    return workspace / f"000_{chapter}.qc.json"


def trailing_silence_sec(
    audio: np.ndarray,
    sample_rate: int,
    threshold_ratio: float = 0.02,
) -> float:
    if len(audio) == 0:
        return 0.0
    peak = float(np.max(np.abs(audio)))
    if peak <= 0:
        return float(len(audio) / sample_rate)
    threshold = peak * threshold_ratio
    frame = max(1, int(sample_rate * 0.02))
    silent_samples = 0
    for start in range(len(audio) - frame, -1, -frame):
        chunk = audio[start : start + frame]
        if float(np.max(np.abs(chunk))) >= threshold:
            break
        silent_samples += frame
    silent_samples = min(silent_samples, len(audio))
    return round(float(silent_samples / sample_rate), 3)


def normalize_qc_words(text: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9']+", " ", subtitle_text(text).lower())
    return [word for word in cleaned.split() if word]


def text_match_ratio(expected: str, actual: str) -> float:
    expected_words = normalize_qc_words(expected)
    actual_words = normalize_qc_words(actual)
    if not expected_words:
        return 1.0 if not actual_words else 0.0
    from difflib import SequenceMatcher

    return float(SequenceMatcher(None, " ".join(expected_words), " ".join(actual_words)).ratio())


def analyze_segment_qc(
    segment: dict[str, Any],
    audio: np.ndarray | None,
    sample_rate: int | None,
    *,
    warn_sec_per_word_high: float = QC_WARN_SEC_PER_WORD_HIGH,
    warn_sec_per_word_low: float = QC_WARN_SEC_PER_WORD_LOW,
    warn_trailing_silence_sec: float = QC_WARN_TRAILING_SILENCE_SEC,
    short_word_limit: int = QC_SHORT_WORD_LIMIT,
    short_too_long_sec: float = QC_SHORT_TOO_LONG_SEC,
    asr_text: str | None = None,
) -> dict[str, Any]:
    segment_words = max(1, int(segment.get("wordCount") or word_count(str(segment.get("text", "")))))
    result: dict[str, Any] = {
        "id": segment["id"],
        "order": segment["order"],
        "filename": segment["filename"],
        "speaker": segment.get("speaker"),
        "kind": segment.get("kind"),
        "wordCount": segment_words,
        "text": str(segment.get("text", "")),
        "displayText": subtitle_text(str(segment.get("text", ""))),
        "flags": [],
        "status": "ok",
    }

    if audio is None or sample_rate is None:
        result["flags"].append("MISSING")
        result["status"] = "review"
        return result

    duration = float(len(audio) / sample_rate)
    sec_per_word = duration / segment_words
    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    trailing = trailing_silence_sec(audio, sample_rate)

    result.update(
        {
            "durationSec": round(duration, 3),
            "secPerWord": round(sec_per_word, 3),
            "peak": round(peak, 4),
            "trailingSilenceSec": trailing,
        }
    )

    flags: list[str] = []
    if sec_per_word > warn_sec_per_word_high:
        flags.append("CHECK_LONG")
    if sec_per_word < warn_sec_per_word_low:
        flags.append("CHECK_FAST")
    if trailing > warn_trailing_silence_sec:
        flags.append("TRAILING_SILENCE")
    if peak > 0 and peak < SEGMENT_PEAK_BOOST_BELOW:
        flags.append("TOO_QUIET")
    if len(audio) and float(np.max(np.abs(audio))) > QC_CLIP_PEAK:
        flags.append("CLIPPING")
    if segment_words <= short_word_limit and duration >= short_too_long_sec:
        flags.append("SHORT_TOO_LONG")

    if asr_text is not None:
        ratio = text_match_ratio(str(segment.get("text", "")), asr_text)
        result["asrText"] = asr_text
        result["asrMatchRatio"] = round(ratio, 3)
        expected_words = normalize_qc_words(str(segment.get("text", "")))
        actual_words = normalize_qc_words(asr_text)
        if ratio < QC_ASR_MATCH_RATIO:
            flags.append("ASR_MISMATCH")
        elif len(actual_words) > int(len(expected_words) * 1.3):
            flags.append("ASR_LONGER")
        elif expected_words and len(actual_words) < int(len(expected_words) * 0.7):
            flags.append("ASR_SHORTER")

    result["flags"] = flags
    if flags:
        result["status"] = "review"
    return result


def build_chapter_qc_report(
    workspace: Path,
    manifest: dict[str, Any] | None = None,
    *,
    asr_by_segment_id: dict[str, str] | None = None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    manifest = ensure_segment_defaults(manifest or load_json(manifest_path(workspace)))
    thresholds = thresholds or {}
    warn_sec_per_word_high = float(thresholds.get("warnSecPerWordHigh", QC_WARN_SEC_PER_WORD_HIGH))
    warn_sec_per_word_low = float(thresholds.get("warnSecPerWordLow", QC_WARN_SEC_PER_WORD_LOW))
    warn_trailing_silence_sec = float(thresholds.get("warnTrailingSilenceSec", QC_WARN_TRAILING_SILENCE_SEC))
    short_word_limit = int(thresholds.get("shortWordLimit", QC_SHORT_WORD_LIMIT))
    short_too_long_sec = float(thresholds.get("shortTooLongSec", QC_SHORT_TOO_LONG_SEC))
    compose_drift_sec = float(thresholds.get("composeDriftSec", QC_COMPOSE_DRIFT_SEC))
    silence = inter_segment_silence_sec(manifest, workspace)

    segments_report: list[dict[str, Any]] = []
    sample_rates: set[int] = set()
    expected_duration = 0.0

    for index, segment in enumerate(manifest["segments"]):
        path = workspace / str(segment["filename"])
        audio: np.ndarray | None = None
        sr: int | None = None
        if path.is_file():
            audio, sr = read_mono(path)
            sample_rates.add(sr)

        asr_text = (asr_by_segment_id or {}).get(str(segment["id"]))
        report = analyze_segment_qc(
            segment,
            audio,
            sr,
            warn_sec_per_word_high=warn_sec_per_word_high,
            warn_sec_per_word_low=warn_sec_per_word_low,
            warn_trailing_silence_sec=warn_trailing_silence_sec,
            short_word_limit=short_word_limit,
            short_too_long_sec=short_too_long_sec,
            asr_text=asr_text,
        )
        if audio is not None and sr is not None and "durationSec" in report:
            expected_duration += float(report["durationSec"])
            if index < len(manifest["segments"]) - 1:
                expected_duration += silence
        segments_report.append(report)

    chapter_flags: list[str] = []
    if len(sample_rates) > 1:
        chapter_flags.append("SAMPLE_RATE_MISMATCH")
    raw_path = final_audio_path(workspace)
    raw_duration: float | None = None
    compose_drift: float | None = None
    sample_rate = next(iter(sample_rates)) if len(sample_rates) == 1 else None
    if raw_path.is_file() and sample_rate is not None:
        raw, raw_sr = read_mono(raw_path)
        if raw_sr != sample_rate:
            chapter_flags.append("RAW_SAMPLE_RATE_MISMATCH")
        raw_duration = round(float(len(raw) / raw_sr), 3)
        compose_drift = round(abs(raw_duration - expected_duration), 3)
        if compose_drift > compose_drift_sec:
            chapter_flags.append("COMPOSE_DRIFT")
    elif manifest["segments"]:
        chapter_flags.append("RAW_MISSING")

    review_count = sum(1 for item in segments_report if item["status"] == "review")
    chapter_status = "review" if review_count or chapter_flags else "ok"

    return {
        "workspace": str(workspace).replace("\\", "/"),
        "manifest": str(manifest_path(workspace)).replace("\\", "/"),
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "warnSecPerWordHigh": warn_sec_per_word_high,
            "warnSecPerWordLow": warn_sec_per_word_low,
            "warnTrailingSilenceSec": warn_trailing_silence_sec,
            "shortWordLimit": short_word_limit,
            "shortTooLongSec": short_too_long_sec,
            "composeDriftSec": compose_drift_sec,
            "asrMatchRatio": QC_ASR_MATCH_RATIO,
        },
        "chapter": {
            "status": chapter_status,
            "flags": chapter_flags,
            "segmentCount": len(segments_report),
            "reviewCount": review_count,
            "sampleRate": sample_rate,
            "interSegmentSilenceSec": silence,
            "expectedDurationSec": round(expected_duration, 3),
            "rawDurationSec": raw_duration,
            "composeDriftSec": compose_drift,
            "rawPath": str(raw_path).replace("\\", "/") if raw_path.is_file() else None,
        },
        "segments": segments_report,
        "asr": {
            "enabled": bool(asr_by_segment_id),
            "segmentCount": len(asr_by_segment_id or {}),
            "engine": "faster-whisper" if asr_by_segment_id else None,
            "model": "base" if asr_by_segment_id else None,
        },
    }
