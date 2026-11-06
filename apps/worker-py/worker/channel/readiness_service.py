"""Interpret local observations without claiming current remote verification."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .readiness_repo import ReadinessRepository
from .readiness_schema import aware_timestamp, evidence_date, plan_created_on
from .readiness_types import Finding
from .schema import parse_release_policy


class ReadinessService:
    def __init__(self, repository: ReadinessRepository, as_of: datetime) -> None:
        self.repo = repository
        self.as_of = aware_timestamp(as_of.isoformat())
        self.findings: list[Finding] = []

    def note(self, code: str, source: str, detail: str) -> None:
        self.findings.append(Finding(code, source, detail))

    def age(self, value: Any, source: str, maximum_days: int) -> dict[str, Any]:
        try:
            precision, observed = evidence_date(value)
            if precision == "timestamp":
                elapsed = (self.as_of - aware_timestamp(value)).total_seconds() / 86400
            else:
                # A date-only record has no timezone or time-of-day guarantee.
                elapsed = (self.as_of.date() - observed).days
            state = "future" if elapsed < 0 else "stale" if elapsed > maximum_days else "recent"
            if state != "recent":
                self.note(f"evidence_{state}", source, f"Recorded observation is {state}: {value}")
            return {"recordedAt": value, "precision": precision, "ageDays": elapsed,
                    "freshness": state}
        except (TypeError, ValueError):
            self.note("invalid_observation_date", source, "Observation timestamp is missing or invalid.")
            return {"recordedAt": None, "precision": None, "ageDays": None, "freshness": "unknown"}

    def database(self) -> dict[str, Any]:
        data = self.repo.database_snapshot()
        result = asdict(data)
        known = self.repo.known_migrations()
        result["knownMigrations"] = [{"version": v, "name": n} for v, n in known]
        result["completeRemoteInventory"] = False
        if data.status != "available":
            self.note("database_unavailable", data.source, data.status)
            return result
        unknown = [name for version, name in data.migrations if (version, name) not in known]
        if unknown:
            self.note("unknown_migrations", data.source, "Applied migrations absent from this code: " + ", ".join(unknown))
        if data.unavailable:
            self.note("database_capabilities_unavailable", data.source,
                      "Missing tables/fields: " + ", ".join(data.unavailable))
        for table in ("analytics_captures", "analytics_observations"):
            if data.counts.get(table) == 0:
                self.note("analytics_empty", data.source, f"{table} has zero recorded rows; not zero audience activity.")
        result["captures"] = [dict(row, observation=self.age(row["collected_at"], data.source, 7))
                              for row in data.captures]
        if not data.captures:
            self.note("remote_capture_missing", data.source, "No readable remote capture records.")
        else:
            self.note("remote_inventory_unverified", data.source,
                      "Capture scope is historical evidence; full/current account inventory is unverified.")
        return result

    def release(self) -> dict[str, Any]:
        document = self.repo.json(self.repo.release_policy)
        result: dict[str, Any] = {"source": document.source, "status": document.status}
        if document.status != "available":
            self.note("release_policy_unavailable", document.source, document.status)
            return result
        try:
            policy = parse_release_policy(document.payload)
            local_date = self.as_of.astimezone(ZoneInfo(policy.timezone)).date().isoformat()
        except (ValueError, TypeError, ZoneInfoNotFoundError):
            result["status"] = "invalid_schema"
            self.note("release_policy_invalid", document.source, "Release policy failed schema validation.")
            return result
        result.update(timezone=policy.timezone, evaluatedLocalDate=local_date,
                      maxUploadsPerRolling7Days=policy.max_uploads_per_rolling_7_days)
        result["programs"] = []
        for program in policy.programs:
            window = "expired" if program.ends_on and local_date > program.ends_on else (
                "not_started" if program.starts_on and local_date < program.starts_on else "in_window"
            )
            result["programs"].append({"id": program.program_id, "configuredStatus": program.status,
                                       "windowState": window, "startsOn": program.starts_on,
                                       "endsOn": program.ends_on})
            if program.status == "active" and window != "in_window":
                self.note("active_program_outside_window", document.source, f"{program.program_id}: {window}")
        return result

    def community(self) -> dict[str, Any]:
        documents = self.repo.community()
        observations: list[dict[str, Any]] = []
        schedules: list[datetime] = []
        recorded_comments: set[str] = set()
        verified_comments: set[str] = set()
        partial: list[str] = []
        states: list[dict[str, str]] = []
        supported_documents = 0
        available_domains: set[str] = set()
        invalid_domains: set[str] = set()
        known_schemas = {"community-operations-v1", "video-comment-backfill-v1",
                         "community-post-buffer-v1", "video-comment-backfill-queue-v1"}
        for document in documents:
            states.append({"source": document.source, "status": document.status})
            if document.status != "available":
                self.note("community_evidence_unavailable", document.source, document.status)
                continue
            data = document.payload
            if not isinstance(data.get("schema"), str) or data["schema"] not in known_schemas:
                states[-1]["status"] = "unsupported_schema"
                self.note("community_schema_unknown", document.source, "Unsupported community evidence schema.")
                continue
            supported_documents += 1
            if data.get("captureComplete") is False:
                partial.append(document.source)
            for key in ("comments", "videoComments", "communityPosts", "posts"):
                if key not in data:
                    continue
                domain = "comments" if key in {"comments", "videoComments"} else "postSchedules"
                rows = data[key]
                if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                    invalid_domains.add(domain)
                    self.note("community_rows_invalid", document.source, f"{key} must contain objects.")
                    continue
                if not rows:
                    available_domains.add(domain)
                for row in rows:
                    status = row.get("status")
                    if not isinstance(status, str):
                        invalid_domains.add(domain)
                        self.note("community_rows_invalid", document.source, f"{key} records need a string status.")
                        continue
                    valid_record = True
                    if status in {"published", "published_verified"}:
                        comment_id = row.get("commentId")
                        if domain == "comments" and isinstance(comment_id, str) and comment_id:
                            recorded_comments.add(comment_id)
                            if status == "published_verified":
                                verified_comments.add(comment_id)
                        elif domain == "comments":
                            valid_record = False
                            invalid_domains.add(domain)
                            self.note("community_rows_invalid", document.source, "Published comment needs a commentId.")
                        elif not isinstance(row.get("postId") or row.get("id"), str) or not (
                            row.get("postId") or row.get("id")
                        ):
                            valid_record = False
                            invalid_domains.add(domain)
                            self.note("community_rows_invalid", document.source, "Published post needs a postId or id.")
                        timestamp = next((row[name] for name in ("verifiedAt", "checkedAt", "publishedAt", "date")
                                          if row.get(name)), data.get("date"))
                        if valid_record:
                            observations.append(dict(source=document.source, **self.age(timestamp, document.source, 7)))
                    if domain == "postSchedules" and status in {"scheduled", "scheduled_verified"}:
                        try:
                            schedules.append(aware_timestamp(row.get("scheduledAt")))
                        except ValueError:
                            valid_record = False
                            invalid_domains.add(domain)
                            self.note("community_schedule_invalid", document.source, "Scheduled record needs an aware timestamp.")
                    if valid_record:
                        available_domains.add(domain)
        dated = [row for row in observations if row["recordedAt"] and row["freshness"] != "future"]
        latest = min(dated, key=lambda row: row["ageDays"]) if dated else None
        if latest is None:
            self.note("community_observation_missing", "workspace/community", "No dated publication observation found.")
        if partial:
            self.note("community_inventory_partial", "workspace/community", "Historical inventories explicitly mark captureComplete=false.")
        if not any(value > self.as_of for value in schedules):
            self.note("community_buffer_unverified", "workspace/community", "No future scheduled post found in local evidence.")
        unreadable_documents = supported_documents != len(documents)
        coverage = {domain: "unavailable" if domain not in available_domains else (
            "partial" if domain in invalid_domains or unreadable_documents else "available"
        ) for domain in ("comments", "postSchedules")}
        coverage["documents"] = "unavailable" if supported_documents == 0 else (
            "partial" if unreadable_documents or invalid_domains else "available"
        )
        return {"documents": states, "evidenceCoverage": coverage, "latestRecordedPublication": latest,
                "recordedCommentIds": len(recorded_comments) if "comments" in available_domains else None,
                "explicitlyVerifiedCommentIds": len(verified_comments) if "comments" in available_domains else None,
                "commentCountsScope": "unique IDs in readable local evidence, not a remote catalogue count",
                "latestRecordedSchedule": max(schedules).isoformat() if schedules else None,
                "futureScheduledRecords": sum(value > self.as_of for value in schedules)
                if "postSchedules" in available_domains else None,
                "partialInventories": partial, "remoteCurrentState": "unknown", "automationCurrentState": "unknown"}

    def report(self) -> dict[str, Any]:
        self.findings = []
        database = self.database()
        release = self.release()
        community = self.community()
        plans = self.repo.plans()
        if plans is None:
            self.note("active_plan_inventory_unavailable", "docs/exec-plans/active", "Directory missing or unreadable.")
        plan_rows = [{"source": path, "createdOnFromFilename": plan_created_on(PurePosixPath(path).name),
                      "lastActivityAt": None} for path in plans or ()]
        # Many comments share the same recorded day. Keep diagnostics bounded.
        findings = list(dict.fromkeys(self.findings))
        return {"schema": "channel-readiness-v1", "asOf": self.as_of.isoformat(),
                "reportKind": "local_evidence_diagnostic", "releaseApproval": False,
                "remoteMutationAuthority": False, "currentRemoteState": "not_queried",
                "diagnosticFreshnessDays": 7, "database": database, "releasePolicy": release,
                "community": community, "activePlans": {"count": len(plan_rows) if plans is not None else None,
                    "dateMeaning": "Filename creation date only; not evidence of recent activity or completion.",
                    "items": plan_rows}, "findings": [asdict(item) for item in findings]}
