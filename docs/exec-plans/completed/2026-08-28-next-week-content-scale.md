# Next-Week Content Scale — 2026-08-31 to 2026-09-06

## Goal

Produce, verify, upload, and schedule the complete next-week portfolio: six Dialogue episodes, two `Persuasion` chapters, and fourteen Shorts. Improve script quality through an original, research-informed long-form method rather than imitating competitor wording.

## Authority

The channel owner authorized all items in this weekly plan to be uploaded and scheduled after release checks pass, without per-item confirmation. Failed checks, identity collisions, missing platform metadata, or a deviation from the listed schedule stop the affected item.

## Scope

- Publish existing, packaged Dialogue episode 021 for Series A/B/C as the standard-format inventory.
- Write and produce one new Deep Practice episode 022 for each Dialogue series.
- Produce `Persuasion` chapters 2 and 3 with the approved `mia-smooth` narrator profile.
- Produce Shorts 012–025 as discovery, practice, and long-form return paths.
- Schedule all 22 items in the 2026-08-31 weekly control plan.
- Add a durable long-form writing method and automated AI-style warning.

Excluded: copying or redistributing competitor/TED transcripts; changing already scheduled current-week items; publishing any unlisted replacement without a plan update.

## Status

- Owner: Codex primary agent.
- Last updated: 2026-08-30 Asia/Shanghai.
- State: complete; ready to archive with this branch checkpoint.
- Research, the long-form method, the 22-slot weekly plan, three episode-022 scripts, all long-form cover scenes, and fourteen Shorts manifests/thumbnails are complete.
- `Persuasion` chapters 2 and 3 are fully rendered, packaged, and independently checked: chapter 2 has 105 narration segments and chapter 3 has 155; both report `PASS` with zero warnings.
- All three Dialogue episode 022 packages are fully rendered, checked, and atomically exported: Daily Talk to `H:\Youtube\DailyTalk\episode22`, First Steps to `H:\Youtube\FirstSteps\episode22`, and Polished English to `H:\Youtube\PolishedEnglish\episode22`. The three approved release entries pass the API controller preflight.
- Shorts 012-025 are fully produced and packaged. All fourteen have synchronized manifests, final audio, 1080x1920 H.264/AAC video, dedicated discovery covers, and passing content/audio/video/thumbnail QC with zero preflight warnings. Representative covers were visually sampled. The batch status reports all fourteen as `packaged`.
- The shared API-first release controller owns private upload, metadata, thumbnail, captions, playlist, processing-state checks, scheduling, verification, identity collision protection, retry state, and exact cross-checking against the approved weekly plan. Studio remains the fallback for failures and unsupported fields.
- All 22 products have real remote video IDs in `configs/channel/youtube-release-2026-08-31.json`, pass the local release preflight, and were visibly verified in Studio as scheduled at the approved times. The fourteen Shorts occupy the daily 12:30/18:00 grid; Dialogue and Classics occupy their documented long-form slots.
- Dialogue episode 022 received three new, image-model-generated, text-integrated anime thumbnails and is scheduled for September 3-5 at 20:00. `Persuasion` chapters 1-3 received a coordinated bright illustrated thumbnail set; chapter 1 was replaced in place and chapters 2-3 retained their approved schedules.
- The owner accepted the already-uploaded Shorts cycle without visual rework but rejected its repeated, dark background strategy for future cycles.
- The next Shorts cycle is now blocked on a 30-thumbnail high-view visual research capture, unique background art for every item, US women 25-44 audience evidence, automated luma/saturation gates, and phone-size contact-sheet review. The current cycle's exception is exact and cannot carry forward.

## Research evidence

- Local archived corpus: 85 usable public-caption transcripts from long-form English-learning competitors. Analysis is stored under `workspace/dialogue_podcast_research/youtube_corpus/analysis/`; no competitor video or audio was downloaded.
- Primary TED examples inspected structurally: Tim Urban, Brené Brown, Celeste Headlee, Julian Treasure, and Simon Sinek.
- Official method reference: TEDx Speaker Guide.

## Content architecture

The week uses three connected clusters:

1. **Keep the conversation alive** — First Steps 021/022 and recovery-line Shorts.
2. **Tell a story with a point** — Daily Talk 021/022 and story-shape Shorts.
3. **Be fluent and easy to follow** — Polished English 021/022 and conversational-handoff Shorts.

The Classics line remains a coherent serial release and contributes two narrative-listening anchors.

## Execution plan

1. Freeze research conclusions into the long-form method and quality validator.
2. Lock all 22 content identities and release slots.
3. Validate existing 021 packages without modifying their media fingerprints.
4. Write and preflight the three original 022 Deep Practice scripts.
5. Produce audiobook chapters 2–3 and Dialogue 022 media with serialized GPU access.
6. Produce Shorts 012–025 and bind each to the best available related long video.
7. Run script, audio, video, subtitle, thumbnail, metadata, identity, and schedule checks.
8. Upload private and schedule exact approved times through the API controller; use Studio only for unsupported fields, visible policy checks, or API failure.
9. Reconcile every YouTube video ID and final state into the weekly control plane.
10. Hand off the next-cycle visual research and originality work to
    `docs/exec-plans/active/2026-08-30-shorts-visual-quality.md`; it does not
    reopen the already-uploaded current cycle.

## Validation

- Focused script-validator and research tests pass.
- Each new script passes its profile and has no unresolved AI-style warning.
- All media packages pass product-specific QC.
- No release identity or rolling-capacity conflict exists.
- Every scheduled item has title, description footer, playlist/related-video choice, subtitles where applicable, thumbnail, privacy state, and verified local artifact fingerprint.

## Risks and controls

- GPU-heavy renders are serialized; CPU/script/image tasks may proceed while a render is active.
- Four-upload Monday and Thursday slots may create audience-notification fatigue. The 18:00 Short is a discovery slot and should not displace the 20:00 long-form notification.
- Existing 021 packages predate the new editorial warning. Their wording is not silently changed because that would invalidate rendered media; lessons apply to all 022 scripts.
- Live caption refresh can trigger YouTube bot checks. Archived caption evidence is sufficient for the method and refresh attempts remain metadata/caption-only and low-rate.
- A signed-in Studio tab is not itself remote mutation authority. Upload proceeds only through a verified browser connection or approved YouTube OAuth provider, and every resulting video ID and schedule state must be reconciled before this plan can be archived.

## Archive criteria

All 22 items have passing local packages, real remote video IDs, verified schedule states, and a reconciled weekly plan; the branch is committed and pushed for audit.

The media, remote-ID, schedule, and reconciliation conditions are satisfied.
This plan is archived in the same checkpoint that commits and pushes the final
quality contract and release manifest.
