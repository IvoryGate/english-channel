from __future__ import annotations

import json
import os
from worker.runner import VoxRunner, TtsRequest

def handle_job(payload: dict) -> dict:
    runner = VoxRunner(output_dir=os.getenv("ARTIFACT_DIR", "artifacts"))
    request = TtsRequest(
        job_id=payload["jobId"],
        chapter_id=payload["chapterId"],
        text=payload["text"],
        voice_profile=payload.get("voiceProfile", "default-narrator"),
    )
    return runner.generate_chapter(request)
if __name__ == "__main__":
    sample = os.getenv("SAMPLE_PAYLOAD")
    if sample:
        print(json.dumps(handle_job(json.loads(sample)), indent=2))
    else:
        raise SystemExit(
            "The API-owned BullMQ worker launches this module with SAMPLE_PAYLOAD; "
            "run the API service instead of starting a separate Python queue worker."
        )
