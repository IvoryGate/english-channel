# ELR Visual Identity — Brand Book (source of truth)

Consolidates the visual system for all ELR dialogue series (A/B/C). Other docs reference this; do not duplicate the palette/font tables elsewhere.

Channel avatar is **out of scope** for this doc — it stays neutral ELR brand and is managed separately.

## Channel brand

- **Umbrella**: English Listening Room (ELR) — one neutral channel, multiple levelled series.
- **Viewer ladder**: B (First Steps, A2-B1) → A (Daily Talk, B1-B2) → C (Polished English, B2-C1) → Classic Listening audiobook.
- **Visual gradient**: warm → cool → deep (amber → teal → plum), matching the "casual → professional" ladder.

## Per-series palette (定稿)

| Series | accent | wave bar | subtitle primary (spoken) | subtitle secondary (waiting) | subtitle outline | video bg dominant |
| --- | --- | --- | --- | --- | --- | --- |
| A · Daily Talk · B1-B2 | amber `#E9A319` | orange `#EA580C` | amber `#E9A319` | gray `#B0B0B0` | dark brown `#3B2A1A` | light cream wall |
| B · First Steps · A2-B1 | teal `#2A9D8F` | bright teal `#14B8A6` | teal `#2A9D8F` | gray `#B0B0B0` | dark teal `#1A4A47` | light cream wall |
| C · Polished English · B2-C1 | deep plum `#5C4B7A` | rose `#E11D48` | deep plum `#5C4B7A` | gray `#B0B0B0` | dark plum `#2A1F3A` | light cream wall |

### Why these colors

- **Subtitle primary = accent color** (not ivory): all three accents are mid-to-dark tones, which contrast well against the light cream video_bg wall. The previous ivory `#FFF8E7` was near-invisible on the cream wall (pollution). The accent-as-primary gives both contrast AND brand identity in every subtitle frame.
- **Subtitle outline = dark per-series accent**: reinforces brand identity in the stroke, and guarantees contrast on the cream wall even where background props (plants, frames) bleed into the subtitle band.
- **Subtitle secondary = neutral gray** `#B0B0B0`: waiting words stay quiet across all series — the spoken highlight is what carries the brand.
- **Wave bar color** is the only place a second accent appears (A: orange, B: bright teal, C: rose) — gives the audio visualizer a distinct energy per series without touching the subtitle band.

### Color pollution rules

1. Never put a light color (ivory, white, pale yellow) as subtitle fill on the light cream wall — it disappears.
2. Never put the wave bar color into the subtitle band — they are different visual zones (subtitle = top-center above heads; wave = lower-middle band).
3. The subtitle outline must always be the dark per-series accent, never a generic dark brown across all series (that leaked Series A's amber-brown into B and C).

## Font system (bundled, OFL licensed)

Fonts live in [`assets/fonts/`](../../assets/fonts/) with `LICENSE.txt`. All are SIL Open Font License (free for commercial use, no attribution required).

| Series | Main title (bold) | Script prefix (handwritten) | Karaoke ASS |
| --- | --- | --- | --- |
| A · Daily Talk | Inter Bold | Caveat | Inter |
| B · First Steps | Inter Bold | Caveat | Inter |
| C · Polished English | Manrope Bold | Caveat | Manrope |

### Why differentiate C

C is B2-C1 "premium / Real Talk". Manrope is a geometric sans with a more refined, modern feel than Inter — gives C a quieter, more polished typographic identity vs the warmer, friendlier Inter used by A/B. The handwritten Caveat prefix is shared across all three to keep the "personal hook" beat consistent.

### Bundling rationale

Previously `thumbnail_overlay.py` fell back to Windows system fonts (Segoe Script / Segoe UI / Arial). On non-Windows machines or CI, it fell back to DejaVu — completely different look. Bundling guarantees identical render output everywhere.

## Layout (frozen, shared across all series)

Authoritative spec lives in [`thumbnail_templates.md`](thumbnail_templates.md). Summary:

- **16:9** export (1920×1080) for thumbnail; **2560×1440 (2K)** for video bg
- Female host **left**, male host **right**
- Podcast desk + two condenser microphones
- Top-left: level badge (`A2-B1`, `B1-B2`, `B2-C1`)
- Top-right: show public name
- Center: layered hook text (prefix script → main white/bold → suffix pill)
- **No episode numbers** on thumbnail
- Video bg uses the **no-text scene**; thumbnail adds text overlay in PIL
- Subtitles render **above heads** (ASS `MarginV≈100`) on the light cream central wall
- Waveform: **lower-middle** fixed-position FFT bars, bottom-aligned, grow upward only

## Per-episode flexibility (anti-homogeneity policy)

Homogeneous covers don't attract viewers. The frozen layout + frozen host faces give brand consistency; the **scene, outfits, and action must vary per episode** to give each cover a reason to click.

### Must vary per episode (in `youtube.json`)

| Field | What it controls | Example |
| --- | --- | --- |
| `coverScene` | Scene props and setting | "cozy cafe with plants and pendant light" |
| `coverOutfitFemale` | Female host wardrobe | "cream knit sweater, gold hoop earrings" |
| `coverOutfitMale` | Male host wardrobe | "brown jacket over black tee" |
| `coverAction` | Host poses / expressions | "Nora gesturing, Ethan laughing" |

**Rule**: never reuse the previous episode's `coverScene`/`coverOutfit*`/`coverAction`. The `--print-prompts` step should flag duplicates against the last episode in the series.

### Locked per series (never vary)

| Field | Source |
| --- | --- |
| Host face / hair / age band | [`workspace/characters/registry.json`](../../workspace/characters/registry.json) |
| Layout | this doc + `thumbnail_templates.md` |
| accent / wave bar / subtitle colors | `workspace/shows/tools/show_config.json` |
| Fonts | `assets/fonts/` + this doc |
| Show label | `show_config.json` `thumbnail.label` |

### Scene variants per series (anti-homogeneity menu)

Pick a different one each episode; do not exhaust the list in consecutive weeks.

| Series | Scene variants |
| --- | --- |
| A · Daily Talk | cozy cafe / warm living-room nook / kitchen table with window / home study with bookshelf |
| B · First Steps | home study desk with notebook / kitchen table with mug / balcony with plants / classroom with whiteboard |
| C · Polished English | minimal modern studio / quiet lounge with armchair / corner office with city view / rooftop terrace at dusk |

## Host visual anchors (locked)

Six distinct host identities, fixed in [`workspace/characters/registry.json`](../../workspace/characters/registry.json). Faces and age bands never change; outfits and scene vary per episode via `youtube.json`.

| Series | Female (left) | Male (right) |
| --- | --- | --- |
| A · Daily Talk | Nora (late 20s, brown hair bun, cream knit) | Ethan (late 20s, dark wavy hair, brown jacket) |
| B · First Steps | Riley (mid 20s, auburn hair, teal cardigan) | Sam (mid 20s, dark blond hair, hoodie) |
| C · Polished English | Mia (early 30s, black bob, plum blouse) | Leo (early 30s, dark hair side part, blazer) |

Art style (all series): 2D comic / hand-drawn podcast illustration, bold clean outlines, flat cel-shaded color, warm soft lighting. Explicitly NOT photorealistic, NOT 3D CGI, NOT semi-realistic skin texture.

## Waveform (audio bars)

- Style: `rounded-bars-transparent` (all series, this round — per-series style differentiation is a future task)
- Color: per-series `waveBarColor` (A: orange `#EA580C`, B: bright teal `#14B8A6`, C: rose `#E11D48`)
- Position: lower-middle band, fixed-position FFT bars, bottom-aligned, grow upward only — no horizontal scroll

## Source-of-truth map

| What | Where | Notes |
| --- | --- | --- |
| Palette + fonts + layout + flexibility policy | this doc | source of truth |
| Layout details + host visual policy | [`thumbnail_templates.md`](thumbnail_templates.md) | references this doc |
| Color config (read by renderer) | [`workspace/shows/tools/show_config.json`](../../workspace/shows/tools/show_config.json) | must match this doc's palette table |
| Color code defaults | [`.cursor/skills/audiobook-chapter-tts/scripts/media/thumbnail_tokens.py`](../../.cursor/skills/audiobook-chapter-tts/scripts/media/thumbnail_tokens.py) | fallback when config missing |
| Host visual anchors | [`workspace/characters/registry.json`](../../workspace/characters/registry.json) | faces/hair/age locked |
| Pipeline + commands | [`EPISODE_PIPELINE.md`](EPISODE_PIPELINE.md) + [`VIDEO_PIPELINE.md`](VIDEO_PIPELINE.md) | render → pack flow |
| Font files | [`assets/fonts/`](../../assets/fonts/) + `LICENSE.txt` | OFL licensed |

## Revision history

- 2026-07-19: Initial brand book — consolidated from `thumbnail_templates.md`, `show_config.json`, `thumbnail_tokens.py`, `registry.json`, `VIDEO_PIPELINE.md`. Fixed subtitle color pollution (ivory → accent on light cream wall). Added per-episode flexibility policy. Bundled OFL fonts.
