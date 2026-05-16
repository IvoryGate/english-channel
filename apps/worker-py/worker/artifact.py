from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import soundfile as sf


def write_chapter_artifact(
    output_dir: str,
    job_id: str,
    chapter_id: str,
    sample_rate: int,
    chunks: list[np.ndarray],
    trace: dict,
) -> tuple[str, str]:
    base = Path(output_dir) / chapter_id / job_id
    base.mkdir(parents=True, exist_ok=True)

    audio_path = base / "chapter.wav"
    meta_path = base / "trace.json"
    merged = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
    sf.write(audio_path.as_posix(), merged, sample_rate)
    with meta_path.open("w", encoding="utf-8") as fp:
        json.dump(trace, fp, indent=2)
    return audio_path.as_posix(), meta_path.as_posix()
