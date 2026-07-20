from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def normalize_token(text: str) -> str:
  return re.sub(r"[^a-z0-9']+", "", text.lower())


def spoken_text_from_turns(turns: list[dict[str, Any]]) -> str:
  parts = [str(turn.get("text", "")).strip() for turn in turns]
  return " ".join(part for part in parts if part)


def align_audio_words(
  audio_path: Path,
  *,
  language: str = "en",
  model_size: str = "base",
  device: str = "cpu",
  compute_type: str = "int8",
  reference_text: str | None = None,
  vad_filter: bool = False,
) -> dict[str, Any]:
  from faster_whisper import WhisperModel

  model = WhisperModel(model_size, device=device, compute_type=compute_type)
  segments, info = model.transcribe(
    str(audio_path),
    language=language,
    word_timestamps=True,
    # VAD often drops the second host after concat silence — off by default for karaoke
    vad_filter=vad_filter,
  )

  words: list[dict[str, Any]] = []
  for segment in segments:
    if not segment.words:
      continue
    for word in segment.words:
      token = (word.word or "").strip()
      if not token:
        continue
      words.append(
        {
          "word": token,
          "start": round(float(word.start), 3),
          "end": round(float(word.end), 3),
          "confidence": round(float(word.probability), 4),
        }
      )

  report: dict[str, Any] = {
    "schema": "media-word-alignment-v1",
    "audio": str(audio_path).replace("\\", "/"),
    "language": language,
    "durationSec": round(float(info.duration), 3),
    "wordCount": len(words),
    "words": words,
  }

  if reference_text:
    ref_tokens = [normalize_token(part) for part in reference_text.split() if normalize_token(part)]
    hyp_tokens = [normalize_token(word["word"]) for word in words]
    matched = sum(1 for token in ref_tokens if token in hyp_tokens)
    coverage = matched / max(1, len(ref_tokens))
    report["referenceCoverage"] = round(coverage, 4)
    report["referenceWordCount"] = len(ref_tokens)

  return report


def align_turn_clips(
  clips: list[Path],
  turns: list[dict[str, Any]],
  *,
  gap_sec: float = 0.35,
  language: str = "en",
  model_size: str = "base",
  device: str = "cpu",
  compute_type: str = "int8",
) -> dict[str, Any]:
  """Align each host clip alone, then stitch timelines across concat gaps."""
  import soundfile as sf

  from media.turn_alignment import force_script_words, merge_turn_alignments

  if len(clips) != len(turns):
    raise ValueError(f"clip count {len(clips)} != turn count {len(turns)}")

  turn_alignments: list[dict[str, Any]] = []
  coverages: list[float] = []
  clip_durations: list[float] = []
  for clip, turn in zip(clips, turns):
    if not clip.is_file():
      raise FileNotFoundError(f"Missing clip: {clip}")
    text = str(turn.get("text", "")).strip()
    audio, sample_rate = sf.read(str(clip), dtype="float32")
    clip_dur = float(len(audio) / sample_rate) if sample_rate else 0.0
    clip_durations.append(clip_dur)
    piece = align_audio_words(
      clip,
      language=language,
      model_size=model_size,
      device=device,
      compute_type=compute_type,
      reference_text=text or None,
      vad_filter=False,
    )
    if piece.get("referenceCoverage") is not None:
      coverages.append(float(piece["referenceCoverage"]))
    scripted = force_script_words(piece["words"], text, clip_duration_sec=clip_dur)
    turn_alignments.append(
      {
        "speaker": str(turn.get("speaker", "")),
        "turnId": str(turn.get("id", "")),
        "words": scripted,
      }
    )

  merged = merge_turn_alignments(
    turn_alignments,
    gap_sec=gap_sec,
    clip_durations_sec=clip_durations,
  )
  merged["audio"] = ",".join(str(path).replace("\\", "/") for path in clips)
  merged["alignmentMode"] = "per-clip-scripted"
  if coverages:
    merged["referenceCoverage"] = round(sum(coverages) / len(coverages), 4)
  return merged


def align_turn_clips_scripted(
  clips: list[Path],
  turns: list[dict[str, Any]],
  *,
  gap_sec: float = 0.35,
) -> dict[str, Any]:
  """Audiobook-style timing: clip WAV duration + script text, no per-clip ASR."""
  import soundfile as sf

  from media.turn_alignment import force_script_words, merge_turn_alignments

  if len(clips) != len(turns):
    raise ValueError(f"clip count {len(clips)} != turn count {len(turns)}")

  turn_alignments: list[dict[str, Any]] = []
  clip_durations: list[float] = []
  for clip, turn in zip(clips, turns):
    if not clip.is_file():
      raise FileNotFoundError(f"Missing clip: {clip}")
    text = str(turn.get("text", "")).strip()
    audio, sample_rate = sf.read(str(clip), dtype="float32")
    clip_dur = float(len(audio) / sample_rate) if sample_rate else 0.0
    clip_durations.append(clip_dur)
    scripted = force_script_words([], text, clip_duration_sec=clip_dur)
    turn_alignments.append(
      {
        "speaker": str(turn.get("speaker", "")),
        "turnId": str(turn.get("id", "")),
        "words": scripted,
      }
    )

  merged = merge_turn_alignments(
    turn_alignments,
    gap_sec=gap_sec,
    clip_durations_sec=clip_durations,
  )
  merged["audio"] = ",".join(str(path).replace("\\", "/") for path in clips)
  merged["alignmentMode"] = "per-clip-scripted-no-asr"
  return merged


def write_words_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
