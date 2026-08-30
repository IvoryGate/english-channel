from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDIA_SCRIPTS = REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"
sys.path.insert(0, str(MEDIA_SCRIPTS))

from media.compose_media_video import build_ffmpeg_command  # noqa: E402
import media.compose_media_video as compose_media_video  # noqa: E402
from media.generate_karaoke_ass import generate_karaoke_ass  # noqa: E402
from media.generate_media_srt import generate_media_srt  # noqa: E402
from media.thumbnail_tokens import DEFAULT_TOKENS  # noqa: E402
from media.turn_alignment import assign_words_to_turns  # noqa: E402


def test_turn_based_ass_does_not_mix_speakers() -> None:
    words = [
        {"word": "Hi", "start": 0.0, "end": 0.2},
        {"word": "there.", "start": 0.2, "end": 0.5},
        {"word": "Hello", "start": 0.9, "end": 1.1},
        {"word": "friend.", "start": 1.1, "end": 1.4},
    ]
    turns = assign_words_to_turns(
        words,
        [
            {"id": "p001", "speaker": "Riley", "text": "Hi there."},
            {"id": "p002", "speaker": "Sam", "text": "Hello friend."},
        ],
    )
    ass = generate_karaoke_ass([], DEFAULT_TOKENS["series_b"], turns=turns)
    assert "{\\kf20}Hi" in ass
    assert "there." in ass
    assert "Hello" in ass
    assert "Hi" not in ass.split("Hello")[1]


def test_ass_timestamp_and_karaoke_tags() -> None:
    words = [
        {"word": "Hello", "start": 0.0, "end": 0.4},
        {"word": "world", "start": 0.4, "end": 0.9},
    ]
    ass = generate_karaoke_ass(words, DEFAULT_TOKENS["series_b"])
    assert "0:00:00.00" in ass
    assert "0:00:00.90" in ass
    assert "{\\kf40}Hello" in ass
    assert "{\\kf50}world" in ass
    assert "PlayResX: 2560" in ass
    assert "\\kf" in ass


def test_media_srt_chunks_words() -> None:
    words = [
        {"word": "one", "start": 0.0, "end": 0.2},
        {"word": "two", "start": 0.2, "end": 0.4},
        {"word": "three", "start": 0.4, "end": 0.6},
    ]
    srt = generate_media_srt(words, words_per_cue=2)
    assert "00:00:00,000 --> 00:00:00,400" in srt
    assert "one two" in srt
    assert "three" in srt


def test_force_script_words_keeps_script_surface() -> None:
    from media.turn_alignment import force_script_words

    asr = [
        {"word": "12", "start": 0.0, "end": 0.3, "confidence": 0.9},
        {"word": "tenses", "start": 0.3, "end": 0.7, "confidence": 0.9},
    ]
    out = force_script_words(asr, "twelve tenses", clip_duration_sec=0.8)
    assert [w["word"] for w in out] == ["twelve", "tenses"]


def test_merge_uses_clip_durations_not_asr_tail() -> None:
    from media.turn_alignment import merge_turn_alignments

    merged = merge_turn_alignments(
        [
            {"turnId": "p001", "speaker": "Riley", "words": [{"word": "Hi", "start": 0.0, "end": 0.2}]},
            {"turnId": "p002", "speaker": "Sam", "words": [{"word": "Yo", "start": 0.0, "end": 0.2}]},
        ],
        gap_sec=0.3,
        clip_durations_sec=[1.0, 1.0],
    )
    assert merged["turns"][1]["words"][0]["start"] == 1.3
    assert merged["durationSec"] == 2.3


def test_build_ffmpeg_command_includes_layers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(compose_media_video, "resolve_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(compose_media_video, "detect_hw_encoder", lambda: "")
    command = build_ffmpeg_command(
        background_jpg=Path("bg.jpg"),
        audio_wav=Path("audio.wav"),
        ass_path=Path("subs.ass"),
        waveform_mov=Path("wave.mov"),
        output_mp4=Path("out.mp4"),
    )
    joined = " ".join(command)
    assert "overlay=906:1093" in joined
    assert "shortest=1" in joined
    assert "scale=2560:1440" in joined
    assert "-b:v" in command
    assert "5M" in command
