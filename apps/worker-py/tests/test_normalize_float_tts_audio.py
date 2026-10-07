import importlib.util
import json
from pathlib import Path

import numpy as np
import soundfile as sf


SCRIPT = Path(__file__).parents[3] / "scripts" / "normalize_float_tts_audio.py"
SPEC = importlib.util.spec_from_file_location("normalize_float_tts_audio", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_segment(directory: Path, stem: str, peak: float) -> Path:
    path = directory / f"{stem}.wav"
    sf.write(path, np.array([0.0, peak, -peak], dtype=np.float32), 48_000, subtype="FLOAT")
    path.with_name(f"{stem}.trace.json").write_text("{}\n", encoding="utf-8")
    return path


def test_normalize_directory_repairs_quiet_and_clipping_segments(tmp_path: Path) -> None:
    quiet = _write_segment(tmp_path, "quiet", 0.2)
    loud = _write_segment(tmp_path, "loud", 0.98)
    unchanged = _write_segment(tmp_path, "unchanged", 0.6)

    changed = MODULE.normalize_directory(tmp_path, 0.89, boost_below=0.3)

    assert changed == 2
    for path, reason in ((quiet, "too_quiet"), (loud, "clipping_guard")):
        audio, _ = sf.read(path, dtype="float32")
        assert float(np.max(np.abs(audio))) == np.float32(0.89)
        trace = json.loads(path.with_name(f"{path.stem}.trace.json").read_text(encoding="utf-8"))
        assert trace["postProcessing"]["reason"] == reason
        assert trace["outputSha256"] == MODULE.sha256_file(path)

    audio, _ = sf.read(unchanged, dtype="float32")
    assert float(np.max(np.abs(audio))) == np.float32(0.6)
