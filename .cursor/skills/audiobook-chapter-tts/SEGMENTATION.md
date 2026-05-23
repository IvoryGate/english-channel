# Segmentation And Delivery Cues

## Segment Granularity

Use semantic units:

- Narration sentence or coherent narration beat.
- One speaker's dialogue turn.
- A narrator transition such as `This was invitation enough.`
- One full quoted turn per segment, even when the source uses semicolons across clauses.

Avoid:

- Combining multiple speakers in one segment.
- Combining narration and dialogue in one segment.
- Splitting one speaker's long dialogue at semicolons or mid-quote continuations.
- Splitting only by character count.
- Repeating the global narrator instruction inside every segment.

`segment_chapter.py` merges consecutive sentences when a quoted turn is still open or a clause continues after `;`.

## Manifest Shape

```json
{
  "bookTitle": "Pride and Prejudice",
  "bookSlug": "pride_and_prejudice",
  "chapterNumber": 2,
  "chapterId": "chapter_002",
  "globalControl": "one consistent cloned audiobook narrator, same voice throughout, calm British literary narration, restrained expression",
  "characterProfiles": {
    "Mr. Bennet": "Mr Bennet, dry ironical calm, consistent manner",
    "Mrs. Bennet": "Mrs Bennet, anxious fluttering, consistent manner"
  },
  "cfgValue": 2.35,
  "segments": [
    {
      "id": "001",
      "order": 1,
      "filename": "001_narrator.wav",
      "kind": "narration",
      "speaker": "narrator",
      "deliveryCue": "subtle dry social irony",
      "text": "It is a truth universally acknowledged...",
      "wordCount": 23
    }
  ]
}
```

## Character Profiles

For dialogue consistency, define one stable cue per speaker in `characterProfiles`:

```json
"characterProfiles": {
  "Mr. Bennet": "Mr Bennet, dry ironical calm, steady throughout",
  "Mrs. Bennet": "Mrs Bennet, anxious fluttering, steady throughout"
}
```

`compose_control` prepends the speaker profile to dialogue segments and always keeps a short `deliveryCue`, including for long unsplit turns. Full decision table: `CONTROLS.md`.

### Narration splits

When the model swallows an opening word or a sentence has two delivery beats, use two narration segments (e.g. `002` “It was then disclosed…” and `002b` “Observing his second daughter…”). IDs may use a letter suffix; `order` stays sequential.

## Delivery Cue Guidelines

Delivery cues should describe small performance changes:

- `plain understated narration`
- `quiet deadpan amusement`
- `mild impatience`
- `eager to share news, still restrained`
- `light comic transition`

### Energy that tends to work (VoxCPM2)

Segments **009** / **010** sound strong when:

- `deliveryCue` uses an **active verb** (`bursting out`, `deadpan comic correction`) not a flat label (`matter-of-fact`)
- dialogue has **13–22 words** (not 2-word quips with huge `max_len`)
- **character profile + deliveryCue** both apply on every dialogue segment, including long unsplit turns
- the text already has exclamation or conflict

Very short lines (≤4 words): automatic `max_len` 56; quiet peaks are boosted after render (peak < 0.45 → 0.88). See `CONTROLS.md`.

### Long dialogue

Keep the full quoted turn in one segment. Use one `deliveryCue` for the whole speech; do not split at semicolons inside the same quote.

Avoid strong acting cues unless requested:

- `dramatic`
- `shouting`
- `wildly excited`
- `different character voice`

## Short Segments

Segments of 12 words or fewer are fragile with VoxCPM2. Use compact control and `max_len`.

If a very short segment still produces extra speech, either:

1. Regenerate it with a smaller `max_len`.
2. Mark it with a synthesis group and generate it with a neighboring segment.
3. Keep the semantic segment in the manifest but render grouped audio for playback.
