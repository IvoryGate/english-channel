# Dialogue Podcast Scriptwriting Workflow

## ELR show archive

```text
workspace/shows/series_a/   Daily Talk (B1-B2) — Ethan & Nora
workspace/shows/series_b/   First Steps (A2-B1) — Riley & Sam
workspace/shows/series_c/   Polished English (B2-C1) — Leo & Mia
workspace/shows/tools/      prepare_episode_manifest.py, render_episode.py
```

Strategy: [`docs/shows/strategy.md`](../../../docs/shows/strategy.md)

Legacy `workspace/polished_english/` is deprecated; episode_001 lives under `series_a/`.

## Research Inputs (other skills)

Topic investigation flow: [`docs/shows/EPISODE_PIPELINE.md`](../../../docs/shows/EPISODE_PIPELINE.md) § Topic selection · channel list [`docs/shows/COMPETITOR_CHANNELS.md`](../../../docs/shows/COMPETITOR_CHANNELS.md).

```text
run_research_refresh.py --channel <slug>   → scrape one competitor (anti-ban)
refresh_topic_backlog.py --all             → merge into topic_backlog.json
select_next_topic.py --show series_X --apply
```

Key handoff files:

```text
workspace/dialogue_podcast_research/youtube_corpus/analysis/episode_brief_suggestions.json
workspace/dialogue_podcast_research/youtube_corpus/analysis/youtube_research_report.md
workspace/shows/series_*/topic_backlog.json
```

## Draft A New Episode

1. Read `RESEARCH.md` and the series bible (`docs/shows/series_*/bible.md`).
2. Get the topic from `select_next_topic.py --show <series> --apply` (writes `topic_selection_<date>.json` from real competitor research; excludes already-produced topics); or fall back to a user brief. See `docs/shows/EPISODE_PIPELINE.md` § Topic selection.
3. **Series C** / Leo-Mia narrative engine → `POLISHED_ENGLISH.md` + **polished-english-episode-script**.
4. **Series A** → Class-style packaging, B1-B2 word band (1800-2400 spoken words).
5. **Series B** → J&May-style contract, A2-B1 word band (1400-1900 spoken words).
6. Draft with exactly two hosts; **speed=1.0** always.
7. Apply `QC.md`; stop for user review.

## Validate A Saved Draft

```powershell
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/validate_podcast_script.py workspace/shows/series_a/episode_001/000_episode_001.draft.md --profile series_a
```

Profiles: `series_a`, `series_b`, `series_c`, `polished_english` (alias of series_c constraints).

## Render handoff (after approval)

See [`docs/shows/EPISODE_PIPELINE.md`](../../../docs/shows/EPISODE_PIPELINE.md) for full render → QC → pack flow.

```powershell
$man = "workspace/shows/series_a/episode_001/000_episode_001.episode_manifest.json"
.\.conda-env\python.exe workspace/shows/tools/prepare_episode_manifest.py --draft workspace/shows/series_a/episode_001/000_episode_001.draft.md
.\.conda-env\python.exe scripts/run_episode_render.py --manifest $man --skip-existing
# After human audio OK:
.\.conda-env\python.exe scripts/launch_episode_pack.py --show series_a --episode episode_001 --workspace workspace/shows/series_a/episode_001 --detach
# After pack/export completes, write the topic back as done:
.\.conda-env\python.exe workspace/shows/tools/mark_topic_done.py --show series_a --episode episode_001 --auto
```

## Voice reference extraction (ops)

```powershell
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/extract_host_reference_clips.py --series all
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/smoke_voice_demo.py --hosts Ethan
```

## Defaults

| Profile | Spoken words | Max duration |
| --- | --- | --- |
| `series_b` | 1400-1900 | 20 min |
| `series_a` | 1800-2400 | 20 min |
| `series_c` | 2000-2800 | 20 min |

Host count: exactly two per episode.
