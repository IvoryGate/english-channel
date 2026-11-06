# Community Operations Recovery

## Goal

Restore daily Community posts and useful channel comments on every video,
including the historical catalogue, under the owner's 2026-10-18 approval.

## Scope

Seven Community posts weekly; one content-specific interaction per video;
continuous sequential historical backfill in video comment sections; substantive reply review within
24 hours; weekly audience-feedback review feeding video planning.

## System Boundaries

`docs/COMMUNITY_OPERATIONS.md`, `configs/channel/programming.json`, browser-only
YouTube operations, and ignored evidence in `workspace/community/`.

## Status

Owner: Codex. Started 2026-10-18. Initial audit found exactly one published
post, dated 2026-08-31, with zero comments and two likes. Recovery demand poll
published as `UgkxhCX_nWtIxVVY_gDJONLzjVdOTgV3kR2T` on 2026-10-18.
Ten public videos now have verified content-specific channel comments and
remote comment IDs in `workspace/community/operations.json`. Pin submissions
were made for all ten; two pin results were immediately verified and the
others remain explicitly unverified. Seven Community posts are remotely
scheduled for 2026-10-19 through 2026-10-25 at 12:00 Asia/Shanghai; their
IDs, exact text and verified times are in
`workspace/community/posts-2026-10-19.json`. Historical backfill remains open.
Heartbeat `automation-2` is active at 10:15 and 22:15 Asia/Shanghai for new
public video interactions, substantive replies, the remaining historical
catalogue, and replenishment of the daily Community post buffer. It must
honour real browser availability. On 2026-10-18 the owner explicitly removed
the agent-imposed daily ten-item limit and requested continuous backfill in
the actual video comment sections. Community posts are a separate operation.

## Plan

2026-10-18 continuation: 96 unique public videos now have verified interaction
comments, with remote comment IDs persisted across operations.json and the
comment-backfill ledgers through batch9. This includes all 38 current-week
videos public at the morning capture and further historical long videos and
Shorts. Pin attempts without authoritative confirmation remain unverified.
The channel Videos tab exposed 120 long videos in a partial DOM capture;
remaining captured long IDs are queued in video-backfill-pending-2026-10-18.json.
190 Shorts IDs are persisted in shorts-backfill-inventory-2026-10-18.json;
that inventory is partial. Full Shorts inventory and the rest of the catalogue remain open. Automation
now wakes every 15 minutes for continuous backfill, then returns to 10:15 and
22:15 daily maintenance after full remote coverage is verified. The 96-comment
count is not a claim that historical backfill is complete.

1. Record the policy and maintain an append-preserving remote-action ledger.
2. Backfill published video comment sections sequentially, without a daily cap.
3. Prepare and schedule daily Community posts; check existing scheduled posts
   before creating each one.
4. Run daily follow-up for new videos, due replies, and historical backfill.
5. Review after two weeks using observed participation, not invented targets.

## Validation

Validate configuration JSON; verify real remote post/comment links and record
only authoritative success. Check existing channel comments before writing.
No broad test suite needed for copy and operational records.

## Risks And Decisions

Do not duplicate existing interactions, mass-post generic promotion, or treat
missing metrics as zero. Pin only when the normal account UI permits it.
Do not bypass platform restrictions. Never claim a draft is scheduled.

## Archive Criteria

Historical backfill complete, daily operating cadence verified, and review
recorded. Until then keep the plan active and report exact counts.
