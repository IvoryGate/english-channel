# YouTube Packaging

This document defines legacy package construction only. It does not authorize
upload, scheduling, playlist mutation, or publication. Channel identity,
capacity, idempotency, and authority are owned by the shared control plane.

Use this guide when the user asks for a YouTube title, description, tags, or cover image for a chapter audiobook video.

This is an **opt-in** step. Do not generate titles or covers during initial render, QC, or subtitle generation unless the user asks.

## When To Run

Run YouTube packaging when:

- the user asks for a title, thumbnail, cover, or upload metadata for a chapter; or
- the user confirms chapter audio is acceptable and asks to prepare the video for upload.

Recommended order:

1. chapter audio rendered and QC passed
2. user approves audio
3. subtitles generated (if requested)
4. **YouTube packaging** (this doc)
5. final video assembly under `videos/` (outside this skill unless the user asks)

## Inputs

Read these before drafting packaging:

- `000_chapter_XXX.source.txt` — chapter plot, dialogue, and emotional beats
- `000_chapter_XXX.segments.json` — `bookTitle`, `bookSlug`, `chapterNumber`, speaker names
- optional: `000_chapter_XXX.run.json` — duration for description copy
- reference cover: `videos/pride&prejudice/chapter_01/chapter_01-封面.jpg` — visual template for this project

If author name is missing from the manifest, infer from the book or ask once.

## Output Files

Write packaging artifacts into the chapter workspace first:

```text
workspace/<book_slug>/chapter_XXX/
├── 000_chapter_XXX.youtube.json
├── 000_chapter_XXX.youtube_description.txt
└── 000_chapter_XXX.cover.jpg
```

After user approval, copy or regenerate the final cover into the video folder:

```text
videos/<book_display_slug>/chapter_XX/
└── chapter_XX-封面.jpg
```

Use the same slug style as existing videos (`pride&prejudice`, not `pride_and_prejudice`).

## Title Design

### Goal

Pick **one final YouTube title** for the chapter. It must attract clicks while staying faithful to the chapter. It is not a summary of the whole book.

The same title (or its short on-image form) must appear on the cover. Do not use a different hook on the thumbnail than in the upload title.

### Process

1. Read the full chapter source text.
2. Identify one **dominant beat**: conflict, reversal, secret, confrontation, proposal, departure, revelation, or emotional turn.
3. Name the most recognizable characters or place when relevant.
4. Draft internally if needed, then choose **one** final title.
5. Store it as `title` in `000_chapter_XXX.youtube.json`.
6. Derive `coverTitle` from the same title — usually the most readable short phrase for the image, not a different concept.

### Rules

- Deliver **one title only** to the user unless they explicitly ask for alternates.
- Include book identity: `Pride and Prejudice` or accepted short form `Pride & Prejudice`.
- Include chapter number: `Chapter 37`, `Ch. 37`, or `Chapter Thirty-Seven` — stay consistent within a series.
- Include format keyword: `Audiobook`, `Full Chapter`, or `Chapter Audiobook`.
- Prefer **specific scene language** over generic literary phrasing.
- Keep total length under **70 characters** when possible; hard cap **100 characters**.
- Do not spoil major future plot points from later chapters.
- Do not use clickbait that the chapter cannot deliver.
- Avoid duplicate titles across nearby chapters; check neighboring chapter packaging if it exists.

### Good Example

```text
Poor Charlotte! | Pride & Prejudice Ch. 38 | Audiobook
```

### Weak Patterns

```text
Pride and Prejudice Chapter 38
Jane Austen Audiobook
A Very Important Chapter
Elizabeth Has Feelings
```

## Chapter Description

Do **not** reuse a generic channel boilerplate as the main body. Each chapter needs its own hook, summary, highlights, timestamps, and engagement question.

### What To Avoid

Generic copy like this performs poorly because it could describe any chapter:

```text
📖 In this chapter:
– British English listening practice
– Immersive audiobook narration
– Classic English literature
```

Replace those bullets with **plot-specific moments** from this chapter only.

### Description Structure

Assemble the upload description in this order:

1. **openingHook** — one sentence: book, author, chapter, and this chapter's tension
2. **chapterSummary** — 2-3 sentences on what actually happens here
3. **Chapter timestamps** — 4-8 key plot beats with video timestamps
4. **In this chapter** — 4-6 bullets naming scenes, characters, or turns (not generic learning claims)
5. **seriesBoilerplate** — 1-2 sentences max about the series; keep it short
6. **Playlist** — series playlist label
7. **engagementQuestion** — one question tied to this chapter's characters or conflict
8. **subscribeCta** — channel CTA
9. **hashtags** — upload tags line

### Timestamp Rules

Final video assembly adds a **3-second intro** before chapter audio starts. All published timestamps must include this offset:

```text
videoTimestampSec = segmentAudioStartSec + videoIntroOffsetSec
```

Defaults:

- `videoIntroOffsetSec`: **3**
- first narration marker usually lands at **`0:03`**, not `0:00`
- use the current segment WAV timings from disk (same source as compose / SRT)

Format timestamps for YouTube description chapters as `M:SS` or `H:MM:SS`:

```text
0:03 The gentlemen leave Rosings
1:12 Lady Catherine on Darcy's attachment
4:05 Elizabeth must return to town
```

Rules:

- pick **4-8 markers**, not one per segment
- choose plot turns, scene changes, new speakers, or emotional reversals
- map each marker to a real `segmentId` in `000_chapter_XXX.segments.json`
- labels should be short, readable, and spoiler-safe for future chapters
- keep markers in chronological order
- if the user changes the final video intro length, rerun with `--intro-offset`

### Marker Selection Process

1. Read `000_chapter_XXX.source.txt` and identify major beats.
2. Find the segment where each beat begins in `000_chapter_XXX.segments.json`.
3. Write markers into `000_chapter_XXX.youtube.json`:

```json
"chapterMarkers": [
  { "segmentId": "001", "label": "Return from Rosings" },
  { "segmentId": "006", "label": "Lady Catherine on Darcy's attachment" },
  { "segmentId": "010", "label": "Elizabeth must leave soon" }
]
```

4. Run timestamp assembly:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/prepare_youtube_packaging.py --workspace workspace/pride_and_prejudice/chapter_037
```

This resolves timestamps, writes the full `description`, and creates `000_chapter_XXX.youtube_description.txt` for copy-paste upload.

### Example Description Shape

```text
Listen to Pride and Prejudice Chapter 37 by Jane Austen — Elizabeth is back under Lady Catherine's watchful eye, and every polite question carries hidden pressure.

After leaving Rosings, Elizabeth finds herself drawn into another round of Lady Catherine's commanding conversation — about departures, propriety, travel, and the unspoken future Elizabeth might have had as Darcy's niece.

🎧 Chapter timestamps:
0:03 Return from Rosings
0:42 Elizabeth imagines Lady Catherine's indignation
1:28 Lady Catherine on Darcy's attachment to Rosings
3:06 Elizabeth refuses to extend her stay
4:38 Lady Catherine insists on proper travel arrangements

📖 In this chapter:
– Elizabeth returns from Rosings with mixed feelings
– Lady Catherine mourns the departure of Darcy and Colonel Fitzwilliam
– A pointed conversation about how long Elizabeth may stay
– Lady Catherine's views on daughters, propriety, and travel
– Elizabeth holds her ground with quiet firmness

Pride and Prejudice is one of the most beloved novels in English literature. This chapter-by-chapter audiobook series pairs classic storytelling with calm British English narration for immersive listening practice.

🎧 Playlist:
Pride and Prejudice | English Audiobook & Listening Practice

💬 If you were Elizabeth, would you have accepted Lady Catherine's invitation to stay longer?

If you enjoy immersive English listening and classic literature, subscribe to English Listening Room for more British English audiobooks and storytelling experiences.

#englishlistening #learnenglish #englishaudiobook #storytelling #prideandprejudice #janeausten #englishpodcast #englishlearning
```

### Tags

Include 8-15 tags in `hashtags` or a separate `tags` array mixing book, author, chapter, genre, and format (`audiobook`, `classic literature`, `english audiobook`).

Keep description prose plain and upload-ready. Do not invent quotes not present in the chapter.

## Cover Image

### Goal

Generate a **16:9 YouTube thumbnail** that matches the chapter mood and displays the **same title** chosen for upload.

Reference mood: `videos/pride&prejudice/chapter_01/chapter_01-封面.jpg` — cinematic Regency, warm light, readable typography — but do **not** copy one fixed layout formula.

### Visual Style Rules

- **Bright and inviting is allowed.** Sunny gardens, golden hour, soft daylight, pastel interiors, spring countryside, and lively estate scenes are all valid.
- **Avoid dead black.** Do not default to a solid black panel, black void, or heavy dark gradient for text.
- **Do not lock into "left scene / right black text block."** Vary composition:
  - full-bleed scenic background with text overlay
  - centered title over landscape
  - characters in environment with text integrated into sky or lower third
  - soft vignette or light color wash instead of a black sidebar
- Prefer **warm, airy, or softly contrasted** palettes over gloomy or crushed-black thumbnails.
- Keep text readable with subtle shadow, glow, or a **light translucent panel** only when needed — not a full black column.
- Period accuracy still matters for Pride & Prejudice: Regency clothing, settings, and tone.

### Title On Cover

The cover must use the chapter's chosen upload title, split for readability if needed:

- `title`: full YouTube upload title
- `coverTitle`: short on-image headline taken from the same title (not a different hook)
- optional supporting lines: book name, chapter number, `FULL AUDIOBOOK`, author

Example:

```text
Upload title: Poor Charlotte! | Pride & Prejudice Ch. 38 | Audiobook
Cover lines:
  POOR CHARLOTTE!
  PRIDE & PREJUDICE
  CHAPTER 38 · FULL AUDIOBOOK
  By Jane Austen
```

### Process

1. Finalize `title` first.
2. From the chapter source, choose one visual scene that fits the title mood:
   - setting (estate, garden, carriage, lane, drawing room)
   - 1-2 characters with period-accurate clothing
   - emotional cue (tension, wit, warmth, departure, reflection)
3. Draft a **cover brief** in `000_chapter_XXX.youtube.json`:
   - `coverScene` — one paragraph visual description
   - `coverTitle` — exact headline from the upload title
   - `coverTextOverlay` — full on-image text stack
   - `coverImagePrompt` — full generation prompt
4. Generate the image with the image-generation tool:
   - request aspect ratio: `16:9`
   - also request **exact output size `1920x1080` pixels** in the prompt
   - filename: `000_chapter_XXX.cover.jpg` in the chapter workspace
5. **Always normalize after generation**, even when `16:9` was requested. The image tool may still return 3:2 (for example `1536x1024`).

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/normalize_youtube_cover.py --input workspace/pride_and_prejudice/chapter_038/000_chapter_038.cover.jpg
```

Default normalize mode is **`auto`**:
- already ~16:9 → resize only
- wrong ratio → **top-crop** (keep the top text, crop from the bottom)

Do **not** use center-crop for covers with top titles. Use `--mode contain` only if you prefer padded letterboxing over losing bottom scene content.

Reference cover size: `videos/pride&prejudice/chapter_01/chapter_01-封面.jpg` is `1920x1080`.

6. Open or inspect the normalized result for:
   - on-image title matches `coverTitle` / upload title
   - text legibility at thumbnail size
   - bright enough overall tone; no dead-black background
   - period accuracy
   - no modern objects, logos, or watermarks
   - no grotesque faces or mangled hands
7. If text is illegible, misspelled, or off-title, regenerate with a tighter prompt, then rerun `normalize_youtube_cover.py`.

### On-Image Text Template

Use this hierarchy unless the user specifies otherwise:

```text
Line 1 (largest): coverTitle — taken from the upload title
Line 2: PRIDE & PREJUDICE
Line 3: CHAPTER 38 · FULL AUDIOBOOK
Line 4 (script/cursive): By Jane Austen
```

Keep on-image text short. Prefer 4 lines or fewer.

### Layout Safe Zone

When title text sits in the **upper third** (default):

- put all title lines in the top area
- keep faces, carriage, and key scene action in the **lower two-thirds**
- leave a little breathing room at the very top edge
- normalization uses **top-crop** if the generator returns the wrong ratio, so bottom scene content may be trimmed — never place essential text near the bottom edge

When the generator already returns true `1920x1080`, normalization only resizes if needed and does not crop.

When writing `coverImagePrompt`:

- explicitly request a **YouTube thumbnail, 16:9, exact size 1920x1080 pixels**
- specify **Regency-era England** for Pride & Prejudice
- name the scene, characters, clothing, and mood
- request **bright, warm, inviting lighting** when it fits the chapter; sunny or golden atmosphere is welcome
- forbid **solid black background, black sidebar, dead-black void, or heavy dark gradient**
- place the title text using the exact `coverTitle` wording in the **upper third**
- keep main scene action in the **lower two-thirds** so top-crop normalization does not damage text
- request **large readable serif title text** with subtle shadow or soft glow
- allow text over sky — not only a right-side text column
- request **no watermark, no logo, no modern elements**
- do not include subtitles, play buttons, or UI chrome

Example prompt skeleton:

```text
YouTube thumbnail, exact 1920x1080 pixels, 16:9 aspect ratio, bright cinematic Regency-era illustration.
Scene: [setting and action from chapter in lower two-thirds].
Characters: [names], period-accurate clothing, expressive but restrained.
Lighting: warm golden hour / soft sunny daylight — avoid dark or black backgrounds.
Title text in upper third, large white serif with subtle shadow:
"[COVER TITLE FROM UPLOAD TITLE]"
"PRIDE & PREJUDICE"
"CHAPTER 38 · FULL AUDIOBOOK"
"By Jane Austen"
No solid black panels, no black sidebar, no dead-black void.
No watermark, no logo, no modern objects, no subtitles.
```

### File Naming

- workspace draft: `000_chapter_XXX.cover.jpg`
- approved publish asset: `videos/<book_display_slug>/chapter_XX/chapter_XX-封面.jpg`

Create the destination folder if needed.

## Packaging JSON Schema

Write `000_chapter_XXX.youtube.json` with:

```json
{
  "bookTitle": "Pride and Prejudice",
  "author": "Jane Austen",
  "chapterNumber": 38,
  "chapterId": "chapter_038",
  "title": "Poor Charlotte! | Pride & Prejudice Ch. 38 | Audiobook",
  "coverTitle": "POOR CHARLOTTE!",
  "videoIntroOffsetSec": 3,
  "openingHook": "...",
  "chapterSummary": "...",
  "chapterHighlights": ["...", "..."],
  "chapterMarkers": [
    { "segmentId": "001", "label": "Breakfast with Mr. Collins" }
  ],
  "descriptionTimestampsBlock": "0:03 Breakfast with Mr. Collins",
  "seriesBoilerplate": "...",
  "playlistLabel": "Pride and Prejudice | English Audiobook & Listening Practice",
  "engagementQuestion": "...",
  "subscribeCta": "...",
  "hashtags": "#englishlistening #learnenglish ...",
  "description": "...",
  "tags": ["..."],
  "coverScene": "...",
  "coverTextOverlay": {
    "primary": "POOR CHARLOTTE!",
    "secondary": "PRIDE & PREJUDICE",
    "chapter": "CHAPTER 38 · FULL AUDIOBOOK",
    "author": "By Jane Austen"
  },
  "coverImagePrompt": "...",
  "coverWorkspacePath": "workspace/pride_and_prejudice/chapter_038/000_chapter_038.cover.jpg",
  "coverPublishPath": "videos/pride&prejudice/chapter_38/chapter_38-封面.jpg"
}
```

## Quality Bar

Before presenting packaging to the user, verify:

- one final `title` is chosen and presented
- `coverTitle` matches the upload title, not a different hook
- title includes book + chapter + audiobook/format signal
- description matches the chapter and does not spoil later plot
- description bullets are chapter-specific, not generic listening-practice filler
- 4-8 chapter markers map to real segment ids and include the 3-second video intro offset
- `prepare_youtube_packaging.py` has been run after markers were added
- cover scene reflects this chapter, not a generic book cover
- cover is bright/warm enough and avoids dead-black backgrounds or black sidebar layouts
- on-image text is short, readable, and matches `coverTitle`
- cover file exists at the workspace path and is exactly `1920x1080` (or documented custom 16:9 size)
- `normalize_youtube_cover.py` has been run after image generation
- publish path follows the existing `videos/` naming convention

## Agent Reporting

When finishing YouTube packaging, report in chat:

1. the final upload title
2. full chapter description or path to `000_chapter_XXX.youtube_description.txt`
3. timestamp block with video offsets applied
4. cover image path
5. confirm cover uses the same title as upload
6. whether text legibility and overall brightness look acceptable
7. ask the user to confirm title, description, and cover before video upload or final assembly

Do not upload to YouTube from this skill unless the user explicitly asks.
