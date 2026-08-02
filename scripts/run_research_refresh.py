"""Safe real-investigation runner: refresh the YouTube research corpus, then re-analyze.

This is the ONLY step in the topic-selection flow that scrapes. It wraps the existing
rate-limited research scripts with hard anti-ban guardrails:

HARD RULES (non-negotiable — slow is fine, bans are not):
  1. Smoke canary first. `collect --smoke` (1 video/channel, candidate-limit 6) must pass
     before any real collection. If the canary hits a rate limit → ABORT, write a
     60-minute cooldown marker, exit non-zero.
  2. One channel at a time. Never `--all-channels` in parallel; serial with a long pause
     between channels.
  3. Conservative caps: candidate-limit 40, sleep 5-10s, channel pause 30s+ (script defaults).
  4. 60-minute cooldown. On ANY rate-limit signal (exit code 2 or "RATE_LIMIT" in output),
     stop immediately, write `rate_limit_until=<now+60min>`, and refuse further runs
     until the cooldown expires.
  5. No discovery+collect in the same run. Discovery enrich is opt-in (`--discover`),
     capped at --max-enrich 20, and runs on its own with no collect after it.
  6. Offline analysis (score/analyze/report) runs after a successful collect — no scraping.

Usage:
    python scripts/run_research_refresh.py --channel jandmaypodcast          # one channel (recommended)
    python scripts/run_research_refresh.py --smoke-only                        # canary, no real collect
    python scripts/run_research_refresh.py --skip-scrape                       # offline re-analyze only
    python scripts/run_research_refresh.py --discover --max-enrich 20           # opt-in discovery enrich
    python scripts/run_research_refresh.py --all-channels --pause-seconds 120  # serial all (slow)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PY = REPO / ".conda-env" / "python.exe"
if not PY.is_file():
    PY = Path(sys.executable)

RESEARCH_SCRIPTS = REPO / ".cursor" / "skills" / "youtube-podcast-research" / "scripts"
ANALYSIS_SCRIPTS = REPO / ".cursor" / "skills" / "youtube-corpus-analysis" / "scripts"
CORPUS_ROOT = REPO / "workspace" / "dialogue_podcast_research" / "youtube_corpus"
COOLDOWN_FILE = CORPUS_ROOT / "rate_limit_until.json"
MANIFEST_DIR = CORPUS_ROOT / "refresh_runs"

RATE_LIMIT_MARKERS = ("RATE_LIMIT", "rate limit", "HTTP Error 429", "too many requests", "try again later")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def log(msg: str) -> None:
    print(f"[{utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}] {msg}", flush=True)


def read_cooldown() -> datetime | None:
    if not COOLDOWN_FILE.is_file():
        return None
    try:
        data = json.loads(COOLDOWN_FILE.read_text(encoding="utf-8"))
        return datetime.fromisoformat(data.get("until_iso", ""))
    except Exception:
        return None


def write_cooldown(minutes: int, reason: str) -> None:
    until = utc_now() + timedelta(minutes=minutes)
    COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
    COOLDOWN_FILE.write_text(json.dumps({
        "until_iso": until.isoformat(),
        "reason": reason,
        "written_at": utc_now().isoformat(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    log(f"COOLDOWN: wrote {minutes}-min cooldown until {until.isoformat()}")


def is_rate_limit(output: str, code: int) -> bool:
    if code == 2:
        return True
    return any(marker in output for marker in RATE_LIMIT_MARKERS)


def run(cmd: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 3600) -> tuple[int, str]:
    log("  $ " + " ".join(str(c) for c in cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout)
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if output.strip():
        for line in output.strip().splitlines()[-20:]:
            print("    " + line, flush=True)
    return int(proc.returncode), output


def env_for() -> dict[str, str]:
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    return env


def collect(channel: str | None, *, smoke: bool, refresh: bool, env: dict[str, str]) -> int:
    cmd = [str(PY), "-u", str(RESEARCH_SCRIPTS / "collect_youtube_corpus.py")]
    if channel:
        cmd += ["--channel", channel]
    if smoke:
        cmd.append("--smoke")
    else:
        cmd += ["--candidate-limit", "40", "--top-n", "20", "--language", "en"]
        if refresh:
            cmd.append("--refresh")
    code, output = run(cmd, cwd=REPO, env=env)
    if is_rate_limit(output, code):
        write_cooldown(60, "collect hit rate limit")
        log("ABORT: rate limit during collect — 60-min cooldown written. Do not retry before it expires.")
        return 2
    return code


def discover(env: dict[str, str], max_enrich: int) -> int:
    cmd = [str(PY), "-u", str(RESEARCH_SCRIPTS / "discover_youtube_podcasts.py"),
           "--enrich", "--dual-host-only", "--max-enrich", str(max_enrich), "--enrich-pause", "8"]
    code, output = run(cmd, cwd=REPO, env=env)
    if is_rate_limit(output, code):
        write_cooldown(60, "discover hit rate limit")
        log("ABORT: rate limit during discover — 60-min cooldown written.")
        return 2
    return code


def offline_analyze(env: dict[str, str]) -> None:
    """Re-run the offline analysis chain (no scraping)."""
    for script, label in [
        (RESEARCH_SCRIPTS / "select_top_videos.py", "select_top_videos"),
        (RESEARCH_SCRIPTS / "score_trending_videos.py", "score_trending"),
        (ANALYSIS_SCRIPTS / "analyze_youtube_corpus.py", "analyze_corpus"),
        (ANALYSIS_SCRIPTS / "generate_research_report.py", "research_report"),
    ]:
        if not script.is_file():
            continue
        log(f"offline: {label}")
        code, _ = run([str(PY), "-u", str(script)], cwd=REPO, env=env)
        if code != 0:
            log(f"  warn: {label} exit {code} (continuing)")


def write_manifest(stages: list[dict[str, Any]], status: str) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    path = MANIFEST_DIR / f"research_refresh_{ts}.json"
    path.write_text(json.dumps({
        "schema": "elr-research-refresh-v1",
        "runAt": utc_now().isoformat(),
        "status": status,
        "stages": stages,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    log(f"manifest={path.as_posix()}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe real-investigation runner for ELR YouTube research (anti-ban).")
    parser.add_argument("--channel", help="Single channel slug to collect (recommended).")
    parser.add_argument("--all-channels", action="store_true", help="Serial all channels (slow, long pauses).")
    parser.add_argument("--smoke-only", action="store_true", help="Run only the smoke canary; no real collection.")
    parser.add_argument("--skip-scrape", action="store_true", help="Offline re-analyze only (no scraping).")
    parser.add_argument("--discover", action="store_true", help="Opt-in discovery enrich (capped, separate from collect).")
    parser.add_argument("--max-enrich", type=int, default=20, help="Discovery enrich cap (default 20).")
    parser.add_argument("--pause-seconds", type=int, default=120, help="Pause between channels for --all-channels (default 120s).")
    args = parser.parse_args()

    # 0. cooldown check
    cooldown = read_cooldown()
    if cooldown and cooldown > utc_now():
        log(f"REFUSE: rate-limit cooldown active until {cooldown.isoformat()}. Wait before retrying.")
        return 3
    if cooldown and cooldown <= utc_now():
        log(f"cooldown expired ({cooldown.isoformat()}) — proceeding.")

    env = env_for()
    stages: list[dict[str, Any]] = []
    status = "ok"

    if args.skip_scrape:
        offline_analyze(env)
        stages.append({"stage": "offline_analyze", "exit": 0})
        write_manifest(stages, status)
        return 0

    # 1. smoke canary (mandatory before any real scrape)
    # The canary tests ONE channel only (1 video, candidate-limit 6) so it stays
    # fast even as DEFAULT_CHANNELS grows. Without --channel, collect_youtube_corpus
    # iterates ALL channels, which made the canary take 10+ min after the 3->10
    # channel expansion.
    sys.path.insert(0, str(REPO / "apps" / "worker-py"))
    DEFAULT_CHANNELS: tuple[dict[str, str], ...] = ()
    try:
        from worker.youtube_podcast_research.workspace import DEFAULT_CHANNELS  # noqa: E402
        smoke_channel = DEFAULT_CHANNELS[0]["slug"]
    except Exception:
        smoke_channel = None
    log(f"STAGE 1: smoke canary (channel={smoke_channel}, 1 video, candidate-limit 6)")
    code = collect(smoke_channel, smoke=True, refresh=False, env=env)
    stages.append({"stage": "smoke", "exit": code})
    if code != 0:
        write_manifest(stages, "aborted_smoke")
        return code
    log("smoke OK — proceeding to real collection.")

    if args.smoke_only:
        write_manifest(stages, "smoke_only_ok")
        return 0

    # 2. real collection (one channel at a time)
    if args.discover:
        log("STAGE 2a: discovery enrich (opt-in, capped)")
        code = discover(env, args.max_enrich)
        stages.append({"stage": "discover", "exit": code})
        if code != 0:
            write_manifest(stages, "aborted_discover")
            return code
        # discovery does not chain into collect in the same run
        offline_analyze(env)
        stages.append({"stage": "offline_analyze", "exit": 0})
        write_manifest(stages, status)
        return 0

    if args.all_channels:
        if not DEFAULT_CHANNELS:
            log("could not import DEFAULT_CHANNELS; pass --channel instead")
            return 2
        for i, ch in enumerate(DEFAULT_CHANNELS):
            if i > 0:
                log(f"inter-channel pause {args.pause_seconds}s (anti-ban)")
                time.sleep(args.pause_seconds)
            log(f"STAGE 2: collect channel {ch['slug']} ({i+1}/{len(DEFAULT_CHANNELS)})")
            code = collect(ch["slug"], smoke=False, refresh=True, env=env)
            stages.append({"stage": "collect", "channel": ch["slug"], "exit": code})
            if code != 0:
                write_manifest(stages, "aborted_collect")
                return code
    elif args.channel:
        log(f"STAGE 2: collect channel {args.channel}")
        code = collect(args.channel, smoke=False, refresh=True, env=env)
        stages.append({"stage": "collect", "channel": args.channel, "exit": code})
        if code != 0:
            write_manifest(stages, "aborted_collect")
            return code
    else:
        log("no --channel/--all-channels specified after smoke; stopping (offline analyze only).")
        offline_analyze(env)
        stages.append({"stage": "offline_analyze", "exit": 0})
        write_manifest(stages, status)
        return 0

    # 3. offline analysis
    log("STAGE 3: offline analysis (no scraping)")
    offline_analyze(env)
    stages.append({"stage": "offline_analyze", "exit": 0})
    write_manifest(stages, status)
    log("research refresh complete — run refresh_topic_backlog.py --all to feed the backlog.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
