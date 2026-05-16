# Segmentation And Delivery Cues

## Segment Granularity

Use semantic units:

- Narration sentence or coherent narration beat.
- One speaker's dialogue turn.
- A narrator transition such as `This was invitation enough.`
- A long sentence split at semicolons only when each part has a clear delivery beat.

Avoid:

- Combining multiple speakers in one segment.
- Combining narration and dialogue in one segment.
- Splitting only by character count.
- Repeating the global narrator instruction inside every segment.

## Manifest Shape

```json
{
  "bookTitle": "Pride and Prejudice",
  "bookSlug": "pride_and_prejudice",
  "chapterNumber": 1,
  "chapterId": "chapter_001",
  "globalControl": "one consistent cloned audiobook narrator, same voice throughout...",
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

## Delivery Cue Guidelines

Delivery cues should describe small performance changes:

- `plain understated narration`
- `quiet deadpan amusement`
- `mild impatience`
- `eager to share news, still restrained`
- `light comic transition`

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
