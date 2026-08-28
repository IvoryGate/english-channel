from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable, Iterable
from uuid import uuid4

from .repo import BookCatalogRepository, OperationLedgerRepository
from .schema import calculate_event_hash
from .types import (
    AudioAcceptancePolicy,
    AudioCandidateDecision,
    AudioSampleReview,
    AuthorityLevel,
    LifecycleState,
    OperationEvent,
    RightsStatus,
    SeriesPolicy,
)


class OperationPolicyError(RuntimeError):
    pass


ALLOWED_TRANSITIONS: dict[LifecycleState | None, frozenset[LifecycleState]] = {
    None: frozenset({LifecycleState.DISCOVERED}),
    LifecycleState.DISCOVERED: frozenset({LifecycleState.RIGHTS_VERIFIED}),
    LifecycleState.RIGHTS_VERIFIED: frozenset({LifecycleState.SOURCE_LOCKED}),
    LifecycleState.SOURCE_LOCKED: frozenset({LifecycleState.PLANNED}),
    LifecycleState.PLANNED: frozenset({LifecycleState.PRODUCING}),
    LifecycleState.PRODUCING: frozenset({LifecycleState.QC_FAILED, LifecycleState.READY_TO_UPLOAD}),
    LifecycleState.QC_FAILED: frozenset({LifecycleState.PRODUCING}),
    LifecycleState.READY_TO_UPLOAD: frozenset({LifecycleState.UPLOADED_PRIVATE}),
    LifecycleState.UPLOADED_PRIVATE: frozenset({LifecycleState.PLATFORM_CHECKED}),
    LifecycleState.PLATFORM_CHECKED: frozenset({LifecycleState.SCHEDULED}),
    LifecycleState.SCHEDULED: frozenset({LifecycleState.PUBLISHED}),
    LifecycleState.PUBLISHED: frozenset({LifecycleState.OBSERVING}),
    LifecycleState.OBSERVING: frozenset({LifecycleState.EXPERIMENT_DECIDED}),
    LifecycleState.EXPERIMENT_DECIDED: frozenset({LifecycleState.RETROSPECTIVE_COMPLETE}),
    LifecycleState.RETROSPECTIVE_COMPLETE: frozenset(),
}

REQUIRED_AUTHORITY = {
    LifecycleState.UPLOADED_PRIVATE: AuthorityLevel.PRIVATE_UPLOAD,
    LifecycleState.SCHEDULED: AuthorityLevel.SCHEDULE,
    LifecycleState.PUBLISHED: AuthorityLevel.AUTONOMOUS,
}


def evaluate_audio_candidate(
    policy: AudioAcceptancePolicy, reviews: Iterable[AudioSampleReview]
) -> AudioCandidateDecision:
    review_list = list(reviews)
    by_case = {review.case_id: review for review in review_list}
    failures: list[str] = []
    if len(by_case) != len(review_list):
        failures.append("duplicate audio review case")
    expected = {case.case_id for case in policy.cases}
    for missing in sorted(expected - set(by_case)):
        failures.append(f"{missing}: missing review")
    for unexpected in sorted(set(by_case) - expected):
        failures.append(f"{unexpected}: unexpected review")
    for case_id in sorted(expected & set(by_case)):
        review = by_case[case_id]
        if review.asr_similarity < policy.minimum_asr_similarity:
            failures.append(f"{case_id}: ASR similarity below threshold")
        if review.true_peak_dbtp > policy.maximum_true_peak_dbtp:
            failures.append(f"{case_id}: true peak exceeds threshold")
        if review.clipped_samples > policy.maximum_clipped_samples:
            failures.append(f"{case_id}: clipped samples exceed threshold")
        if review.electronic_artifact_detected:
            failures.append(f"{case_id}: electronic artifact detected")
        if review.blind_approvals < policy.required_blind_reviewers:
            failures.append(f"{case_id}: insufficient blind-listening approvals")
    return AudioCandidateDecision(not failures, tuple(failures))


class ClassicOperationsService:
    def __init__(
        self,
        policy: SeriesPolicy,
        catalog: BookCatalogRepository,
        ledger: OperationLedgerRepository,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.policy = policy
        self.catalog = catalog
        self.ledger = ledger
        self.now = now or (lambda: datetime.now(timezone.utc))

    def current_state(self, book_slug: str, chapter: int) -> LifecycleState | None:
        events = self.ledger.read(book_slug, chapter)
        return events[-1].to_state if events else None

    def transition(
        self,
        book_slug: str,
        chapter: int,
        to_state: LifecycleState,
        *,
        actor: str,
        reason: str,
        idempotency_key: str,
        evidence: dict[str, Any] | None = None,
    ) -> OperationEvent:
        if not actor.strip() or not reason.strip() or not idempotency_key.strip():
            raise OperationPolicyError("actor, reason, and idempotency_key are required")
        evidence = dict(evidence or {})
        intent_hash = self._intent_hash(book_slug, chapter, to_state, actor, reason, evidence)
        existing = self.ledger.find_by_idempotency_key(book_slug, chapter, idempotency_key)
        if existing:
            if existing.intent_hash != intent_hash:
                raise OperationPolicyError("Idempotency key was already used for a different transition")
            return existing
        current = self.current_state(book_slug, chapter)
        if to_state not in ALLOWED_TRANSITIONS[current]:
            raise OperationPolicyError(f"Transition {current} -> {to_state.value} is not allowed")
        required_authority = REQUIRED_AUTHORITY.get(to_state, AuthorityLevel.PACKAGE_ONLY)
        explicitly_approved_publication = (
            to_state is LifecycleState.PUBLISHED
            and self.policy.authority >= AuthorityLevel.SCHEDULE
            and evidence.get("explicitOwnerApproval") is True
        )
        if self.policy.authority < required_authority and not explicitly_approved_publication:
            raise OperationPolicyError(
                f"Authority level {self.policy.authority.value} cannot enter {to_state.value}; "
                f"level {required_authority.value} is required"
            )
        self._validate_evidence(book_slug, to_state, evidence)
        events = self.ledger.read(book_slug, chapter)
        event = OperationEvent(
            event_id=str(uuid4()),
            sequence=len(events) + 1,
            book_slug=book_slug,
            chapter=chapter,
            occurred_at=self.now().astimezone(timezone.utc).isoformat(),
            actor=actor.strip(),
            event_type="state_transition",
            from_state=current,
            to_state=to_state,
            reason=reason.strip(),
            idempotency_key=idempotency_key.strip(),
            intent_hash=intent_hash,
            previous_event_hash=events[-1].event_hash if events else None,
            event_hash="",
            evidence=evidence,
        )
        event = replace(event, event_hash=calculate_event_hash(event))
        return self.ledger.append(event)

    def _validate_evidence(
        self, book_slug: str, to_state: LifecycleState, evidence: dict[str, Any]
    ) -> None:
        if to_state is LifecycleState.RIGHTS_VERIFIED:
            record = self.catalog.get(book_slug)
            if record.rights_status is not RightsStatus.VERIFIED_PUBLIC_DOMAIN:
                raise OperationPolicyError(f"Rights are not verified for {book_slug}")
            if not record.approved_territories or not record.evidence:
                raise OperationPolicyError(f"Rights evidence is incomplete for {book_slug}")
            missing_territories = sorted(
                set(self.policy.publication_territories) - set(record.approved_territories)
            )
            if missing_territories:
                raise OperationPolicyError(
                    "Rights are not approved for configured publication territories: "
                    + ", ".join(missing_territories)
                )
        elif to_state is LifecycleState.SOURCE_LOCKED:
            digest = evidence.get("sourceSha256")
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
                raise OperationPolicyError("SOURCE_LOCKED requires a 64-character sourceSha256")
        elif to_state is LifecycleState.READY_TO_UPLOAD:
            gates = evidence.get("gates")
            if not isinstance(gates, dict):
                raise OperationPolicyError("READY_TO_UPLOAD requires release gate evidence")
            failed = [gate for gate in self.policy.required_release_gates if gates.get(gate) is not True]
            if failed:
                raise OperationPolicyError(f"Release gates did not pass: {', '.join(failed)}")
        elif to_state is LifecycleState.UPLOADED_PRIVATE:
            if evidence.get("privacyStatus") != "private" or not evidence.get("youtubeVideoId"):
                raise OperationPolicyError("Private upload evidence requires youtubeVideoId and privacyStatus=private")
        elif to_state is LifecycleState.PLATFORM_CHECKED:
            if evidence.get("processingStatus") != "succeeded" or evidence.get("copyrightCheck") != "clear":
                raise OperationPolicyError("Platform processing and copyright checks must pass")
        elif to_state is LifecycleState.SCHEDULED and not evidence.get("scheduledAt"):
            raise OperationPolicyError("SCHEDULED requires scheduledAt")
        elif to_state is LifecycleState.PUBLISHED and not evidence.get("publishedAt"):
            raise OperationPolicyError("PUBLISHED requires publishedAt")
        elif to_state is LifecycleState.EXPERIMENT_DECIDED:
            if not evidence.get("experimentId") or not evidence.get("outcome"):
                raise OperationPolicyError("EXPERIMENT_DECIDED requires experimentId and outcome")
        elif to_state is LifecycleState.RETROSPECTIVE_COMPLETE:
            if not evidence.get("retrospectivePath") or not evidence.get("snapshotIds"):
                raise OperationPolicyError("RETROSPECTIVE_COMPLETE requires a retrospective and snapshots")

    @staticmethod
    def _intent_hash(
        book_slug: str,
        chapter: int,
        to_state: LifecycleState,
        actor: str,
        reason: str,
        evidence: dict[str, Any],
    ) -> str:
        value = json.dumps(
            {
                "bookSlug": book_slug,
                "chapter": chapter,
                "toState": to_state.value,
                "actor": actor.strip(),
                "reason": reason.strip(),
                "evidence": evidence,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
