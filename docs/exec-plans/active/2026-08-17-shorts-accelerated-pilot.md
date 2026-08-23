# 2026-08-17 Shorts accelerated pilot operations

## Goal

Run a fourteen-day, two-Shorts-per-day cold-start validation cycle so the
channel can learn faster without mixing experiment variables or lowering the
visual, audio, brand, and publication gates.

## Scope

- Request 08:00 and 20:30 Asia/Shanghai slots through channel policy during the
  accelerated pilot; the product adapter cannot reserve or publish them alone.
- Keep at least two scheduled Shorts in inventory when production is healthy.
- Use private, duplicate-safe upload; support authenticated Studio as a fallback
  while YouTube API OAuth is unavailable.
- Capture 24-hour directional metrics and seven-day experiment decisions.
- Preserve related-video verification, platform checks, generated editorial
  imagery, CTA/brand treatment, and mains-hum QC for every Short.

API credential provisioning, policy appeals, paid distribution, and changes to
the channel identity remain out of scope.

## System Boundaries

- `configs/shorts/product.json`: product contract and channel program reference.
- `configs/channel/release-policy.json`: channel capacity, authority, and the
  time-bounded accelerated-pilot request.
- `configs/shorts/pilot-2026-08.json`: verified related-video assignments.
- `docs/shorts/README.md`: Studio recovery path and experiment cadence.
- `workspace/shorts/`: ignored media, publication ledger, and analytics state.
- A future scheduled controller may run the production/review loop only after
  its authority and current external state are reconciled.

## Status

- **State:** historical pilot state requires reconciliation before continuation
- **Owner:** Codex
- **Branch:** source preserved at `codex/shorts-pipeline-pilot`; intake occurs on
  `codex/shorts-adapter-intake`.
- **Last update:** 2026-08-23
- The repository records the following 2026-08 schedule state, but this intake
  has not re-read YouTube and grants no new scheduling authority.
- `elr-s-001` is scheduled for 2026-08-18 20:30.
- `elr-s-002` is scheduled for 2026-08-18 08:00.
- `elr-s-003` passed local and Studio checks and is scheduled for 2026-08-19
  08:00 with Related Video verified after reopening the saved item.
- `elr-s-004` passed local and Studio checks and is scheduled for 2026-08-19
  20:30 with Related Video verified after reopening the saved item.
- Dedicated 9:16 discovery covers are now a production gate from `elr-s-005`
  onward; video screenshots are retained only as the initial baseline.
- `elr-s-005` and `elr-s-006` are packaged with unique content hashes,
  dedicated covers, passing visual/audio QC, and reserved release slots on
  2026-08-20 at 08:00 and 20:30 respectively; Studio upload remains pending.
- YouTube API OAuth is absent; the signed-in English Listening Room Studio
  session is the verified upload fallback.

## Plan

1. Keep the next two release slots populated with passing packages.
2. Publish matched morning/evening pairs with one controlled variable change.
3. Record YouTube IDs, schedules, checks, Related Video, and content keys.
4. Collect delivery diagnostics at three hours and experiment metrics at 24
   hours; make formal decisions only after the seven-day/sample gates.
5. After fourteen days, choose the sustainable steady-state cadence from cost,
   quality, reach, retention, conversion, and long-form uplift.

## Validation

- Product and all portfolio contracts pass.
- Each scheduled item has a unique content key and YouTube ID.
- Copyright and community checks pass before scheduling.
- Related Video persists after reopening the saved Studio item.
- Video, caption, brand, CTA, duration, and electrical-hum gates pass.
- Python tests, TypeScript/lint, and encoding checks pass for repository changes.

## Risks And Decisions

- YouTube does not state that higher upload frequency improves long-term
  performance. Twice daily is used only to shorten the learning cycle.
- First-hours metrics can be delayed or adjusted, so they cannot select winners.
- Upload speed never overrides quality, identity, copyright, or duplicate gates.
- Studio fallback depends on the authenticated browser session; OAuth remains
  necessary for fully unattended API operation.

## Archive Criteria

- Fourteen days of scheduled/published inventory are accounted for.
- Experiment cohorts have passed their age and sample gates or are explicitly
  marked inconclusive.
- A documented steady-state cadence and next portfolio decision exist.
- Any remaining OAuth or Studio dependency is recorded with an owner and next
  action.
