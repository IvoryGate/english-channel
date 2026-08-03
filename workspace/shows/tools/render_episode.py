from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"))
sys.path.insert(0, str(TOOLS_DIR))

from audiobook_workspace import compose_control, normalize_segment_peak  # noqa: E402
from prepare_reference_concat_audio import build_concat_audio  # noqa: E402
from render_chapter import load_voxcpm  # noqa: E402
from episode_artifacts import turn_wav_path  # noqa: E402

SHOW_CONFIG_PATH = Path(__file__).resolve().parent / "show_config.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_segment_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def character_profiles_for(show: dict[str, Any]) -> dict[str, str]:
    profiles = dict(show.get("characterProfiles") or {})
    if profiles:
        return {str(k): str(v) for k, v in profiles.items()}
    return {str(k): str(v) for k, v in dict(show.get("deliveryCues") or {}).items()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render dialogue podcast turns (audiobook-parity: one model load, compose_control)."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--segments", help="Comma-separated turn ids, e.g. p003,p015.")
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip turns whose WAV already exists (full-run resume).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="With --skip-existing, still overwrite existing WAVs.",
    )
    parser.add_argument(
        "--no-compose",
        action="store_true",
        help="Skip concat of turn WAVs into 000_episode_XXX.raw.wav.",
    )
    parser.add_argument(
        "--no-self-check",
        action="store_true",
        help="Skip post-compose QC self-check (audiobook parity).",
    )
    args = parser.parse_args()

    if "expandable_segments" in os.environ.get("PYTORCH_CUDA_ALLOC_CONF", ""):
        os.environ.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

    manifest_path = Path(args.manifest)
    workspace = manifest_path.parent
    manifest = load_json(manifest_path)
    show_id = str(manifest["showId"])
    settings = manifest["renderSettings"]
    show = load_json(SHOW_CONFIG_PATH)["shows"][show_id]
    profiles = character_profiles_for(show)
    selected_ids = parse_segment_ids(args.segments)
    known_ids = {str(turn["id"]) for turn in manifest["turns"]}
    unknown_ids = selected_ids - known_ids
    if unknown_ids:
        raise ValueError(f"Unknown segment ids: {sorted(unknown_ids)}")

    to_render: list[dict[str, Any]] = []
    for turn in manifest["turns"]:
        turn_id = str(turn["id"])
        if selected_ids and turn_id not in selected_ids:
            continue
        out = turn_wav_path(workspace, str(turn["filename"]))
        # Selective --segments overwrites (same as render_chapter --segments).
        # Full run with --skip-existing resumes by keeping existing WAVs.
        if not selected_ids and args.skip_existing and not args.force and out.is_file():
            continue
        to_render.append(turn)

    if not to_render:
        print("nothing to render", flush=True)
    else:
        print(f"Loading VoxCPM2 once for {len(to_render)} turn(s)...", flush=True)
        model = load_voxcpm(str(settings.get("modelId", "pretrained_models/VoxCPM2")), args.device)
        sample_rate = int(model.tts_model.sample_rate)
        rendered: list[dict[str, Any]] = []

        for turn in to_render:
            speaker = str(turn["speaker"])
            host = manifest["hosts"][speaker]
            output = turn_wav_path(workspace, str(turn["filename"]))
            output.parent.mkdir(parents=True, exist_ok=True)
            segment = {
                "id": turn["id"],
                "order": turn["order"],
                "filename": turn["filename"],
                "kind": "dialogue",
                "speaker": speaker,
                "text": turn["text"],
                "wordCount": turn.get("wordCount"),
                "deliveryCue": turn.get("deliveryCue") or "natural dialogue delivery",
            }
            if turn.get("maxLen") is not None and int(turn["maxLen"]) <= 128:
                segment["maxLen"] = int(turn["maxLen"])
            request = compose_control(
                segment,
                global_control="",
                pace_cue=None,
                character_profiles=profiles,
            )
            reference_audio = str(REPO_ROOT / host["referenceAudioClean"])
            print(
                f"Rendering {turn['id']} {speaker} -> {output.name} | "
                f"{request['policy']} max_len={request['maxLen']}",
                flush=True,
            )
            kwargs = {
                "text": request["ttsText"],
                "reference_wav_path": reference_audio,
                "cfg_value": float(settings.get("cfgValue", 2.35)),
                "inference_timesteps": int(settings.get("inferenceTimesteps", 10)),
                "normalize": False,
                "denoise": False,
            }
            if request["maxLen"] is not None:
                kwargs["max_len"] = int(request["maxLen"])
            wav = model.generate(**kwargs).astype(np.float32, copy=False)
            wav = normalize_segment_peak(wav)
            sf.write(output, wav, sample_rate)
            rendered.append(
                {
                    "id": turn["id"],
                    "speaker": speaker,
                    "filename": turn["filename"],
                    "sampleRate": sample_rate,
                    "durationSec": round(float(len(wav) / sample_rate), 3),
                    "peak": round(float(np.max(np.abs(wav))) if len(wav) else 0.0, 6),
                    "referenceAudio": host["referenceAudioClean"],
                    "deliveryCue": turn.get("deliveryCue", ""),
                    "policy": request["policy"],
                    "maxLen": request["maxLen"],
                }
            )
            del wav
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

        previous_rendered = list(manifest.get("rendered") or [])
        rendered_ids = {str(item["id"]) for item in rendered}
        if selected_ids or args.skip_existing:
            manifest["rendered"] = [item for item in previous_rendered if str(item.get("id")) not in rendered_ids] + rendered
        else:
            manifest["rendered"] = rendered
        manifest["activeRenderer"] = "elr-show-episode-renderer-v2-audiobook-parity"
        write_json(manifest_path, manifest)
        report_name = str(settings.get("renderReport", "render_report.json"))
        report_path = workspace / "reports" / report_name if not Path(report_name).is_absolute() else Path(report_name)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(report_path, {"rendered": rendered})
        print(f"rendered={len(rendered)}", flush=True)
        del model
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    if not args.no_compose:
        clips = [turn_wav_path(workspace, str(t["filename"])) for t in manifest["turns"]]
        missing = [str(c) for c in clips if not c.is_file()]
        if missing:
            raise FileNotFoundError(f"Cannot compose raw.wav; missing turns: {missing[:5]}")
        episode_id = str(manifest["episodeId"])
        audio_dir = workspace / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        raw_path = audio_dir / f"000_{episode_id}.raw.wav"
        gap = float(settings.get("interTurnSilenceSec", 0.3))
        build_concat_audio(clips, raw_path, gap_sec=gap)
        print(f"raw={raw_path.as_posix()}", flush=True)

        if not args.no_self_check:
            from check_chapter import format_qc_conversation_summary  # noqa: E402
            from check_episode import run_episode_check  # noqa: E402

            print("\n=== QC SELF-CHECK ===", flush=True)
            qc_report = run_episode_check(manifest_path, write_report=False, run_asr_layer=True)
            print(format_qc_conversation_summary(qc_report), flush=True)
            print("请确认后再 master / 视频打包。未确认前不要自动重渲染。", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
