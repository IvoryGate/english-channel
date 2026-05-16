from __future__ import annotations

import json
import os
from redis import Redis
from rq import Worker, Queue, Connection
from worker.runner import VoxRunner, TtsRequest

QUEUE_NAME = "voxcpm-tts"


def handle_job(payload: dict) -> dict:
    runner = VoxRunner(output_dir=os.getenv("ARTIFACT_DIR", "artifacts"))
    request = TtsRequest(
        job_id=payload["jobId"],
        chapter_id=payload["chapterId"],
        text=payload["text"],
        voice_profile=payload.get("voiceProfile", "default-narrator"),
    )
    return runner.generate_chapter(request)


def start_worker() -> None:
    redis = Redis(host=os.getenv("REDIS_HOST", "127.0.0.1"), port=int(os.getenv("REDIS_PORT", "6379")))
    with Connection(redis):
        queue = Queue(name=QUEUE_NAME)
        worker = Worker([queue])
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    sample = os.getenv("SAMPLE_PAYLOAD")
    if sample:
        print(json.dumps(handle_job(json.loads(sample)), indent=2))
    else:
        start_worker()
