# Series B — Delivery Cue Specification

Audiobook-parity emotion model for Riley & Sam. Borrowed from `.cursor/skills/audiobook-chapter-tts/CONTROLS.md`.

## Two-layer model

### Layer 1 — characterProfiles (stable, in header)

One stable voice cue per host, prepended to every turn at render time:

```json
"characterProfiles": {
  "Riley": "Riley, clear coach, patient steady, consistent manner",
  "Sam":   "Sam, hesitant friend, warm slightly unsure, consistent manner"
}
```

### Layer 2 — deliveryCue (per turn, in markdown)

Natural-language performance phrase describing a small delivery shift.

In markdown draft, write as a block before the turn:

```
[Delivery: hesitant learner, searching for words]
Sam:   Um... so "used to" is only for the past?
```

## How cues compose at render time

`compose_control()` builds: `({profile}, {deliveryCue}) {text}`

Example for Sam:
```
(Sam, hesitant friend, warm slightly unsure, consistent manner, hesitant learner, searching for words) Um... so "used to" is only for the past?
```

## Good cue examples

**Sam (learner) cues:**
- `hesitant learner, searching for words`
- `relieved understanding`
- `surprised recognition`
- `self-conscious confession`
- `amused at own mistake`
- `gaining confidence`
- `genuine question, no rush`

**Riley (coach) cues:**
- `patient clear explanation`
- `warm praise, slight smile`
- `gentle correction`
- `encouraging coach, leaning in`
- `thoughtful, slowing down`
- `steady reassurance`

## Avoid

- Flat labels: `dramatic`, `shouting`, `excited`, `happy`, `sad`
- Vague: `emotional`, `different voice`
- Over-the-top: `wildly excited`, `furious`

## Filler and backchannel handling

Fillers (`uh`, `emmm`, `hmm`, `you know`) and backchannels (`Mhm`, `Oh`, `Wait`) are written **inline in the text**, not in the delivery cue:

```
[Delivery: hesitant learner, searching for words]
Sam:   Emmm... so when I say "nice to meet you", that's already an intro?
```

**Sam filler budget**: 1 per 4–6 Sam turns. Use `uh`, `emmm`, `hmm`, `you know`.
**Riley filler budget**: near-zero. Only `Okay.` / `Right.` / `Mhm` as backchannels.

## Emotion field (optional, for JSON handoff)

When converting to `script.json` for the manifest, each turn may carry an `emotion` summary:

```json
{
  "speaker": "Sam",
  "text": "Emmm... so when I say 'nice to meet you', that's already an intro?",
  "deliveryCue": "hesitant learner, searching for words",
  "emotion": "curious"
}
```

`emotion` is a one-word summary for QC tooling; `deliveryCue` is what the renderer uses.

## Revision history

- 2026-07-19: Initial Series B delivery spec (audiobook parity, asymmetric filler budget).
