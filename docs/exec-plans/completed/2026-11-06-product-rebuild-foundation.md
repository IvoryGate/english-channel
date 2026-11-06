# Product Rebuild Foundation

## Goal

Make the channel's actual operating state reviewable before committing more
production capacity. Replace contradictory assumptions with evidence, an
explicit product hypothesis and a bounded, zero-new-spend validation sequence.

## Scope

First vertical slice: repository/product audit, one rebuild entry point,
read-only channel readiness diagnostics, regression tests, and an actionable
quality/market/community validation programme. This is not the completion of
autonomous operations or a claim of subscriber growth.

## System Boundaries

`worker/channel/` diagnostic types/schema/repository/service/transport,
focused tests, `docs/PRODUCT_REBUILD.md`, and existing architecture/index docs.
No remote publication, paid services, database migration, model download,
artifact deletion or automatic-task reactivation in this slice.

## Status

2026-11-06, owner agent Codex. Implementation and local verification complete on
`codex/product-rebuild-foundation`, created from refreshed `origin/main`
`298c75f`. Existing 82-path October work preserved and pushed separately as
`6eb97f1` on `codex/brand-motion-sound-v4`; it is not reviewed trunk.
Generated assets and runtime records remain in place and outside Git.

User constraints: zero new paid spend; 30-60 minutes/week human review;
positioning open to research. Subscriber milestones are ambitions, not promises.

Delivered: read-only readiness command, 21 diagnostic regression cases,
evidence-backed rebuild entry point, six-snippet audio audition specification,
three positioning hypotheses and a concrete creative brief, corrected historical
doc precedence, and archival of the already-completed September 28 plan.
Future product phases remain explicitly unimplemented in PRODUCT_REBUILD.md.

Validation: full lint/type/encoding/docs/architecture passes. Full Node tests
and 249 Python tests pass on normal host execution. Restricted execution
crashed in native NumPy/Torch loading; host verification resolves the local
suite without changing installed packages. Independent review identified and
fixed missing-as-zero, WAL sidecar creation, invalid publication identity and
rounded timestamp ordering; targeted diagnostic/control-plane suite 29 passes.

Archive restored by user: A045/B047/C036 accessible and 205 trace records
audited. A045 local chapter timing can be 235.559 seconds early after mastering;
this remains a separately scoped audio-timeline repair, not hidden by this slice.

Checkpoint PR #21 CI has three failures: two tests require ignored local brand
plates, and one historical recovery schedule disagrees with the original grid.
Checkpoint stays draft and cannot merge. This independent foundation branch
contains neither change; its PR CI must be evaluated separately.

## Plan

1. Preserve prior work; distinguish archival checkpoint from accepted release.
2. Audit product, audio, imagery, market, community, data, resources and plans.
3. Implement a read-only readiness report with honest missing/stale states.
4. Consolidate decisions and sequence later slices by evidence-based exit gates.
5. Test, publish a scoped PR, record unresolved validation and archive this slice
   when its deliverables are complete; later phases get their own plans.

## Validation

No database creation/mutation on diagnosis; missing/corrupt inputs and unknown
migrations remain visible; expired release policies are reported; fixture tests
use explicit dates. Run focused tests and required repository gates. Real local
diagnosis must expose limitations rather than invent current remote metrics.

## Risks And Decisions

- October checkpoint lint passed; full local Python suite failed in NumPy/MKL
  import with Windows exception 0xc0000008 before completing. Do not mark green.
- Shared database has a migration not present on trunk; inspect read-only.
- Some media directories are junctions into E: archive storage, now reconnected.
  Preserve links/assets; sampled availability is not archive-wide integrity.
- Historical community execution is evidenced, continued operation is not.
- Prior automation pause remains effective; this slice adds no scheduler.
- Do not wholesale merge preserved analytics/experiment/production branches.

## Archive Criteria

Readiness command, regression coverage, evidence-backed roadmap and documentation
are delivered in a scoped PR with validation status recorded. Unresolved later
product work is owned by the roadmap, not falsely marked complete here.
