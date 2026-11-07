"""Evidence decisions only; providers/CLI own media-specific final checks."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Callable

from .repo import EvidenceRepository
from .providers import manifest_voice_identities, voice_identity
from .schema import accepted_review, handoff, identity_sha256, object_value, text
from .types import Check, STAGES


class HandoffService:
    def __init__(self, repository: EvidenceRepository, final_audio_check: Callable | None = None):
        self.repo = repository
        self.final_audio_check = final_audio_check

    def validate(self, payload: dict) -> dict:
        checks: list[Check] = []

        def check(stage: str, name: str, operation: Callable) -> None:
            try:
                operation()
            except (ValueError, OSError, KeyError, TypeError, ImportError, RuntimeError) as exc:
                checks.append(Check(stage, name, False, str(exc)))
            else:
                checks.append(Check(stage, name, True, "Evidence verified"))

        check("ready_to_prepare", "contract", lambda: handoff(payload))
        if checks[-1].passed:
            check("ready_to_prepare", "original_brief", lambda: self._brief(payload))
            check("ready_to_prepare", "script_review", lambda: self._script(payload))
            check("ready_to_prepare", "community_drafts", lambda: self._community(payload))
            check("ready_to_prepare", "measurement_plan", lambda: self._measurement(payload))
            check("local_production", "voice_acceptance", lambda: self._voices(payload))
            check("local_production", "visual_evidence", lambda: self._visuals(payload))
            check("package_verified", "local_package", lambda: self._package(payload))
        stages = {}
        inherited = True
        for stage in STAGES[:-1]:
            relevant = [row for row in checks if row.stage == stage]
            inherited = inherited and bool(relevant) and all(row.passed for row in relevant)
            stages[stage] = inherited
        stages["public_release"] = False
        return {"schema": "elr-production-handoff-report-v1", "contentId": payload.get("contentId"),
            "stages": stages, "publicReleaseAllowed": False,
            "publicReleaseReason": "Local evidence cannot grant publication authority or platform acceptance",
            "checks": [asdict(row) for row in checks]}

    def _record(self, payload: dict, field: str, schema: str) -> dict:
        record = self.repo.json(payload[field])
        if record.get("schema") != schema or record.get("contentId") != payload["contentId"]:
            raise ValueError(f"{field} schema/content identity mismatch")
        return record

    def _brief(self, payload: dict) -> None:
        brief = self._record(payload, "brief", "elr-production-brief-v1")
        for key in ("hypothesisId", "audienceNeed", "viewerOutcome", "originalityBasis"):
            text(brief.get(key), key)
        if brief.get("originality") != "original":
            raise ValueError("The brief must declare original work and its basis")
        research = brief.get("research")
        if not isinstance(research, list) or not research:
            raise ValueError("Brief requires referenced research evidence")
        for reference in research:
            self.repo.verify(reference)

    def _script(self, payload: dict) -> None:
        self.repo.verify(payload["script"])
        review = self._record(payload, "scriptReview", "elr-script-review-v1")
        accepted_review(review, ("original_work", "viewer_outcome", "practice_payoff", "spoken_text_only"))
        if review.get("scriptSha256") != payload["script"]["sha256"] or review.get("briefSha256") != payload["brief"]["sha256"]:
            raise ValueError("Script review does not bind the current script and brief")

    def _community(self, payload: dict) -> None:
        record = self._record(payload, "community", "elr-community-drafts-v1")
        if record.get("status") != "draft_only" or record.get("remoteActionAuthorized") is not False:
            raise ValueError("Community handoff is draft-only, with no remote authority")
        for field in ("practicePrompt", "channelAuthoredExample", "followUpDraft", "feedbackRouting"):
            text(record.get(field), field)

    def _measurement(self, payload: dict) -> None:
        record = self._record(payload, "measurementPlan", "elr-measurement-plan-v1")
        rows = record.get("windows")
        if not isinstance(rows, list) or len(rows) != 3 or {object_value(row, "window").get("at") for row in rows} != {"T+24h", "T+7d", "T+28d"}:
            raise ValueError("Measurement plan requires T+24h, T+7d and T+28d windows")
        for row in rows:
            object_value(row, "measurement window")
            text(row.get("source"), "measurement source")
            metrics = row.get("metrics")
            if not isinstance(metrics, list) or not metrics:
                raise ValueError("Each measurement window requires metrics")
            for metric in metrics:
                text(metric, "metric")
        text(record.get("decisionRule"), "decisionRule")
        text(record.get("guardrails"), "guardrails")
        if record.get("missingEvidenceAction") != "hold":
            raise ValueError("Unavailable future observations must hold decisions")

    def _voices(self, payload: dict) -> None:
        manifest = self.repo.json(payload["productionManifest"])
        if manifest.get("episodeId") != payload["episodeId"]:
            raise ValueError("Production manifest episode identity mismatch")
        review = self.repo.json(payload["scriptReview"])
        if review.get("manifestSha256") != payload["productionManifest"]["sha256"]:
            raise ValueError("Script review must bind the prepared production manifest")
        expected = manifest_voice_identities(self.repo.root, manifest)
        voices = payload.get("voices")
        if not isinstance(voices, list) or not voices:
            raise ValueError("Voice identity and acceptance evidence are missing")
        speakers = set()
        for voice in voices:
            object_value(voice, "voice selection")
            speaker = text(voice.get("speakerId"), "speakerId")
            if speaker in speakers:
                raise ValueError("Duplicate speaker identity")
            speakers.add(speaker)
            identity = object_value(voice.get("identity"), "voice identity")
            for field in ("providerId", "modelId", "modelRevision", "localModelPath", "runtimeMode"):
                text(identity.get(field), field)
            object_value(identity.get("providerSettings"), "providerSettings")
            profile = object_value(identity.get("voice"), "voice")
            if profile.get("kind") == "clone":
                self.repo.verify({"path": profile["referencePath"], "sha256": profile["referenceSha256"]})
            elif profile.get("kind") == "preset":
                text(profile.get("voiceId"), "voiceId")
            else:
                raise ValueError("Voice must be an explicit clone or preset")
            if expected.get(speaker) != identity:
                raise ValueError("Accepted voice identity/settings differ from production manifest")
            acceptance = self.repo.json(voice["acceptance"])
            if acceptance.get("schema") != "elr-voice-acceptance-v1" or acceptance.get("scope") != "local_production":
                raise ValueError("Voice acceptance must explicitly cover local production")
            accepted_review(acceptance, ("identity", "rights", "intelligibility", "stability", "naturalness", "appropriate_emotion"))
            if acceptance["reviewer"]["kind"] != "human":
                raise ValueError("Voice production acceptance requires an actual human listening review")
            if acceptance.get("identitySha256") != identity_sha256(identity):
                raise ValueError("Voice acceptance is stale or belongs to another identity/settings")
            self.repo.verify(acceptance["sample"])
            trace = self.repo.json(acceptance["sampleTrace"])
            if (trace.get("schema") != "elr-tts-turn-trace-v1"
                    or trace.get("outputSha256") != acceptance["sample"]["sha256"]
                    or voice_identity(trace["provider"], trace["voice"]) != identity):
                raise ValueError("Accepted sample trace does not bind the chosen voice/settings/audio")
        if speakers != set(expected):
            raise ValueError("Every spoken manifest host needs voice acceptance")

    def _visuals(self, payload: dict) -> None:
        visuals = payload.get("visuals")
        if not isinstance(visuals, list) or len(visuals) != 2 or {object_value(row, "visual").get("role") for row in visuals} != {"thumbnail", "body"}:
            raise ValueError("Visual handoff requires thumbnail and body assets")
        for visual in visuals:
            record = self.repo.json(visual["provenance"])
            if (record.get("schema") != "elr-visual-provenance-v1" or record.get("contentId") != payload["contentId"]
                    or record.get("role") != visual["role"]):
                raise ValueError("Visual provenance identity/role mismatch")
            accepted_review(record, ("identity_consistency", "readability", "no_unintended_text"))
            text(record.get("generator"), "generator")
            text(record.get("transform"), "source-to-final transform")
            self.repo.verify(record["prompt"])
            references = record.get("references")
            if not isinstance(references, list):
                raise ValueError("Visual references must be explicitly listed, even if empty")
            for reference in references:
                self.repo.verify(reference)
            source_size = self.repo.image_dimensions(record["source"])
            if list(source_size) != record.get("sourceCanvas"):
                raise ValueError("Source image dimensions differ from provenance")
            if record.get("output") != visual["artifact"]:
                raise ValueError("Visual output is not bound to provenance")
            if self.repo.image_dimensions(visual["artifact"]) != (1920, 1080):
                raise ValueError("Final visual canvas must be 1920x1080; source dimensions are separate")

    def _package(self, payload: dict) -> None:
        package = object_value(payload.get("package"), "package")
        manifest = self.repo.json(package["manifest"])
        if manifest.get("episodeId") != payload["episodeId"]:
            raise ValueError("Package episode identity mismatch")
        if package["manifest"] != payload["productionManifest"]:
            raise ValueError("Package manifest differs from the accepted production manifest")
        artifacts = package.get("artifacts")
        required = {"master", "video", "captions", "description"}
        if not isinstance(artifacts, dict) or set(artifacts) != required:
            raise ValueError("Package requires master, video, captions and description references")
        for reference in artifacts.values():
            self.repo.verify(reference)
        review = self.repo.json(package["review"])
        if review.get("schema") != "elr-local-package-review-v1" or review.get("contentId") != payload["contentId"]:
            raise ValueError("Local package review identity mismatch")
        accepted_review(review, ("captions_sync", "visual_readability", "promise_fulfilled", "no_unintended_speech"))
        expected_hashes = {role: reference["sha256"] for role, reference in artifacts.items()}
        expected_hashes.update({row["role"]: row["artifact"]["sha256"] for row in payload["visuals"]})
        if review.get("artifactHashes") != expected_hashes or review.get("manifestSha256") != package["manifest"]["sha256"]:
            raise ValueError("Local package review does not bind the current artifacts")
        if self.final_audio_check is None:
            raise ValueError("Final media acceptance provider is unavailable")
        evidence = self.final_audio_check(self.repo.path(payload["workspace"]), payload["episodeId"], encoded=True)
        for stage, role in (("master", "master"), ("encoded", "video")):
            record = evidence[stage]
            if (record.get("schema") != "elr-final-audio-acceptance-v1" or record.get("stage") != stage
                    or record.get("status") != "passed" or record["artifact"]["sha256"] != artifacts[role]["sha256"]
                    or record["sources"]["manifest"] != package["manifest"]["sha256"]):
                raise ValueError("Final media evidence does not bind the declared package")


def evaluate_reference(root, reference: dict, required: str = "local_production", *,
                       expected_context: dict | None = None) -> dict:
    """Controller preflight hook: validate a fingerprinted handoff, never render."""
    repository = EvidenceRepository(root)
    try:
        payload = repository.json(reference)
        if expected_context is not None:
            if payload.get("episodeId") != expected_context["episodeId"]:
                raise ValueError("Handoff targets a different production episode")
            def same_path(actual, expected):
                target = Path(expected)
                target = target if target.is_absolute() else repository.path(str(target))
                if repository.path(actual).resolve() != target.resolve():
                    raise ValueError("Handoff evidence is not the artifact consumed by this production context")
            same_path(payload["workspace"], expected_context["workspace"])
            for field in ("script", "productionManifest"):
                same_path(payload[field]["path"], expected_context[field])
                repository.verify(payload[field])
            actual_visuals = {row["role"]: row["artifact"] for row in payload["visuals"]}
            for role, target in expected_context["visuals"].items():
                same_path(actual_visuals[role]["path"], target)
                repository.verify(actual_visuals[role])
        report = HandoffService(repository).validate(payload)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        return {"passed": False, "requiredStage": required, "error": str(exc), "publicReleaseAllowed": False}
    return {"passed": report["stages"].get(required) is True, "requiredStage": required, **report}
