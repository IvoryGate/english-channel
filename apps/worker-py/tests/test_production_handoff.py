from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from worker.production_handoff.providers import manifest_voice_identities
from worker.production_handoff.repo import EvidenceRepository
from worker.production_handoff.schema import identity_sha256
from worker.production_handoff.service import HandoffService, evaluate_reference
from worker.production_handoff.transport import run_check
from worker.tts.schema import PROVIDER_REVISIONS


def write(root: Path, name: str, value) -> dict:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(value).encode() if isinstance(value, dict) else value)
    return ref(root, path)


def ref(root: Path, path: Path) -> dict:
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def review(*names: str) -> dict:
    return {"status": "accepted", "reviewer": {"kind": "agent", "id": "fixture-reviewer"},
            "reviewedAt": "2026-11-07T10:00:00+08:00", "checks": dict.fromkeys(names, True)}


@pytest.fixture
def evidence(tmp_path):
    root = tmp_path
    content = "pilot:test"
    research = write(root, "research.md", b"Observed public evidence; no guaranteed audience fit.")
    brief = write(root, "brief.json", {"schema": "elr-production-brief-v1", "contentId": content,
        "hypothesisId": "H1", "audienceNeed": "Make a small offer", "viewerOutcome": "Say an offer and limit",
        "originality": "original", "originalityBasis": "Original fictional dialogue", "research": [research]})
    script = write(root, "draft.md", b"Riley: I can help for ten minutes.")
    manifest = {"episodeId": "episode_001", "renderSettings": {"ttsProvider": "kokoro",
        "modelRevision": PROVIDER_REVISIONS["kokoro"], "providerSettings": {"speed": .95}},
        "hosts": {"Riley": {"voice": {"kind": "preset", "voiceId": "af_heart"}}},
        "turns": [{"id": "p001", "order": 1, "speaker": "Riley", "text": "I can help for ten minutes."}]}
    manifest_ref = write(root, "episode/manifest.json", manifest)
    script_review = write(root, "script-review.json", {"schema": "elr-script-review-v1", "contentId": content,
        "scriptSha256": script["sha256"], "briefSha256": brief["sha256"], "manifestSha256": manifest_ref["sha256"],
        **review("original_work", "viewer_outcome", "practice_payoff", "spoken_text_only")})
    community = write(root, "community.json", {"schema": "elr-community-drafts-v1", "contentId": content,
        "status": "draft_only", "remoteActionAuthorized": False, "practicePrompt": "Offer five minutes.",
        "channelAuthoredExample": "I can help for five minutes.", "followUpDraft": "Now offer one page.",
        "feedbackRouting": "Link real responses, or record none; never invent participation."})
    measurement = write(root, "measurement.json", {"schema": "elr-measurement-plan-v1", "contentId": content,
        "windows": [{"at": when, "source": "YouTube Analytics", "metrics": ["retention", "views"]}
                    for when in ("T+24h", "T+7d", "T+28d")], "decisionRule": "Review matched evidence.",
        "guardrails": "Clarity must not fall.", "missingEvidenceAction": "hold"})
    identity = manifest_voice_identities(root, manifest)["Riley"]
    sample = write(root, "sample.wav", b"fixture audio")
    trace = write(root, "sample.trace.json", {"schema": "elr-tts-turn-trace-v1",
        "provider": {key: value for key, value in identity.items() if key != "voice"},
        "voice": identity["voice"], "outputSha256": sample["sha256"]})
    acceptance = write(root, "voice-acceptance.json", {"schema": "elr-voice-acceptance-v1",
        "scope": "local_production", "identitySha256": identity_sha256(identity), "sample": sample,
        "sampleTrace": trace, **review("identity", "rights", "intelligibility", "stability", "naturalness", "appropriate_emotion"),
        "reviewer": {"kind": "human", "id": "synthetic-test-listener"}})
    prompt = write(root, "prompt.txt", b"Original scene. No generated lettering.")
    # Different source/final dimensions must be represented honestly.
    Image.new("RGB", (1672, 941)).save(root / "source.png")
    Image.new("RGB", (1920, 1080)).save(root / "final.png")
    source, final = ref(root, root / "source.png"), ref(root, root / "final.png")
    visuals = []
    for role in ("thumbnail", "body"):
        provenance = write(root, f"{role}-provenance.json", {"schema": "elr-visual-provenance-v1",
            "contentId": content, "role": role, "generator": "fixture", "prompt": prompt, "references": [],
            "source": source, "sourceCanvas": [1672, 941], "output": final, "transform": "Explicit resize",
            **review("identity_consistency", "readability", "no_unintended_text")})
        visuals.append({"role": role, "artifact": final, "provenance": provenance})
    artifacts = {role: write(root, f"episode/{role}.dat", role.encode())
                 for role in ("master", "video", "captions", "description")}
    package_review = write(root, "package-review.json", {"schema": "elr-local-package-review-v1", "contentId": content,
        "manifestSha256": manifest_ref["sha256"],
        "artifactHashes": {**{role: item["sha256"] for role, item in artifacts.items()},
                           "thumbnail": final["sha256"], "body": final["sha256"]},
        **review("captions_sync", "visual_readability", "promise_fulfilled", "no_unintended_speech")})
    handoff = {"schema": "elr-production-handoff-v1", "contentId": content, "episodeId": "episode_001",
        "workspace": "episode", "brief": brief, "script": script, "scriptReview": script_review,
        "community": community, "measurementPlan": measurement, "productionManifest": manifest_ref,
        "voices": [{"speakerId": "Riley", "identity": identity, "acceptance": acceptance}], "visuals": visuals,
        "package": {"manifest": manifest_ref, "artifacts": artifacts, "review": package_review}}
    def final_check(workspace, episode, *, encoded):
        assert workspace == root / "episode" and episode == "episode_001" and encoded
        return {stage: {"schema": "elr-final-audio-acceptance-v1", "stage": stage, "status": "passed",
            "artifact": {"sha256": artifacts[role]["sha256"]}, "sources": {"manifest": manifest_ref["sha256"]}}
            for stage, role in (("master", "master"), ("encoded", "video"))}
    return root, handoff, final_check


def update(root, reference, **changes):
    data = json.loads((root / reference["path"]).read_bytes())
    data.update(changes)
    replacement = write(root, reference["path"], data)
    reference.update(replacement)


def validate(evidence):
    root, handoff, final_check = evidence
    return HandoffService(EvidenceRepository(root), final_check).validate(handoff)


def test_verified_local_package_never_grants_public_release(evidence):
    root, handoff, _ = evidence
    handoff["publicReleaseAllowed"] = True  # user-supplied flag cannot escalate this report
    result = validate(evidence)
    assert result["stages"] == {"ready_to_prepare": True, "local_production": True,
                                "package_verified": True, "public_release": False}
    assert result["publicReleaseAllowed"] is False
    assert not (root / "workspace/channel/channel.sqlite").exists()


def test_future_audience_observations_and_pending_voice_do_not_block_preparation(evidence):
    root, handoff, _ = evidence
    update(root, handoff["voices"][0]["acceptance"], status="pending")
    handoff["package"] = None
    result = validate(evidence)
    assert result["stages"]["ready_to_prepare"] is True
    assert result["stages"]["local_production"] is False
    assert result["stages"]["package_verified"] is False


@pytest.mark.parametrize("field", ["script", "brief", "scriptReview", "community", "measurementPlan"])
def test_edited_preparation_artifact_invalidates_all_later_stages(evidence, field):
    root, handoff, _ = evidence
    (root / handoff[field]["path"]).write_bytes(b"edited after review")
    assert not any(validate(evidence)["stages"].values())


@pytest.mark.parametrize("defect", ["wrong_acceptance_identity", "wrong_sample_trace", "new_manifest_settings", "unknown_rights", "missing_speaker", "agent_acceptance"])
def test_voice_evidence_must_cover_actual_manifest_and_sample(evidence, defect):
    root, handoff, _ = evidence
    voice = handoff["voices"][0]
    if defect == "wrong_acceptance_identity":
        update(root, voice["acceptance"], identitySha256="0" * 64)
    elif defect == "wrong_sample_trace":
        acceptance = json.loads((root / voice["acceptance"]["path"]).read_bytes())
        trace = acceptance["sampleTrace"]
        update(root, trace, outputSha256="0" * 64)
        update(root, voice["acceptance"], sampleTrace=trace)
    elif defect == "new_manifest_settings":
        manifest = json.loads((root / handoff["productionManifest"]["path"]).read_bytes())
        manifest["renderSettings"]["providerSettings"]["speed"] = 1.1
        update(root, handoff["productionManifest"], **manifest)
        update(root, handoff["scriptReview"], manifestSha256=handoff["productionManifest"]["sha256"])
    elif defect == "unknown_rights":
        update(root, voice["acceptance"], checks={"identity": True, "rights": None, "intelligibility": True, "stability": True})
    elif defect == "agent_acceptance":
        update(root, voice["acceptance"], reviewer={"kind": "agent", "id": "automated-check"})
    else:
        handoff["voices"] = []
    result = validate(evidence)
    assert result["stages"]["ready_to_prepare"] is True
    assert result["stages"]["local_production"] is False


@pytest.mark.parametrize("defect", ["source_claim", "wrong_canvas", "changed_prompt"])
def test_visual_provenance_is_bound_to_real_source_and_final_canvas(evidence, defect):
    root, handoff, _ = evidence
    visual = handoff["visuals"][0]
    if defect == "source_claim":
        update(root, visual["provenance"], sourceCanvas=[1920, 1080])
    elif defect == "wrong_canvas":
        Image.new("RGB", (1672, 941)).save(root / "final.png")
        visual["artifact"].update(ref(root, root / "final.png"))
        update(root, visual["provenance"], output=visual["artifact"])
    else:
        (root / "prompt.txt").write_bytes(b"unreviewed prompt")
    assert validate(evidence)["stages"]["local_production"] is False


def test_missing_measurement_window_blocks_preparation_without_demanding_real_data(evidence):
    root, handoff, _ = evidence
    update(root, handoff["measurementPlan"], windows=[])
    assert validate(evidence)["stages"]["ready_to_prepare"] is False


def test_missing_or_wrong_final_acceptance_cannot_claim_package_verified(evidence):
    root, handoff, final_check = evidence
    no_provider = HandoffService(EvidenceRepository(root)).validate(handoff)
    assert no_provider["stages"]["local_production"] is True
    assert no_provider["stages"]["package_verified"] is False
    def stale(*args, **kwargs):
        result = final_check(*args, **kwargs)
        result["encoded"]["artifact"]["sha256"] = "0" * 64
        return result
    assert HandoffService(EvidenceRepository(root), stale).validate(handoff)["stages"]["package_verified"] is False


def test_refingerprinted_caption_edit_still_requires_new_package_review(evidence):
    root, handoff, _ = evidence
    captions = handoff["package"]["artifacts"]["captions"]
    captions.update(write(root, captions["path"], b"Unreviewed caption timing"))
    result = validate(evidence)
    assert result["stages"]["local_production"] is True
    assert result["stages"]["package_verified"] is False


def test_controller_hook_and_cli_are_read_only_and_exit_for_required_stage(evidence, capsys):
    root, handoff, final_check = evidence
    reference = write(root, "handoff.json", handoff)
    assert evaluate_reference(root, reference)["passed"] is True
    assert run_check(root, root / "handoff.json", "package_verified", final_check) == 0
    assert run_check(root, root / "handoff.json", "public_release", final_check) == 2
    capsys.readouterr()
    (root / "handoff.json").write_bytes(b"{}")
    assert evaluate_reference(root, reference)["passed"] is False


@pytest.mark.parametrize("field", ["episodeId", "workspace", "script", "productionManifest", "visuals", "changed_actual_bytes"])
def test_controller_cannot_apply_valid_handoff_to_other_consumed_files(evidence, field):
    root, handoff, _ = evidence
    reference = write(root, "handoff.json", handoff)
    context = {"episodeId": handoff["episodeId"], "workspace": root / "episode",
        "script": root / handoff["script"]["path"],
        "productionManifest": root / handoff["productionManifest"]["path"],
        "visuals": {row["role"]: root / row["artifact"]["path"] for row in handoff["visuals"]}}
    assert evaluate_reference(root, reference, expected_context=context)["passed"] is True
    if field == "visuals":
        context["visuals"]["body"] = root / "other-body.png"
    elif field == "changed_actual_bytes":
        context["script"].write_bytes(b"Unreviewed actual script")
    elif field == "episodeId":
        context[field] = "episode_999"
    else:
        context[field] = root / "other" / field
    assert evaluate_reference(root, reference, expected_context=context)["passed"] is False
