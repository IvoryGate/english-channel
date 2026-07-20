# Polished English Show Profile

Use this profile when the user asks for `polished_english`, Leo and Mia, a polished daily-talk English episode, or a show-shaped script rather than a simple lesson.

## Show Positioning

`polished_english` is a two-host daily-talk English learning show. It should sound like Leo and Mia are talking through a real topic together, not delivering a classroom lesson.

- Default hosts: `Leo` and `Mia`.
- Default level: B1-B2 unless the user specifies otherwise.
- Default shape: a formal episode is 15-20 minutes; short or smoke drafts must state the shorter target.
- Read character identities before drafting when available:
  - `workspace/characters/leo/identity.md`
  - `workspace/characters/mia/identity.md`
- Use research and competitor material for aggregate structure only. Never copy hooks, title formulas, anecdotes, branded lines, or transcript passages.

## Host Roles

- Leo: facilitator and phrase tightener. He names useful patterns briefly, keeps the spine clear, and avoids long lectures.
- Mia: listener energy and real-world friction. By default she already uses English in life and work; she is not a clueless beginner unless the brief says so.
- Teaching emerges from the conversation. The hosts can name phrases, but the episode should feel like a useful chat that happens to teach.
- Do not include on-mic production ethics such as "we are not copying other channels" or "this is independent."

## Episode Organization

When the user gives only a topic, turn it into this product shape:

| Block | Job | Rule |
| --- | --- | --- |
| Cold open | Hook + stake | In the first 30-45 seconds, answer why the listener should stay. Prefer a thesis-first paradox, pain, or promise, then evidence from a scene. |
| Host intro | Series identity | After the hook, add a very short "I'm Leo / I'm Mia" style intro when writing a formal episode. Keep it under about 15 seconds, avoid catchphrases, and immediately reconnect it to the episode problem. Do not open with host names before the hook. |
| Early contract | Retention signal | Once the hook settles, casually promise a slow recap or word tour later. Say it friend-to-friend, not as a "vocabulary section." |
| Body | Develop one spine | Use 2-3 threads only. Each thread should be story or pushback -> short phrase tightening -> natural example. |
| Micro-pocket | Mid-episode reset | For full episodes, after the first thread lands, slow down 2 phrases already heard for 20-45 seconds, then return to the chat. |
| Turn | Wake-up friction | Add one pattern interrupt, disagreement, embarrassment, time pressure, or dignity problem so the advice has resistance. |
| Recycle | Apply under pressure | Reuse thread language in a new mini-scene where one host resists and the other negotiates a tiny realistic next step. Prefer conflict over a dry Monday-Sunday plan. |
| Word tour | Memory payoff | End with 2-4 phrases already used in the body. Before the tour, give one honest line about the concrete payoff of staying. |
| Close | Warm landing | One listener action or light follow/save line when it fits. Do not over-CTA. |

## Archetypes

- A - Narrative: scene -> tension -> phrases in context -> recycle -> word tour. Default for most topics.
- B - Checklist: hook -> a small number of tips with before/after examples -> practice -> word tour. Use only when the brief is explicitly list-shaped.
- C - Topic-deep: values or big topic -> key lexis seeded early -> dialogue explores meanings -> word tour. Use for mindset, money, success, identity, or culture topics.

## Thread Discipline

- Cap full episodes at 2-3 threads.
- A thread is a communicative move or sticky idea the listener can carry, not just a subtopic.
- For formal episodes, prefer the series mechanism: one real problem -> one phrase cluster -> one usable sentence the listener can adapt today.
- If a fourth idea appears, cut it, mention it in one line, or save it for another episode.
- Avoid explaining the same concept four ways. Once a term is clear, move into a new scene, example, objection, or application.
- Add a little human drift: one 5-15 second aside, callback, or joke per major act is useful. It should reveal host personality and then return to the spine.
- Avoid "pillar", "chapter", "first/second/third thing", and "vocabulary section" as on-mic syllabus language.
- Use question-flow transitions: "Here's where it gets awkward", "Next friction", "The part people miss is...", "Tiny pause, pocket this", "Last head-trip to name."

## Formal Duration Budget

For a publishable `polished_english` episode, target 15-20 minutes unless the user asks for a smoke demo.

- Spoken words: about 1.9k-2.8k English words.
- Cold open + brief host intro: 180-300 words.
- Act 1: 450-650 words.
- Micro-pocket: 80-140 words.
- Act 2: 550-800 words.
- Recycle: 300-500 words.
- Word tour + close: 250-450 words.

If a script is only 4-6 minutes, label it as a smoke demo and do not treat it as a formal episode.

## Emotion And Delivery Control

The current generation path should use explicit emotional intent and delivery notes. Do not rely on old `speed` fields.

In Markdown drafts, add a short delivery note when a section needs a clear performance shift:

```text
[Delivery: warm pushback, medium energy, amused but not silly]
Leo: ...
Mia: ...
```

For TTS or render handoff manifests, prefer fields like these if the current pipeline supports them:

```json
{
  "speaker": "leo",
  "text": "That's the trap, though. Fluent is not the same as fast.",
  "emotion": "calm conviction",
  "delivery": "slow the first sentence slightly; land the contrast",
  "intensity": 2
}
```

Guidelines:

- `emotion` names the feeling: warm, amused, skeptical, relieved, embarrassed, thoughtful, encouraging, calm conviction.
- `delivery` gives a human-readable performance instruction: shorter beats, softer landing, quick aside, slight hesitation, clean recap.
- `intensity` is 1-3. Use 1 for subtle, 2 for clear, 3 only for rare high-energy moments.
- Punctuation still matters: commas, periods, ellipses, questions, and line breaks should support the intended reading.
- Use laughter and fillers sparingly in spoken text: "Ha.", "Hmm...", "I mean...", "Oof." Avoid filler on most lines and avoid long "hahaha" strings.
- Word tour lines should be calm and clear; do not overload them with jokes or heavy acting.

## Output Additions

For `polished_english`, include these blocks in the draft:

```text
Title: ...
Description: ...
Target Level: B1-B2
Estimated Duration: ...
Hosts: Leo, Mia
Show Profile: polished_english
Archetype: A narrative | B checklist | C topic-deep
Learner Problem: ...
Key Phrases: ...

[Teaching Plan]
T1: ...
T2: ...
T3: ...

[Structure Map]
Cold open: ...
Host intro: ...
Early contract: ...
Micro-pocket: ...
Recycle: ...
Word tour: ...

[Intro Hook]
Leo: ...
Mia: ...
```

Dialogue line format should be `Leo: ...` and `Mia: ...` for validator compatibility. Markdown emphasis around names is optional, but plain `Name:` is preferred in saved drafts.

## Publish Packaging

When the user asks for YouTube or show notes, include:

- Title: concrete situation plus outcome or paradox.
- One-line promise: must match the body and word tour.
- Three outcome bullets beginning with verbs.
- Lexis teaser: 4-8 items aligned with the word tour.
- CTA: replay, practice, follow, or save; no fake PDFs or unavailable resources.

## Quality Bar

Before presenting a polished draft, check:

- The first 30-45 seconds carry a clear stake.
- Formal episodes hook first, then introduce Leo/Mia briefly, then reconnect to the topic.
- The early contract previews the later slow recap or word tour.
- There are no more than 3 threads.
- The script is long enough for the requested format: 15-20 minutes for formal episodes, explicitly labeled if shorter.
- The episode does not repeat one explanation under new wording; each act adds a scene, objection, example, or usable transformation.
- The episode uses question-flow transitions, not syllabus labels.
- A full episode has a micro-pocket after the first major thread unless intentionally waived.
- The recycle scene has friction or resistance.
- Every word-tour item was already heard in the body.
- Leo and Mia match their roles and identities.
- Delivery notes or emotion fields exist where performance matters.
- No `speed` field is required or recommended.
