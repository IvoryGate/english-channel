# Legacy Pipeline Parity Evidence

## Purpose

This record accounts for every path changed by three pre-unification branches.
It prevents a branch from being marked superseded only because a later tree
looks similar. Comparisons use each branch's merge base `2a22230` and the local
unified tree descended from `64415a6`.

Disposition terms:

- `identical`: the source blob was already present unchanged.
- `evolved`: the current implementation contains a later contract or behavior;
  source tests and diffs were reviewed before retaining current.
- `ported`: a missing contract/test was restored or semantically recreated.
- `not ported`: historical plan or unsafe/obsolete entry point retained only in
  Git history, with a reason below.

## Research And Topic Selection

Source: `feat/youtube-research-topic-selection` at `379ac46`.

Original path count: 43 — 19 identical, 2 evolved, and 22 absent before this
audit.

### Identical: 19

- All six files under `.cursor/skills/youtube-corpus-analysis/`.
- `.cursor/skills/youtube-podcast-research/{CORPUS,SKILL,WORKFLOW}.md`.
- Five research wrapper scripts: `_bootstrap.py`,
  `collect_youtube_corpus.py`, `discover_youtube_podcasts.py`,
  `score_trending_videos.py`, and `select_top_videos.py`.
- `worker/youtube_podcast_research/{__init__,bootstrap,browser,rate_limit}.py`.
- `scripts/run_research_refresh.py`.

### Evolved: 2

- `.cursor/skills/youtube-podcast-research/CHANNELS.md`.
- `apps/worker-py/worker/youtube_podcast_research/workspace.py`.

The two current files agree and add `englishgoalpodcast`; retaining the older
pair would silently remove a discovery source.

### Ported: 8 source paths

- Read-only browser research boundary:
  `.cursor/skills/youtube-browser-automation/{SKILL,WORKFLOW}.md` and
  `scripts/{_bootstrap,youtube_search}.py`. The docs were rewritten to forbid
  login and account mutation.
- Research regression tests:
  `test_dialogue_podcast_research.py` and
  `test_youtube_corpus_analysis.py`.
- Evidence documents: `docs/shows/competitor_script_analysis.md` and
  `docs/shows/youtube_playlists.md`. Playlist claims are explicitly marked as
  an unreconciled historical proposal.

### Not ported: 14

The historical execution plan
`2026-07-11-youtube-trending-research-playwright.md` is superseded by the
current unification and parity plans.

The following 13 browser/account scripts were not ported:

- `_probe_studio_branding.py`
- `analyze_own_channel.py`
- `close_browser_profile.ps1`
- `enhance_channel_avatar.py`
- `fetch_channel_avatar.py`
- `open_channel_branding.ps1`
- `open_youtube_login.ps1`
- `prepare_channel_avatar.py`
- `render_avatar_rim_text.py`
- `save_browser_session.py`
- `update_channel_avatar.py`
- `verify_studio_avatar.py`
- `verify_youtube_session.py`

They mix session persistence, local branding work, brittle Studio selectors,
and direct channel publication without the shared authority, idempotency, or
audit provider. Public market search is restored; account operations remain a
future shared-control-plane slice.

## Episode Audio Mastering

Source: `feat/episode-audio-mastering` at `7615554`.

Original path count: 3 — all were absent before this audit.

- `apps/worker-py/tests/test_episode_audio_master.py`: ported; proves the
  current master filter retains the speech chain and packaging prefers the
  master over raw audio.
- `docs/shows/AUDIO_MASTERING.md`: ported and reconciled with the Classic
  Listening audio-acceptance boundary.
- `docs/exec-plans/active/2026-07-17-elr-episode-audio-mastering.md`: not
  ported; its implementation is already present and the historical active plan
  would misstate current work.

## Audiobook Skill And Media

Source: `feat/audiobook-skill-opt-in-srt` at `9dce05c`.

Original path count: 41 — 16 identical, 16 evolved, and 9 absent before this
audit.

### Identical: 16

- `check_chapter.py`, `clean_reference_audio.py`, `compose_chapter.py`,
  `generate_chapter_srt.py`, `prepare_youtube_packaging.py`,
  `rebuild_manifest_from_source.py`, `render_book_chapters.py`, and
  `segment_chapter.py`.
- `media/{__init__,align_media_words,bar_waveform,generate_media_srt,
  thumbnail_compositor,thumbnail_overlay,turn_alignment}.py`.
- The old skill-level `monitor_book_chapters.py` wrapper blob was identical,
  but its delegated repository script was absent. The orphan wrapper was
  removed during this audit and current docs point to the locked Classics
  controller instead.

### Evolved: 16

- Documentation: `SEGMENTATION.md`, `SKILL.md`, `VOXCPM2.md`, `WORKFLOW.md`,
  and `docs/LOCAL_RUNTIME.md`.
- Runtime/config policy: `.gitignore` and `apps/worker-py/requirements.txt`.
- Scripts: `audiobook_workspace.py`, `render_chapter.py`,
  `normalize_youtube_cover.py`, and
  `media/{compose_media_video,cover_pipeline,generate_karaoke_ass,
  host_visuals,media_layout,thumbnail_tokens}.py`.

Current versions retain later low-memory loading, deterministic branding,
atomic partial-file promotion, media verification, intro/outro composition,
updated subtitle layout, and current D-volume runtime rules. Restoring older
blobs would regress these behaviors.

### Ported: 7

- Regression tests: `test_bar_waveform.py`, `test_host_visuals.py`, and
  `test_media_video_pipeline.py`. The host prompt assertion was adapted to the
  newer split between baked-cover and text-free background prompts.
- Skill contracts: `CONTROLS.md`, `QC.md`, `SUBTITLES.md`, and `YOUTUBE.md`.
  The YouTube contract now states that packaging grants no account authority.

### Not ported: 2

- `docs/exec-plans/active/2026-05-17-audiobook-opt-in-srt.md`: completed
  historical scope; importing it as active would be false.
- `scripts/monitor_book_chapters.py`: obsolete long-running controller that
  bypasses the unified Classic Listening config and shared GPU entry point.

## Additional Defect Found

The restored host-visual tests exposed that six host identities were read from
ignored `workspace/characters/registry.json`. That made visual generation
depend on one machine's hidden runtime file. The same pure configuration is now
tracked at `configs/shows/host-visuals.json`; code and documentation resolve to
that path. The original root-workspace file was not changed.

## Validation Evidence

- Six restored regression modules: 24 passed after adapting the evolved prompt
  contract and migrating the host registry.
- Read-only browser CLI help imports successfully without opening a browser.
- Current-vs-source diffs were reviewed for all 18 differing paths across the
  research and audiobook branches.
- No source branch, account session, remote channel, runtime media, or root
  workspace file was changed.
