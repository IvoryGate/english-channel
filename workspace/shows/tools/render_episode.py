from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"))
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT / "apps" / "worker-py"))

from prepare_reference_concat_audio import build_concat_audio  # noqa: E402
from episode_artifacts import turn_wav_path  # noqa: E402
from worker.tts.dialogue import dialogue_turn_is_reusable, dialogue_turn_spec  # noqa: E402
from worker.tts.process import run_provider_batch  # noqa: E402
from worker.tts.schema import resolve_provider_config  # noqa: E402
from worker.tts.trace import TRACE_SCHEMA, atomic_write_json, sha256_file, turn_trace_path  # noqa: E402

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_segment_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render dialogue turns with one manifest-selected provider load per invocation."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--segments", help="Comma-separated turn ids, e.g. p003,p015.")
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reuse turns whose WAV and complete trace identity still match.",
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
    settings = manifest["renderSettings"]
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
        # Selective --segments overwrites. Full-run resume reuses only a WAV
        # whose provider/voice/text/settings identity and recorded hash match.
        if (
            not selected_ids
            and args.skip_existing
            and not args.force
            and dialogue_turn_is_reusable(REPO_ROOT, manifest, turn, out)
        ):
            continue
        to_render.append(turn)

    if not to_render:
        print("nothing to render", flush=True)
    else:
        if "ttsProvider" not in settings:
            settings["device"] = args.device
        provider = resolve_provider_config(REPO_ROOT, settings)
        print(
            f"Loading {provider.provider_id} once for {len(to_render)} turn(s)...",
            flush=True,
        )
        requests: list[dict[str, Any]] = []
        specs: dict[str, dict[str, Any]] = {}
        previous_trace: dict[str, dict[str, Any]] = {}
        for turn in to_render:
            turn_id = str(turn["id"])
            output = turn_wav_path(workspace, str(turn["filename"]))
            spec = dialogue_turn_spec(REPO_ROOT, manifest, turn)
            specs[turn_id] = spec
            prior_path = turn_trace_path(output)
            if prior_path.is_file():
                try:
                    previous_trace[turn_id] = load_json(prior_path)
                except (OSError, ValueError):
                    pass
            requests.append(
                {
                    "id": turn_id,
                    "outputPath": str(output),
                    "text": spec["normalizedText"],
                    "voice": spec["workerVoice"],
                    "referenceText": manifest["hosts"][str(turn["speaker"])].get("referenceText", ""),
                    "seed": spec["seed"],
                    "maxLen": turn.get("maxLen"),
                }
            )
        results = run_provider_batch(
            REPO_ROOT,
            provider,
            requests,
            label=f"elr-{manifest['episodeId']}-{provider.provider_id}",
        )
        by_id = {str(item["id"]): item for item in results}
        rendered: list[dict[str, Any]] = []

        for turn in to_render:
            turn_id = str(turn["id"])
            speaker = str(turn["speaker"])
            output = turn_wav_path(workspace, str(turn["filename"]))
            result = by_id[turn_id]
            spec = specs[turn_id]
            prior = previous_trace.get(turn_id) or {}
            prior_hash = prior.get("outputSha256")
            retry_number = int(prior.get("retryNumber") or -1) + 1 if prior else 0
            trace = {
                "schema": TRACE_SCHEMA,
                "turnId": turn_id,
                "episodeId": manifest["episodeId"],
                "speaker": speaker,
                "renderedAt": datetime.now(timezone.utc).isoformat(),
                "provider": {
                    **provider.to_trace(REPO_ROOT),
                    "packageVersion": result["packageVersion"],
                    "modelLoadSec": result["modelLoadSec"],
                },
                "voice": spec["voice"],
                "normalizedText": spec["normalizedText"],
                "seed": spec["seed"],
                "effectiveSettings": provider.settings,
                "identitySha256": spec["identity"]["sha256"],
                "sampleRate": result["sampleRate"],
                "durationSec": result["durationSec"],
                "generationSec": result["generationSec"],
                "peak": result["peak"],
                "outputSha256": result["outputSha256"],
                "watermark": result["watermark"],
                "retryNumber": retry_number,
                "priorArtifactSha256": prior_hash,
            }
            atomic_write_json(turn_trace_path(output), trace)
            print(
                f"Rendered {turn_id} {speaker} -> {output.name} | "
                f"provider={provider.provider_id} seed={spec['seed']}",
                flush=True,
            )
            rendered.append(
                {
                    "id": turn_id,
                    "speaker": speaker,
                    "filename": turn["filename"],
                    "sampleRate": result["sampleRate"],
                    "durationSec": result["durationSec"],
                    "peak": result["peak"],
                    "providerId": provider.provider_id,
                    "tracePath": turn_trace_path(output).relative_to(REPO_ROOT).as_posix(),
                    "outputSha256": sha256_file(output),
                    "deliveryCue": turn.get("deliveryCue", ""),
                    "maxLen": turn.get("maxLen"),
                }
            )

        previous_rendered = list(manifest.get("rendered") or [])
        rendered_ids = {str(item["id"]) for item in rendered}
        if selected_ids or args.skip_existing:
            manifest["rendered"] = [item for item in previous_rendered if str(item.get("id")) not in rendered_ids] + rendered
        else:
            manifest["rendered"] = rendered
        manifest["activeRenderer"] = "elr-show-episode-renderer-v3-provider-batch"
        write_json(manifest_path, manifest)
        report_name = str(settings.get("renderReport", "render_report.json"))
        report_path = workspace / "reports" / report_name if not Path(report_name).is_absolute() else Path(report_name)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(report_path, {"provider": provider.to_trace(REPO_ROOT), "rendered": rendered})
        print(f"rendered={len(rendered)}", flush=True)

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
