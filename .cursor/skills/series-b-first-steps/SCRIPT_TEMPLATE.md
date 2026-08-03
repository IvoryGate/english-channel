# Series B — First Steps Script Template

Use this structure for every Series B episode. Frozen sections are marked **[FROZEN]**.

## Header (metadata block)

```
Title: [Learn N English topic — contrarian claim | Easy English Podcast A2-B1]
Description: [One sentence learner problem + promise]
Target Level: A2-B1
Estimated Duration: 12-18 minutes
Hosts: Riley, Sam
Show Profile: series_b
Learner Problem: [One sentence]
Key Phrases: [3-5 phrases, comma-separated]

characterProfiles:
  Riley: "Riley, clear coach, patient steady, consistent manner"
  Sam:   "Sam, hesitant friend, warm slightly unsure, consistent manner"
```

## Body

### [Intro Hook]  — 起 (25%)

**[FROZEN cold open]**

```
[Music sting]
Riley: Hi, I'm Riley.
Sam:   And I'm Sam. Welcome to the English Listening Room.
```

**[Hook — pick one template from STYLE.md §B.2]**

```
Sam:   [Hook teaser — contrarian claim / scene / embarrassment setup]
Riley: [Hook reaction — "Sounds wrong, right? But by the end, you'll [X]."]
```

**[Contract + level callout]**

```
Riley: If you are A2 or B1, this one is for you. By the end, you'll [specific promise].
```

### [Teaching Dialogue]  — 承 (45%)

3 teaching beats. Each beat follows the 4-beat learner-asks loop:

```
[Delivery: hesitant learner, searching]
Sam:   [learner question — 1 sentence, often with a filler like "So wait..." or "Hmm..."]

[Delivery: patient clear explanation]
Riley: [teacher explanation — 2-4 sentences, gloss every new word inline]
       Example: "Relentless — that means she didn't stop. She kept going."

[Delivery: relieved understanding]
Sam:   [learner mirror — repeat key phrase, apply to self, 1-2 short sentences]

[Delivery: warm praise]
Riley: [teacher praise — "Exactly." / "You got it." / "Nice."]
```

Example beat (fill in real content):

```
[Delivery: hesitant learner, searching]
Sam:   So wait... "used to" is only for the past?

[Delivery: patient clear explanation]
Riley: Right. "Used to" locks the habit in the past. It means: not anymore.
       "I used to study French" — so you don't now.

[Delivery: relieved understanding]
Sam:   Not anymore. Okay. So "I used to study French" means I don't now.

[Delivery: warm praise]
Riley: Exactly. You got it.
```

Repeat for 3 beats. Use strict alternation; Riley may take 2-line runs for longer explanations.

### [Meta Pivot]  — 转 (20%)

**[Pivot line — shift from rules to mindset/identity]**

```
[Delivery: thoughtful, slowing down]
Riley: But here's the thing most learners miss. [Meta insight — mindset or identity shift].
```

Then a short role-play or real-world confidence beat:

```
[Delivery: hesitant but willing]
Sam:   [Tries the phrase in a role-play scenario — with a filler]

[Delivery: encouraging coach]
Riley: [Praise + one correction or refinement]
```

### [Recap And CTA]  — 合 (10%)

```
[Delivery: warm recap, steady]
Riley: So today: [one-sentence recap of the 3 beats].

[Delivery: friendly challenge]
Sam:  Your turn. [One-sentence comment challenge — e.g., "Write one sentence with 'used to' in the comments."]

[Delivery: closing invitation]
Riley: We read every comment. See you next time.

**[FROZEN sign-off]**

Riley: This is Riley.
Sam:   And this is Sam.
Riley: And you've been listening to First Steps, from the English Listening Room.
Sam:   Bye.
[Music sting]
```

## Validation checklist

- [ ] Header has all fields including `characterProfiles`
- [ ] Cold open opens with a concrete task or mishap before the brand
- [ ] "English Listening Room" spoken once after dual intro
- [ ] Hook uses one of 3 templates (contrarian-number default)
- [ ] 3 teaching beats with learner-asks 4-beat loop
- [ ] Every new word glossed inline by Riley
- [ ] Meta pivot shifts to mindset/identity (not just more content)
- [ ] Sign-off uses frozen chassis
- [ ] Every turn has `[Delivery: …]`
- [ ] 1400–1900 spoken words
- [ ] Sam has 1 filler per 4–6 turns; Riley near-zero
- [ ] Average sentence 8–12 words
- [ ] `validate_podcast_script.py --profile series_b` returns `ok=true`

## Revision history

- 2026-07-19: Initial Series B template (contrarian hooks, learner-asks loop, brand name, delivery cues).
