from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import soundfile as sf

from .audio_metrics import audio_texture_metrics
from .audio_render import _atomic_write_wav, _default_model_factory, _mono_float, _resample
from .io import atomic_write_json, sha256_file
from .schema import load_json_object, parse_audio_acceptance_policy


AUDITION_SCHEMA = "classic-listening-narrator-audition-v1"


class NarratorAuditionError(RuntimeError):
    pass


ModelFactory = Callable[[str, str], Any]


def _runtime_path(root: Path, value: str, field: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise NarratorAuditionError(f"{field} must be project-relative")
    return root / relative


def _tracked_path(config_path: Path, value: str, field: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise NarratorAuditionError(f"{field} must be project-relative")
    if relative.parts and relative.parts[0] == "configs":
        for ancestor in config_path.resolve().parents:
            if (ancestor / "configs").is_dir():
                return ancestor / relative
        raise NarratorAuditionError(f"Cannot resolve tracked config path: {value}")
    return config_path.resolve().parent / relative


def load_audition_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != AUDITION_SCHEMA:
        raise NarratorAuditionError("Unsupported narrator audition config")
    required_strings = (
        "auditionId", "bookSlug", "casesRef", "outputRoot", "modelId", "device"
    )
    for key in required_strings:
        if not isinstance(payload.get(key), str) or not str(payload[key]).strip():
            raise NarratorAuditionError(f"{key} must be a non-empty string")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        raise NarratorAuditionError("The current narrator audition requires exactly three candidates")
    ids: set[str] = set()
    blind_codes: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise NarratorAuditionError("Each narrator candidate must be an object")
        for key in (
            "id", "blindCode", "sourceProfileId", "referencePath", "referenceSha256",
            "promptText", "provenanceStatus",
        ):
            if not isinstance(candidate.get(key), str) or not str(candidate[key]).strip():
                raise NarratorAuditionError(f"candidate.{key} must be a non-empty string")
        if len(str(candidate["referenceSha256"])) != 64:
            raise NarratorAuditionError("candidate.referenceSha256 must be a SHA-256 digest")
        if candidate["id"] in ids or candidate["blindCode"] in blind_codes:
            raise NarratorAuditionError("Candidate ids and blind codes must be unique")
        ids.add(str(candidate["id"]))
        blind_codes.add(str(candidate["blindCode"]))
        for key in ("cfgValue", "inferenceTimesteps"):
            if not isinstance(candidate.get(key), (int, float)) or isinstance(candidate.get(key), bool):
                raise NarratorAuditionError(f"candidate.{key} must be numeric")
            if float(candidate[key]) <= 0:
                raise NarratorAuditionError(f"candidate.{key} must be positive")
        for key in ("normalize", "denoise"):
            if not isinstance(candidate.get(key), bool):
                raise NarratorAuditionError(f"candidate.{key} must be boolean")
    sample_rate = payload.get("sampleRate")
    if not isinstance(sample_rate, int) or isinstance(sample_rate, bool) or sample_rate < 16000:
        raise NarratorAuditionError("sampleRate must be an integer of at least 16000")
    silence = payload.get("silenceBetweenCasesSec")
    if not isinstance(silence, (int, float)) or isinstance(silence, bool) or silence < 0:
        raise NarratorAuditionError("silenceBetweenCasesSec must be non-negative")
    return payload


def run_narrator_audition(
    runtime_root: Path,
    config_path: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    model_factory: ModelFactory = _default_model_factory,
) -> dict[str, Any]:
    root = runtime_root.resolve()
    config = load_audition_config(config_path)
    cases_path = _tracked_path(config_path, str(config["casesRef"]), "casesRef")
    acceptance = parse_audio_acceptance_policy(load_json_object(cases_path))
    output_root = _runtime_path(root, str(config["outputRoot"]), "outputRoot")
    model_path = _runtime_path(root, str(config["modelId"]), "modelId")
    references: list[tuple[dict[str, Any], Path]] = []
    for candidate in config["candidates"]:
        reference = _runtime_path(root, str(candidate["referencePath"]), "referencePath")
        if not reference.is_file():
            raise NarratorAuditionError(f"Narrator reference does not exist: {reference}")
        actual_hash = sha256_file(reference)
        if actual_hash != str(candidate["referenceSha256"]).lower():
            raise NarratorAuditionError(f"Narrator reference hash mismatch: {candidate['id']}")
        references.append((candidate, reference))

    preflight = {
        "schema": "classic-listening-narrator-audition-preflight-v1",
        "auditionId": config["auditionId"],
        "bookSlug": config["bookSlug"],
        "candidateCount": len(references),
        "caseCount": len(acceptance.cases),
        "candidateBlindCodes": [candidate["blindCode"] for candidate, _ in references],
        "outputRoot": str(output_root),
        "dryRun": dry_run,
    }
    if dry_run:
        return preflight

    model = model_factory(str(model_path), str(config["device"]))
    model_rate = int(model.tts_model.sample_rate)
    target_rate = int(config["sampleRate"])
    silence = np.zeros(round(target_rate * float(config["silenceBetweenCasesSec"])), dtype=np.float32)
    candidate_reports: list[dict[str, Any]] = []
    mapping: dict[str, str] = {}
    for candidate, reference in references:
        blind_code = str(candidate["blindCode"])
        mapping[blind_code] = str(candidate["id"])
        case_reports: list[dict[str, Any]] = []
        combined: list[np.ndarray] = []
        for index, case in enumerate(acceptance.cases):
            output = output_root / "blind" / blind_code / f"{case.case_id}.wav"
            reused = output.is_file() and not force
            if reused:
                audio, rate = sf.read(output, dtype="float32")
                audio = _mono_float(audio)
                if int(rate) != target_rate:
                    raise NarratorAuditionError(f"Existing audition audio has wrong sample rate: {output}")
            else:
                generated = model.generate(
                    text=case.text,
                    prompt_wav_path=str(reference),
                    prompt_text=str(candidate["promptText"]),
                    reference_wav_path=str(reference),
                    cfg_value=float(candidate["cfgValue"]),
                    inference_timesteps=int(candidate["inferenceTimesteps"]),
                    normalize=bool(candidate["normalize"]),
                    denoise=bool(candidate["denoise"]),
                )
                audio = _resample(_mono_float(generated), model_rate, target_rate)
                _atomic_write_wav(output, audio, target_rate)
            case_reports.append(
                {
                    "caseId": case.case_id,
                    "dimension": case.dimension,
                    "text": case.text,
                    "path": output.relative_to(root).as_posix(),
                    "sha256": sha256_file(output),
                    "reused": reused,
                    "textureMetrics": audio_texture_metrics(output),
                }
            )
            combined.append(audio)
            if index < len(acceptance.cases) - 1:
                combined.append(silence)
        review_audio = output_root / "review" / f"{blind_code}.wav"
        _atomic_write_wav(review_audio, np.concatenate(combined), target_rate)
        candidate_reports.append(
            {
                "blindCode": blind_code,
                "reviewAudio": review_audio.relative_to(root).as_posix(),
                "reviewAudioSha256": sha256_file(review_audio),
                "cases": case_reports,
            }
        )

    report = {
        "schema": "classic-listening-narrator-audition-report-v1",
        "auditionId": config["auditionId"],
        "bookSlug": config["bookSlug"],
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "modelPath": str(model_path),
        "modelSampleRate": model_rate,
        "outputSampleRate": target_rate,
        "blindReviewRequired": True,
        "status": "awaiting_blind_review",
        "candidates": candidate_reports,
    }
    atomic_write_json(output_root / "review-sheet.json", report)
    atomic_write_json(
        output_root / "private-mapping.json",
        {
            "schema": "classic-listening-narrator-audition-mapping-v1",
            "auditionId": config["auditionId"],
            "mapping": mapping,
            "candidates": [
                {
                    "id": candidate["id"],
                    "blindCode": candidate["blindCode"],
                    "sourceProfileId": candidate["sourceProfileId"],
                    "referencePath": candidate["referencePath"],
                    "referenceSha256": candidate["referenceSha256"],
                    "provenanceStatus": candidate["provenanceStatus"],
                    "cfgValue": candidate["cfgValue"],
                    "inferenceTimesteps": candidate["inferenceTimesteps"],
                }
                for candidate, _ in references
            ],
        },
    )
    report["reviewSheet"] = str(output_root / "review-sheet.json")
    report["privateMapping"] = str(output_root / "private-mapping.json")
    return report
