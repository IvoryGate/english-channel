# 2026-07-14 ELR formal 2K publish (A/B/C episode 01)

## Goal

Ship one **formal** YouTube package per dialogue series at **≥2K (2560×1440)**, with hot-theme topic selection (no politics, no duplicates), full packaging like audiobook exports, delivered under `H:\Youtube\<Series>\episode01\`.

## Scope

- Lock publish workflow in `docs/shows/ELR_YOUTUBE_PUBLISH.md`
- Raise media pipeline defaults from 1080p → 2560×1440
- Select one fresh topic each for A/B/C
- Produce script → TTS → cover/bg → ASS → mp4 → `H:\Youtube` export
- Export helper script

## Non-goals

- Full 20-minute first cuts (first formal ship targets a complete short episode ~4–7 min unless render capacity allows longer)
- Live YouTube upload automation
- Regenerating Pride audiobook packs

## Status

- **State:** completed; the first 2K packs shipped and VoxCPM production was
  subsequently restored. Ongoing episode production is owned by the ELR
  production orchestrator plan.
- **Last update:** 2026-08-03

## Plan

1. Workflow + layout constants (2K)
2. Topic lock (hot / non-political / non-duplicate)
3. Scripts + manifests + TTS
4. 2K comic covers + video bgs
5. Subtitles + compose
6. Export to `H:\Youtube`

## Validation

- `ffprobe` reports ≥2560×1440 on exported mp4 and cover jpg
- Each `H:\Youtube\...` folder has mp4, 封面, srt, wav, title, description, youtube.json
- Titles do not match prior pilot hooks (15-min alone / understand-not-improving / polite-unclear)

## Archive criteria

Three series episode01 packs on `H:\Youtube` complete and workflow doc checked in.
