"""Bounded, offline two-arm audition using the existing provider and trace path."""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from . import audition_audio
from .dialogue import dialogue_turn_spec
from .process import run_provider_batch
from .schema import resolve_provider_config
from .trace import TRACE_SCHEMA, atomic_write_json, canonical_hash, sha256_file, trace_is_reusable, turn_trace_path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def round_one(plan: dict) -> list[dict]:
    if plan.get("schema") != "elr-audio-audition-plan-v1":
        raise ValueError("Unknown audition schema")
    if plan["contract"]["newPaidSpend"] != 0 or plan["contract"]["downloadsAllowed"]:
        raise ValueError("Audition must be offline with zero new spend")
    arms = [next(row for row in plan["candidates"] if row["id"] == key) for key in plan["budget"]["round1Arms"]]
    if len(arms) != 2 or any(row["ttsProvider"] != "chatterbox_500m" for row in arms):
        raise ValueError("This runner implements the two Chatterbox round-one arms only")
    variable = arms[1]["changedSetting"]
    changed = {key for key in set(arms[0]["providerSettings"]) | set(arms[1]["providerSettings"])
               if arms[0]["providerSettings"].get(key) != arms[1]["providerSettings"].get(key)}
    if changed != {variable}:
        raise ValueError("The paired arms must differ in exactly the declared setting")
    for key in ("ttsProvider", "modelRevision", "device", "runtimeMode"):
        if arms[0].get(key, "default") != arms[1].get(key, "default"):
            raise ValueError("Paired provider identities must match")
    count = sum(len(row["utterances"]) for row in plan["snippets"])
    if count * 2 > plan["budget"]["maximumInitialUtteranceGenerations"]:
        raise ValueError("Corpus exceeds initial generation budget")
    if plan["budget"]["chatterboxTurnsPerProcess"] != 2 or plan["budget"]["maximumConcurrentGpuJobs"] != 1:
        raise ValueError("Audition requires two-turn serial batches")
    return arms


def model_hashes(path: Path, revision: str) -> dict[str, str]:
    source = read_json(path / "source.json")
    if source["sha"] != revision:
        raise ValueError("Local model source revision differs from plan")
    files = {row["rfilename"]: row for row in source["siblings"]}
    result = {}
    for name in ("conds.pt", "ve.safetensors", "t3_cfg.safetensors", "s3gen.safetensors", "tokenizer.json"):
        file = path / name
        row = files[name]
        digest = sha256_file(file)
        if row.get("lfs"):
            if digest != row["lfs"]["sha256"]:
                raise ValueError(f"Model fingerprint mismatch: {name}")
        else:
            content = file.read_bytes()
            blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
            if blob != row["blobId"]:
                raise ValueError(f"Model Git blob mismatch: {name}")
        result[name] = digest
    return result


def recovery_evidence(root: Path, plan: dict, previous_run_id: str | None) -> dict:
    """One named repair consumes the existing two-attempt allowance, not a fresh budget."""
    if previous_run_id is None:
        return {}
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", previous_run_id):
        raise ValueError("Invalid previous run ID")
    path = root / "workspace/runtime/audio-quality-reset" / previous_run_id / "run.json"
    previous = read_json(path)
    if (previous.get("status") != "incomplete" or previous.get("completedUtterances") != 0
            or previous.get("priorAttemptedUtterances", 0) != 0
            or previous.get("attemptedUtterances") != 2
            or "CUDA" not in previous.get("error", "") or "out of memory" not in previous.get("error", "")):
        raise ValueError("Only the first failed CUDA-OOM pair qualifies for this named repair")
    if previous["attemptedUtterances"] > plan["budget"]["maximumDefectRetriesTotal"]:
        raise ValueError("Named repair exceeds the cumulative retry budget")
    if any(arm.get("runtimeMode") != "staged_cpu_offload" for arm in round_one(plan)):
        raise ValueError("CUDA-OOM repair must change both arms to staged CPU offload")
    return {"previousRunId": previous_run_id, "previousRunSha256": sha256_file(path),
        "retryReason": "CUDA OOM with all model phases resident; stage unchanged FP32 weights through CPU",
        "priorAttemptedUtterances": previous["attemptedUtterances"],
        "priorElapsedSec": previous["elapsedSec"],
        "retryUtteranceId": plan["snippets"][0]["utterances"][0]["id"],
        "retrySeedOffset": plan["seedPlan"]["namedDefectRetryOffset"]}


def prepare(root: Path, plan_path: Path, run_id: str, voice_evidence: Path,
            previous_run_id: str | None = None) -> tuple[dict, dict, Path]:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", run_id):
        raise ValueError("Run ID must contain only letters, digits, underscores or hyphens")
    plan = read_json(plan_path)
    arms = round_one(plan)
    if previous_run_id == run_id:
        raise ValueError("Repair requires a new run ID")
    recovery = recovery_evidence(root, plan, previous_run_id)
    destination = root / "workspace/runtime/audio-quality-reset" / run_id
    registry = read_json(root / plan["voicePlan"]["registryPath"])
    hosts = {}
    for alias, speaker in plan["voicePlan"]["chatterbox_500m"].items():
        profile = registry["profiles"][speaker]
        reference = root / profile["referenceAudioClean"]
        hosts[alias] = {"speakerIdentity": speaker, "referenceText": profile["referenceText"],
            "voice": {"kind": "clone", "referencePath": profile["referenceAudioClean"], "referenceSha256": sha256_file(reference)}}
    provider = resolve_provider_config(root, arms[0])
    if not provider.interpreter.is_file():
        raise ValueError("Local provider interpreter unavailable")
    frozen = {"sourcePlanSha256": sha256_file(plan_path), "voiceMapping": hosts,
        "voiceEvidence": str(voice_evidence), "voiceEvidenceSha256": sha256_file(voice_evidence),
        "verifiedModelFileHashes": model_hashes(provider.local_model_path, provider.model_revision),
        "provider": provider.to_trace(root), "recovery": recovery}
    frozen["sourceCodeHashes"] = {name: sha256_file(root / "apps/worker-py/worker/tts" / name)
        for name in ("schema.py", "trace.py", "dialogue.py", "process.py", "isolated_worker.py", "chatterbox_memory.py", "audition.py", "audition_audio.py")}
    frozen["fingerprint"] = canonical_hash(frozen)
    state_path = destination / "run.json"
    if state_path.exists():
        state = read_json(state_path)
        if state["frozen"]["fingerprint"] != frozen["fingerprint"]:
            raise ValueError("Run inputs changed; use a new run ID and retain previous artifacts")
    else:
        state = {"schema": "elr-audio-audition-run-v1", "status": "prepared", "frozen": frozen,
            "attemptedUtterances": 0, "completedUtterances": 0,
            "priorAttemptedUtterances": recovery.get("priorAttemptedUtterances", 0),
            "cumulativeAttemptedUtterances": recovery.get("priorAttemptedUtterances", 0),
            "elapsedSec": recovery.get("priorElapsedSec", 0.0),
            "reviewCompleted": False, "publicReleaseAllowed": False,
            "peakRamMiB": None, "peakVramMiB": None,
            "memoryMeasurementNote": "Peak memory is not instrumented; unavailable is not zero.",
            "codeCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}
        atomic_write_json(state_path, state)
    return plan, state, destination


def tasks(root: Path, plan: dict, state: dict, destination: Path) -> list[dict]:
    arms = round_one(plan)
    rows = []
    order = 0
    for snippet in plan["snippets"]:
        for utterance in snippet["utterances"]:
            order += 1
            for arm in arms:
                manifest = {"renderSettings": {**arm, "seedBase": plan["seedPlan"]["seedBase"]},
                            "hosts": state["frozen"]["voiceMapping"]}
                turn = {**utterance, "order": order, "deliveryCue": snippet["performanceIntent"]}
                recovery = state["frozen"].get("recovery", {})
                if utterance["id"] == recovery.get("retryUtteranceId"):
                    turn["ttsSeedOffset"] = recovery["retrySeedOffset"]
                spec = dialogue_turn_spec(root, manifest, turn)
                output = destination / "raw" / arm["id"] / f"{utterance['id']}.wav"
                rows.append({"candidateId": arm["id"], "snippetId": snippet["id"], "output": output,
                    "spec": spec, "request": {"id": arm["id"] + ":" + utterance["id"], "text": spec["normalizedText"],
                        "seed": spec["seed"], "voice": spec["workerVoice"],
                        "providerSettings": spec["effectiveSettings"], "outputPath": str(output)}})
    return rows


def verify_review(plan: dict, destination: Path) -> None:
    """A reusable raw take is not proof that the listening deliverable survives."""
    try:
        review = read_json(destination / "review.json")
        code_map = read_json(destination / "private-code-map.json")
        expected_ids = {snippet["id"] for snippet in plan["snippets"]}
        pairs = review["pairs"]
        if len(pairs) != len(expected_ids) or {row["snippetId"] for row in pairs} != expected_ids:
            raise ValueError("Blind review snippet coverage changed")
        arms = {row["id"] for row in round_one(plan)}
        for pair in pairs:
            snippet_id = pair["snippetId"]
            mapping = code_map[snippet_id]
            if set(mapping) != {"A", "B"} or set(mapping.values()) != arms:
                raise ValueError("Blind review mapping is incomplete")
            expected_files = [f"listen/{snippet_id}-{code}.wav" for code in ("A", "B")]
            if pair["files"] != expected_files or len(pair["outputSha256"]) != 2:
                raise ValueError("Blind listening paths changed")
            for name, digest in zip(expected_files, pair["outputSha256"]):
                if sha256_file(destination / name) != digest:
                    raise ValueError("Blind listening file changed")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError("Saved blind-review artifacts are missing or invalid; retain raw takes and repair review separately") from exc


def render(root: Path, plan: dict, state: dict, destination: Path) -> dict:
    state_path = destination / "run.json"
    budget = plan["budget"]
    rows = tasks(root, plan, state, destination)
    pending = [row for row in rows if not trace_is_reusable(row["output"], row["spec"]["identity"]["sha256"])]
    if not pending and state.get("status") == "awaiting_blind_review":
        verify_review(plan, destination)
        return state  # Preserve the same blind labels and any reviewer work.
    if state.get("status") == "incomplete":
        raise ValueError("Failed trial is retained; diagnose its named defect before starting another run")
    started = time.monotonic()
    elapsed_before = state["elapsedSec"]

    def save() -> None:
        state["elapsedSec"] = elapsed_before + time.monotonic() - started
        state["cumulativeAttemptedUtterances"] = state.get("priorAttemptedUtterances", 0) + state["attemptedUtterances"]
        atomic_write_json(state_path, state)

    try:
        state["status"] = "rendering"
        save()
        for index in range(0, len(pending), 2):
            batch = pending[index:index + 2]
            remaining = budget["maximumTotalWallMinutes"] * 60 - (elapsed_before + time.monotonic() - started)
            cumulative = state.get("priorAttemptedUtterances", 0) + state["attemptedUtterances"] + len(batch)
            if (remaining <= 0 or state["attemptedUtterances"] + len(batch) > budget["maximumInitialUtteranceGenerations"]
                    or cumulative > budget["maximumInitialUtteranceGenerations"] + budget["maximumDefectRetriesTotal"]):
                raise ValueError("Audition generation/time budget exhausted")
            if shutil.disk_usage(destination).free < budget["minimumFreeDiskGiB"] * 1024**3:
                raise ValueError("Audition free-disk requirement failed")
            if sum(path.stat().st_size for path in destination.rglob("*") if path.is_file()) > budget["maximumArtifactsMiB"] * 1024**2:
                raise ValueError("Audition artifact budget exhausted")
            state["attemptedUtterances"] += len(batch)
            save()  # Persist intent before spawning: crashes never grant free retries.
            result = run_provider_batch(root, batch[0]["spec"]["provider"], [row["request"] for row in batch],
                label="audio-quality-audition", timeout_sec=min(remaining, budget["batchWatchdogSeconds"]), offline=True)
            for row, actual in zip(batch, result):
                spec = row["spec"]
                if actual["id"] != row["request"]["id"] or actual["effectiveSettings"] != spec["effectiveSettings"]:
                    raise ValueError("Provider did not confirm the requested turn settings")
                if actual.get("runtimeMode", "default") != spec["provider"].runtime_mode:
                    raise ValueError("Provider did not confirm the requested runtime mode")
                atomic_write_json(turn_trace_path(row["output"]), {
                    "schema": TRACE_SCHEMA, "identitySha256": spec["identity"]["sha256"],
                    "candidateId": row["candidateId"], "snippetId": row["snippetId"],
                    "provider": {**spec["provider"].to_trace(root), "providerSettings": spec["effectiveSettings"]},
                    "voice": spec["voice"], "normalizedText": spec["normalizedText"], "seed": spec["seed"],
                    "deliveryCueStatus": "editorial_only",
                    "recovery": state["frozen"].get("recovery", {}), **actual})
                state["completedUtterances"] += 1
            save()
            print(f"audition turns={state['completedUtterances']}/{len(rows)}", flush=True)
        if elapsed_before + time.monotonic() - started >= budget["maximumTotalWallMinutes"] * 60:
            raise ValueError("Audition time budget exhausted before review assembly")
        assemble(plan, rows, destination, deadline=started + budget["maximumTotalWallMinutes"] * 60 - elapsed_before)
        if sum(path.stat().st_size for path in destination.rglob("*") if path.is_file()) > budget["maximumArtifactsMiB"] * 1024**2:
            raise ValueError("Audition artifact budget exhausted during assembly")
        state["status"] = "awaiting_blind_review"
        save()
        return state
    except BaseException as exc:
        state["status"] = "incomplete"
        state["error"] = f"{type(exc).__name__}: {exc}"
        save()
        raise


def assemble(plan: dict, rows: list[dict], destination: Path, *, deadline: float | None = None) -> None:
    settings = plan["assembly"]
    code_map = {}
    review = {"schema": "elr-audio-blind-review-v1", "status": "pending", "dimensions": plan["blindReview"]["dimensions"], "pairs": []}
    for snippet in plan["snippets"]:
        if deadline is not None and time.monotonic() >= deadline:
            raise ValueError("Audition time budget exhausted during assembly")
        arms = [arm["id"] for arm in round_one(plan)]
        secrets.SystemRandom().shuffle(arms)
        raw_paths, listen_paths = [], []
        for code, candidate in zip(("A", "B"), arms):
            raw = destination / "assembled" / f"{snippet['id']}-{candidate}.wav"
            audition_audio.concatenate([row["output"] for row in rows if row["snippetId"] == snippet["id"] and row["candidateId"] == candidate], raw, settings["round1GapSec"])
            raw_paths.append(raw)
            listen_paths.append(destination / "listen" / f"{snippet['id']}-{code}.wav")
        measurements = audition_audio.match_pair(raw_paths, listen_paths,
            target=settings["targetIntegratedLufs"], peak=settings["maximumTruePeakDbtp"],
            maximum_difference=settings["maximumPairLoudnessDifferenceLu"])
        code_map[snippet["id"]] = dict(zip(("A", "B"), arms))
        review["pairs"].append({"snippetId": snippet["id"], "performanceIntent": snippet["performanceIntent"],
            "files": [path.relative_to(destination).as_posix() for path in listen_paths],
            "outputSha256": [sha256_file(path) for path in listen_paths],
            "loudness": measurements, "scores": None, "preference": None, "reviewerId": None})
        if deadline is not None and time.monotonic() >= deadline:
            raise ValueError("Audition time budget exhausted during assembly")
    atomic_write_json(destination / "private-code-map.json", code_map)
    atomic_write_json(destination / "review.json", review)
