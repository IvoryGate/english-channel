# Series A — Delivery Cue Specification

Audiobook-parity emotion model for Ethan & Nora. Borrowed from `.cursor/skills/audiobook-chapter-tts/CONTROLS.md`.

## Two-layer model

### Layer 1 — characterProfiles (stable, in header)

One stable voice cue per host, prepended to every turn at render time:

```json
"characterProfiles": {
  "Ethan": "Ethan, curious learner, warm slightly hesitant, consistent manner",
  "Nora": "Nora, warm peer coach, steady encouraging, consistent manner"
}
```

### Layer 2 — deliveryCue (per turn, in markdown)

Natural-language performance phrase describing a small delivery shift. Active verbs over flat labels.

In markdown draft, write as a block before the turn:

```
[Delivery: hesitant learner realizing]
Ethan: Oh. So "used to" is only for the past?
```

## How cues compose at render time

`compose_control()` builds: `({profile}, {deliveryCue}) {text}`

Example for Ethan:
```
(Ethan, curious learner, warm slightly hesitant, consistent manner, hesitant learner realizing) Oh. So "used to" is only for the past?
```

## Good cue examples (verb-forward, restrained)

- `warm encouragement rising`
- `hesitant learner realizing`
- `quiet conviction`
- `playful pushback`
- `self-conscious confession`
- `steady patient explanation`
- `relieved understanding`
- `gentle correction`
- `amused recognition`
- `thoughtful pause before answer`

## Avoid

- Flat labels: `dramatic`, `shouting`, `excited`, `happy`, `sad`
- Vague: `emotional`, `different voice`
- Over-the-top: `wildly excited`, `furious`

## Filler and backchannel handling

Fillers (`uh`, `um`, `you know`) and backchannels (`Mhm`, `Hmm`, `Oh`) are written **inline in the text**, not in the delivery cue:

```
[Delivery: hesitant learner, searching for words]
Ethan: Um... so when I say "nice to meet you", that's already an intro?
```

The cue describes the *performance*, the text carries the *sound*.

## Emotion field (optional, for JSON handoff)

When converting to `script.json` for the manifest, each turn may carry an `emotion` summary:

```json
{
  "speaker": "Ethan",
  "text": "Um... so when I say 'nice to meet you', that's already an intro?",
  "deliveryCue": "hesitant learner, searching for words",
  "emotion": "curious"
}
```

`emotion` is a one-word summary for QC tooling; `deliveryCue` is what the renderer uses.

## Revision history

- 2026-07-19: Initial Series A delivery spec (audiobook parity).
