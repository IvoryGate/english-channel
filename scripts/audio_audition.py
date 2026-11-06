from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/worker-py"))
from worker.tts.audition import prepare, render  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or render a bounded offline blind audio trial.")
    parser.add_argument("--plan", type=Path, default=ROOT / "configs/quality/audio-audition-v1.json")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--voice-evidence", type=Path, default=ROOT / "docs/exec-plans/completed/2026-09-09-tts-provider-migration.md")
    parser.add_argument("--render", action="store_true", help="Generate at most the two first-round arms and prepare blind review.")
    parser.add_argument("--previous-run-id", help="Retain and charge the first CUDA-OOM trial when using staged offload.")
    args = parser.parse_args()
    plan, state, destination = prepare(ROOT, args.plan, args.run_id, args.voice_evidence, args.previous_run_id)
    if args.render:
        state = render(ROOT, plan, state, destination)
    print(json.dumps({"status": state["status"], "runPath": str(destination), "completedUtterances": state["completedUtterances"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
