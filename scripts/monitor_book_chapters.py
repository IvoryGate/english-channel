from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO_ROOT / ".conda-env" / "python.exe"
DEFAULT_RENDER_SCRIPT = (
    REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts" / "render_book_chapters.py"
)
DEFAULT_LOG = REPO_ROOT / "logs" / "monitor_book_chapters.log"
DEFAULT_END = 61

_stop_requested = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _format_duration(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


class MonitorLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.log_path.open("a", encoding="utf-8", newline="\n")

    def close(self) -> None:
        self._file.close()

    def write(self, message: str) -> None:
        line = message.rstrip()
        print(line, flush=True)
        self._file.write(line + "\n")
        self._file.flush()

    def log(self, message: str) -> None:
        self.write(f"[{_format_ts(_utc_now())}] {message}")


def _handle_stop(signum: int, _frame: object | None) -> None:
    global _stop_requested
    _stop_requested = True


def build_render_command(
    python: Path,
    render_script: Path,
    chapter: int,
    workspace_root: str,
) -> list[str]:
    return [
        str(python),
        str(render_script),
        "--start",
        str(chapter),
        "--end",
        str(chapter),
        "--workspace-root",
        workspace_root,
    ]


def run_chapter(
    *,
    chapter: int,
    python: Path,
    render_script: Path,
    workspace_root: str,
    logger: MonitorLogger,
    retry_on_failure: int,
) -> int:
    cmd = build_render_command(python, render_script, chapter, workspace_root)
    attempts = 1 + max(retry_on_failure, 0)

    for attempt in range(1, attempts + 1):
        if _stop_requested:
            logger.log(f"chapter {chapter:03d} cancelled before start (stop requested)")
            return 130

        attempt_label = f"attempt {attempt}/{attempts}" if attempts > 1 else "attempt 1/1"
        logger.log(f"chapter {chapter:03d} started ({attempt_label})")
        logger.write(f"  command: {' '.join(cmd)}")

        started = time.monotonic()
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
        )
        elapsed = time.monotonic() - started

        if result.stdout:
            logger.write("  stdout:")
            for line in result.stdout.rstrip().splitlines():
                logger.write(f"    {line}")

        if result.stderr:
            logger.write("  stderr:")
            for line in result.stderr.rstrip().splitlines():
                logger.write(f"    {line}")

        logger.log(
            f"chapter {chapter:03d} finished in {_format_duration(elapsed)} "
            f"(exit code {result.returncode})"
        )

        if result.returncode == 0:
            return 0

        if attempt < attempts:
            logger.log(
                f"chapter {chapter:03d} failed with exit code {result.returncode}; retrying once"
            )
            continue

        logger.log(
            f"chapter {chapter:03d} failed after {attempts} attempt(s); stopping monitor"
        )
        return result.returncode

    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sequentially render audiobook chapters one at a time using render_book_chapters.py."
        )
    )
    parser.add_argument("--start", type=int, default=30, help="First chapter to render (default: 30).")
    parser.add_argument(
        "--end",
        type=int,
        default=DEFAULT_END,
        help=f"Last chapter to render inclusive (default: {DEFAULT_END}).",
    )
    parser.add_argument(
        "--workspace-root",
        default="workspace",
        help="Workspace root passed to render_book_chapters.py (default: workspace).",
    )
    parser.add_argument(
        "--python",
        type=Path,
        default=DEFAULT_PYTHON,
        help="Python executable for rendering (default: .conda-env/python.exe).",
    )
    parser.add_argument(
        "--render-script",
        type=Path,
        default=DEFAULT_RENDER_SCRIPT,
        help="Path to render_book_chapters.py.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=DEFAULT_LOG,
        help="Progress log file (default: logs/monitor_book_chapters.log).",
    )
    parser.add_argument(
        "--retry-on-failure",
        type=int,
        default=1,
        help="Number of retries after a failed chapter before stopping (default: 1).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.start < 1:
        print("error: --start must be >= 1", file=sys.stderr)
        return 2
    if args.end < args.start:
        print("error: --end must be >= --start", file=sys.stderr)
        return 2
    if not args.python.is_file():
        print(f"error: python executable not found: {args.python}", file=sys.stderr)
        return 2
    if not args.render_script.is_file():
        print(f"error: render script not found: {args.render_script}", file=sys.stderr)
        return 2

    signal.signal(signal.SIGINT, _handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_stop)

    logger = MonitorLogger(args.log_file)
    monitor_started = _utc_now()
    monitor_started_mono = time.monotonic()
    logger.log(
        "monitor started "
        f"(chapters {args.start:03d}-{args.end:03d}, workspace-root={args.workspace_root})"
    )
    logger.log(
        "skip note: render_book_chapters.py skips chapters whose "
        "000_<chapter>_raw.wav already exists unless --force is used"
    )

    exit_code = 0
    chapters_started = 0
    chapters_succeeded = 0

    try:
        for chapter in range(args.start, args.end + 1):
            if _stop_requested:
                logger.log("stop requested; exiting before next chapter")
                exit_code = 130
                break

            chapters_started += 1
            chapter_exit = run_chapter(
                chapter=chapter,
                python=args.python,
                render_script=args.render_script,
                workspace_root=args.workspace_root,
                logger=logger,
                retry_on_failure=args.retry_on_failure,
            )

            if chapter_exit == 0:
                chapters_succeeded += 1
                continue

            exit_code = chapter_exit
            break
    finally:
        total_elapsed = time.monotonic() - monitor_started_mono
    logger.log(
        "monitor stopped "
        f"(started={chapters_started}, succeeded={chapters_succeeded}, "
        f"total runtime {_format_duration(total_elapsed)}, exit code {exit_code})"
    )
    logger.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
