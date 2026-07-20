# Series C — Polished English Style Guide

Human-feel dialogue rules, thesis-first hooks, and narrative engine for Leo & Mia (B2–C1).

Reference: [`competitor_script_analysis.md`](../../../docs/shows/competitor_script_analysis.md) + [`docs/shows/series_c/bible.md`](../../../docs/shows/series_c/bible.md) + character identity files.

## C.1 Frozen cold-open chassis (use verbatim every episode)

```
[Music sting]
Leo:  Hey. Welcome back to Polished English, the show where two people talk
      about real life, and you overhear the English you actually need.
Mia:  I'm Mia.
Leo:  And I'm Leo. And this is the English Listening Room. [+ thesis-first hook line]
```

Rules:
- **Mia intros first** (listener voice), **Leo second** (facilitator) — Mia leads with story/feeling, Leo tightens.
- Wait — per character dynamics, Leo is the facilitator who tightens phrases; Mia is the listener voice. Class pattern is teacher-first; J&May is teacher-first. For C, the "lead" is the listener-voice (Mia) because the show is daily-talk not classroom. So **Mia first**, **Leo second**.
- Dual intro lives inside the welcome sentence, fused with hook.
- "English Listening Room" spoken once right after dual intro — brand beat.
- Hook: **thesis-first** (recommended) — 1–2 sharp lines (paradox / pain / promise) before or tightly woven with the first story beat. Scene-first allowed if scene instantly carries stake; still resolve "why stay" within ~45s.

## C.2 Hook templates (pick one per episode)

| ID | Pattern | Template | When |
|---|---|---|---|
| T1 | Thesis-first paradox (default) | "Busy doesn't mean better. Sometimes the busy work is the thing keeping you small." | Mindset / philosophy |
| T2 | Thesis-first pain | "You already know the word. You just can't reach it in the meeting." | Workplace / performance |
| T3 | Scene-first with immediate stake | "It's 11pm. You're rewriting the same email for the fourth time. Why?" | Relatable scene |
| T4 | Pattern-interrupt | "If you understand 100% of this show every time, you might be coasting. And coasting is its own problem." | Self-assessment |

## C.3 Human-feel dialogue rules

### Rhythm — daily talk, not classroom
1. **Strict alternation as default** (Leo→Mia→Leo→Mia).
2. **Multi-line runs allowed**: same host may take 2–3 consecutive turns for a brief story or tightening beat. Max 4 sentences.
3. **Short reactive beats as handoffs**: `Yeah.` / `Right?` / `Exactly.` / `Mhm.` / `Oh, that's good.` — connective tissue.
4. **Long/short sentence variation**: short (≤8 words) and medium (12–20 words) alternate. Avoid 3+ long sentences in a row.
5. **Mia pushback**: Mia resists, questions, or pushes back at least once per episode (time, dignity, "I won't talk to my phone"). This is what makes Leo's answer land harder.
6. **Leo tightens**: Leo names a pattern or tightens a phrase in short conversational beats; Mia grounds it with "what I'd actually say."

### Fillers (human feel, sparse)
- **Mia — slightly more**: `uh`, `um`, `hmm`, `I mean`, `sort of` allowed 1 per 6–8 Mia turns. Listener energy.
- **Leo — cleaner**: near-zero fillers when tightening a phrase; may use one in relational banter.
- **Backchannels allowed freely**: `Mhm`, `Hmm`, `Oh`, `Oof`, `Right?`.
- **Light laugh**: `Ha.` / `Heh.` / single low-key `Yeah, that's fair.` — only when context supports, never stacked (`hahahaha` forbidden).
- **Forbidden**: `emmm`/`额` spellings; filler every line; laughing through word tour.

### Inline polish (signature move)
Target language **emerges** in chat. When a strong phrase first appears, Leo may **tighten** it in a short beat:

```
Mia:  So I said, "Let's circle back on that next week."
Leo:  Right — "circle back" is softer than "we'll talk later." It keeps the door open.
Mia:  Yeah. It sounds like a plan, not a brush-off.
```

Happens ~6–8× per episode. This is "polish" not "lesson."

### Emotion / delivery cues
Every turn carries `[Delivery: …]` per DELIVERY.md. Cues are natural-language performance phrases:
- Good: `warm facilitator, leaning in`, `listener pushback, half-joking`, `quiet conviction`, `self-conscious confession`, `amused recognition`
- Avoid: `dramatic`, `shouting`, `excited`, `happy`, `sad`

### Voice clone prosody (critical)
The TTS clone path does **not** reliably honor `emotion` tags. Authors must shape feeling in the **spoken text**:
- **Punctuation**: commas/periods for breathing; `…` for hesitation; `?`/`!` where natural; em dashes for self-correction.
- **Wording**: contractions, short vs long clauses, repetition for emphasis.
- **Rhythm**: split or join lines so TTS reads the intended cadence.
- **`pause_after`**: between segments for beats (surprise, turn-taking, word-tour slowness); longer on the final segment for outro tail.

Do **not** rely on `emotion` alone to carry surprise, warmth, or urgency.

## C.4 起承转合 structure (C series: 20/40/25/15)

| Phase | Word position (of ~2000–2800) | Content |
|---|---|---|
| 起 (20%) | 0–20% | Cold-open sting → welcome + show name → dual intro → **thesis-first hook** (paradox/pain/promise) → short story beat → early contract (one line promising slow end recap) → B2/C1 callout |
| 承 (40%) | 20–60% | 2–3 threads max, each: story / pushback → short tighten in dialogue. **Question-flow** transitions (no "pillar/chapter" syllabus). Optional **micro-pocket** after first thread (~20–45s, 2 phrases already heard, friend-to-friend). |
| 转 (25%) | 60–85% | **Pattern interrupt** + **Mia pushback** (resistance → tiny compromise). **Conflict recycle** — reuse thread language in a new mini-situation under negotiation, not a Mon–Sun timetable. |
| 合 (15%) | 85–100% | **Honest stay payoff** line (concrete payoff of listening to end) → **Word tour** 2–4 items, all pre-heard, English gloss only, longer `pause_after` → short close → optional one light follow/subscribe → sign-off: `This is Mia. / And this is Leo. / And you've been listening to Polished English, from the English Listening Room. Bye.` |

## C.5 Series C differentiation (vs Class & J&May)

- **Daily talk fiction** — sounds like two people discussing a topic, not a class. No "today we teach you," no "listen like a student."
- **Thesis-first hook** — Class uses scene/confession; J&May uses contrarian-number. C uses thesis-first paradox/pain (more intellectual, B2-C1).
- **Mia pushback** — neither competitor has real pushback; C makes it a structural requirement (转).
- **Per-turn `deliveryCue`** — audiobook parity (neither competitor has this).
- **Brand name spoken** — "English Listening Room" once per episode.
- **Anti-listicle discipline** — cap 2–3 threads; no cognitive whiplash.
- **Honest word tour** — no bait-and-switch "secrets"; payoff line before tour.

## C.6 Title formula

`[Concrete situation] + [outcome or paradox] | Polished English Podcast B2-C1`

Examples:
- `When busy keeps you small — the English of doing less better | Polished English Podcast B2-C1`
- `The email you rewrote four times — softening claims at work | Polished English Podcast B2-C1`

## C.7 Forbidden anti-patterns

- Stealing specific hooks, numbered list angles, or anecdotes from competitor samples.
- Omitting the early oral contract (P0) on a full episode while still writing an end recap.
- Promising a word tour / PDF in copy but omitting it in the script.
- On-mic "ethics disclaimers" (independence, plagiarism, "we're not like channel X").
- Syllabus voice ("first pillar," "today three things," "vocabulary section").
- Listicle sprawl (many unrelated subtopics in one episode).
- Word tour bait (promising a "secret" that never appeared in body).
- Mia as default beginner (unless brief says so).
- Over-writerly Mia (constant punchline slogans / meme density).
- Leaning on `emotion` tags instead of punctuation + wording + pause_after.
- Filler / laugh spam (`uh`/`hmm`/`haha` on most lines).
- Short or zero `pause_after` on the last segment when a musical outro is planned.

## Revision history

- 2026-07-19: Initial Series C style guide (consolidates polished-english-episode-script + audiobook-parity delivery cues + brand name + human-feel dialogue).
