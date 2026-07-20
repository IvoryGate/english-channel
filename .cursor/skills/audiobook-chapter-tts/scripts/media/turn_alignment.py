from __future__ import annotations

import re
from typing import Any


def normalize_token(text: str) -> str:
    return re.sub(r"[^a-z0-9']+", "", text.lower())


def tokenize_turn_text(text: str) -> list[str]:
    return [token for token in (normalize_token(part) for part in text.split()) if token]


def assign_words_to_turns(
    words: list[dict[str, Any]],
    turns: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not turns:
        return [{"speaker": "", "turnId": "", "words": words}]

    grouped: list[dict[str, Any]] = []
    cursor = 0
    for turn in turns:
        ref_tokens = tokenize_turn_text(str(turn.get("text", "")))
        turn_words: list[dict[str, Any]] = []
        ref_index = 0
        while cursor < len(words) and ref_index < len(ref_tokens):
            word = words[cursor]
            cursor += 1
            hyp = normalize_token(str(word.get("word", "")))
            if not hyp:
                continue
            if hyp == ref_tokens[ref_index] or _tokens_close(hyp, ref_tokens[ref_index]):
                turn_words.append(word)
                ref_index += 1
        grouped.append(
            {
                "turnId": str(turn.get("id", "")),
                "speaker": str(turn.get("speaker", "")),
                "words": turn_words,
            }
        )
    return grouped


def _tokens_close(left: str, right: str) -> bool:
    if left == right:
        return True
    # Avoid matching tiny tokens like "a"/"and" via startswith
    if min(len(left), len(right)) >= 4 and (left.startswith(right) or right.startswith(left)):
        return True
    if {left, right} <= {"ok", "okay"}:
        return True
    return False


def display_tokens(text: str) -> list[str]:
    """Keep script surface forms (twelve, not ASR '12') for on-screen karaoke."""
    return [part for part in str(text).split() if part.strip()]


def force_script_words(
    asr_words: list[dict[str, Any]],
    script_text: str,
    *,
    clip_duration_sec: float,
) -> list[dict[str, Any]]:
    """Show script wording with timings derived from ASR / clip duration.

    Karaoke must match the written episode text, while still following each
    turn's audio timeline. Prefer real clip duration as the clock source so
    concat gaps do not drift across dozens of turns.
    """
    display = display_tokens(script_text)
    if not display:
        return []

    clip_dur = max(0.05, float(clip_duration_sec))
    if asr_words:
        start = max(0.0, float(asr_words[0]["start"]))
        end = max(start + 0.05, float(asr_words[-1]["end"]))
        end = min(end, clip_dur)
        # If ASR ends far early, stretch toward clip end (minus tiny pad).
        if end < clip_dur * 0.75:
            end = max(end, min(clip_dur - 0.02, clip_dur * 0.98))
    else:
        start = 0.0
        end = clip_dur

    if len(asr_words) == len(display):
        out: list[dict[str, Any]] = []
        for hyp, surface in zip(asr_words, display):
            w_start = max(0.0, min(float(hyp["start"]), clip_dur))
            w_end = max(w_start + 0.03, min(float(hyp["end"]), clip_dur))
            out.append(
                {
                    "word": surface,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                    "confidence": float(hyp.get("confidence") or 1.0),
                }
            )
        return out

    weights = [max(1, len(normalize_token(token)) or 1) for token in display]
    total_w = float(sum(weights))
    span = max(0.05, end - start)
    out = []
    cursor = start
    for index, (surface, weight) in enumerate(zip(display, weights)):
        dur = span * (weight / total_w)
        w_end = end if index == len(display) - 1 else min(end, cursor + dur)
        out.append(
            {
                "word": surface,
                "start": round(cursor, 3),
                "end": round(max(cursor + 0.03, w_end), 3),
                "confidence": 1.0,
            }
        )
        cursor = w_end
    return out


def merge_turn_alignments(
    turn_alignments: list[dict[str, Any]],
    *,
    gap_sec: float = 0.0,
    clip_durations_sec: list[float] | None = None,
) -> dict[str, Any]:
    """Stitch per-turn word timings onto the concatenated episode clock.

    Always advance the timeline by real clip duration (+ gap), never by the
    last ASR word end — otherwise silence tails accumulate huge drift.
    """
    words: list[dict[str, Any]] = []
    turns: list[dict[str, Any]] = []
    offset = 0.0
    for index, item in enumerate(turn_alignments):
        speaker = str(item.get("speaker", ""))
        turn_id = str(item.get("turnId", ""))
        turn_words = []
        for word in item.get("words") or []:
            shifted = {
                **word,
                "start": round(float(word["start"]) + offset, 3),
                "end": round(float(word["end"]) + offset, 3),
                "speaker": speaker,
                "turnId": turn_id,
            }
            turn_words.append(shifted)
            words.append(shifted)
        turns.append({"turnId": turn_id, "speaker": speaker, "words": turn_words})
        if clip_durations_sec is not None and index < len(clip_durations_sec):
            offset += float(clip_durations_sec[index]) + gap_sec
        elif turn_words:
            offset = float(turn_words[-1]["end"]) + gap_sec
        else:
            offset += gap_sec
    if clip_durations_sec:
        duration = sum(float(x) for x in clip_durations_sec) + gap_sec * max(0, len(clip_durations_sec) - 1)
    else:
        duration = float(words[-1]["end"]) if words else 0.0
    return {
        "schema": "media-word-alignment-v1",
        "wordCount": len(words),
        "durationSec": round(duration, 3),
        "words": words,
        "turns": turns,
    }
