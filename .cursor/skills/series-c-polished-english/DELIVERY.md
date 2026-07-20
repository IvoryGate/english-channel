# Series C — Delivery Cue Specification

Audiobook-parity emotion model for Leo & Mia. Borrowed from `.cursor/skills/audiobook-chapter-tts/CONTROLS.md`.

## Two-layer model

### Layer 1 — characterProfiles (stable, in header)

One stable voice cue per host, prepended to every turn at render time:

```json
"characterProfiles": {
  "Leo": "Leo, facilitator, warm precise, consistent manner",
  "Mia": "Mia, listener voice, warm slightly self-aware, consistent manner"
}
```

### Layer 2 — deliveryCue (per turn, in markdown)

Natural-language performance phrase describing a small delivery shift.

In markdown draft, write as a block before the turn:

```
[Delivery: listener voice, slightly self-conscious]
Mia:  So I rewrote that email four times. Same email. Four times.
```

## How cues compose at render time

`compose_control()` builds: `({profile}, {deliveryCue}) {text}`

Example for Mia:
```
(Mia, listener voice, warm slightly self-aware, consistent manner, listener voice, slightly self-conscious) So I rewrote that email four times. Same email. Four times.
```

## Good cue examples

**Leo (facilitator) cues:**
- `quiet conviction`
- `facilitator tightening, conversational`
- `warm, leaning in`
- `pattern interrupt, direct`
- `patient, slowing down`
- `practical, steady`
- `warm landing`

**Mia (listener voice) cues:**
- `listener recognition, slight laugh`
- `listener pushback, half-joking but real`
- `self-conscious confession`
- `amused recognition`
- `reluctant but willing`
- `genuine question, no rush`
- `applying to self, half-joking`

## Avoid

- Flat labels: `dramatic`, `shouting`, `excited`, `happy`, `sad`
- Vague: `emotional`, `different voice`
- Over-the-top: `wildly excited`, `furious`

## Voice clone prosody (critical)

The TTS clone path does **not** reliably honor `emotion` tags. Shape feeling in the **spoken text**:

- **Punctuation**: commas/periods for breathing; `…` for hesitation; `?`/`!` where natural; em dashes for self-correction or aside.
- **Wording**: contractions, short vs long clauses, repetition for emphasis.
- **Rhythm**: split or join lines so TTS reads the intended cadence.
- **`pause_after`**: between segments for beats; longer on final segment for outro tail.

Do **not** rely on `emotion` alone to carry surprise, warmth, or urgency.

## Filler and backchannel handling

Fillers (`uh`, `um`, `hmm`, `I mean`) and backchannels (`Mhm`, `Oh`, `Oof`, `Right?`) are written **inline in the text**, not in the delivery cue:

```
[Delivery: listener voice, searching]
Mia:  Um... so "circle back" is softer than "we'll talk later"?
```

**Mia filler budget**: 1 per 6–8 Mia turns. Use `uh`, `um`, `hmm`, `I mean`, `sort of`.
**Leo filler budget**: near-zero when tightening a phrase; may use one in relational banter.

## Light laugh (rare, motivated)

Only when context supports — shared joke, defusing awkwardness, warm aside. Never every banter line.

```
[Delivery: amused recognition, slight laugh]
Mia:  Ha. Four times. I know that feeling.
```

- Allowed: `Ha.` / `Heh.` / single low-key `Yeah, that's fair.`
- Forbidden: stacked `hahahaha`; laughing through word tour or dense teaching.

## Emotion field (optional, for JSON handoff)

When converting to `script.json` for the manifest, each turn may carry an `emotion` summary:

```json
{
  "speaker": "sarah",
  "text": "Um... so 'circle back' is softer than 'we'll talk later'?",
  "deliveryCue": "listener voice, searching",
  "emotion": "curious",
  "pause_after": 0.4,
  "speed": 1.0
}
```

`emotion` is a one-word summary for QC tooling; `deliveryCue` is what the renderer uses. Do **not** use `emotion` as the primary prosody lever for clones.

## Revision history

- 2026-07-19: Initial Series C delivery spec (audiobook parity, asymmetric filler budget, voice clone prosody rules).
