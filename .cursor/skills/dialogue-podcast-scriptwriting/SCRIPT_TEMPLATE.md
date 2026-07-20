# Script Template

## Required Header

```text
Title: [Specific learner outcome]
Description: [2-4 short paragraphs or concise YouTube description]
Target Level: [beginner | intermediate | upper-intermediate]
Estimated Duration: [minutes]
Hosts: Mia, Leo
Show Profile: [general | polished_english]
Learner Problem: [one concrete problem]
Key Phrases: [3-7 phrases]
```

Use any host names the user provides. Otherwise default to `Mia` and `Leo`.
For `polished_english`, use `Leo, Mia`, set `Show Profile: polished_english`, and apply `POLISHED_ENGLISH.md`.

## Default Structure

```text
[Intro Hook]
Mia: [Name the mistake or situation in a vivid way.]
Leo: [Promise the outcome and invite the listener into the practice.]

[Mini Dialogue 1: The Problem]
Mia: [Say the awkward/basic version.]
Leo: [React naturally, then identify why it sounds off.]

[Teaching Beat 1]
Leo: [Give the natural phrase.]
Mia: [Ask a learner-style follow-up question.]
Leo: [Explain the usage in plain language.]

[Practice Beat]
Mia: [Set up a situation.]
Leo: [Model the answer.]
Mia: [Try a variation.]
Leo: [Confirm or correct.]

[Mini Dialogue 2: Natural Version]
Mia: [Role-play with the improved phrases.]
Leo: [Continue the scenario naturally.]

[Recap]
Mia: [Ask for the three takeaways.]
Leo: [List the takeaways briefly.]

[CTA]
Mia: [Ask the listener to practice one line or comment an answer.]
Leo: [Close warmly.]
```

## Style Rules

- Make the script sound spoken, not like an essay.
- Keep one teaching focus per episode.
- Use contractions in dialogue unless the episode teaches formal English.
- Add short repetition prompts when useful: `Say it with us: ...`
- Avoid long monologues; if one host speaks for more than 4 sentences, split the turn.
- Prefer examples in realistic contexts: work, travel, small talk, shopping, study, phone calls, online meetings.

## Description Template

```text
In this episode, we practice [learner problem] so you can sound more natural when [situation].

You will learn:
- [phrase 1]
- [phrase 2]
- [phrase 3]

Listen, repeat the examples, and write your own sentence in the comments.
```

## TTS-Ready Turn Guidance

For later voice generation, every dialogue turn should be easy to map to one speaker:

```text
Mia: One clear thought per turn.
Leo: One clear response per turn.
```

Do not include three or more speakers unless the user asks for a guest episode.

## Polished English Extension

Use this extension only for `polished_english` or when the user asks for a more show-shaped Leo/Mia episode.

```text
[Teaching Plan]
T1: [sticky communicative move or phrase]
T2: [sticky communicative move or phrase]
T3: [optional; omit rather than overstuff]

[Structure Map]
Cold open: [stake within 30-45 seconds]
Host intro: [brief "I'm Leo / I'm Mia" after the hook, then back to the problem]
Early contract: [casual promise of slow recap or word tour]
Act 1: [T1 story or friction]
Micro-pocket: [2 pre-heard phrases, 20-45 seconds for full episodes]
Act 2: [T2 plus pushback or pattern interrupt]
Recycle: [new mini-scene with resistance and tiny realistic next step]
Word tour: [2-4 pre-heard phrases plus honest payoff line]
Close: [warm landing and one light action]

[Intro Hook]
[Delivery: thesis-first, warm but direct]
Leo: [Open with a paradox, pain, or promise.]
Mia: [Ground it in a real scene or pushback.]

[Host Intro]
Leo: [Briefly introduce Leo after the hook, not before.]
Mia: [Briefly introduce Mia, then reconnect to the episode's problem.]

[Early Contract]
Leo: [Casually say a few phrases will be slowed down later.]
Mia: [Make it sound useful, not like a class segment.]

[Act 1]
Mia: [Story, mistake, awkward choice, or real-life friction.]
Leo: [Short tightening beat; no lecture.]

[Micro-Pocket]
[Delivery: slower, calm, friend-to-friend]
Leo: [Phrase 1 already heard + plain gloss.]
Mia: [Phrase 2 already heard + quick natural example.]

[Recycle]
Mia: [Resists the advice because of time, dignity, work pressure, or habit.]
Leo: [Negotiates a tiny realistic step using earlier language.]

[Word Tour]
[Delivery: clear, slow, low drama]
Leo: [Honest payoff line, then phrase 1.]
Mia: [Phrase 2 or template variation.]

[Close]
Leo: [Warm landing.]
Mia: [One listener question or light follow/save line.]
```

### Emotion And Delivery Notes

For current-model render handoff, add delivery notes where performance matters:

```text
[Delivery: amused pushback, medium energy]
Mia: I love that plan in theory. In real life, my calendar just hissed at me.
```

If converting to a manifest, prefer `emotion`, `delivery`, and optional `intensity` fields. Do not add or require `speed`; pacing belongs in the text, delivery note, and section rhythm.

### Formal Episode Length

For `polished_english`, a formal script should target 15-20 minutes, about 1.9k-2.8k spoken English words. Use a shorter length only for a smoke demo and label it clearly.
