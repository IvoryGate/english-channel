"""Print episode production progress — for agent/human self-check.

  python scripts/check_episode_production_status.py --episode episode_003
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SERIES = ["series_a", "series_b", "series_c"]
LOCK = REPO / "logs" / "gpu_production.lock"
TOOLS = REPO / "workspace" / "shows" / "tools"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def pid_alive(pid: int) -> bool:
    sys.path.insert(0, str(REPO / "scripts"))
    from gpu_production_lock import pid_alive as _alive  # noqa: E402

    return _alive(pid)


def tail_lines(path: Path, n: int = 6) -> list[str]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-n:]


def find_production_pids(episode: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    if sys.platform != "win32":
        return out
    try:
        import subprocess

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO),
        )
        if result.returncode != 0 or not result.stdout.strip():
            return out
        raw = json.loads(result.stdout)
        rows = raw if isinstance(raw, list) else [raw]
        needle = episode.replace("_", "")
        for row in rows:
            cmd = str(row.get("CommandLine") or "")
            pid = int(row.get("ProcessId") or 0)
            if pid <= 0:
                continue
            if "english-channel" not in cmd.lower() and str(REPO).lower() not in cmd.lower():
                continue
            if episode in cmd or any(k in cmd for k in ("monitor_episode", "render_episode", "pack_episode", "resume_episode")):
                if episode in cmd or "monitor_episode" in cmd or "render_episode" in cmd:
                    out.append((pid, cmd[:200]))
    except Exception:
        pass
    return out


def qc_summary(series: str, episode: str) -> dict[str, object]:
    """Read reports/000_<episode>.qc.json if present."""
    qc_path = REPO / "workspace" / "shows" / series / episode / "reports" / f"000_{episode}.qc.json"
    if not qc_path.is_file():
        return {"qc": "missing", "review_count": 0, "blocking": False, "review_ids": []}

    report = json.loads(qc_path.read_text(encoding="utf-8"))
    chapter = report.get("chapter") or {}
    review_count = int(chapter.get("reviewCount") or 0)
    review_ids = [str(row["id"]) for row in report.get("segments") or [] if row.get("status") == "review"]

    sys.path.insert(0, str(TOOLS))
    from check_episode import has_blocking_qc_issues  # noqa: E402

    blocking = has_blocking_qc_issues(report)
    if blocking:
        qc_label = "FAIL"
    elif review_count > 0:
        qc_label = "pass (advisory)"
    else:
        qc_label = "pass"
    return {
        "qc": qc_label,
        "review_count": review_count,
        "blocking": blocking,
        "review_ids": review_ids,
        "flags": list(chapter.get("flags") or []),
    }


def series_status(episode: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for series in SERIES:
        ws = REPO / "workspace" / "shows" / series / episode
        manifest = ws / f"000_{episode}.episode_manifest.json"
        expected = 0
        if manifest.is_file():
            expected = len(json.loads(manifest.read_text(encoding="utf-8")).get("turns") or [])
        turns_dir = ws / "audio" / "turns"
        done = len(list(turns_dir.glob("*.wav"))) if turns_dir.is_dir() else 0
        mp4 = (ws / "video" / f"000_{episode}.mp4").is_file()
        pct = round(100 * done / expected, 1) if expected else 0.0
        if mp4:
            phase = "DONE"
        elif done >= expected and expected > 0:
            phase = "PACK"
        elif done > 0:
            phase = "RENDER"
        else:
            phase = "PENDING"
        rows.append(
            {
                "series": series,
                "turns": f"{done}/{expected}",
                "pct": pct,
                "mp4": mp4,
                "phase": phase,
                **qc_summary(series, episode),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Episode production status self-check.")
    parser.add_argument("--episode", default="episode_003")
    parser.add_argument("--log-glob", default="", help="Optional render log path to tail.")
    args = parser.parse_args()

    print(f"[{utc_now()}] episode production status — {args.episode}")
    print()

    for row in series_status(args.episode):
        mp4 = "yes" if row["mp4"] else "no"
        qc = str(row.get("qc", "missing"))
        review = int(row.get("review_count") or 0)
        qc_detail = f" qc={qc}"
        if review:
            ids = row.get("review_ids") or []
            preview = ",".join(ids[:5])
            if len(ids) > 5:
                preview += ",..."
            qc_detail += f" review={review} [{preview}]"
        print(
            f"  {row['series']:10} {row['phase']:7} turns={row['turns']:8} "
            f"({row['pct']:5.1f}%) mp4={mp4}{qc_detail}"
        )

    print()
    if LOCK.is_file():
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        pid = int(lock.get("pid") or -1)
        alive = pid_alive(pid)
        print(f"  gpu_lock: pid={pid} label={lock.get('label')} alive={alive}")
    else:
        print("  gpu_lock: (none — legacy run or idle)")

    procs = find_production_pids(args.episode)
    print()
    if procs:
        print(f"  processes ({len(procs)}):")
        for pid, cmd in procs:
            print(f"    pid={pid} {cmd}")
    else:
        print("  processes: none matching episode production")

    log_path = Path(args.log_glob) if args.log_glob else None
    if log_path is None:
        candidates = sorted((REPO / "logs").glob(f"*{args.episode}*.render.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        log_path = candidates[0] if candidates else None

    if log_path and log_path.is_file():
        print()
        print(f"  render log tail ({log_path.name}):")
        for line in tail_lines(log_path):
            print(f"    {line}")

    # Exit: 0=in progress or done, 1=all pending no procs, 2=stale lock
    rows = series_status(args.episode)
    all_done = all(r["mp4"] for r in rows)
    any_active = any(r["phase"] in ("RENDER", "PACK") for r in rows) or bool(procs)
    if all_done:
        return 0
    if any_active and procs:
        return 0
    if any_active and not procs:
        print()
        print("  WARNING: work incomplete but no production process found — may need resume.")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
