# ELR Series Thumbnail Templates

Channel avatar stays neutral **ELR** brand. Each dialogue series uses a **fixed visual system** inspired by educational podcast packaging (symmetrical two-host scene + layered hook text), with **original ELR hosts and wording only**.

> **Source of truth**: palette, fonts, subtitle colors, layout, and per-episode flexibility policy now live in [`VISUAL_IDENTITY.md`](VISUAL_IDENTITY.md). This doc keeps the layout detail and host visual policy; refer to `VISUAL_IDENTITY.md` for the full brand book.

## Production workflow

1. `--print-prompts` → `coverImagePrompt` + `videoBgImagePrompt` (no text in generated image)
2. Image-generation tool → save `000_episode_XXX.cover_source.png` and optional `000_episode_XXX.video_bg_source.png`
3. `render_episode_thumbnail.py --from-image ...` → normalize cover, export thumbnail + video background
4. (Automated) `pack_episode.py` step 0 runs the hookText consistency check + the render above; use `--skip-thumbnail` to defer.

## Cover normalization methodology

Image-generation tools rarely emit a true 16:9 frame (they produce 3:2 1536x1024 even when "16:9" is requested), and ELR covers bake text — level badge, show label, hook title, brand tag — directly into the pixels. The normalization step must therefore **never crop text** and **never stretch** the artwork. `normalize_youtube_cover.py` exposes several modes; the pipeline picks one per artifact.

### Mode map

| Mode | What it does | Used for |
| --- | --- | --- |
| `auto` | Resize if already ~16:9, else **top-crop** (crop from bottom, keeps top text) | **Video background** (`video_bg.jpg`) — no text to preserve, must fill the frame |
| `top-crop` | Scale to fill, crop from bottom only | Audiobook chapter covers (legacy) |
| `center-crop` | Scale to fill, crop top+bottom equally | Rare; only when text is centered |
| `contain` | Scale to fit, pad sides with edge color | Fallback; leaves solid side bars |
| `blur-fill` | Scale to fill width, center-crop to height, light Gaussian blur | Soft color-matched backdrop layer (no readable text) |
| `blur-fill-composite` | `blur-fill` backdrop + sharp cover contained on top, **rounded corners + feathered edges + small margin** | **Episode thumbnails / covers** (`thumbnail.png`, `thumbnail_cover.jpg`) |

### Episode cover = `blur-fill-composite` (default)

The episode cover (with baked-in text) is normalized with `blur-fill-composite` so that:

1. The 16:9 frame is **seamless** — no solid side bars; the sides are a soft blurred extension of the cover itself.
2. All baked-in text is **preserved** — the sharp cover is *contained* (scaled to fit), never cropped, so edge text (level badge, brand tag) is never cut.
3. The cover **blends softly** into the backdrop via rounded corners + feathered edges instead of a hard seam.

Tuned defaults (in `normalize_youtube_cover.py::_blur_fill_composite`):

| Parameter | Default | Meaning |
| --- | --- | --- |
| `blur_radius` | `8.0` | Light blur on the backdrop (若隐若现 — shapes/colors visible, text unreadable) |
| `safe_margin` | `0.04` | 4% inset on all sides so the cover floats inside the frame |
| `corner_radius` | `48` | Rounded-corner radius in pixels |
| `feather` | `16.0` | Edge feather width in pixels for the soft transition |

> If the backdrop still feels too soft or too sharp, tune `blur_radius` (lower = sharper, higher = softer). If text crowds the frame edge, raise `safe_margin`. These are the only knobs; do **not** switch the cover to `auto`/`top-crop` — that re-introduces text cropping.

### Video background = `auto` (direct crop)

The video background (`video_bg.jpg`) is the **no-text scene** (`video_bg_source.png` if provided, else the cover source). It is normalized with `auto` (top-crop fill) so it fills 16:9 cleanly with no blur and no side bars — the center stays clean for subtitles and audio bars overlaid during video composition.

### Where the choice is wired

`cover_pipeline.py::prepare_outputs_from_generated` calls:

- `normalize_generated_cover(cover_source, cover_jpg, mode="blur-fill-composite")` → `thumbnail.png` / `thumbnail_cover.jpg`
- `normalize_generated_cover(bg_source, video_bg_jpg, mode="auto")` → `video_bg.jpg`

`normalize_generated_cover` forwards `safe_margin` only for `contain` / `blur-fill-composite` (the modes with a sharp text layer). `blur-fill` and `auto` ignore it (background fill, no text).

### Why not just generate at 16:9?

The image-generation tool's `aspect_ratio="16:9"` still returns 3:2. Even if a future tool emits true 16:9, baked-in text placed near the frame edge remains at risk under any downstream crop (square/vertical reformat, player UI overlays). The `blur-fill-composite` method is robust to both: it preserves the full artwork and lets the blurred fill absorb any ratio mismatch. Keep this method even after tooling improves.

Host visual anchors live in [`workspace/characters/registry.json`](../../workspace/characters/registry.json). **Faces and age bands are fixed per host**; scene, outfits, and actions change per episode via `youtube.json`.

## Shared layout

- **16:9** export (1920×1080)
- Female host **left**, male host **right**
- Podcast desk + two microphones
- Top-left: level badge (`A2-B1`, `B1-B2`, `B2-C1`)
- Top-right: show public name
- Center: layered hook text (prefix script → main white → suffix pill)
- **No episode numbers** on thumbnail
- Video background uses the **no-text scene**; thumbnail adds text overlay in PIL

## Host visual policy

| Rule | Detail |
| --- | --- |
| Cross-series | Six distinct host identities (Ethan, Nora, Riley, Sam, Leo, Mia) |
| Within series | Pair shares comparable age band; different face, hair, wardrobe cues |
| Per episode | `coverScene`, `coverAction`, `coverOutfitFemale`, `coverOutfitMale` in `youtube.json` |
| Forbidden | Competitor logos, Anna/Jake likeness, celebrity faces |

## Series B — First Steps

| Element | Spec |
| --- | --- |
| Hosts | Riley (female teacher, left) + Sam (male co-learner, right), both mid 20s |
| Accent | Teal `#2A9D8F` |
| Label | `FIRST STEPS · Easy English` |
| Hook style | Number or contrarian promise |
| Scene mood | Home study / kitchen table, notebook, clock, mug |

## Series A — Daily Talk

| Element | Spec |
| --- | --- |
| Hosts | Nora (female, left) + Ethan (male, right), both late 20s |
| Accent | Warm amber `#E9A319` |
| Label | `DAILY TALK · English Conversations` |
| Hook style | Emotional scene line (2 layers max) |
| Scene mood | Cozy cafe or warm living-room podcast nook |

## Series C — Polished English

| Element | Spec |
| --- | --- |
| Hosts | Mia (female, left) + Leo (male, right), both early 30s |
| Accent | Deep plum `#5C4B7A` |
| Label | `POLISHED ENGLISH · Real Talk` |
| Hook style | Paradox or workplace/social tension |
| Scene mood | Minimal modern studio or quiet lounge |

## youtube.json cover fields

```json
{
  "hookText": "Practice English Alone Every Day (Only 15 Minutes!)",
  "coverScene": "Home study desk with notebook, wall clock, teal mug",
  "coverAction": "Riley explaining with a notebook, Sam listening with a hopeful smile",
  "coverOutfitFemale": "teal cardigan over white tee",
  "coverOutfitMale": "soft gray hoodie",
  "coverText": {
    "prefix": "Practice",
    "main": "15 MINUTES A DAY",
    "suffix": "ALONE AT HOME",
    "badge": "Easy Practice"
  }
}
```

If `coverText` is omitted, the tool auto-splits `hookText` into layers.

## Per-episode flexibility (anti-homogeneity)

Homogeneous covers do not attract viewers. The frozen layout + frozen host faces give brand consistency; **scene, outfits, and action must vary per episode**.

### Must vary per episode (in `youtube.json`)

| Field | What it controls |
| --- | --- |
| `coverScene` | Scene props and setting |
| `coverOutfitFemale` | Female host wardrobe |
| `coverOutfitMale` | Male host wardrobe |
| `coverAction` | Host poses / expressions |

**Rule**: never reuse the previous episode's `coverScene` / `coverOutfit*` / `coverAction`. Scene variant menus per series live in [`VISUAL_IDENTITY.md`](VISUAL_IDENTITY.md).

### Locked per series (never vary)

- Host face / hair / age band — [`workspace/characters/registry.json`](../../workspace/characters/registry.json)
- Layout — this doc + `VISUAL_IDENTITY.md`
- accent / wave bar / subtitle colors — `workspace/shows/tools/show_config.json`
- Fonts — `assets/fonts/` (Inter for A/B, Manrope for C, Caveat for handwritten prefix)
- Show label — `show_config.json` `thumbnail.label`

## Classic Listening (audiobook)

Keep existing Regency drama-hook chapter thumbnails; do not reuse podcast templates.

## File convention

Artifacts now live in typed subdirectories (see [`EPISODE_PIPELINE.md`](EPISODE_PIPELINE.md) "Episode directory structure"). The cover-source and video-bg-source images that this tool consumes/produces:

```text
workspace/shows/series_X/episode_XXX/video/000_episode_XXX.cover_source.png
workspace/shows/series_X/episode_XXX/video/000_episode_XXX.video_bg_source.png
workspace/shows/series_X/episode_XXX/video/000_episode_XXX.thumbnail.png
workspace/shows/series_X/episode_XXX/video/000_episode_XXX.video_bg.jpg
```

The thumbnail report is written to `reports/000_episode_XXX.thumbnail_report.json`. All paths are resolved by `episode_artifacts.py::artifact_paths()`.
