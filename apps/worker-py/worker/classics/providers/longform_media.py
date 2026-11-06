"""Classic adapter into the approved shared long-form media implementation."""
from pathlib import Path
import sys
from typing import Any


def shared_media_root(repo_root: Path) -> None:
    root = str(repo_root / '.cursor/skills/audiobook-chapter-tts/scripts')
    if root not in sys.path:
        sys.path.insert(0, root)


def write_shared_captions(repo_root: Path, output: Path, cues: list[dict[str, Any]]) -> None:
    shared_media_root(repo_root)
    from media.generate_karaoke_ass import generate_phrase_cue_ass
    from media.thumbnail_tokens import DEFAULT_TOKENS
    output.write_text(generate_phrase_cue_ass(cues, DEFAULT_TOKENS['series_a']), encoding='utf-8', newline='\n')


def render_shared_spectrum(repo_root: Path, audio: Path, output: Path) -> Path:
    shared_media_root(repo_root)
    from media.radial_waveform import render_radial_waveform_video
    return render_radial_waveform_video(audio, output, width=800, height=800,
        bar_rgb=(255, 255, 255), avatar_path=repo_root / 'public/branding/english_listening_room_avatar_v2.png')


def compose_shared_body(repo_root: Path, background: Path, audio: Path, ass: Path, output: Path) -> None:
    shared_media_root(repo_root)
    from media.compose_media_video import compose_media_video
    from media.thumbnail_tokens import DEFAULT_TOKENS
    compose_media_video(background_jpg=background, audio_wav=audio, ass_path=ass,
        output_mp4=output, tokens=DEFAULT_TOKENS['series_a'], encoder='libx264',
        fonts_dir=repo_root / 'assets/fonts', report_path=output.with_suffix('.compose.json'))
