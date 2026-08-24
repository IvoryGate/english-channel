from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKER_ROOT = REPO / "apps" / "worker-py"
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))

from worker.classics.config import ConfigError, load_book_config  # noqa: E402
from worker.classics.io import atomic_write_json, read_json  # noqa: E402
from worker.classics.paths import ClassicPaths  # noqa: E402
from worker.classics.preflight import preflight_chapter  # noqa: E402
from worker.classics.providers.hardware import heavy_resource_lease  # noqa: E402
from worker.classics.run_state import RunStateStore, utc_now  # noqa: E402
from worker.classics.segment import rechunk_manifest_payload  # noqa: E402


def command_ingest(args: argparse.Namespace) -> int:
    from worker.classics.epub_ingest import ingest_book

    config = load_book_config(REPO, args.book)
    inventory = ingest_book(REPO, config, force=args.force)
    paths = ClassicPaths(REPO, config.slug)
    RunStateStore(paths.state).write(
        {
            "schema": "classic-listening-run-state-v1",
            "bookSlug": config.slug,
            "status": "READY",
            "phase": "INGESTED",
            "startedAt": utc_now(),
            "chapterState": {f"chapter_{number:03d}": "INGESTED" for number in range(1, config.chapter_count + 1)},
            "inventoryPath": paths.inventory.relative_to(REPO).as_posix(),
        }
    )
    print(f"book={config.slug}")
    print(f"chapters={inventory['chapterCount']}")
    print(f"words={inventory['totalWordCount']}")
    print(f"inventory={paths.inventory}")
    return 0


def command_preflight(args: argparse.Namespace) -> int:
    config = load_book_config(REPO, args.book)
    report = preflight_chapter(REPO, config, args.chapter)
    for check in report.checks:
        print(f"[{check.status.upper()}] {check.name}: {check.detail}")
    return 0 if report.ok else 1


def command_status(args: argparse.Namespace) -> int:
    config = load_book_config(REPO, args.book)
    paths = ClassicPaths(REPO, config.slug)
    state = RunStateStore(paths.state).read()
    if args.json:
        print(json.dumps(state or {"bookSlug": config.slug, "status": "NOT_STARTED"}, ensure_ascii=False, indent=2))
        return 0
    if state is None:
        print(f"book={config.slug} status=NOT_STARTED")
        return 0
    print(f"book={config.slug} status={state.get('status')} phase={state.get('phase')}")
    print(f"updated={state.get('updatedAt')}")
    print(f"inventory={state.get('inventoryPath')}")
    return 0


def command_preview_voice(args: argparse.Namespace) -> int:
    from worker.classics.audio_render import render_audio

    config = load_book_config(REPO, args.book)
    trace = render_audio(
        REPO,
        config,
        args.chapter,
        parse_segment_ids(args.segments),
        preview_name=args.name,
        force=args.force,
        cfg_value=args.cfg_value,
        inference_timesteps=args.inference_timesteps,
        isolated_preview=args.isolated or args.cfg_value is not None or args.inference_timesteps is not None,
    )
    print(f"segments={len(trace['segments'])}")
    print(f"preview={REPO / str(trace['previewPath'])}")
    print(f"trace={REPO / str(trace['tracePath'])}")
    return 0


def command_preview_voice_variants(args: argparse.Namespace) -> int:
    from worker.classics.audio_render import _default_model_factory, render_audio

    config = load_book_config(REPO, args.book)
    model_path = config.runtime_path(REPO, str(config.render["modelId"]))
    model = _default_model_factory(str(model_path), str(config.render.get("device", "cuda")))
    selected = parse_segment_ids(args.segments)
    for value in args.variant:
        parts = value.split(":")
        if len(parts) != 3:
            raise ValueError("Each --variant must use NAME:CFG:STEPS")
        name, cfg_text, steps_text = parts
        trace = render_audio(
            REPO,
            config,
            args.chapter,
            selected,
            preview_name=name,
            force=True,
            cfg_value=float(cfg_text),
            inference_timesteps=int(steps_text),
            isolated_preview=True,
            model_factory=lambda *_: model,
        )
        print(f"variant={name} preview={REPO / str(trace['previewPath'])}")
    return 0


def command_audio_metrics(args: argparse.Namespace) -> int:
    from worker.classics.audio_metrics import audio_texture_metrics

    reports = []
    for value in args.file:
        path = Path(value)
        if not path.is_absolute():
            path = REPO / path
        reports.append(audio_texture_metrics(path))
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0


def command_build_v2_proof(args: argparse.Namespace) -> int:
    from worker.classics.v2_proof import build_v2_proof

    config = load_book_config(REPO, args.book)
    scenes: list[tuple[str, Path]] = []
    for value in args.scene:
        end_id, separator, path_text = value.partition(":")
        if not separator or not end_id.isdigit() or not path_text:
            raise ValueError("Each --scene must use END_SEGMENT_ID:IMAGE_PATH")
        scenes.append((end_id.zfill(3), Path(path_text)))
    result = build_v2_proof(
        REPO,
        config,
        args.chapter,
        args.preview_name,
        sorted(parse_segment_ids(args.segments)),
        scenes,
        transition_sec=args.transition_sec,
        model_name=args.model,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_build_v2_chapter(args: argparse.Namespace) -> int:
    from worker.classics.v2_chapter import build_v2_chapter

    config = load_book_config(REPO, args.book)
    scene_manifest = Path(args.scene_manifest)
    if not scene_manifest.is_absolute():
        scene_manifest = REPO / scene_manifest
    result = build_v2_chapter(
        REPO,
        config,
        args.chapter,
        args.preview_name,
        scene_manifest,
        transition_sec=args.transition_sec,
        model_name=args.model,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_recompose_v2_final(args: argparse.Namespace) -> int:
    from worker.classics.v2_chapter import recompose_v2_final

    config = load_book_config(REPO, args.book)
    result = recompose_v2_final(REPO, config, args.chapter)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_render_brand_voice(args: argparse.Namespace) -> int:
    from worker.classics.brand_voice import render_brand_voice

    config = load_book_config(REPO, args.book)
    trace = render_brand_voice(REPO, config, force=args.force)
    for clip in trace["clips"]:
        print(f"{clip['kind']}={REPO / str(clip['path'])}")
        print(f"{clip['kind']}_duration={clip['durationSec']}")
    print(f"trace={REPO / str(trace['tracePath'])}")
    return 0


def command_render_audio(args: argparse.Namespace) -> int:
    from worker.classics.audio_render import render_audio

    config = load_book_config(REPO, args.book)
    trace = render_audio(REPO, config, args.chapter, force=args.force)
    print(f"segments={len(trace['segments'])}")
    print(f"raw={REPO / str(trace['rawPath'])}")
    print(f"trace={REPO / str(trace['tracePath'])}")
    return 0


def parse_chapters(value: str) -> list[int]:
    selected: set[int] = set()
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError("Chapter range start must not exceed its end")
            selected.update(range(start, end + 1))
        else:
            selected.add(int(token))
    if not selected:
        raise ValueError("At least one chapter is required")
    return sorted(selected)


def parse_segment_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    selected = {part.strip().zfill(3) for part in value.split(",") if part.strip()}
    if any(not item.isdigit() for item in selected):
        raise ValueError("Segment ids must be comma-separated numbers")
    return selected


def command_render_chapter_brand_voice(args: argparse.Namespace) -> int:
    from worker.classics.brand_voice import render_chapter_brand_voice

    config = load_book_config(REPO, args.book)
    trace = render_chapter_brand_voice(REPO, config, parse_chapters(args.chapters), force=args.force)
    for clip in trace["clips"]:
        print(f"chapter={clip['chapter']} kind={clip['kind']} duration={clip['durationSec']} path={clip['path']}")
    print(f"trace={REPO / str(trace['tracePath'])}")
    return 0


def command_render_audio_range(args: argparse.Namespace) -> int:
    from worker.classics.audio_render import _default_model_factory, render_audio

    config = load_book_config(REPO, args.book)
    chapters = parse_chapters(args.chapters)
    model_path = config.runtime_path(REPO, str(config.render["modelId"]))
    model = _default_model_factory(str(model_path), str(config.render.get("device", "cuda")))
    for chapter in chapters:
        trace = render_audio(REPO, config, chapter, force=args.force, model_factory=lambda *_: model)
        print(f"chapter={chapter} segments={len(trace['segments'])} raw={trace['rawPath']}")
    return 0


def command_package(args: argparse.Namespace) -> int:
    from worker.classics.chapter_package import package_chapter

    config = load_book_config(REPO, args.book)
    result = package_chapter(REPO, config, args.chapter, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_qc(args: argparse.Namespace) -> int:
    from worker.classics.qc import qc_chapter

    config = load_book_config(REPO, args.book)
    report = qc_chapter(REPO, config, args.chapter)
    print(f"status={report['status']} segments={report['actualSegmentCount']} warnings={len(report['warnings'])}")
    print(f"report={REPO / str(report['reportPath'])}")
    return 0 if report["status"] == "PASS" else 1


def command_render_chapter_visuals(args: argparse.Namespace) -> int:
    from worker.classics.production import render_chapter_visuals

    config = load_book_config(REPO, args.book)
    result = render_chapter_visuals(REPO, config, parse_chapters(args.chapters), force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_qc_asr(args: argparse.Namespace) -> int:
    from worker.classics.asr_qc import asr_qc_chapter

    config = load_book_config(REPO, args.book)
    selected = parse_segment_ids(args.segments) if args.segments else None
    report = asr_qc_chapter(REPO, config, args.chapter, selected_ids=selected, model_name=args.model)
    print(f"checked={report['checkedSegmentCount']} mean_similarity={report['meanSimilarity']}")
    print(f"review={','.join(report['reviewSegmentIds']) or 'none'}")
    print(f"report={REPO / str(report['reportPath'])}")
    return 0 if not report["reviewSegmentIds"] else 1


def command_produce(args: argparse.Namespace) -> int:
    from worker.classics.production import produce_chapters

    config = load_book_config(REPO, args.book)
    result = produce_chapters(REPO, config, parse_chapters(args.chapters), force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_rechunk(args: argparse.Namespace) -> int:
    config = load_book_config(REPO, args.book)
    paths = ClassicPaths(REPO, config.slug)
    manifest_path = paths.segments(args.chapter)
    payload = read_json(manifest_path)
    before = len(payload["segments"])
    updated = rechunk_manifest_payload(
        payload, max_words=args.max_words, preserve_through=args.preserve_through
    )
    updated["cfgValue"] = config.voice["cfgValue"]
    updated["inferenceTimesteps"] = config.voice["inferenceTimesteps"]
    atomic_write_json(manifest_path, updated)
    print(f"chapter={args.chapter} segments={before}->{len(updated['segments'])} preserve_through={args.preserve_through}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classic Listening audiobook production control.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    ingest = subparsers.add_parser("ingest", help="Verify EPUB provenance and create chapter source/manifests.")
    ingest.add_argument("--book", required=True)
    ingest.add_argument("--force", action="store_true")
    ingest.set_defaults(func=command_ingest)
    preflight = subparsers.add_parser("preflight", help="Validate one chapter before GPU rendering.")
    preflight.add_argument("--book", required=True)
    preflight.add_argument("--chapter", required=True, type=int)
    preflight.set_defaults(func=command_preflight)
    status = subparsers.add_parser("status", help="Show persisted book production state.")
    status.add_argument("--book", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)
    preview = subparsers.add_parser("preview-voice", help="Render a small Riley approval sample before a chapter run.")
    preview.add_argument("--book", required=True)
    preview.add_argument("--chapter", required=True, type=int)
    preview.add_argument("--segments", default="008,009,010,011,012")
    preview.add_argument("--name", default="riley-voice-gate-001")
    preview.add_argument("--force", action="store_true", help="Regenerate selected audio instead of reusing it.")
    preview.add_argument("--cfg-value", type=float, help="Preview-only VoxCPM guidance override.")
    preview.add_argument("--inference-timesteps", type=int, help="Preview-only VoxCPM step override.")
    preview.add_argument(
        "--isolated",
        action="store_true",
        help="Write generated segment variants under the preview directory without replacing production WAVs.",
    )
    preview.set_defaults(func=command_preview_voice)
    variants = subparsers.add_parser(
        "preview-voice-variants",
        help="Render isolated Riley parameter variants with one shared model load.",
    )
    variants.add_argument("--book", required=True)
    variants.add_argument("--chapter", required=True, type=int)
    variants.add_argument("--segments", required=True)
    variants.add_argument(
        "--variant",
        action="append",
        required=True,
        metavar="NAME:CFG:STEPS",
    )
    variants.set_defaults(func=command_preview_voice_variants)
    metrics = subparsers.add_parser(
        "audio-metrics",
        help="Measure comparable spectral texture metrics for audio candidates.",
    )
    metrics.add_argument("--file", action="append", required=True)
    metrics.set_defaults(func=command_audio_metrics)
    proof = subparsers.add_parser(
        "build-v2-proof",
        help="Build a word-aligned, multi-scene review proof without replacing chapter exports.",
    )
    proof.add_argument("--book", required=True)
    proof.add_argument("--chapter", required=True, type=int)
    proof.add_argument("--preview-name", required=True)
    proof.add_argument("--segments", required=True)
    proof.add_argument("--scene", action="append", required=True, metavar="END_SEGMENT_ID:IMAGE_PATH")
    proof.add_argument("--transition-sec", type=float, default=1.5)
    proof.add_argument("--model", default="base")
    proof.set_defaults(func=command_build_v2_proof)
    v2_chapter = subparsers.add_parser(
        "build-v2-chapter",
        help="Build a complete versioned multi-scene chapter and YouTube review package.",
    )
    v2_chapter.add_argument("--book", required=True)
    v2_chapter.add_argument("--chapter", required=True, type=int)
    v2_chapter.add_argument("--preview-name", required=True)
    v2_chapter.add_argument("--scene-manifest", required=True)
    v2_chapter.add_argument("--transition-sec", type=float, default=1.5)
    v2_chapter.add_argument("--model", default="base")
    v2_chapter.set_defaults(func=command_build_v2_chapter)
    recompose = subparsers.add_parser(
        "recompose-v2-final",
        help="Rebuild the versioned final chapter with reset timestamps and refresh its export verification.",
    )
    recompose.add_argument("--book", required=True)
    recompose.add_argument("--chapter", required=True, type=int)
    recompose.set_defaults(func=command_recompose_v2_final)
    brand_voice = subparsers.add_parser(
        "render-brand-voice",
        help="Generate the spoken Classic Listening intro and outro with the configured narrator.",
    )
    brand_voice.add_argument("--book", required=True)
    brand_voice.add_argument("--force", action="store_true")
    brand_voice.set_defaults(func=command_render_brand_voice)
    render = subparsers.add_parser("render-audio", help="Render and compose all narration segments for one chapter.")
    render.add_argument("--book", required=True)
    render.add_argument("--chapter", required=True, type=int)
    render.add_argument("--force", action="store_true")
    render.set_defaults(func=command_render_audio)
    chapter_brand = subparsers.add_parser(
        "render-chapter-brand-voice", help="Generate chapter-specific Classic Listening intros and outros."
    )
    chapter_brand.add_argument("--book", required=True)
    chapter_brand.add_argument("--chapters", required=True)
    chapter_brand.add_argument("--force", action="store_true")
    chapter_brand.set_defaults(func=command_render_chapter_brand_voice)
    audio_range = subparsers.add_parser("render-audio-range", help="Render several chapters while reusing one loaded model.")
    audio_range.add_argument("--book", required=True)
    audio_range.add_argument("--chapters", required=True)
    audio_range.add_argument("--force", action="store_true")
    audio_range.set_defaults(func=command_render_audio_range)
    package = subparsers.add_parser("package", help="Master, subtitle, compose, verify, and export one chapter.")
    package.add_argument("--book", required=True)
    package.add_argument("--chapter", required=True, type=int)
    package.add_argument("--force", action="store_true")
    package.set_defaults(func=command_package)
    qc = subparsers.add_parser("qc", help="Run structural and acoustic checks on rendered narration segments.")
    qc.add_argument("--book", required=True)
    qc.add_argument("--chapter", required=True, type=int)
    qc.set_defaults(func=command_qc)
    visuals = subparsers.add_parser("render-chapter-visuals", help="Render chapter thumbnails and branding clips.")
    visuals.add_argument("--book", required=True)
    visuals.add_argument("--chapters", required=True)
    visuals.add_argument("--force", action="store_true")
    visuals.set_defaults(func=command_render_chapter_visuals)
    asr = subparsers.add_parser("qc-asr", help="Transcribe narration segments locally and compare them with source text.")
    asr.add_argument("--book", required=True)
    asr.add_argument("--chapter", required=True, type=int)
    asr.add_argument("--segments")
    asr.add_argument("--model", default="base")
    asr.set_defaults(func=command_qc_asr)
    produce = subparsers.add_parser("produce", help="Run chapter branding, narration, visuals, packaging, and export.")
    produce.add_argument("--book", required=True)
    produce.add_argument("--chapters", required=True)
    produce.add_argument("--force", action="store_true")
    produce.set_defaults(func=command_produce)
    rechunk = subparsers.add_parser("rechunk", help="Bound narration segment length while preserving source coverage.")
    rechunk.add_argument("--book", required=True)
    rechunk.add_argument("--chapter", required=True, type=int)
    rechunk.add_argument("--max-words", type=int, default=30)
    rechunk.add_argument("--preserve-through", type=int, default=0)
    rechunk.set_defaults(func=command_rechunk)
    return parser


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "ops":
        from worker.classics.transport import main as operations_main

        return operations_main(["--repo-root", str(REPO), *sys.argv[2:]])
    args = build_parser().parse_args()
    try:
        heavy_commands = {
            "preview-voice",
            "preview-voice-variants",
            "build-v2-proof",
            "build-v2-chapter",
            "recompose-v2-final",
            "render-brand-voice",
            "render-audio",
            "render-chapter-brand-voice",
            "render-audio-range",
            "package",
            "render-chapter-visuals",
            "qc-asr",
            "produce",
        }
        if args.command in heavy_commands:
            with heavy_resource_lease(REPO, f"classics:{args.command}"):
                return int(args.func(args))
        return int(args.func(args))
    except (ConfigError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
