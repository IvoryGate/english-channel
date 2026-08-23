from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


class AuthorityLevel(IntEnum):
    PACKAGE_ONLY = 0
    PRIVATE_UPLOAD = 1
    SCHEDULE = 2
    AUTONOMOUS = 3


class LifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    RIGHTS_VERIFIED = "RIGHTS_VERIFIED"
    SOURCE_LOCKED = "SOURCE_LOCKED"
    PLANNED = "PLANNED"
    PRODUCING = "PRODUCING"
    QC_FAILED = "QC_FAILED"
    READY_TO_UPLOAD = "READY_TO_UPLOAD"
    UPLOADED_PRIVATE = "UPLOADED_PRIVATE"
    PLATFORM_CHECKED = "PLATFORM_CHECKED"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    OBSERVING = "OBSERVING"
    EXPERIMENT_DECIDED = "EXPERIMENT_DECIDED"
    RETROSPECTIVE_COMPLETE = "RETROSPECTIVE_COMPLETE"


class RightsStatus(str, Enum):
    REVIEW_REQUIRED = "review_required"
    VERIFIED_PUBLIC_DOMAIN = "verified_public_domain"
    REJECTED = "rejected"


@dataclass(frozen=True)
class SeriesPolicy:
    slug: str
    authority: AuthorityLevel
    publication_territories: tuple[str, ...]
    chapters_per_week: int
    ready_buffer_chapters: int
    release_policy_ref: str
    release_program_id: str
    required_release_gates: tuple[str, ...]
    analytics_windows_hours: tuple[int, ...]
    max_thumbnail_variants: int
    require_single_changed_variable: bool


@dataclass(frozen=True)
class RightsEvidence:
    kind: str
    territory: str
    url: str
    note: str


@dataclass(frozen=True)
class BookCatalogRecord:
    slug: str
    title: str
    author: str
    language: str
    first_published_year: int
    author_death_year: int
    rights_status: RightsStatus
    approved_territories: tuple[str, ...]
    reviewed_at: str | None
    evidence: tuple[RightsEvidence, ...]
    source_url: str


@dataclass(frozen=True)
class AudioAcceptanceCase:
    case_id: str
    dimension: str
    text: str


@dataclass(frozen=True)
class AudioAcceptancePolicy:
    cases: tuple[AudioAcceptanceCase, ...]
    minimum_asr_similarity: float
    maximum_true_peak_dbtp: float
    maximum_clipped_samples: int
    required_blind_reviewers: int


@dataclass(frozen=True)
class AudioSampleReview:
    case_id: str
    asr_similarity: float
    true_peak_dbtp: float
    clipped_samples: int
    electronic_artifact_detected: bool
    blind_approvals: int


@dataclass(frozen=True)
class AudioCandidateDecision:
    accepted: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class OperationEvent:
    event_id: str
    sequence: int
    book_slug: str
    chapter: int
    occurred_at: str
    actor: str
    event_type: str
    from_state: LifecycleState | None
    to_state: LifecycleState
    reason: str
    idempotency_key: str
    intent_hash: str
    previous_event_hash: str | None
    event_hash: str
    evidence: dict[str, Any] = field(default_factory=dict)
