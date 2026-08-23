from __future__ import annotations

import re
import textwrap
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import soundfile as sf


def _tokens(text: str) -> list[re.Match[str]]:
    return list(re.finditer(r"\S+", text))


def _normalized_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold().replace("’", "'"))


def _index_map(source: list[str], target: list[str]) -> list[int]:
    if not source:
        return []
    if not target:
        return [0] * len(source)
    mapping = [0] * len(source)
    matcher = SequenceMatcher(a=source, b=target, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            continue
        source_count = max(1, i2 - i1)
        target_count = j2 - j1
        for offset, source_index in enumerate(range(i1, i2)):
            if target_count <= 0:
                target_index = max(0, min(len(target) - 1, j1 - 1))
            else:
                fraction = offset / max(1, source_count - 1)
                target_index = j1 + round(fraction * max(0, target_count - 1))
            mapping[source_index] = max(0, min(len(target) - 1, target_index))
    for index in range(1, len(mapping)):
        mapping[index] = max(mapping[index], mapping[index - 1])
    return mapping


def split_source_cues(text: str, *, max_words: int = 18, max_chars: int = 92) -> list[dict[str, Any]]:
    matches = _tokens(text)
    if not matches:
        return []
    result: list[dict[str, Any]] = []
    start = 0
    while start < len(matches):
        hard_end = min(len(matches), start + max_words)
        end = hard_end
        while end > start + 1:
            start_char = matches[start].start()
            end_char = matches[end - 1].end()
            if end_char - start_char <= max_chars:
                break
            end -= 1
        if end < len(matches):
            preferred = [
                index
                for index in range(start + 5, end)
                if re.search(r"[,;:.!?][\"'’”)]*$", matches[index].group())
            ]
            if preferred:
                end = preferred[-1] + 1
        start_char = 0 if start == 0 else matches[start].start()
        end_char = len(text) if end == len(matches) else matches[end - 1].end()
        while end_char < len(text) and not text[end_char].isspace():
            end_char += 1
        source = text[start_char:end_char].strip()
        lines = textwrap.wrap(
            source,
            width=46,
            break_long_words=False,
            break_on_hyphens=False,
        )
        if len(lines) > 2:
            midpoint = start + max(1, (end - start) // 2)
            end = midpoint
            end_char = matches[end - 1].end()
            while end_char < len(text) and not text[end_char].isspace():
                end_char += 1
            source = text[start_char:end_char].strip()
            lines = textwrap.wrap(source, width=46, break_long_words=False, break_on_hyphens=False)
        result.append(
            {
                "text": "\n".join(lines),
                "sourceText": source,
                "startToken": start,
                "endToken": end - 1,
            }
        )
        start = end
    return result


def timed_source_cues(
    display_text: str,
    spoken_text: str,
    words: list[dict[str, Any]],
    *,
    offset: float,
    duration: float,
) -> list[dict[str, Any]]:
    chunks = split_source_cues(display_text)
    if not chunks:
        return []
    usable_words = [word for word in words if _normalized_token(str(word.get("word", "")))]
    if not usable_words:
        per_chunk = duration / len(chunks)
        return [
            {
                "start": offset + index * per_chunk,
                "end": offset + (index + 1) * per_chunk,
                "text": chunk["text"],
            }
            for index, chunk in enumerate(chunks)
        ]

    display_tokens = [_normalized_token(match.group()) for match in _tokens(display_text)]
    spoken_tokens = [_normalized_token(match.group()) for match in _tokens(spoken_text)]
    asr_tokens = [_normalized_token(str(word["word"])) for word in usable_words]
    display_to_spoken = _index_map(display_tokens, spoken_tokens)
    spoken_to_asr = _index_map(spoken_tokens, asr_tokens)

    cues: list[dict[str, Any]] = []
    for chunk in chunks:
        spoken_start = display_to_spoken[int(chunk["startToken"])]
        spoken_end = display_to_spoken[int(chunk["endToken"])]
        asr_start = spoken_to_asr[spoken_start]
        asr_end = spoken_to_asr[spoken_end]
        start = max(0.0, float(usable_words[asr_start]["start"]) - 0.08)
        end = min(duration, float(usable_words[asr_end]["end"]) + 0.12)
        cues.append({"start": offset + start, "end": offset + end, "text": chunk["text"]})

    for index in range(len(cues) - 1):
        if cues[index]["end"] >= cues[index + 1]["start"]:
            boundary = (cues[index]["end"] + cues[index + 1]["start"]) / 2.0
            cues[index]["end"] = boundary - 0.015
            cues[index + 1]["start"] = boundary + 0.015
    return cues


def align_segment_files(
    manifest: dict[str, Any],
    segment_dir: Path,
    selected_ids: list[str],
    *,
    silence_sec: float,
    model_name: str = "base",
) -> dict[str, Any]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8", local_files_only=True, cpu_threads=4)
    by_id = {str(segment["id"]): segment for segment in manifest["segments"]}
    cursor = 0.0
    cues: list[dict[str, Any]] = []
    segment_reports: list[dict[str, Any]] = []
    for index, segment_id in enumerate(selected_ids):
        segment = by_id[segment_id]
        audio_path = segment_dir / str(segment["filename"])
        info = sf.info(audio_path)
        duration = float(info.frames / info.samplerate)
        transcribed, _ = model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=False,
            condition_on_previous_text=False,
            word_timestamps=True,
        )
        words: list[dict[str, Any]] = []
        transcript_parts: list[str] = []
        for result in transcribed:
            transcript_parts.append(result.text.strip())
            for word in result.words or []:
                words.append({"word": word.word, "start": word.start, "end": word.end})
        cues.extend(
            timed_source_cues(
                str(segment["displayText"]),
                str(segment["spokenText"]),
                words,
                offset=cursor,
                duration=duration,
            )
        )
        transcript = " ".join(part for part in transcript_parts if part)
        expected_normalized = " ".join(
            token for token in (_normalized_token(match.group()) for match in _tokens(str(segment["spokenText"]))) if token
        )
        transcript_normalized = " ".join(
            token for token in (_normalized_token(match.group()) for match in _tokens(transcript)) if token
        )
        similarity = SequenceMatcher(None, expected_normalized, transcript_normalized, autojunk=False).ratio()
        segment_reports.append(
            {
                "id": segment_id,
                "durationSec": round(duration, 3),
                "transcript": transcript,
                "wordTimestampCount": len(words),
                "similarity": round(similarity, 4),
                "status": "PASS" if similarity >= 0.78 else "REVIEW",
            }
        )
        cursor += duration
        if index < len(selected_ids) - 1:
            cursor += silence_sec
    return {"durationSec": cursor, "cues": cues, "segments": segment_reports}
