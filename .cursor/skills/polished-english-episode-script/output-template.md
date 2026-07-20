# Episode script draft — `polished_english` (content only)

> Copy this file per episode. Replace angle brackets. **Dialogue must be English.** Meta may be Chinese or English. **On-mic names**: **Leo** & **Mia** (daily talk, not a classroom show).

---

## Episode meta

- **Working title**: <short English title>
- **Theme** (user-specified): <…>
- **CEFR target**: <B1 | B2 | B1–B2>
- **Archetype**: <A narrative | B checklist | C topic-deep> (see SKILL.md — informs **conversation shape**, not a lesson plan)
- **Target length band**: full episode **~20–28 min** spoken (see SKILL.md § Duration & density); **short/smoke**: state cap (e.g. &lt;2 min)
- **Reference use**: <bullets: ideas from research or articles; paraphrase only — no long quotes>
- **Identity files** (read before dialogue): [`workspace/characters/leo/identity.md`](../../../workspace/characters/leo/identity.md), [`workspace/characters/mia/identity.md`](../../../workspace/characters/mia/identity.md)

---

## Teaching plan (internal consistency)

| Thread ID | What you want listeners to remember | Key phrase / idea | First appears (beat) |
|-----------|-------------------------------------|-------------------|----------------------|
| T1 | … | … | … |
| T2 | … | … | … |
| T3 | … | … | … |

**Recycle**: In beat **R**, **conflict recycle** — Leo and Mia **reuse T1–T2** language while one **resists** (time, dignity) and the other **negotiates** a tiny realistic step — still **natural talk**, not a Mon–Sun timetable unless the brief asks for it.

**Micro-pocket** (full episodes): after **T1** lands, **~20–45s** — **2** phrases **already heard**, slow gloss, then “back to the chat.”

**Word tour** (slow, **2–4** items): phrases **already used** in chat; **before** the tour, **one honest line** on why staying helps (concrete payoff — no fake “secrets”). Optional: recap a **movable template** if the body demonstrated it. Sound like **friends summarizing**.

**Narrative spine**: See **SKILL.md § Narrative engine (起承转合)** — thesis-first hook, **question-flow** act bridges (no “pillar” syllabus on-mic).

---

## Structure map (for editors — full episodes)

| Block | ~Time | Focus | Spoken transition (example vibe, not fixed wording) |
|-------|-------|--------|------------------------------------------------------|
| Cold open | 0:00–~1:00 | **起** — stake + first evidence | thesis-first or scene + immediate “why stay” |
| Act 1 | … | T1 | “sweet spot / mess-up first” |
| Micro-pocket | … | 2 phrases | “tiny pause / pocket / back to chat” |
| Act 2 | … | T2 + **转** pushback / pattern interrupt | “next friction — output” |
| Act 3 | … | T3 + recycle **R** | “last head-trip — plateau” or natural |
| Word tour + close | … | **合** — recap + CTA | honest payoff → slow phrases |

---

## Script — dialogue

Use **subsection headings** in the draft for clarity (e.g. `### Cold open`, `### Act 1`, `### Micro-pocket`, …). They are **not** read aloud.

**Leo** — …
**Mia** — …

(Continue in alternating turns. **Daily talk**; **Voice_clone**: prosody in **punctuation** + `pause_after`, not `emotion`.)

---

## Recycle mini-scene

**Leo** — …
**Mia** — …

---

## Word tour

**Leo** — …
**Mia** — …

---

## Close

**Leo** — …
**Mia** — …

Punctuate the **last** spoken line for a clear landing. In **`script.json`**, set a **longer `pause_after` on the final segment** (often **1.2–3.0 s**) for tail silence / bed fade.

**Optional listener prompt** (one question, English): …

---

## Takeaways (publishable bullets)

- …
- …

---

## Publish packaging (optional — YouTube / show notes)

Only if the user needs discovery copy. Follow **SKILL.md § Packaging block**; original wording only.

- **Title** (English): concrete **pain / paradox + outcome**; **original** — not generic “Learn English Tips / Lesson 1.”
- **One-line promise** (+ level): …
- **3 outcome bullets** (verbs): …
- **Lexis teaser** (matches Word tour): …
- **CTA** (replay / follow; no fake PDF): …

---

## Production notes (optional — not for TTS)

If the episode has **before/after** or **triple examples** (e.g. email blunt / mush / clear), note **on-screen contrast** for editors (labels, lower-thirds). **Do not** put these brackets into JSON `text` unless the pipeline supports them.

---

## Studio `script.json`（定稿后由本 Skill 导出）

仅当用户要 **compile / render** 时，基于上文转成 JSON 数组。硬约束：

- 每段 **`"speed": 1.0`**；节奏靠 **`"pause_after"`** 与标点。  
- **`pause_after`**：接在该段**之后**的静音秒数；**最后一段**宜略长。  
- `"speaker"`：`alex`（**Leo** 声线）| `sarah`（**Mia** 声线）—与 `episode.yaml` 的 `participants` 一致。  
- `text` 里写 **Leo / Mia** 的自述与对白即可。

参考音：`workspace/characters/leo/` 与 `workspace/characters/mia/`（`character.yaml` + `reference.wav` + `reference_text`）。
