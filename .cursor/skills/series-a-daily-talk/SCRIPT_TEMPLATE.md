# Series A — Daily Talk Script Template

Use this structure for every Series A episode. Frozen sections are marked **[FROZEN]** — do not alter wording except for hook content.

## Header (metadata block)

```
Title: [English Podcast For ... | Hook | Learn English]
Description: [One sentence learner problem + promise]
Target Level: B1-B2
Estimated Duration: 16-20 minutes
Hosts: Ethan, Nora
Show Profile: series_a
Learner Problem: [One sentence]
Key Phrases: [3-5 phrases, comma-separated]

characterProfiles:
  Ethan: "Ethan, curious learner, warm slightly hesitant, consistent manner"
  Nora:  "Nora, warm peer coach, steady encouraging, consistent manner"
```

## Body

### [Intro Hook]  — 起 (30%)

**[FROZEN cold open]**

```
[Music sting]
Nora:  [Open in the specific scene, mistake, or social tension. Do not start with a welcome.]
Ethan: I'm Ethan.
Nora:  And I'm Nora. And this is the English Listening Room.
```

**[Hook — pick one template from STYLE.md §A.2]**

```
Nora:  [Hook line — question / story / paradox / teaser / game]
Ethan:  [Reaction — 1-2 sentences, learner perspective]
```

**[Topic announcement + B1/B2 callout + CTA + comment prompt]**

```
Nora:  And today we're talking about [topic]. If you are B1 or B2, this one is for you.
Ethan: Before we start — if you like this episode, tap like, and share it with one friend who also needs this.
Nora:  And tell us in the comments, [comment prompt question].
```

**[Optional "who is this for"]**

```
Ethan: This is for you if you've ever [pain point].
```

### [Teaching Dialogue]  — 承 (40%)

3–5 teaching beats. Each beat follows this micro-structure:

```
Nora:  [Teaching idea + metaphor]
Ethan: [Inline vocab question] / [Personal anecdote]
Nora: [Gloss + example]
Ethan: [Mirror / apply to self]
Nora: [Affirm + handoff]
```

Example beat (fill in real content):

```
[Delivery: warm setup, medium energy]
Nora:  So the first idea is this: [metaphor]. Right?

[Delivery: curious learner, slight hesitation]
Ethan: Hmm. [Vocab question] — what does [word] mean here?

[Delivery: patient explanation]
Nora:  [Word] means [gloss]. For example, [example 1]. And [example 2].

[Delivery: applying to self, relieved]
Ethan: Oh, okay. So like that time I [personal anecdote]. That was [word]?

[Delivery: warm affirmation]
Nora:  Exactly. You got it.
```

Repeat for 3–5 beats. Use strict alternation with occasional 2-line runs.

### [Word Tour]  — 转 (20%)

**[FROZEN pivot line]**

```
Nora:  And before we close, let's slow down for our word tour and look again at
       some of the most useful words from today.
```

Then for each of ~8–10 words:

```
Nora:  [Word]. That means [gloss]. For example, [example 1]. And [example 2].
Ethan: Repeat: [word].
Nora:  Nice.
```

### [Recap And CTA]  — 合 (10%)

```
[Delivery: warm recap, steady]
Nora:  So today we talked about [idea 1], [idea 2], and [idea 3]. [One-sentence synthesis].

[Delivery: learner gratitude]
Ethan: I really needed this one. [Optional homework line: "Tonight I'll write one sentence using [word]."]

[Delivery: closing invitation]
Nora:  Share your sentence in the comments. We read them all.

**[FROZEN sign-off]**

Nora:  This is Nora.
Ethan: And this is Ethan.
Nora:  And you've been listening to Daily Talk, from the English Listening Room.
Ethan: Bye.
[Music sting]
```

## Validation checklist

- [ ] Header has all fields including `characterProfiles`
- [ ] Cold open opens with a specific scene or failed moment before the brand
- [ ] "English Listening Room" spoken once after dual intro
- [ ] Hook uses one of 5 templates (A–E)
- [ ] 3–5 teaching beats with inline vocab glosses
- [ ] Word Tour covers 8–10 words
- [ ] Sign-off uses frozen chassis
- [ ] Every turn has `[Delivery: …]`
- [ ] 1800–2400 spoken words
- [ ] ≤1 filler per 8–12 turns
- [ ] `validate_podcast_script.py --profile series_a` returns `ok=true`

## Revision history

- 2026-07-19: Initial Series A template (frozen chassis + brand name + delivery cues).
