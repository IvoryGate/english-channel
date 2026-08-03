from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "workspace" / "shows" / "tools"
for import_path in (REPO / "scripts", TOOLS):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from elr_production import (  # noqa: E402
    EpisodeContext,
    build_context,
    preflight_episode,
    reports_ok,
)
from elr_run_state import RunStateStore, state_path, utc_now  # noqa: E402
from episode_workspace import normalize_episode_id, resolve_series  # noqa: E402
from gpu_production_lock import (  # noqa: E402
    DEFAULT_RENDER_BATCH_SIZE,
    GpuProductionLock,
    pid_alive,
    validate_render_batch_size,
)


DEFAULT_PYTHON = REPO / ".conda-env" / "python.exe"
PREPARE_MANIFEST = TOOLS / "prepare_episode_manifest.py"
MONITOR_PRODUCTION = REPO / "scripts" / "monitor_episode_production.py"
MONITOR_RENDER = REPO / "scripts" / "monitor_episode_render.py"
SERIES_CFG = {"series_a": 2.35, "series_b": 2.15, "series_c": 2.35}


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, message: str) -> None:
        line = message.rstrip()
        print(line, flush=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")

    def event(self, message: str) -> None:
        self.write(f"[{utc_now()}] {message}")


def run_streamed(
    cmd: list[str],
    *,
    logger: RunLogger,
    heartbeat: Callable[[str], Any] | None = None,
) -> int:
    logger.write("  command: " + subprocess.list2cmdline(cmd))
    env = {**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE", "PYTHONUNBUFFERED": "1"}
    process = subprocess.Popen(
        cmd,
        cwd=str(REPO),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.rstrip()
        logger.write("    " + line)
        if heartbeat is not None:
            heartbeat(line)
    return int(process.wait())


def prepare_command(context: EpisodeContext, python: Path) -> list[str]:
    draft = context.workspace / f"000_{context.episode_id}.draft.md"
    manifest = context.workspace / f"000_{context.episode_id}.episode_manifest.json"
    return [
        str(python),
        "-u",
        str(PREPARE_MANIFEST),
        "--draft",
        str(draft),
        "--show",
        context.show_id,
        "--output",
        str(manifest),
    ]


def monitor_command(
    context: EpisodeContext,
    python: Path,
    *,
    batch_size: int,
    force: bool,
    log_path: Path,
) -> list[str]:
    cmd = [
        str(python),
        "-u",
        str(MONITOR_PRODUCTION),
        "--show",
        context.show_id,
        "--episode",
        context.episode_id,
        "--workspace",
        str(context.workspace),
        "--episode-num",
        str(context.episode_num),
        "--youtube-root",
        str(context.youtube_root),
        "--cfg",
        str(SERIES_CFG[context.show_id]),
        "--batch-size",
        str(batch_size),
        "--retry-on-failure",
        "2",
        "--qc-no-asr",
        "--log",
        str(log_path),
    ]
    if force:
        cmd.append("--force")
    return cmd


def audio_render_command(
    context: EpisodeContext,
    python: Path,
    *,
    batch_size: int,
    force: bool,
    log_path: Path,
) -> list[str]:
    manifest = context.workspace / f"000_{context.episode_id}.episode_manifest.json"
    cmd = [
        str(python),
        "-u",
        str(MONITOR_RENDER),
        "--manifest",
        str(manifest),
        "--device",
        "cuda",
        "--cfg",
        str(SERIES_CFG[context.show_id]),
        "--batch-size",
        str(batch_size),
        "--retry-on-failure",
        "2",
        "--no-self-check",
        "--turns-only",
        "--log-file",
        str(log_path),
    ]
    if force:
        cmd.append("--force")
    return cmd


def _contexts(args: argparse.Namespace) -> list[EpisodeContext]:
    return [
        build_context(REPO, show_id, args.episode, Path(args.youtube_root))
        for show_id in resolve_series(args.series)
    ]


def _print_preflight(report: Any) -> None:
    print(f"{report.show_id}/{report.episode_id}: {'PASS' if report.ok else 'FAIL'}", flush=True)
    for check in report.checks:
        marker = {"pass": "OK", "warn": "WARN", "error": "ERROR"}[check.status]
        print(f"  [{marker}] {check.name}: {check.detail}", flush=True)


def command_preflight(args: argparse.Namespace) -> int:
    reports = []
    for index, context in enumerate(_contexts(args)):
        report = preflight_episode(
            context,
            runtime_checks=not args.no_runtime_checks and index == 0,
            scaffold_metadata=not args.no_scaffold_metadata,
        )
        reports.append(report)
        _print_preflight(report)
    return 0 if reports_ok(reports) else 2


def _initial_state(
    args: argparse.Namespace,
    contexts: list[EpisodeContext],
    log_path: Path,
    *,
    status: str,
) -> dict[str, Any]:
    return {
        "schema": "elr-production-run-v1",
        "episodeId": contexts[0].episode_id,
        "series": [context.show_id for context in contexts],
        "batchSize": args.batch_size,
        "status": status,
        "phase": "STARTING",
        "pid": os.getpid(),
        "startedAt": utc_now(),
        "logPath": str(log_path),
        "command": subprocess.list2cmdline(sys.argv),
        "seriesState": {context.show_id: {"phase": "PENDING", "status": "PENDING"} for context in contexts},
    }


def _set_series_state(store: RunStateStore, show_id: str, **changes: Any) -> None:
    current = store.read() or {}
    series_state = dict(current.get("seriesState") or {})
    entry = dict(series_state.get(show_id) or {})
    entry.update(changes)
    entry["updatedAt"] = utc_now()
    series_state[show_id] = entry
    store.update(seriesState=series_state, currentSeries=show_id, **changes)


def execute_production(args: argparse.Namespace) -> int:
    validate_render_batch_size(args.batch_size)
    python = DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else Path(sys.executable)
    contexts = _contexts(args)
    episode_id = contexts[0].episode_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(args.run_log) if args.run_log else REPO / "logs" / "elr_runs" / f"{episode_id}_{timestamp}.log"
    store = RunStateStore(state_path(REPO, episode_id))
    logger = RunLogger(log_path)
    store.write(_initial_state(args, contexts, log_path, status="RUNNING"))
    logger.event(f"ELR production started episode={episode_id} series={[c.show_id for c in contexts]} batch={args.batch_size}")

    try:
        reports = []
        for index, context in enumerate(contexts):
            _set_series_state(store, context.show_id, phase="PREPARE", status="RUNNING")
            logger.event(f"{context.show_id}: prepare manifest")
            code = run_streamed(prepare_command(context, python), logger=logger, heartbeat=store.heartbeat)
            if code != 0:
                raise RuntimeError(f"{context.show_id} prepare failed with exit {code}")

            _set_series_state(store, context.show_id, phase="PREFLIGHT", status="RUNNING")
            report = preflight_episode(context, runtime_checks=index == 0, scaffold_metadata=True)
            reports.append(report)
            for check in report.checks:
                logger.write(f"  [{check.status.upper()}] {check.name}: {check.detail}")
            if not report.ok:
                raise RuntimeError(f"{context.show_id} preflight failed")
            _set_series_state(store, context.show_id, phase="READY", status="READY")

        if not reports_ok(reports):
            raise RuntimeError("preflight failed")

        if args.preflight_only:
            store.update(status="DONE", phase="PREFLIGHT_COMPLETE", finishedAt=utc_now())
            logger.event("Preflight complete")
            return 0

        with GpuProductionLock(f"elr_{episode_id}"):
            for context in contexts:
                _set_series_state(store, context.show_id, phase="RENDER_PACK_EXPORT", status="RUNNING")
                logger.event(f"{context.show_id}: render, pack, verify, export")
                child_log = log_path.with_name(f"{log_path.stem}.{context.show_id}.log")
                code = run_streamed(
                    monitor_command(
                        context,
                        python,
                        batch_size=args.batch_size,
                        force=args.force,
                        log_path=child_log,
                    ),
                    logger=logger,
                    heartbeat=store.heartbeat,
                )
                if code != 0:
                    raise RuntimeError(f"{context.show_id} production failed with exit {code}")
                _set_series_state(store, context.show_id, phase="DONE", status="DONE")

        store.update(status="DONE", phase="DONE", currentSeries="", finishedAt=utc_now(), detail="All requested series completed.")
        logger.event("ELR production completed")
        return 0
    except KeyboardInterrupt:
        store.update(status="CANCELLED", phase="CANCELLED", finishedAt=utc_now(), error="Interrupted by user.")
        logger.event("ELR production cancelled")
        return 130
    except Exception as exc:
        current = store.read() or {}
        current_show = str(current.get("currentSeries") or "")
        if current_show:
            _set_series_state(store, current_show, status="FAILED", error=str(exc))
        store.update(status="FAILED", phase="FAILED", finishedAt=utc_now(), error=str(exc))
        logger.event(f"ELR production failed: {exc}")
        return 2


def execute_audio_render(args: argparse.Namespace) -> int:
    validate_render_batch_size(args.batch_size)
    python = DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else Path(sys.executable)
    contexts = _contexts(args)
    episode_id = contexts[0].episode_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(args.run_log) if args.run_log else REPO / "logs" / "elr_runs" / f"{episode_id}_audio_{timestamp}.log"
    store = RunStateStore(state_path(REPO, episode_id))
    logger = RunLogger(log_path)
    store.write(_initial_state(args, contexts, log_path, status="RUNNING"))
    logger.event(f"ELR audio-first render started episode={episode_id} series={[c.show_id for c in contexts]} batch={args.batch_size}")

    try:
        reports = []
        for index, context in enumerate(contexts):
            _set_series_state(store, context.show_id, phase="AUDIO_PREPARE", status="RUNNING")
            logger.event(f"{context.show_id}: prepare manifest for audio")
            code = run_streamed(prepare_command(context, python), logger=logger, heartbeat=store.heartbeat)
            if code != 0:
                raise RuntimeError(f"{context.show_id} prepare failed with exit {code}")

            _set_series_state(store, context.show_id, phase="AUDIO_PREFLIGHT", status="RUNNING")
            report = preflight_episode(
                context,
                runtime_checks=index == 0,
                scaffold_metadata=True,
                require_visuals=False,
            )
            reports.append(report)
            for check in report.checks:
                logger.write(f"  [{check.status.upper()}] {check.name}: {check.detail}")
            if not report.ok:
                raise RuntimeError(f"{context.show_id} audio preflight failed")
            _set_series_state(store, context.show_id, phase="AUDIO_READY", status="READY")

        if not reports_ok(reports):
            raise RuntimeError("audio preflight failed")

        with GpuProductionLock(f"elr_audio_{episode_id}"):
            for context in contexts:
                _set_series_state(store, context.show_id, phase="AUDIO_RENDER", status="RUNNING")
                logger.event(f"{context.show_id}: render turn WAVs; visuals may be generated concurrently")
                child_log = log_path.with_name(f"{log_path.stem}.{context.show_id}.render.log")
                code = run_streamed(
                    audio_render_command(
                        context,
                        python,
                        batch_size=args.batch_size,
                        force=args.force,
                        log_path=child_log,
                    ),
                    logger=logger,
                    heartbeat=store.heartbeat,
                )
                if code != 0:
                    raise RuntimeError(f"{context.show_id} audio render failed with exit {code}")
                _set_series_state(store, context.show_id, phase="AUDIO_DONE", status="DONE")

        store.update(
            status="DONE",
            phase="AUDIO_DONE",
            currentSeries="",
            finishedAt=utc_now(),
            detail="Turn WAVs complete. Run produce/resume after visual assets are ready.",
        )
        logger.event("ELR audio-first render completed")
        return 0
    except KeyboardInterrupt:
        store.update(status="CANCELLED", phase="CANCELLED", finishedAt=utc_now(), error="Interrupted by user.")
        logger.event("ELR audio-first render cancelled")
        return 130
    except Exception as exc:
        current = store.read() or {}
        current_show = str(current.get("currentSeries") or "")
        if current_show:
            _set_series_state(store, current_show, status="FAILED", error=str(exc))
        store.update(status="FAILED", phase="FAILED", finishedAt=utc_now(), error=str(exc))
        logger.event(f"ELR audio-first render failed: {exc}")
        return 2


def _detach(args: argparse.Namespace) -> int:
    validate_render_batch_size(args.batch_size)
    contexts = _contexts(args)
    episode_id = contexts[0].episode_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO / "logs" / "elr_runs" / f"{episode_id}_{timestamp}.log"
    child_args = [arg for arg in sys.argv[1:] if arg not in {"--detach", "--visible-window"}]
    child_args.extend(["--run-log", str(log_path)])
    cmd = [str(DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else Path(sys.executable)), "-u", str(Path(__file__).resolve()), *child_args]
    store = RunStateStore(state_path(REPO, episode_id))
    payload = _initial_state(args, contexts, log_path, status="STARTING")
    payload["pid"] = -1
    payload["command"] = subprocess.list2cmdline(cmd)
    store.write(payload)
    creationflags = 0
    stdout: Any = subprocess.DEVNULL
    if args.visible_window and sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_CONSOLE
        stdout = None
    process = subprocess.Popen(
        cmd,
        cwd=str(REPO),
        stdout=stdout,
        stderr=subprocess.STDOUT if stdout is not None else None,
        creationflags=creationflags,
        env={**os.environ, "PYTHONUNBUFFERED": "1", "KMP_DUPLICATE_LIB_OK": "TRUE"},
    )
    # Update only launch facts. If the child already changed STARTING to
    # RUNNING, RunStateStore.update preserves that newer status.
    store.update(pid=process.pid, command=subprocess.list2cmdline(cmd), logPath=str(log_path))
    print(f"started pid={process.pid}")
    print(f"status={store.path}")
    print(f"log={log_path}")
    return 0


def command_produce(args: argparse.Namespace) -> int:
    validate_render_batch_size(args.batch_size)
    if args.dry_run:
        python = DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else Path(sys.executable)
        for context in _contexts(args):
            print(f"{context.show_id}: workspace={context.workspace}")
            print("  prepare=" + subprocess.list2cmdline(prepare_command(context, python)))
            print(
                "  produce="
                + subprocess.list2cmdline(
                    monitor_command(
                        context,
                        python,
                        batch_size=args.batch_size,
                        force=args.force,
                        log_path=REPO / "logs" / "elr_runs" / f"{context.episode_id}.{context.show_id}.log",
                    )
                )
            )
        return 0
    if args.detach:
        return _detach(args)
    return execute_production(args)


def command_render_audio(args: argparse.Namespace) -> int:
    validate_render_batch_size(args.batch_size)
    if args.dry_run:
        python = DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else Path(sys.executable)
        for context in _contexts(args):
            print(f"{context.show_id}: workspace={context.workspace}")
            print("  prepare=" + subprocess.list2cmdline(prepare_command(context, python)))
            print(
                "  audio="
                + subprocess.list2cmdline(
                    audio_render_command(
                        context,
                        python,
                        batch_size=args.batch_size,
                        force=args.force,
                        log_path=REPO / "logs" / "elr_runs" / f"{context.episode_id}.{context.show_id}.audio.log",
                    )
                )
            )
        return 0
    if args.detach:
        return _detach(args)
    return execute_audio_render(args)


def command_status(args: argparse.Namespace) -> int:
    episode_id = normalize_episode_id(args.episode)
    store = RunStateStore(state_path(REPO, episode_id))
    state = store.read()
    if state is None:
        print(f"No production state found for {episode_id}.")
        return 1
    pid = int(state.get("pid") or -1)
    alive = pid_alive(pid)
    if state.get("status") in {"STARTING", "RUNNING"} and not alive:
        state["effectiveStatus"] = "INTERRUPTED"
    else:
        state["effectiveStatus"] = state.get("status")
    state["processAlive"] = alive
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    print(f"episode={episode_id} status={state['effectiveStatus']} phase={state.get('phase')} pid={pid} alive={alive}")
    print(f"updated={state.get('updatedAt')} heartbeat={state.get('heartbeatAt')}")
    print(f"log={state.get('logPath')}")
    for show_id, item in (state.get("seriesState") or {}).items():
        print(f"  {show_id}: status={item.get('status')} phase={item.get('phase')}")
    if state.get("error"):
        print(f"error={state['error']}")
    return 0


def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--episode", required=True, help="Episode number, such as 17 or episode_017.")
    parser.add_argument("--series", default="all", choices=["all", "series_a", "series_b", "series_c"])
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_RENDER_BATCH_SIZE)
    parser.add_argument("--force", action="store_true", help="Re-render existing turn WAVs.")
    parser.add_argument("--detach", action="store_true", help="Run in the background and return PID/status/log paths.")
    parser.add_argument("--visible-window", action="store_true", help="With --detach on Windows, open a visible console.")
    parser.add_argument("--dry-run", action="store_true", help="Print canonical paths and commands without writing or running.")
    parser.add_argument("--preflight-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--run-log", default="", help=argparse.SUPPRESS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="English Listening Room production control.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="Validate scripts, manifests, assets, runtime, and capacity.")
    preflight.add_argument("--episode", required=True)
    preflight.add_argument("--series", default="all", choices=["all", "series_a", "series_b", "series_c"])
    preflight.add_argument("--youtube-root", default=r"H:\Youtube")
    preflight.add_argument("--no-runtime-checks", action="store_true")
    preflight.add_argument("--no-scaffold-metadata", action="store_true")
    preflight.set_defaults(func=command_preflight)

    produce = subparsers.add_parser("produce", help="Prepare, preflight, then render/pack/export serially.")
    _add_run_args(produce)
    produce.set_defaults(func=command_produce)

    resume = subparsers.add_parser("resume", help="Resume using existing turn WAVs and package artifacts.")
    _add_run_args(resume)
    resume.set_defaults(func=command_produce, force=False)

    render_audio = subparsers.add_parser(
        "render-audio",
        help="Render/resume turn WAVs while approved visual assets are generated separately.",
    )
    _add_run_args(render_audio)
    render_audio.set_defaults(func=command_render_audio)

    status = subparsers.add_parser("status", help="Show persisted progress without inspecting a hidden terminal.")
    status.add_argument("--episode", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if getattr(args, "visible_window", False) and not getattr(args, "detach", False):
        raise SystemExit("--visible-window requires --detach")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
