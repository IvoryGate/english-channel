from pathlib import Path
import numpy as np
from worker.artifact import write_chapter_artifact


def test_write_chapter_artifact(tmp_path: Path) -> None:
    trace = {"jobId": "j1", "chapterId": "c1"}
    audio, meta = write_chapter_artifact(
        output_dir=tmp_path.as_posix(),
        job_id="j1",
        chapter_id="c1",
        sample_rate=24000,
        chunks=[np.zeros(240, dtype=np.float32)],
        trace=trace,
    )
    assert Path(audio).exists()
    assert Path(meta).exists()
