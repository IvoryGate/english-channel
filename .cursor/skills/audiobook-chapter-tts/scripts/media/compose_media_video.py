from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from media.bar_waveform import render_bar_waveform_video
from media.media_layout import HEIGHT, WAVE_HEIGHT, WAVE_WIDTH, WAVE_X, WAVE_Y, WIDTH
from media.thumbnail_tokens import ThumbnailTokens, hex_to_rgb


_HW_CACHE: str | None = None


def _probe_encoder(encoder: str) -> bool:
    """Actually open `encoder` on a tiny test pattern (list check is not enough)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    try:
        proc = subprocess.run(
            [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15",
                "-t", "0.2",
                "-c:v", encoder, "-preset", "p1" if "nvenc" in encoder else "veryfast",
                "-f", "null", "-",
            ],
            capture_output=True, text=True, timeout=30,
        )
        return proc.returncode == 0
    except Exception:
        return False


def detect_hw_encoder() -> str:
    """Pick the best available hardware H.264 encoder, or "" for libx264.

    Auto mode prefers NVENC (NVIDIA discrete GPU — genuinely faster than
    libx264 when the driver supports it). QSV (Intel iGPU) and AMF (AMD) are
    NOT auto-picked: for this static-background + subtitle workflow the
    encoder is not the bottleneck (the 2560x1440 filter graph is), and iGPU
    encoders are often not faster than libx264 medium while adding frame-upload
    overhead. They remain available via ``encoder="qsv"`` / ``"amf"`` opt-in.

    Each encoder is probed by actually opening it — listing in
    ``ffmpeg -encoders`` is not sufficient (e.g. an outdated NVIDIA driver
    lists h264_nvenc but fails to open it with "nvenc API version" mismatch).
    Result is cached for the run.
    """
    global _HW_CACHE
    if _HW_CACHE is not None:
        return _HW_CACHE
    if _probe_encoder("h264_nvenc"):
        _HW_CACHE = "h264_nvenc"
    else:
        _HW_CACHE = ""  # auto: libx264; use encoder="qsv"/"amf" to force iGPU/AMD
    return _HW_CACHE


def has_nvenc() -> bool:
    """Backwards-compatible alias; True if NVENC is the chosen hardware encoder."""
    return detect_hw_encoder() == "h264_nvenc"


def _escape_filter_path(path: Path) -> str:
    value = path.resolve().as_posix()
    value = value.replace(":", "\\:")
    value = value.replace("'", "\\'")
    return value


def build_ffmpeg_command(
    *,
    background_jpg: Path,
    audio_wav: Path,
    ass_path: Path,
    waveform_mov: Path,
    output_mp4: Path,
    fonts_dir: Path | None = None,
    preset: str = "veryfast",
    crf: int = 18,
    video_bitrate: str = "5M",
    maxrate: str = "6M",
    bufsize: str = "10M",
    encoder: str = "auto",
) -> list[str]:
    _ = crf  # Kept for API compatibility; bitrate mode is the formal default.
    ass = _escape_filter_path(ass_path)
    fonts = _escape_filter_path(fonts_dir) if fonts_dir and fonts_dir.is_dir() else None

    if fonts:
        ass_filter = f"ass='{ass}':fontsdir='{fonts}'"
    else:
        ass_filter = f"ass='{ass}'"

    filter_complex = (
        f"[0:v]scale={WIDTH}:{HEIGHT},setsar=1[bg];"
        f"[1:v]scale={WAVE_WIDTH}:{WAVE_HEIGHT},format=rgba[wave];"
        f"[bg][wave]overlay={WAVE_X}:{WAVE_Y}:shortest=1:format=auto[bgwave];"
        f"[bgwave]{ass_filter}[v]"
    )

    # Pick encoder: hardware (NVENC/QSV/AMF) when available for fast GPU encoding
    # with quality parity to libx264 medium; fall back to libx264 otherwise.
    hw = detect_hw_encoder() if encoder == "auto" else (
        "h264_nvenc" if encoder == "nvenc" else
        "h264_qsv" if encoder == "qsv" else
        "h264_amf" if encoder == "amf" else ""
    )
    if hw == "h264_nvenc":
        # p5 = slow-ish NVENC preset (good quality); vbr + bitrate caps match the
        # libx264 target; spatial-aq + rc-lookahead improve perceptual quality.
        nvenc_preset = "p5" if preset in ("medium", "slow", "p5") else "p4"
        video_args = [
            "-c:v", "h264_nvenc",
            "-preset", nvenc_preset,
            "-rc", "vbr",
            "-b:v", video_bitrate,
            "-maxrate", maxrate,
            "-bufsize", bufsize,
            "-spatial_aq", "1",
            "-rc-lookahead", "16",
            "-g", "60",  # 2s keyframe interval @30fps
        ]
    elif hw == "h264_qsv":
        # Intel QuickSync: veryfast preset, VBR with bitrate caps. QSV encodes
        # on the integrated GPU, freeing the CPU for the filter graph.
        video_args = [
            "-c:v", "h264_qsv",
            "-preset", "veryfast",
            "-b:v", video_bitrate,
            "-maxrate", maxrate,
            "-bufsize", bufsize,
            "-g", "60",
        ]
    elif hw == "h264_amf":
        # AMD AMF: balanced preset, VBR bitrate caps.
        video_args = [
            "-c:v", "h264_amf",
            "-quality", "balanced",
            "-b:v", video_bitrate,
            "-maxrate", maxrate,
            "-bufsize", bufsize,
            "-g", "60",
        ]
    else:
        video_args = [
            "-c:v", "libx264",
            "-preset", preset,
            "-b:v", video_bitrate,
            "-maxrate", maxrate,
            "-bufsize", bufsize,
        ]

    return [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-framerate",
        "30",
        "-i",
        str(background_jpg),
        "-i",
        str(waveform_mov),
        "-i",
        str(audio_wav),
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "2:a",
        *video_args,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-pix_fmt",
        "yuv420p",
        str(output_mp4),
    ]


def compose_media_video(
    *,
    background_jpg: Path,
    audio_wav: Path,
    ass_path: Path,
    output_mp4: Path,
    tokens: ThumbnailTokens,
    fonts_dir: Path | None = None,
    report_path: Path | None = None,
    waveform_mov: Path | None = None,
    encoder: str = "auto",
    preset: str = "veryfast",
) -> dict[str, Any]:
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    temp_wave = waveform_mov or output_mp4.with_name(f"{output_mp4.stem}.barwave.mov")
    bar_rgb = hex_to_rgb(tokens.wave_bar_color)

    render_bar_waveform_video(audio_wav, temp_wave, bar_rgb=bar_rgb)
    command = build_ffmpeg_command(
        background_jpg=background_jpg,
        audio_wav=audio_wav,
        ass_path=ass_path,
        waveform_mov=temp_wave,
        output_mp4=output_mp4,
        fonts_dir=fonts_dir,
        encoder=encoder,
        preset=preset,
    )
    subprocess.run(command, check=True)

    used_encoder = "libx264"
    for cand in ("h264_nvenc", "h264_qsv", "h264_amf"):
        if cand in command:
            used_encoder = cand
            break
    report: dict[str, Any] = {
        "schema": "media-video-compose-v3",
        "outputMp4": str(output_mp4).replace("\\", "/"),
        "backgroundJpg": str(background_jpg).replace("\\", "/"),
        "audioWav": str(audio_wav).replace("\\", "/"),
        "assPath": str(ass_path).replace("\\", "/"),
        "waveformMov": str(temp_wave).replace("\\", "/"),
        "waveformStyle": "rounded-bars-transparent",
        "waveBarColor": tokens.wave_bar_color,
        "waveWidth": WAVE_WIDTH,
        "waveHeight": WAVE_HEIGHT,
        "waveX": WAVE_X,
        "waveY": WAVE_Y,
        "videoEncoder": used_encoder,
        "ffmpegCommand": command,
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report
