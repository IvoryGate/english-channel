# English Listening Room — Multi-Series Strategy

> Growth, publication, experimentation, analytics, and autonomy are governed by
> [`AUTONOMOUS_GROWTH_SYSTEM.md`](AUTONOMOUS_GROWTH_SYSTEM.md). Until its
> baseline is complete, the existing 63-video dialogue inventory is the
> experiment bank and new episode production beyond episode 021 is paused.
> The first signed-in Studio baseline is recorded in
> [`YOUTUBE_BASELINE_2026-08-17.md`](YOUTUBE_BASELINE_2026-08-17.md). It selects
> First Steps for reach, Daily Talk for satisfaction, and Polished English as a
> low-cadence authority/conversion bet.

Channel umbrella: **English Listening Room (ELR)**. One neutral channel brand for two complementary promises: Classic Listening literary audiobooks and levelled practical-English dialogue series. The ready-to-paste live channel copy lives in [`CHANNEL_DESCRIPTION.md`](CHANNEL_DESCRIPTION.md).

## Active series (A/B/C)

| Series | Public name | CEFR | Hosts | Cadence target |
| --- | --- | --- | --- | --- |
| **A** | Daily Talk | B1-B2 | Ethan & Nora | Weekly |
| **B** | First Steps | A2-B1 | Riley & Sam | Weekly |
| **C** | Polished English | B2-C1 | Leo & Mia | Every 2 weeks |
| **Classic** | Pride & Prejudice Audiobook | — | Narrator | Automated / daily |

For the two-week 020/021 validation sprint, use one weekly slot per series so
each product role gets two observations quickly. After that sprint, the working
capacity prior returns to 50% First Steps, 35% Daily Talk, and 15% Polished
English until a complete 28-day cycle is reviewed.

**Cancelled for now:** Series D (Quick Fix short format).

## Hard constraints

- Every dialogue episode **≤ 20 minutes** at **`speed=1.0`**
- Level differentiation via **sentence length, grammar, vocabulary, recap density** — not slower speech
- Three independent host pairs for variety and parallel production
- Original scripts only; competitor corpus informs structure and packaging, not wording

## Viewer ladder

```text
Short clip / search → Series B (First Steps)
  → Series A (Daily Talk)
    → Series C (Polished English)
  → Classic Listening audiobook for immersion
```

## Production pipeline

```text
research brief → draft.md → validate_podcast_script.py
  → script.json → episode_manifest.json → render_episode.py → YouTube pack
```

Shared tooling:

- Voice registry: [`workspace/dialogue_podcast_research/voices/voice_profiles.json`](../../workspace/dialogue_podcast_research/voices/voice_profiles.json)
- Character bibles: [`workspace/characters/`](../../workspace/characters/)
- Production archive: [`workspace/shows/`](../../workspace/shows/)

## Weekly cadence (steady state)

| Week pattern | Podcast output |
| --- | --- |
| W1 | B + A |
| W2 | B + C |
| W3 | B + A |
| W4 | B + (A or C) |

**Hard cap:** ≤ 5 channel uploads per week including P&P chapters.

## Phase roadmap

### Phase 1 (0-4 weeks) — infrastructure

- Voice references for Series A/B extracted and smoke-tested
- Show bibles, workspace layout, episode_001 under Series A
- Three podcast playlists + thumbnail template spec

### Phase 2 (1-3 months) — three-series run

- Target: B≥4, A≥4, C≥2 published episodes
- Title packaging A/B tests (Class-style vs J&May-style hooks)

### Phase 3 (3-6 months) — steady state

- Target: A≥12, B≥12, C≥6 cumulative
- Shorts from best-performing episodes; evaluate second classic audiobook

## Stop / scale rules

| Signal | Action |
| --- | --- |
| Series median views < 40% of channel podcast median for 3 episodes | Cut cadence 50%; keep hosts |
| Clone instability | Swap reference clip or tune cfg; do not change speed |
| 4 weeks without script review capacity | Pause B or A; protect C quality |
| Render > 20 min | Trim script and re-validate |

## Related docs

- [`AUTONOMOUS_GROWTH_SYSTEM.md`](AUTONOMOUS_GROWTH_SYSTEM.md)
- [`series_a/bible.md`](series_a/bible.md)
- [`series_b/bible.md`](series_b/bible.md)
- [`series_c/bible.md`](series_c/bible.md)
- [`youtube_playlists.md`](youtube_playlists.md)
- [`thumbnail_templates.md`](thumbnail_templates.md)
