---
name: self-coaching
description: Coach the user on how effectively they use AI, by reading their own Claude Code chat history and judging it against five metric families (input quality, interaction depth, verification, skill transfer, context fit), then showing the scored metrics with evidence and concrete habit changes. Use when the user asks how well they use AI, wants their prompting reviewed, asks for a "self coaching" / AI-skill assessment, or wants to improve how they work with AI.
---

# Self-coaching: assess and improve how the user works with AI

Read the user's real conversations, judge them yourself against the five
metric families below, and show the user their metrics plus what to change
this week. There is no scoring script: you are the evaluator. Every score
must be backed by a quote from the user's own history.

## Workflow

### 1. Pull the conversations

`scripts/extract_conversations.py` is the only script. It reads
`~/.claude/projects/<project>/<session>.jsonl` and emits clean JSON with
tool results, sidechains, thinking blocks and CLI plumbing stripped out —
only real human and assistant turns survive.

```bash
python3 scripts/extract_conversations.py --since-days 30 --out /tmp/conv.json
```

Flags: `--project <substring>` to scope to one codebase, `--limit N` for the
N most recent sessions, `--min-user-turns 2` to drop stubs, `--since-days N`
for the time window, `--preview-chars` / `--max-user-chars` to control how
much text is kept per turn.

Aim for 15–30 sessions. If the window yields fewer than ~8, widen it
(`--since-days 90`). Write extracts to a scratchpad, never into the user's
repo.

### 2. Read the sessions

Read `/tmp/conv.json` — the first user turn of every session, and the full
turn sequence of at least 8 of them (the shortest, the longest, and a spread
in between). If the file is large, read the first prompts of all sessions
first to build the map, then open the interesting ones.

What to extract per session as you read:

- the first prompt, verbatim (this is the main evidence for Nhóm 1)
- how many human turns followed, and what kind they were: refinement,
  challenge, correction, or just "ok, next"
- whether the user ever checked the output — pasted an error back, asked for
  a source, asked for a test run (`tool_calls` on assistant turns shows what
  was actually executed: test/build/lint commands are a verification signal)
- whether the user asked *why/how*, or only *what*
- what type of task it was (see Nhóm 5)

### 3. Classify before you score (Nhóm 5 first)

Tag each session:

- **Quick task** — lookup, translation, one-line command, known-answer fix.
  Correct behaviour is one clear question and leaving.
- **Deep task** — design decisions, strategy, learning a concept, anything
  touching production, anything with trade-offs.

Score Nhóm 1–4 on the deep tasks only. Never mark a quick task down for
being one turn — that is the right behaviour, and treating it as shallow is
the most common way this assessment goes wrong.

### 4. Judge the five groups

Score each group 1–5 using the bands in `references/rubric.md`. For each,
write down the signals you observed, the counts you actually saw (say
"7 of 21 deep tasks", not "often"), and the quotes that drove the score.

Read the transcripts to separate the two causes of a long conversation:
productive iteration (the user refines, challenges, redirects) versus a
repair loop (the AI kept missing because the first prompt was thin). Counts
cannot tell these apart; reading can.

### 5. Show the metrics and coach

Follow `references/report_template.md`. Rules:

- **Show the metrics table first.** The user asked to see their metrics —
  lead with the five scores and the observed counts, then the narrative.
- **Evidence or silence.** Every strength and gap cites a real quote
  (trimmed) with its date. No generic prompting advice.
- **Rewrite their own prompt.** For the biggest gap, take one of the user's
  actual weak prompts and show a rewritten version side by side.
- **Three changes maximum**, each with the signal that should move next time.
- **Coach, don't grade.** Neutral, specific, non-moralising.
- **Mirror the user's language.** If their history and request are in
  Vietnamese, write the report in Vietnamese.

Interventions per weakness are in `references/playbook.md`.

## The five metric families

**Nhóm 1 — Chất lượng đầu vào (Input Quality).** Does the request state a
goal, constraints, and a desired output format, or is it 3–5 vague words
("viết email", "sửa code này")? Is background context supplied — who reads
it, what it is for, a reference example — or left for the AI to guess? The
average length/detail of the first message in each conversation is a crude
indicator, but it correlates well with how much thinking happened before
asking.

**Nhóm 2 — Tương tác & lặp (Interaction Depth).** After the first answer,
does the user dig deeper, ask for the reasoning, or stop right there? How
often do they push back — "tại sao lại vậy", "cái này có chắc không", "thử
cách khác xem" — a sign of active critical thinking? Average rounds per
conversation: one turn on a deep task suggests grab-and-go; consistently
very high turns can instead mean the AI kept misunderstanding, which is also
worth flagging but has a different cause and a different fix.

**Nhóm 3 — Xác minh & tư duy phản biện (Verification).** Does the user check
what the AI produced — find an outside source, run the code, cross-check the
numbers — or accept all of it? How often do they catch the AI being wrong or
misunderstanding? If that is close to never across many sessions, the likely
explanation is "not checking carefully", not "the AI is always right". Also
watch for output taken as-is: no edits, no follow-up discussion after a
result arrives.

**Nhóm 4 — Học & chuyển giao kỹ năng (Skill Transfer).** Does the user ask
"why / how" in order to do it themselves next time, or only to get the
artifact and use it now? Are the last ~20 sessions the same request shape
asked the same way, with no improvement? Compare prompt quality and
specificity in the earliest window versus the most recent one within the
same topic — that comparison is the strongest available evidence of whether
the user is learning from the AI or just consuming it.

**Nhóm 5 — Phù hợp mục đích (Context Fit).** This group exists to prevent
misjudging the other four. Classify every session before applying them, and
apply "should have gone deeper / should have learned" only to deep tasks. A
quick lookup answered in a single turn is correct behaviour and must never
be scored down for it.

## Privacy

The history is the user's private work. Analyze it locally, keep extracts in
a scratchpad, quote only the short snippets needed as evidence, and never
publish or send transcript contents anywhere without the user asking.
