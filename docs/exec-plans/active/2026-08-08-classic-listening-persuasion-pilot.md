# Classic Listening Persuasion Automation Pilot

## Goal

Revive the Classic Listening audiobook line with a reusable, observable, resume-safe production controller, using Jane Austen's `Persuasion` chapter 1 as the first complete pilot. The pilot must begin with a recorded public-domain source, preserve exact text traceability, render resumable segment audio, enforce strict quality gates, and finish as a verified 2K upload package.

The pilot is deliberately one chapter. Once its voice, segmentation, QC thresholds, visual identity, and package contract are approved, a follow-up plan will roll the same controller across chapters 2-24 without redesigning the pipeline.

## Scope

Included:

- Register the downloaded Project Gutenberg English EPUB for `Persuasion` by stable book slug and SHA-256.
- Add a tracked, book-agnostic Classic Listening production configuration contract.
- Extract exactly 24 chapters while excluding the title page, contents, and Project Gutenberg license.
- Preserve source text, normalized spoken text, segment manifests, voice/reference provenance, render settings, and artifact fingerprints.
- Use single-voice semantic segmentation: narration and quoted dialogue remain separate performance units, but every segment is rendered by the same Riley-based Classic Listening narrator.
- Add one public controller with `ingest`, `preflight`, `render-audio`, `qc`, `package`, `status`, and `resume` commands.
- Persist run state, heartbeat, current phase, chapter state, input fingerprints, failures, and retry details.
- Render chapter 1 with resumable per-segment VoxCPM2 audio using the Series B female Riley reference and a separately approved Classic Listening narrator preview.
- Run structural, acoustic, and ASR-assisted QC; require explicit acceptance or repair for content anomalies.
- Produce a publication master, subtitles, YouTube metadata, a native 2K thumbnail in the established `Pride and Prejudice` cinematic-classic style, a separate no-text video background, Classic Listening-specific 2K intro/outro clips containing the existing ELR avatar, and a verified 2560x1440 MP4.
- Stage the upload package under an `.incomplete` directory and promote it atomically only after verification.
- Add focused tests and update code, docs, and the repository-local audiobook Skill together.

Non-goals:

- Rendering chapters 2-24 in this first branch.
- Automatically uploading to or scheduling on YouTube.
- Reprocessing the already-published `Pride and Prejudice` videos.
- Adding a web UI or extending the current API/BullMQ job schema.
- Supporting translated, abridged, annotated, or modern copyrighted editions.
- Automatically accepting uncertain text segmentation or audio-content anomalies.
- Reusing embedded EPUB images, commercial audiobook recordings, film stills, or modern cover art.

## System Boundaries

Expected tracked code and configuration:

- `scripts/classics.py` — public controller.
- `scripts/classics_production.py` — canonical paths, preflight, phase construction, and verification.
- `scripts/classics_run_state.py` — atomic state and heartbeat persistence.
- `apps/worker-py/worker/classics/` — source ingestion, config, artifact paths, manifests, fingerprints, rendering adapters, and QC helpers.
- `apps/worker-py/tests/test_classics_*.py` — focused unit and integration tests.
- `configs/classics/persuasion.json` — tracked source, voice, character, render, mastering, and packaging contract.
- `src/brand/classic-listening-intro.tsx`, `src/brand/classic-listening-outro.tsx`, and Remotion registration — deterministic Classic Listening branding compositions.
- `assets/branding/classics/` — approved generated classic background sources and reusable visual tokens.
- `assets/branding/video/classic-listening-intro.mp4` and `classic-listening-outro.mp4` — verified 2K branding clips.
- `docs/classics/PIPELINE.md` — operator workflow and artifact contract.
- `.cursor/skills/audiobook-chapter-tts/` — compatibility wrappers and updated instructions pointing to the canonical controller.
- `docs/TTS_PIPELINE.md`, `README.md`, and relevant show/visual documentation.

Ignored runtime inputs and outputs:

- `books/public-domain/persuasion-jane-austen-gutenberg-105.epub`.
- `workspace/classics/persuasion/`.
- `logs/classics_runs/`.
- Configurable export root, expected to use the existing `H:\Youtube` production convention only after the required filesystem permission is available.

Existing capabilities to reuse:

- VoxCPM2 local runtime and model paths.
- Per-segment rendering and selective regeneration concepts from `audiobook-chapter-tts`.
- ELR run-state, heartbeat, GPU-lock, detached-launch, resume, mastering, 2K verification, and atomic-export patterns.
- Existing subtitle, waveform, cover normalization, and media composition primitives where their interfaces are genuinely book-agnostic.

## Status

- Owner: Codex primary agent.
- Last updated: 2026-08-24.
- State: source code is protected at `8d548d0` and is being semantically ported
  onto the accepted Classic Listening foundation. The chapter 1 V2 review
  package exists, but chapters 2-3 and all publication remain blocked until a
  clean narrator/provider passes the tracked acceptance policy.
- Intake branch: `codex/persuasion-pilot-intake`.
- Protected source: `codex/classics-persuasion-pilot`; its 33 media files are
  retained untracked and fingerprinted in
  `docs/classics/PERSUASION_MEDIA_INVENTORY.md`.

### Progress Log — 2026-08-08

- Created the isolated `codex/classics-persuasion-pilot` worktree from current `origin/main`; the unrelated dirty ELR branch remains untouched.
- Added the versioned `Persuasion` config, canonical Classic Listening paths, atomic state storage, EPUB spine ingestion, exact source coverage segmentation, preflight checks, and the public `ingest`, `preflight`, `preview-voice`, and `status` commands.
- Verified the registered Project Gutenberg EPUB and extracted exactly 24 chapters / 83,527 words. Chapter 24 excludes the embedded Gutenberg license. Chapter 1 contains 2,596 words and 72 stable single-voice segments with 100% normalized ordered coverage.
- Registered `classic-listening-riley-narrator` against the Series B Riley clean reference and verified the reference SHA-256. Added a low-peak-memory VoxCPM2 loading path after reproducing the upstream loader's host-memory spike.
- Rejected the first generated sample after ASR proved that VoxCPM2 spoke the parenthetical style-control text. Changed synthesis to source-only text, regenerated the sample, and verified the ASR result exactly matches the selected Austen sentence.
- Generated text-free intro/outro and chapter-cover backgrounds with ImageGen. Added deterministic 2560x1440 Remotion compositions that preserve the existing ELR avatar and exact typography. Rendered an 8.04-second 2K intro, an 8.04-second 2K outro, and a 2K chapter 1 cover candidate.
- Focused Python tests pass (`12 passed`). Media probes confirm native 2560x1440 H.264 outputs and 2560x1440 PNG storyboards.
- Current gate: user approval of the Riley voice direction and the classic visual direction. Full chapter rendering remains intentionally blocked until approval.
- Release tooling note: the Remotion source and local render are working, but `package-lock.json` has not yet been refreshed because the required network approval was rejected by the current Codex usage limit. Do not commit or release with the package manifest/lock mismatch unresolved.
- Visual review feedback established that historical Classic Listening viewers are primarily women aged 55 and over. The first dark-library treatment was rejected as too simple, too empty through the middle/lower frame, and silent. The bright honey/ivory/blush backgrounds and female-led chapter cover remain valid, but the card-based branding treatment and synthetic music-only audio were also rejected. Version 3 uses VoxCPM2-generated Riley speech, a hero-scale ELR avatar, voice-timed kinetic typography, drawn ink paths, an opening-book animation, and stable large-type reading beats. The earlier video candidates remain versioned and are not promoted as approved assets.
- Version 3 voice and render verification is complete. VoxCPM2 generated a 9.06-second intro and 8.74-second outro from the registered Series B Riley reference. The final 2560x1440 H.264/AAC candidates are 10.048 and 11.051 seconds, with integrated speech loudness of -16.3 and -15.7 LUFS and true peaks below -2.4 dBTP. Research inputs were the existing ELR spoken-brand clips, W3C older-user guidance on readable presentation and sufficient time, Adobe kinetic-typography guidance on voice-led text motion, and YouTube's 5-20-second end-screen timing and staged-element guidance.
- Version 3 was rejected for an electronic voice artifact and an unattractive opening-book device. Version 4 regenerates both spoken clips from the Riley reference at the project's documented corrective setting of `cfgValue: 2.15` and 12 inference steps, rather than attempting to hide the artifact with aggressive filtering. ASR recovered the intended wording from both new clips, and high-frequency energy above 8 kHz fell most clearly on the outro. The final 2560x1440 H.264/AAC candidates remain 10.048 and 11.051 seconds, measure -16.3 and -15.3 LUFS, and peak below -2.4 dBTP. The book drawing is removed completely and replaced by a synchronized, text-led action cue with a drawn play symbol: `BEGIN CHAPTER ONE` in the intro and `SUBSCRIBE AND CONTINUE` in the outro. Version 4 remains a listening-approval candidate because objective checks cannot replace subjective review of voice texture.
- Listening review accepted the version 4 intro but found a small residual electronic quality in the outro. Two outro-only regenerations were compared. Candidate A (`cfgValue: 2.0`, 14 steps) increased high-frequency energy and was rejected. Candidate B (`cfgValue: 1.9`, 16 steps) preserved the complete ASR transcript with lower model guidance and was promoted to the version 5 outro candidate. The intro remains untouched. The rebuilt 2560x1440 H.264/AAC outro is 11.051 seconds, measures -15.7 LUFS with a -2.4 dBTP true peak, and retains the approved action-cue visuals.
- The version 5 branding direction is approved for production. The rollout scope is now chapters 1-3, each delivered as a complete YouTube upload package rather than audio-only output. The controller now supports full chapter audio rendering, chapter ranges with a shared loaded model, structural/acoustic QC, mastering, SRT/ASS generation, chapter-specific intro/outro speech, deterministic 2K thumbnails, body-video rendering, final composition, verification, and export metadata. Chapters 2 and 3 received new text-free historical scenes through ImageGen; required title copy remains deterministic. Narration is being rendered serially on the GPU, with completed segment WAVs retained for resume.

### Quality Revision — 2026-08-17

- User review blocked publication of the V1 chapter packages for three reasons: audible electronic/current-like voice texture, subtitles that do not track the spoken audio closely enough, and a single static body image that makes long chapters feel inert.
- The next approval artifact is a versioned, approximately two-minute chapter 1 V2 proof. It must include representative narration, a long subtitle split, three plot-relevant historical scenes, restrained camera motion, and sentence-boundary crossfades. Existing V1 exports remain intact until the proof is approved.
- Voice correction begins with small Riley A/B samples rather than immediately regenerating all three chapters. Candidate settings are compared for content recovery, high-frequency texture, long-sentence stability, loudness, and listening quality. A gentle post-process may be evaluated only after generation settings are selected.
- Subtitle timing is derived from actual per-word audio timestamps. Normal cues retain the complete spoken source segment; only text that exceeds the two-line display limit is split, at punctuation or semantic boundaries using real word times. Burned body subtitles start at body time zero, while exported YouTube SRT files add the measured intro offset.
- Each chapter receives a tracked scene manifest keyed to narration segment ranges. Target density is 8-12 story beats per chapter, with scene changes only at sentence or paragraph boundaries, 1.2-1.8 second crossfades, and restrained 2-4 percent pan/zoom motion.
- ImageGen remains text-free and background-only. Distinct scene prompts are dispatched as independent built-in image jobs in bounded parallel waves, then checked for period accuracy, character/style continuity, warm older-audience lighting, subtitle-safe composition, malformed anatomy, accidental text, and watermarks before project adoption.
- After V2 proof approval, chapters 1-3 will be regenerated and repackaged with new versioned outputs. Release gates include structural QC PASS, ASR content review, subtitle coverage and sync sampling, visual transition inspection, native 2560x1440 media probes, and complete YouTube package verification.
- The chapter 1 V2 proof is now built and awaits listening approval. It uses isolated Riley candidate B (`cfgValue: 1.9`, 16 steps) across segments 001-005, 21 source-only cues aligned from word timestamps, and three ImageGen historical scenes with 1.5-second crossfades plus restrained 2-4 percent motion. The 118.97-second proof probes as native 2560x1440 H.264 with 48 kHz AAC; V1 chapter files and exports were not replaced.
- The approved proof settings have now been extended across the full chapter 1 review package. Candidate B rendered all 106 expected audio segments with structural QC `PASS`; the mastered body is 1178.9 seconds at 48 kHz, with a -1.499 dBFS peak and no missing or extra segments. Word alignment produced 247 source-only subtitle cues with mean ASR similarity 0.9818. Eleven plot-specific warm Regency scenes cover the chapter with 1.5-second crossfades and restrained motion; eight new text-free backgrounds were generated through built-in ImageGen and recorded in the tracked scene manifest.
- The final review video is exactly 20:00 at native 2560x1440 with 48 kHz stereo AAC. A timestamp-reset filter concat now fully re-encodes the intro, body, and outro to prevent the H.264 timestamp/index corruption found during the first final-package inspection. Post-repair QA sampled the intro, every body-scene region, and the outro; an automated full-program scan found no black interval lasting one second or longer. The complete YouTube package is exported for review, not uploaded or marked published.
- A follow-up investigation found that the audible artifact is speech-coupled high-frequency texture rather than removable stationary hum. A native 48 kHz Riley candidate was prepared, but VoxCPM2 resamples reference input to its 16 kHz encoder rate, so the planned reference-rate A/B was stopped before producing or promoting any comparison artifact. Further release work is blocked on a clean TTS provider/model passing blind listening review, not on additional denoise or reference upsampling.
- The reusable product, publishing, experiment, analytics, and retrospective contract is now defined in `docs/classics/AUTONOMOUS_OPERATING_MODEL.md`; implementation is tracked separately in `docs/exec-plans/active/2026-08-17-classic-listening-autonomous-operations.md`.

## Audited Input

- Title: `Persuasion`.
- Author: Jane Austen, 1775-1817.
- Original publication: 1817.
- Source: Project Gutenberg eBook 105, English.
- Local source: `books/public-domain/persuasion-jane-austen-gutenberg-105.epub`.
- SHA-256: `f848c20f7445a04cf56465c9325a06dc44480bcaa3bf464363239ea61e54f477`.
- EPUB MIME: `application/epub+zip`.
- EPUB spine items: 27.
- Expected content: title page, contents, 24 chapter documents.
- Approximate spine words: 87,255 before removal of navigation and Project Gutenberg boilerplate.
- Long-chapter stress case: chapter 21, approximately 7,035 words before final ingestion normalization.
- Known ingestion hazard: chapter 24 shares its document with the full Project Gutenberg license; extraction must stop before the license marker.

## Product And Technical Decisions

1. `Persuasion` is the first new book and chapter 1 is the acceptance pilot.
2. Source rights are a production gate. The config records the source page, eBook number, author dates, original-publication year, local path, SHA-256, and Project Gutenberg status. This record covers the source text only.
3. The controller accepts a stable book slug and chapter selection, not arbitrary workspace paths. Canonical paths are derived from tracked config.
4. Production source of truth must live in tracked code roots. The `.cursor` Skill remains an operator/compatibility layer, not the only production implementation.
5. Source fidelity uses two fields when pronunciation normalization is necessary:
   - `displayText`: exact normalized edition text shown in subtitles.
   - `spokenText`: TTS-safe text with traceable pronunciation substitutions.
   Every substitution must be recorded; silent rewriting is forbidden.
6. Concatenated segment `displayText` must cover 100% of normalized chapter source in order. No dropped or invented prose is allowed.
7. This production is single-voice. Every narration and dialogue segment uses the Series B female Riley reference at `assets/voices/series_b/riley_reference_clean.wav` (SHA-256 `9330f8278c50fae1a7142953b73cbec3bd89f7fafe61d76ecb24681985b4b189`). Optional character labels support traceability and subtle delivery cues only; they never route to a different voice. The old alternating-speaker fallback is forbidden.
8. Add a dedicated `classic-listening-riley-narrator` profile that reuses Riley's timbre but replaces the Series B teaching prompt with restrained, mature, reflective literary delivery. Dialogue may receive light differential expression, but no character impersonation or voice change.
9. The Riley reference requires a provenance/license record and a user-approved Classic Listening preview before chapter rendering. Prior use in Series B does not replace the audiobook approval record.
10. Infrastructure failures and missing files may retry automatically. Content anomalies, ASR mismatches, and voice-quality issues enter a review queue and are not silently overwritten.
11. GPU rendering is serial and protected by the existing production lock. Source preparation, metadata, and approved visual generation may run in parallel.
12. Formal audio targets are 48 kHz mono, `-16 LUFS` integrated, and no higher than `-1.5 dBTP`, with before/after measurements persisted. Pilot results may tighten denoise settings but may not weaken traceability.
13. Formal video and thumbnail outputs are native 2560x1440. The thumbnail and subtitle-friendly no-text background are separate approved assets.
14. Classic Listening receives its own intro/outro rather than reusing the conversation-oriented clips. Both retain the exact existing ELR avatar (`assets/branding/english_listening_room_avatar_v2.png`) as the brand anchor. AI image generation may create the background layer only; the avatar, logo, typography, and animation are composed deterministically so the face and text cannot drift.
15. Intro/outro backgrounds use a warmer classic-literature language: Regency library or drawing room, parchment and engraved ornament, candlelight, aged paper, deep brown/burgundy/antique-gold accents, and restrained motion. The existing lines `one conversation at a time` and other podcast-specific copy are not used. Candidate copy is `Classic Listening`, `Persuasion`, `By Jane Austen` for the intro and `Continue the story` / `Subscribe for the next chapter` for the outro.
16. Chapter covers continue the established `Pride and Prejudice` visual family: cinematic historically grounded Regency scene, warm dramatic light, emotional chapter hook, large high-contrast white serif typography, book title, chapter number, `FULL AUDIOBOOK`, and author line. Do not use the A/B/C comic podcast layout. Generate the scene without text, then add exact typography deterministically to avoid misspellings.
17. YouTube upload remains a human action. The pipeline ends at a verified package plus a publication ledger entry in `exported` state.
18. The primary historical audience for this line is women aged 55 and over. Visuals therefore prioritize brightness, warmth, legibility, emotional reassurance, familiar domestic detail, and welcoming female-centered imagery. Night scenes remain honey-lit and cozy rather than dark; middle and lower thirds remain intentionally furnished. Branding clips require coordinated audio and more than a single static title motion.
19. Branding audio follows the established show workflow: VoxCPM2 synthesizes dedicated spoken intros and outros using the same Riley reference as the audiobook narrator. Instrumental-only branding audio is not a substitute. The motion language is voice-led kinetic typography rather than a collection of presentation cards: each spoken phrase triggers a text reveal, ink stroke, title assembly, or page turn. The exact ELR avatar remains a hero element at roughly half the frame height, and emoji are forbidden. Older-viewer guidance requires large high-contrast type, limited simultaneous messages, stable reading holds, and restrained camera movement. The outro keeps a stable final state long enough for a YouTube end-screen overlay.
20. Branding voice generation may override the chapter narrator's synthesis parameters when a documented quality correction is needed. For version 4, branding uses `cfgValue: 2.15` and 12 inference steps while preserving the registered Riley reference and persisting the override in the generation trace. The book-page motif is prohibited; lower-third motion instead carries an explicit, readable action cue synchronized to the voice.

## Canonical Runtime Layout

```text
workspace/classics/persuasion/
├── 000_book.inventory.json
├── 000_book.production.json
└── chapter_001/
    ├── 000_chapter_001.source.txt
    ├── 000_chapter_001.segments.json
    ├── audio/
    │   ├── segments/
    │   │   ├── 001_narrator.wav
    │   │   └── ...
    │   ├── 000_chapter_001.raw.wav
    │   └── 000_chapter_001.master.wav
    ├── subtitles/
    │   ├── 000_chapter_001.srt
    │   └── 000_chapter_001.karaoke.ass
    ├── video/
    │   ├── 000_chapter_001.cover_source_16x9.png
    │   ├── 000_chapter_001.video_bg_source_16x9.png
    │   ├── 000_chapter_001.thumbnail.png
    │   └── 000_chapter_001.mp4
    └── reports/
        ├── 000_chapter_001.run.json
        ├── 000_chapter_001.qc.json
        ├── 000_chapter_001.master_report.json
        ├── 000_chapter_001.youtube.json
        └── 000_chapter_001.verification.json
```

## Public Controller Contract

Expected operator surface:

```powershell
$py = ".\.conda-env\python.exe"
& $py scripts/classics.py ingest --book persuasion
& $py scripts/classics.py preflight --book persuasion --chapter 1
& $py scripts/classics.py render-brand-voice --book persuasion
& $py scripts/classics.py render-audio --book persuasion --chapter 1 --detach --visible-window
& $py scripts/classics.py qc --book persuasion --chapter 1
& $py scripts/classics.py package --book persuasion --chapter 1
& $py scripts/classics.py status --book persuasion
& $py scripts/classics.py resume --book persuasion --chapter 1
```

The later rollout must support chapter ranges without changing semantics:

```powershell
& $py scripts/classics.py produce --book persuasion --chapters 2-24
```

## Human Approval Gates

1. **Source gate** — confirm the registered EPUB, edition, language, SHA-256, public-domain basis, and chapter inventory.
2. **Segmentation gate** — approve chapter 1 source coverage, narration/dialogue boundaries, pronunciation substitutions, and the restrained single-narrator delivery style. Optional character-label uncertainty does not select another voice.
3. **Voice gate** — approve a Riley-based Classic Listening preview containing narration, a female dialogue turn, a male dialogue turn read in the same timbre, a short fragile line, and one longer sentence.
4. **Audio QC gate** — listen to and accept or repair every flagged segment; strict QC must then pass or record an explicit accepted exception with reason.
5. **Visual gate** — approve the Riley-avatar Classic Listening intro/outro storyboards and 2K renders, the cinematic Regency chapter thumbnail, and the separate no-text body background.
6. **Final package gate** — approve the verified MP4, master WAV, subtitles, title, description, timestamps, and export directory before manual upload.

## Plan

### Milestone 1: Isolated branch and contracts

- Preserve the unrelated dirty ELR work and create the target branch from latest `main`.
- Add the active plan to that branch without carrying unrelated changes.
- Define versioned schemas for book config, book inventory, segment manifests, run state, QC, and verification.
- Add canonical path helpers; reject paths that escape the repository workspace or configured export root.
- Add tests for schema errors, path derivation, source hashes, and atomic state writes.

### Milestone 2: EPUB ingestion and source fidelity

- Parse the OPF manifest/spine instead of searching a flattened EPUB with chapter regexes.
- Validate title, author, language, MIME, SHA-256, and expected chapter count.
- Extract chapter documents 1-24 in spine order.
- Remove navigation, headings not intended for narration, and Project Gutenberg boilerplate without touching novel text.
- Persist an inventory containing per-chapter source hashes and word counts.
- Add fixtures/tests for the shared chapter-24/license boundary and for rejection of unexpected source changes.

### Milestone 3: Generic single-voice segmentation and review

- Implement quote-aware semantic segmentation that keeps narration and dialogue turns distinct.
- Add an optional tracked `Persuasion` character registry for traceability and restrained delivery hints, not voice routing.
- Default uncertain quoted speech to the same Riley narrator with a neutral literary-dialogue cue; never guess an alternating character voice.
- Enforce exact normalized source coverage and stable segment IDs.
- Validate short-fragment policies and cap controls before GPU work.
- Prepare and approve the chapter 1 manifest; block rendering on text-coverage, segmentation, or pronunciation-review failures rather than optional speaker-label uncertainty.

### Milestone 4: Observable controller and resume behavior

- Implement the public commands and canonical phase graph.
- Persist book-level and chapter-level states such as `INGESTED`, `SEGMENT_REVIEW`, `VOICE_REVIEW`, `AUDIO_RENDER`, `QC_REVIEW`, `PACK_READY`, `VERIFIED`, `EXPORTED`, and `FAILED`.
- Record PID, heartbeat, active command, log, start/finish times, fingerprints, failure reason, and retry count.
- Reuse the global GPU production lock and serial rendering behavior.
- Resume only missing or fingerprint-stale artifacts; never treat mere file existence as completion.
- Add dry-run, interruption, stale-PID, retry, and resume tests.

### Milestone 5: Narrator profile and chapter 1 audio pilot

- Define `classic-listening-riley-narrator` using the Series B Riley clean reference, with restrained, mature, reflective Regency delivery and one consistent timbre across narration and dialogue.
- Record the Riley reference path/hash/provenance and confirm it is usable for this production.
- Generate the voice-gate preview and pause for approval.
- Render chapter 1 segments to partial files and atomically promote each successful WAV.
- Compose the raw chapter only when every expected segment exists, fingerprints match, and no orphan segment files remain.
- Persist the exact model, device, reference, controls, settings, segment durations, and input hashes.

### Milestone 6: Strict QC, repair, and mastering

- Run structural checks for source coverage, missing/extra files, compose drift, sample rate, channels, duration, silence, clipping, and fingerprints.
- Run ASR on suspicious segments and calibrate the final match thresholds from the approved pilot; persist transcripts and similarity evidence.
- Produce a concise review queue with source text, ASR text, flags, and recommended action.
- Regenerate or trim only explicitly selected segments, then recompose and rerun strict QC.
- Master approved audio to the formal loudness/true-peak targets and write a before/after report.
- Do not allow mastering to conceal speech defects that require rerendering.

### Milestone 7: Subtitles, visual package, and verified export

- Generate SRT and karaoke timing from finalized segment/master timing without rewriting display text.
- Generate chapter 1 title candidates, summary, chapter markers, description, tags, and visual prompts from approved source/manifests.
- Enforce the 100-character YouTube title limit and timestamp validity.
- Use image generation to create text-free classic-literature background candidates for a dedicated Classic Listening intro/outro. Preserve the existing ELR avatar exactly and add it, the logo, and copy in the deterministic Remotion composition.
- Render and approve new 2560x1440 Classic Listening intro/outro clips. Do not upscale or reuse the current 1920x1080 conversation clips.
- Generate a text-free cinematic Regency scene for the chapter 1 cover, using the established `Pride and Prejudice` drama-hook composition as the reference family; overlay exact serif typography in code.
- Produce and approve the native 2K thumbnail and a separate calmer no-text body background with clean subtitle space.
- Compose a 2560x1440 MP4 as `Classic Listening intro -> chapter body -> Classic Listening outro`, measure the real intro duration, and shift YouTube chapter timestamps by that exact duration.
- Stage all required upload files under `.incomplete`, validate them, then atomically promote the directory.
- Write a verification report and an `exported` publication-ledger record; do not claim `published` without a real YouTube ID/URL.

### Milestone 8: Documentation and release gates

- Document the controller, approval gates, recovery flow, artifact layout, public-domain provenance, and troubleshooting.
- Update the audiobook Skill to use the canonical controller and remove broken references to the missing repository monitor.
- Add or repair the missing mastering documentation referenced by existing show docs.
- Run focused tests, the full Python suite, encoding/docs/architecture checks, lint, and build.
- Complete the chapter 1 dry-run and real pilot verification.
- Archive this plan only after the code, tests, docs, approved pilot package, and verification evidence all satisfy the criteria below.

## Validation

Repository gates:

- `npm run check:encoding`
- `npm run check:docs`
- `npm run check:architecture`
- `npm run lint`
- `npm test`
- Focused `apps/worker-py/tests/test_classics_*.py` suite.

Pilot functional gates:

- Source SHA-256 matches the registered Gutenberg EPUB.
- EPUB metadata is English `Persuasion` by Jane Austen.
- Inventory contains exactly 24 chapters and excludes the Gutenberg license.
- Chapter 1 segment display text has 100% ordered normalized-source coverage.
- Every segment resolves to the single `classic-listening-riley-narrator` profile; no multi-voice routing is present.
- Riley-based Classic Listening voice preview has explicit approval and reference provenance/hash is recorded.
- Every expected segment WAV exists exactly once; no orphan files are present.
- Run and artifact fingerprints match current source, manifest, reference, model, and settings.
- Strict QC has no unresolved flags or records an explicitly approved exception.
- Master audio measures near `-16 LUFS` and does not exceed `-1.5 dBTP`.
- Subtitle text matches approved display text and timings fit the final program.
- Classic Listening intro, outro, thumbnail, background, and MP4 are 2560x1440.
- Intro/outro contain the exact existing ELR avatar and no podcast/conversation-specific copy.
- Cover matches the approved cinematic Regency/large-serif Classic Listening reference and does not use a dialogue-podcast comic layout.
- MP4 has valid video/audio streams and positive duration.
- Title is at most 100 characters; timestamps are monotonic and within duration.
- Export promotion occurs only after complete-package verification.
- `status` and `resume` work after a simulated interruption without rerendering valid segments.

## Risks And Decisions

- The current book scripts are specialized to `Pride and Prejudice`; copying their alternating-speaker fallback into `Persuasion` would silently invent character routing. The new single-voice contract removes that dependency while preserving semantic dialogue boundaries.
- Project Gutenberg marks the source public domain in the USA but instructs readers outside the USA to check local law. The selected author/publication dates are deliberately conservative, and the production record must retain that evidence.
- Chapter 24 contains the Gutenberg license in the same spine document. Marker-based removal must be tested and source coverage must be computed after removal.
- The existing `Pride and Prejudice` runtime data contains stale/orphan artifacts, demonstrating that file-exists resume logic is insufficient. Fingerprints and exact expected-file sets are required.
- The existing API job model cannot represent book ingestion, segment review, approval gates, or packaging. API integration is deferred until the local production contract is stable.
- Existing mastering documentation is referenced but missing. The pilot must establish one durable source of truth rather than relying only on tool defaults.
- Visual generation is not allowed to weaken the final pack gate. Audio may render while approved visuals are prepared, but package/export requires both assets.
- The existing ELR intro/outro are 1920x1080 and say `one conversation at a time`; they remain valid for A/B/C but are not valid Classic Listening assets. The new clips must be rendered natively at 2K and keep the existing avatar unchanged.
- Image generation may vary historical backgrounds, but it must not regenerate the ELR avatar or bake required text. Deterministic composition owns identity and typography.
- Export to `H:\Youtube` is outside the repository workspace and may require explicit filesystem approval during implementation.
- Runtime artifacts, EPUBs, model weights, and final media remain ignored and must not be committed.

## Archive Criteria

Archive this plan to `docs/exec-plans/completed/` in the same finishing PR only when:

- The public controller and documented command surface agree.
- The reusable config, ingestion, state, fingerprint, and verification contracts are tested.
- `Persuasion` chapter 1 has passed every required human and automated gate.
- A complete verified 2K upload package exists in the approved export location.
- No code path depends solely on the broken/missing legacy monitor entry point.
- Code, tests, docs, Skill instructions, and quality gates pass together.
- The follow-up scope for chapters 2-24 is recorded without leaving unfinished pilot work hidden in this plan.

## Follow-Up Plan

After the pilot is approved, create a separate short-lived plan/branch for `Persuasion` chapters 2-24. That rollout should batch ingestion and manifest review, serialize GPU rendering, parallelize non-GPU metadata/visual preparation, enforce per-chapter QC and atomic export, and maintain a publication ledger with real YouTube IDs and URLs after manual upload.
