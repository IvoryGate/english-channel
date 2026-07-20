from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.rate_limit import (
    DEFAULT_MAX_SLEEP_INTERVAL_SEC,
    DEFAULT_SLEEP_INTERVAL_SEC,
    merge_ydl_opts,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
AUDIOBOOK_SCRIPTS = REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"
sys.path.insert(0, str(AUDIOBOOK_SCRIPTS))

from clean_reference_audio import clean_reference  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_yt_dlp() -> Any:
    try:
        import yt_dlp
    except ImportError as exc:
        raise SystemExit(
            "yt-dlp is required. Install with: "
            ".\\.conda-env\\python.exe -m pip install -r apps/worker-py/requirements.txt"
        ) from exc
    return yt_dlp


def download_audio(video_url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    outtmpl = str(output_path.with_suffix("")) + ".%(ext)s"
    opts = merge_ydl_opts(
        {
            "quiet": True,
            "no_warnings": True,
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
        },
        sleep_interval=DEFAULT_SLEEP_INTERVAL_SEC,
        max_sleep_interval=DEFAULT_MAX_SLEEP_INTERVAL_SEC,
    )
    with load_yt_dlp().YoutubeDL(opts) as ydl:
        ydl.download([video_url])


def resolve_source_wav(source_dir: Path, video_id: str) -> Path:
    for candidate in sorted(source_dir.glob(f"{video_id}.*")):
        if candidate.suffix.lower() in {".wav", ".m4a", ".webm", ".opus", ".mp3"}:
            return candidate
    wav = source_dir / f"{video_id}.wav"
    if wav.is_file():
        return wav
    raise FileNotFoundError(f"No downloaded audio found in {source_dir} for {video_id}")


def extract_clip(source_wav: Path, start_sec: float, end_sec: float, output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.1, end_sec - start_sec)
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(start_sec),
        "-i",
        str(source_wav),
        "-t",
        str(duration),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    return {
        "source": str(source_wav).replace("\\", "/"),
        "clip": str(output_path).replace("\\", "/"),
        "startSec": start_sec,
        "endSec": end_sec,
        "durationSec": round(duration, 3),
    }


def write_reference_text_sidecar(clean_path: Path, reference_text: str) -> str:
    sidecar = clean_path.with_suffix(".reference.txt")
    sidecar.write_text(reference_text.strip() + "\n", encoding="utf-8", newline="\n")
    return str(sidecar).replace("\\", "/")


def resolve_clip_source(
    clip: dict[str, Any],
    config: dict[str, Any],
    source_dir: Path,
    skip_download: bool,
) -> Path:
    video_id = str(clip.get("sourceVideoId") or config["sourceVideoId"])
    source_url = str(clip.get("sourceUrl") or config["sourceUrl"])
    source_wav = source_dir / f"{video_id}.wav"
    if not skip_download or not resolve_source_wav(source_dir, video_id).is_file():
        print(f"Downloading audio ({video_id})...")
        download_audio(source_url, source_dir / video_id)
    return resolve_source_wav(source_dir, video_id)


def process_series(
    clips_config_path: Path,
    skip_download: bool = False,
    hosts: set[str] | None = None,
) -> dict[str, Any]:
    config = load_json(clips_config_path)
    if config.get("manualCuration"):
        series = str(config.get("series", clips_config_path.parent.name))
        print(f"Skipping {series}: manualCuration=true (existing clean wavs are authoritative).")
        return {"series": series, "skipped": True, "reason": "manualCuration"}

    series = str(config["series"])
    series_root = clips_config_path.parent
    source_dir = series_root / "source"
    report: dict[str, Any] = {"series": series, "hosts": {}}

    for host_name, clip in config["clips"].items():
        if hosts and host_name not in hosts:
            continue
        if clip.get("manualCuration"):
            print(f"Skipping {host_name}: manualCuration=true")
            report["hosts"][host_name] = {"skipped": True, "reason": "manualCuration"}
            continue

        source_wav = resolve_clip_source(clip, config, source_dir, skip_download)
        raw_path = series_root / f"{host_name.lower()}_reference_raw.wav"
        clean_path = series_root / f"{host_name.lower()}_reference_clean.wav"
        clip_report = extract_clip(
            source_wav,
            float(clip["startSec"]),
            float(clip["endSec"]),
            raw_path,
        )
        clean_report = clean_reference(raw_path, clean_path, tempo_ratio=1.0)
        reference_text = str(clip["referenceText"])
        clip_report["referenceText"] = reference_text
        clip_report["referenceTextFile"] = write_reference_text_sidecar(clean_path, reference_text)
        clip_report["clean"] = clean_report
        report["hosts"][host_name] = clip_report
        print(f"{series} {host_name}: {clean_path}")

    write_json(series_root / "reference_extraction.report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Download source audio and extract host reference clips.")
    parser.add_argument(
        "--series",
        choices=["series_a", "series_b", "all"],
        default="all",
        help="Which series clip config to process.",
    )
    parser.add_argument("--skip-download", action="store_true", help="Reuse existing source audio.")
    parser.add_argument("--hosts", help="Comma-separated host names to process, e.g. Sam,Riley.")
    args = parser.parse_args()
    selected_hosts = {part.strip() for part in (args.hosts or "").split(",") if part.strip()} or None

    configs: list[Path] = []
    if args.series in {"series_a", "all"}:
        configs.append(REPO_ROOT / "assets" / "voices" / "series_a" / "clips.json")
    if args.series in {"series_b", "all"}:
        configs.append(REPO_ROOT / "assets" / "voices" / "series_b" / "clips.json")

    for config_path in configs:
        if not config_path.is_file():
            raise FileNotFoundError(f"Missing clip config: {config_path}")
        process_series(config_path, skip_download=args.skip_download, hosts=selected_hosts)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
