---
name: polished-english-episode-script
description: 'Produces Series C (Polished English) episodes: Leo & Mia daily-talk B2-C1, narrative engine (thesis-first hook, 起承转合, question-flow acts, micro-pocket, conflict recycle, honest word-tour payoff), anti-listicle discipline, optional YouTube production notes. Markdown + script.json (speed=1.0). Voice_clone: punctuation + pause_after; sparse laughs/fillers.'
---

# Polished English — episode script workflow (content only)

## Mandatory path for this show

For **`series_c`** / **`polished_english`** (Polished English, B2-C1, Leo & Mia), do **not** jump straight to `script.json`. Always:

1. **Read character identity files** for each speaker in the episode (**default**: [`workspace/characters/leo/identity.md`](../../../workspace/characters/leo/identity.md), [`workspace/characters/mia/identity.md`](../../../workspace/characters/mia/identity.md) — see [`workspace/characters/README.md`](../../../workspace/characters/README.md)). Use them for **voice, habits, and Leo–Mia dynamics**; do not contradict them without a deliberate series decision.  
2. **Read show bible**: [`docs/shows/series_c/bible.md`](../../../docs/shows/series_c/bible.md) and strategy [`docs/shows/strategy.md`](../../../docs/shows/strategy.md).  
3. Run this skill → fill **[output-template.md](output-template.md)** (English dialogue + teaching table + **§ Narrative engine** structure map for full episodes).  
4. After user sign-off → emit **`workspace/shows/series_c/episode_XXX/000_episode_XXX.script.json`** using **§ Studio JSON** below.

## Scope

- **Output**: Markdown draft (template) + optional **`script.json`** segment list for Studio compile.
- **Not in scope**: Running TTS yourself unless the user explicitly asks; cover art; YouTube packaging.

## Show voice & default hosts (`polished_english`)

- **Daily talk first**: The show sounds like **two people discussing a topic** — work, habits, social life, language — not a class. **Do not** open or run the episode as “today we teach you…,” “our job is to give you chunks,” or “listen like a student.” Ideas and **usable phrases** ride on **stories, opinions, and back‑and‑forth**, not meta‑lessons about the podcast format.
- **Default hosts (on-mic names)**: **Leo** and **Mia** — read [`workspace/characters/leo/identity.md`](../../../workspace/characters/leo/identity.md) and [`workspace/characters/mia/identity.md`](../../../workspace/characters/mia/identity.md). **Studio wiring**: JSON segment keys remain **`alex`** (Leo’s line) and **`sarah`** (Mia’s line); map to clone voices in `episode.yaml` (`participants: alex: leo`, `sarah: mia`) — see e.g. [`workspace/episodes/polished_english/candidate_89_polish_trial/episode.yaml`](../../../workspace/episodes/polished_english/candidate_89_polish_trial/episode.yaml).
- **Spoken intro hygiene**: **Never** explain internal production ethics on-mic — e.g. “we don’t copy other channels,” “we’re totally independent,” “we’re not like X.” That reads as **defensive** and breaks the fiction of a natural chat. Keep originality rules in **this Skill / bible / registry** only.
- **How “teaching” shows up**: Target language **emerges** in chat; **Leo** may **tighten** a line or name a pattern in **short, conversational** beats — **Mia** grounds it with “what I’d actually say.” Avoid long uninterrupted explanation. The optional end **slow recap** (P0) should sound like **“phrases we kept coming back to”** or **“if you want to pocket these”** — not “vocabulary section” or “now the lesson.”
- **Subscribe / platform CTA**: **Occasionally** include **one light** line (follow / subscribe / save) where it fits the close — **not** every paragraph, not hype trains, no fake PDFs.
- **Default Mia calibration**: Unless the user **explicitly** asks for a “beginner learner” episode, write **Mia** as someone who **already uses English in real life** (work, cities, meetings). She can be wrong about **tactics or ego**, stuck on **plateaus**, or embarrassed by **choices** — she is **not** playing “clueless tourist English.”

## Narrative engine — 起承转合 + retention (full episodes)

Use this for **every** full-length draft when the user only gives a **topic**: it turns “theme → script” into the same **product shape** as the reference episode (cold open, acts, pocket, recycle, word tour, close). **Daily talk** rules still apply — this section is **structure**, not “teacher mode.”

### 起承转合 (mapped)

| Phase | Role | What listeners experience | `polished_english` execution |
|-------|------|---------------------------|------------------------------|
| **起** | **Hook + stake** | “Why should I stay in the first 30–45 seconds?” | **Thesis-first** (recommended): **1–2 sharp lines** — paradox, pain, or promise (e.g. busy ≠ better; coasting vs stretch) **before** or **tightly woven with** the first story beat. Then **evidence** (Mia’s scene, failure, irony). **Scene-first** is allowed if the scene **instantly** carries the stake; still resolve “why stay” within ~**45s**. |
| **承** | **Develop one spine** | Depth, not whiplash | **2–3 threads max** for a full episode (e.g. input → practice → plateau). **Do not** “打地鼠” through many unrelated tips in one act. Each thread: **story / pushback → short tighten** in dialogue. |
| **转** | **Turn / friction** | Mid-episode wake-up | **Pattern interrupt** (e.g. “if you understand 100% of this show every time, you might be coasting”) and/or **Mia pushback** (time, dignity, “I won’t talk to my phone”) so Leo’s answer lands harder. |
| **合** | **Land + carry-out** | Memory + warmth | **Conflict recycle** (see below) → **Word tour** with **honest payoff** → **short close** + optional **like/follow** (one light line). |

### Act transitions — **question flow**, not “course outline”

- **Forbidden** on-mic (breaks daily-talk fiction): “**First pillar** / **Second pillar**,” “**Chapter 2**,” “**Vocabulary section**,” “Today we have **three** things…” as a **syllabus**.
- **Use** instead: “Here’s where people mess up first —,” “**Next friction** —,” “**Last head-trip** to name —,” “**Mile marker** — that was the [input / output / plateau] **piece**,” “There’s a reason your brain checks out —,” etc. Same structure, **natural speech**.

### Micro-pocket (mid-episode)

- **When**: After the **first major thread** lands (often ~**6–12 min** in a long episode).
- **What**: **~20–45 seconds** of dialogue — **2** phrases **already heard**, glossed slowly, friend-to-friend (“tiny pause / pocket these / back to the chat”).
- **Why**: Fights mid-roll **drop-off**; gives a second chance to listeners who zone out.
- **Second pocket**: Only if the episode is **long** and truly needs it — don’t stack pockets every 3 minutes.

### Recycle — **conflict > timetable**

- **Mandatory** for full episodes (unless user waives): reuse thread language in a **new mini-situation**.
- **Prefer** **negotiation**: one host **resists** (“tomorrow is insane,” “I won’t do a spreadsheet week”) — the other offers **tiny, bleak-realistic** steps (elevator seconds, whisper memo, one sentence rewrite). Avoid **Monday–Sunday schedule** readouts unless the user explicitly wants that format; they often sound like **admin**, not conversation.

### Word tour (end) — **honest “stay” line**

- **P0**: **2–4** items, **all pre-heard** in body; English gloss only; longer **`pause_after`** on tour lines in JSON.
- **Before the tour**: **One sentence** that states the **concrete payoff** of listening to the end — e.g. “four phrases we kept using + the **email three-pass** we demonstrated” — **not** fake “secrets” or clickbait you don’t deliver.
- **Optional**: Slow-walk a **movable template** (e.g. blunt / mush / clear) **only** if it already appeared in the episode.

### Anti-listicle discipline (hard rule)

- **Cap** at **2–3 threads** per episode. If you think of a fourth topic (shadowing, grammar Twitter, travel hacks, exam labels…) → **one line** in passing, **cut**, or **save for another episode**.
- **Symptom to fix**: many **short Q&A** blocks on unrelated subtopics in a row — listeners feel **cognitive whiplash**; the spine weakens.

### Title + packaging (optional block in draft)

- **Title (English)**: **Concrete** situation + **outcome** or **paradox**; **original** wording — not generic “Learn English / Tips / Lesson1.”
- **One-line promise**: Must match what the **Word tour** and body **actually deliver** (level + payoff).
- **Lexis teaser**: Align with **Word tour** lemmas only — no bait‑and‑switch.

### Production notes (video / editors) — **not for TTS**

- In the Markdown draft, include **`## Production notes (optional — not for TTS)`** when the episode has **before/after** or **triple examples** (e.g. email tones): suggest **on-screen contrast** (labels, colors, side‑by‑side text) so **YouTube** viewers get value **without** high audio density.
- **Never** put bracketed stage directions into JSON **`text`** unless the compile pipeline explicitly supports them.

## Voice clone: emotion field vs punctuation (mandatory for `polished_english`)

Hosts (**Leo / Mia** in copy; **`alex` / `sarah`** in JSON) use **voice_clone**. The TTS clone path does **not** reliably honor the JSON **`emotion`** tag for performance — treat `emotion` as **documentation for editors** only, not as a prosody control.

**Authors must shape feeling in the spoken text itself:**

- **Punctuation**: commas and periods for breathing; `…` for hesitation or trailing thought; `?` / `!` where natural; em dashes for self-correction or aside — without stuffing the line.
- **Wording**: word choice, contractions, short clauses vs long ones, repetition for emphasis.
- **Rhythm**: split or join lines so TTS reads in the intended cadence; use **`pause_after`** between segments for beats (surprise, turn-taking, word-tour slowness).

Do **not** rely on `emotion` alone to carry surprise, warmth, or urgency.

### Voice clone: laughter & fillers (write into `text`, use rarely)

**Clone models do not “act in”** extended laughter or rich non‑lexical sounds the way a human mic performance might. If a moment needs **amusement**, **thinking time**, or **natural hesitation**, put it in the **spoken line** in **English** — only when **both** context and meaning support it.

| Device | When it fits | How to write (examples) | Avoid |
|--------|----------------|-------------------------|--------|
| **Light laugh / chuckle** | Shared joke lands, defusing awkwardness, warm aside — **not** every banter line | Short cues the model can read: *Ha.* *Heh.* or a single low‑key *Yeah, that’s fair.* + `pause_after` | Stacked *hahahaha*; laughing through **word tour** or dense teaching unless one deliberate beat |
| **Thinking / hesitation** | Searching for a word, polite pushback, self‑correction | *Uh…*, *Um…*, *Hmm…*, *I mean…*, *sort of…* — usually **once** in a turn, not every sentence | *Erm*/*emmm*/*额*‑style spellings; filler **every** line; fillers that **flatten** clarity when a line needs to land cleanly |
| **Reaction crumbs** | Surprise, sympathy, backchannel | *Oh*, *Wow*, *Oof*, *Right?* — keep **short** | Strings of interjections that sound like a transcript dump |

**Rules of thumb**

- **Sparse**: aim for **a few** such moments per **section** (open / body / close), not per line. If in doubt, **omit**.  
- **Match persona**: **Mia** may hesitate or laugh slightly **more** (listener energy); **Leo** stays a bit **cleaner** when **tightening** a phrase, unless the beat is relational banter.  
- **Dense explanation**: default to **clear** sentences; add a filler only if it **sounds like real speech** (e.g. *“So, uh, the softer version would be…”*).  
- **JSON**: still **no** stage directions in brackets unless the pipeline explicitly supports them — laughter and fillers live in **`text`** like any other words.

## Outro: dialogue first, then bed / fade (mixing contract)

Listeners should hear the **last line at full level**, then any **music / bed** eases out **after** speech ends — not ducked under the final sentence.

**Script / JSON:**

- Give the **final segment** a slightly longer **`pause_after`** (often **1.2–3.0 s**, more if a word-tour close) so the exported WAV includes **tail silence** after the last word. That gap is where post-production (or a future bed mix) can **fade the music** without touching the voice.
- Avoid expecting `emotion` or a master fade to “carry” the outro feel; use punctuation + final pause.

**Pipeline (this repo):** Merges **per-segment `pause_after`**, appends silence **after the last utterance**, and applies **fade-in only** on the master — **no** whole-file fade-out on speech, so the last line is not pulled down by a master duck.

## Canonical specs (read if unsure)

- Series bible: [docs/shows/polished_english/bible.md](docs/shows/polished_english/bible.md)
- **Structure theory (transcript-backed, English Leap–class corpus)**: [docs/shows/polished_english/competitor_script_structure_report.md](docs/shows/polished_english/competitor_script_structure_report.md) — §0 **取证** + §0.5–0.7 **量化** + **§0.7.5 我方优先级**；精读样本 §0.2—0.4 用于「话术**功能**」而非逐句借用。
- **Default on-mic hosts**: **Leo** (facilitator, tightens phrases), **Mia** (listener voice, stories) — see `workspace/shows/polished_english/show.yaml` (`leo`, `mia` among `character_ids`).
- **Character assets**: `workspace/characters/leo/` and `workspace/characters/mia/` — each contains `character.yaml` + reference audio + **`identity.md`**. Studio **`participants`** maps JSON keys `alex` → `leo`, `sarah` → `mia`. Do **not** invent new paths under `data/reference_audio/`.
- **Never** name or mirror third-party show hosts; all stories and lines are **original**.

## Inputs the user should provide

1. **Theme** — one sentence plus optional sub-focus (e.g. workplace, social, mindset).
2. **CEFR** — default **B1–B2** unless specified.
3. **Archetype** — pick one:
   - **A — Narrative**: scene → tension → chunks in context → recycle → word tour.
   - **B — Checklist**: hook → N tips with **before/after** → optional short vocab segment → close.
   - **C — Topic-deep**: values/big-topic → advance target lexis early (plain list in meta) → dialogue explores meanings → word tour.
4. **Reference articles** — URLs, excerpts, or pasted notes: use for **ideas and facts only**; **no** long quotes, **no** sentence-level paraphrase of distinctive phrasing from competitors or paywalled sources.

## Competitor-informed writing workflow (public copy → our shape)

**Sources**: [docs/shows/polished_english/bible.md](docs/shows/polished_english/bible.md) (titles, descriptions, CSV window) + [competitor_script_structure_report.md](docs/shows/polished_english/competitor_script_structure_report.md) (**41 集字幕**统计、逐集摘录、§0.7.5）。**Learn structure and *function* of beats, never reuse their wording, hooks, story beats, or branded strings.**

### Episode beat sheet (map dialogue to time — default full episode)

Use as a **skeleton**; compress for smoke tests. Order follows report **§0.0**.

| Phase | ~Time | Job in dialogue | `polished_english` rule |
|-------|-------|-----------------|-------------------------|
| **Open** | 0–3 min | **Stake + hook** (thesis-first or scene-first) + easy hello | **§ Narrative engine — 起**: listener knows **why stay** within ~**30–45s**; then **short** series welcome + Leo/Mia chemistry — **no** classroom preamble, **no** on-mic “we aren’t copying anyone.” |
| **Early contract** | often **first ~3 min** (corpus: many episodes **verbally preview** a later vocab block around **~10–15%** runtime — often *promise*, not the tour itself) | One **casual** line that you’ll **slow down a few phrases** at the end | **P0** per §0.7.5: **friend-to-friend** wording (e.g. “we’ll replay a few phrases slowly”) — **not** “vocabulary lesson next.” |
| **Body** | ~3 min → ~last 5 min | Archetype **A / B / C** as **conversation** — stories, opinions, pushback | **§ 承 + 转**: **2–3 threads max**; **question-flow** transitions; **pattern interrupt** + Mia pushback where useful; optional **Micro-pocket** after first thread; **no** long teacher monologue. |
| **Recycle** | 1.5–3 min | New micro-scene reusing thread language | **§ 合 (partial)**: **conflict recycle** preferred — resist → negotiate tiny real step; **not** mandatory Mon–Sun timetable. Waivable only if user says smoke episode. |
| **Word tour + land** | ~3–5 min | Slow items **already heard**; optional template recap | **P0**: 2–4 items; **honest “stay” line** before tour; **longer `pause_after`** on tour lines; see § Outro for **last** segment. |
| **CTA + close** | final minute | Platform CTA + one **action** or question | Calibrate CTA intensity; **homework / shadow** only if user wants (corpus: not universal). |

### Default production choices (from §0.7.5 — **original execution**)

- **P0**: Early **oral contract** that a **slow end recap** exists + **deliver** it; word-tour lemmas **pre-heard** in body.  
- **P1**: Stable **Leo–Mia** rhythm + **short** hello that fits **daily talk** (avoid cloning competitor **branded** catchphrases).  
- **P2**: Optional **gentle** framing of the recap; optional **“you don’t need every word”**-class reassurance **once** if audience is anxious.  
- **P3**: **Homework / shadow / PDF** only when product or user explicitly commits.

### Pattern map (observed → `polished_english`)

| Layer | Competitor (observed — bible + **subtitle corpus** in structure report) | Our rule |
|--------|--------------------------------------|----------|
| **Spoken length** | Common ~**19–29 min**; sampled quarter **mean ~25:08** | Full episode **20–28 min** unless user sets another band; **smoke**: state cap in meta. |
| **Level copy** | **B1 / B2** (sometimes “strong A2”) | Meta: **CEFR** + optional one-line audience line. |
| **Open** | **Scene**, **brain picture**, or **direct “today we’re talking about…”** (see report §0.7.3 Hook 粗分类) | **Hook** in 2–4 turns; **no** mirrored viral strings or competitor host patterns. |
| **Early vocab signal** | **word tour** often **named early** (median ~**13%** of runtime, often within **~3 min** in corpus — frequently a **preview**) | **P0**: one **original** line that promises a **slow recap** later (see beat sheet). |
| **Mid** | **A** narrative; **B** tips + **before/after**; **C** values + preset lexis | Match **A / B / C**; always **chunk → recycle**; optional reassurance beat. |
| **Close** | **Word tour** / gentle variant; **Repeat** drills in subtitles; **subscribe** nearly ubiquitous in corpus | **Word tour** 2–4 items; **optional** repeat-after / one action; CTA **without** copying their slogans. |
| **Discovery copy** | Long-tail SEO tails; **PDF** in descriptions > in speech | **Our** naming; honest keywords; **no** fake PDF / Drive. |
| **Topic mix** | Life skill × English; lists; occasional buzzwords | **Invent** framing; **do not** copy title formulas verbatim. |
| **Tone** | Emoji hype **vs** calm word-tour promise | Default: **clean, calm, daily conversational** — listeners **overhear** two hosts; emoji only if user asks. |

### Duration & density budget (calibrate before drafting)

Use to size the **Markdown** script (spoken, two hosts, B1–B2):

1. **Hook + problem** — ~2–4 min → ~**300–500** words.  
2. **Body** (conversation, stories, light “polish” beats) — ~**12–18** min → ~**1.8k–2.7k** words.  
3. **Recycle** — ~1.5–3 min → ~**200–450** words.  
4. **Word tour + close** — ~3–5 min → ~**450–750** words.  

**Full episode** (aggregate): **2.6k–4.0k** English words for ~**22–28 min** at natural dialogue pace; **rebalance** if user gives a hard cap. **Smoke tests**: slash every section; meta must state **short** duration.

### Packaging block (optional — after Takeaways in template)

When the user needs **title + description** (YouTube, show notes):

- **Title** (English): benefit + specific situation; **original** wording only.  
- **One-line promise**: outcome + level.  
- **3 bullets**: listener outcomes (start with verbs).  
- **Lexis teaser**: 4–8 items aligned with **Word tour** (same lemmas).  
- **CTA**: replay / practice line; playlist mention only if product exists.

Do **not** paste competitor hashtags, channel slogans, or “Learn English Fast” tail unless user explicitly wants SEO tails—in which case **vary** phrasing.

### Quality bar (format + duration + honesty)

- [ ] **Format**: Archetype A/B/C stated in meta; beats follow **§ Episode beat sheet** (or documented waiver for smoke episodes).  
- [ ] **Early contract (P0)**: Within **first ~3 minutes** of spoken script, hosts **once** promise a **slow end recap** of today’s key phrases (your wording; not copied from structure report quotes). Optionally mention **one mid-episode pocket** if using that format.  
- [ ] **Hook / 起**: First **30–45s** answer “**why stay**” (thesis-first or scene with immediate stake).  
- [ ] **Spine**: **≤3 threads**; no **listicle whiplash** (see § Anti-listicle).  
- [ ] **Transitions**: **No** “pillar / chapter” syllabus on-mic; use **question-flow** bridges.  
- [ ] **Micro-pocket**: Present on **full** episodes after first major thread (unless user waives).  
- [ ] **Recycle**: **Tension** or pushback, not only a calendar grid.  
- [ ] **Word tour**: **Honest payoff** sentence before recap — no undelivered “secrets.”  
- [ ] **Duration**: Meta target matches rough word budget (§ Duration & density).  
- [ ] **Level**: Syntax and vocabulary match declared CEFR.  
- [ ] **Threads / phrases**: Each highlighted phrase **appears in talk** before the slow recap; word-tour items **pre-heard** in dialogue.  
- [ ] **Daily talk**: Reads as **co-host chat**, not a lesson to “students”; **no** defensive on-mic disclaimers about copying or independence.  
- [ ] **Packaging truth**: No inflated level; no promised PDF/word tour missing from script.  
- [ ] **Originality**: No competitor host names; no “English Leap” / *cozy little place* / third-party brand strings in our script or packaging.
- [ ] **Identity**: Dialogue respects each speaker’s **`workspace/characters/<id>/identity.md`** (background, habits, **Leo–Mia** dynamic, red lines).
- [ ] **Clone prosody**: Emotion carried by **punctuation + wording + pause_after**, not by `emotion` alone.  
- [ ] **Laughs / fillers**: If used, they are **few**, **English**, in **`text`**, and **motivated** by context — not wallpaper *uh*/*haha* on every turn (see § Voice clone: laughter & fillers).
- [ ] **Outro**: Final segment has enough **`pause_after`** for a clean speech end before any bed fade.

### Anti-patterns

- Stealing **specific** hooks, numbered list angles, or anecdotes from bible samples / CSV titles or **competitor_script_structure_report §0.6** excerpts.  
- Omitting the **early oral contract** (P0) on a **full** episode while still writing a end recap — listeners get no **structural** anchor.  
- Promising **gentle word tour** (or PDF) in copy but omitting it in the script.  
- Mixing **two description tones** (emoji hype + academic) in one pack without intent.  
- Reusing **metaphor chains** or chunk lists already in [registry.yaml](docs/content/registry.yaml) for this show (check when user cares about series coherence).
- Leaning on **`emotion`** tags instead of **punctuation and line breaks** for voice_clone episodes.
- **Filler / laugh spam** — *uh*, *hmm*, *haha* on most lines, or long *hahaha* strings, or non‑English filler spellings — **distracts** learners and often **does not** render as “natural” on clone TTS anyway.
- **Short or zero** `pause_after` on the **last** segment when a musical outro is planned — leaves no room to fade bed after speech.
- **On-mic “ethics disclaimers”** — independence, plagiarism, “we’re not like channel X” — **breaks** daily-talk fiction; keep those rules in **writer docs only**.
- **Syllabus voice** — “first pillar, second pillar,” “today three things,” “vocabulary section” as **course outline**.
- **Listicle sprawl** — many unrelated subtopics (shadowing + grammar + travel + exams…) in one episode; **cut** or **move** to future episodes.
- **Word tour bait** — promising a “secret” or template at the end that **never appeared** in the body.
- **Mia as default beginner** — unless the brief says so; default is **experienced user** with human setbacks.
- **Over-writerly Mia** — constant punchline slogans / meme density; keep her **spoken** and **pushback‑driven**.

## Workflow (execute in order)

### 1) Ingest references

- Extract: definitions, mechanisms, 1–2 memorable **facts** (with light attribution in meta, e.g. “after User ref: …”), tensions, and **misconceptions** to debunk.
- Discard: catchy title wording, anecdote structure, or jokes from references — replace with **new** scenes.

### 2) Optional anti-repeat (repo)

- If the user cares about series consistency, skim [docs/content/registry.yaml](docs/content/registry.yaml) and [docs/kb/topics/](docs/kb/topics/) for overlapping episode titles/topics; avoid repeating the same **metaphor chain** or **chunk list** as a recent episode.

### 3) Design 1–3 **threads** (phrases / ideas to land)

- Each thread = a **communicative move** or **sticky idea** you want listeners to **carry** (e.g. softening a claim, naming a plateau, choosing input at the right difficulty).
- Each thread: **first** natural use in dialogue → **then** a **short** tighten or rephrase in **conversation** (usually **Leo** naming it, **Mia** trying it) — **not** a seminar.
- Tie to **register** (formal / neutral / informal) only when it helps the chat sound real for B1–B2.

### 4) Draft dialogue

- **Size** sections using **§ Duration & density budget** (full vs smoke) before writing long body text.
- **Plan the spine**: From the user **theme**, lock **2–3 threads** only; write them in the **Teaching plan** table in the template. Everything else is **cut or next episode**.
- **Structure map**: In the Markdown draft, add a **Structure map** table (time bands + focus + **spoken** transition style) — see [output-template.md](output-template.md).
- **Open — §起**: **Thesis-first cold open** (recommended) or scene-first with immediate stake; then **short** show hello — see **§ Narrative engine** and report §0.2—0.4 for *hook function*.
- **Early contract (P0)**: After hook stabilizes, **one** turn pair: **slow end recap** + optional **mid pocket** (friend-to-friend wording).
- **Body — § 承 + 转**: Archetype **A / B / C** as **daily talk**; **question-flow** act changes; **pattern interrupt** + **Mia pushback** where useful; **Micro-pocket** after first thread (full episodes).
- **Reassurance**: optional **one** line if B1 listeners may freeze (**original** wording). **Sparse** laughs/fillers in **`text`** only when needed (§ **Voice clone: laughter & fillers**).
- **Recycle — § 合 (partial)**: **Conflict recycle** — reuse thread language under **resistance** → **tiny compromise**; avoid dry week-grid unless requested.
- **Word tour**: **2–4** items, **pre-heard**; **honest stay payoff** line before tour; optional **template** recap if demonstrated in body; longer **`pause_after`** on tour lines in JSON.
- **Close**: warm landing; optional **one** listener question (English); **occasional** light **follow / subscribe / save**; **last JSON segment**: generous **`pause_after`** (see § Outro).
- **Production notes**: If before/after or triple examples → add **`## Production notes (not for TTS)`** for editors (on-screen labels, chapters).

### 5) Quality gates (blocker if failed)

Run the checklist in **§ Competitor-informed writing workflow → Quality bar** plus:

- [ ] 100% **original** examples; no competitor “skin” or mirrored episode arcs.
- [ ] **Spoken-length intent** in meta matches word budget (full vs short).
- [ ] Optional **packaging** (if any) matches script content (level, lexis, CTAs).

### 6) Export to Studio `script.json` (when user wants compile/render)

Build a **JSON array** of segments. Each object:

| Field | Rule |
|-------|------|
| `id` | Stable slug, unique. |
| `speaker` | `alex` (**Leo**’s audio via `participants`) or `sarah` (**Mia**’s audio) — lowercase keys; see `episode.yaml`. |
| `text` | English line; on-mic names **Leo** / **Mia** in prose; no bracket stage directions unless the pipeline explicitly supports them. **Encode emphasis and tone with punctuation** (clone path ignores `emotion` for performance). |
| `emotion` | Optional tag for humans / non-clone tooling; **do not** use it as the primary prosody lever for Leo/Mia clones. |
| `pause_after` | Seconds of silence **after** this segment (between lines **and** **after the final line** — use a longer value on the **last** segment for outro tail / bed fade). |
| `speed` | **Must be the number `1.0`** on every segment. Omit only if your toolchain re-injects default — in this repo, **always write `1.0`** for clarity. Non-unity values **fail Pydantic validation**. |

Order segments in speak order. After writing JSON, point the user to:

`python -m src.cli studio compile polished_english <slug>` then `python -m src.cli render --studio-episode polished_english <slug>` (or `scripts\invoke-python.cmd` on Windows).

## Output format

Fill [output-template.md](output-template.md). Deliver **one** continuous artifact: meta + teaching table + full script sections in that order. When exporting JSON, either append a fenced `json` block at the end of the chat or write the file under `workspace/polished_english/episode_XXX/000_episode_XXX.script.json` if the user asked for a full pipeline handoff. Episode numbers are internal only — see `workspace/polished_english/README.md`.

**Line format** (Markdown phase only):

```text
**Leo** — …
**Mia** — …
```

Use em dashes or consistent plain hyphen per file — do not mix styles within one draft. (**JSON** still uses `alex` / `sarah` keys mapped to **leo** / **mia** voices.)

## Tone

- **Daily talk**: warm, human, **overheard conversation** — not a class.
- Prefer **back-and-forth**; solo stretches stay **short**.
- Humour: light, original, tied to the scene — not meme dumps.

## Reference articles — allowed use

| Allowed | Disallowed |
|---------|------------|
| Facts, models, statistics (paraphrased) | Copying hook sentences or titles |
| Structural “problem space” | Same anecdote order or punchline |
| Terminology the user explicitly wants taught | Pasting copyrighted paragraphs |

If the user supplies only one thin article, **invent** contrasting viewpoints in dialogue while staying truthful to the theme.

## When the user omits archetype

- Default **A (narrative)**.
- If the theme is explicitly “N ways to…”, “tips”, “habits”, use **B**.
- If the theme is values/money/success/life philosophy with sparse “how-to”, use **C**.

**Hook shape** (optional picker — **invent** execution): see structure report **§0.7.3** (*H1*悬念/画面, *H5* 直球话题, *H2* 情绪契约, etc.). Use only as **category**, never as copy-paste wording.
