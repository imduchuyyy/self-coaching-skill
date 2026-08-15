# Scoring rubric

Score 1–5 per group, on **deep tasks only** (Nhóm 5 governs which those are).
Judge by reading; the counts below are anchors, not formulas. When a sample is
small (<8 deep tasks), give a range instead of a point score and say why.

## Nhóm 1 — Chất lượng đầu vào (Input Quality)

Look at the first user message of each deep-task session for: stated goal,
constraints, desired format/length, audience or background, a reference
example, pasted material (code, error, link, doc).

| Score | What it looks like |
|---|---|
| 1 | Mostly 3–8 vague words. "sửa code này", "viết email". No goal, no context. AI has to guess every time. |
| 2 | One line of what, never why. Context appears only when the AI asks for it. |
| 3 | Task is clear and usually scoped, but goal, audience, or output format is left implicit. Occasional good prompt. |
| 4 | Most deep tasks open with goal + constraints, plus relevant material pasted in. Format stated when it matters. |
| 5 | Consistently states goal, constraints, format, and the background needed; supplies an example or the real artifact. AI rarely needs a clarifying round. |

Do not reward length by itself. A long prompt that is mostly pasted logs with
no stated goal is a 2, not a 4.

## Nhóm 2 — Tương tác & lặp (Interaction Depth)

| Score | What it looks like |
|---|---|
| 1 | Nearly all deep tasks end after one turn. Answer taken and gone. |
| 2 | A few follow-ups, all mechanical ("continue", "now the next file"). No probing. |
| 3 | Regular refinement, occasional "why did you do it that way". Little pushback on substance. |
| 4 | Follow-ups routinely ask for reasoning or alternatives; the user redirects when an answer misses. |
| 5 | Sustained dialogue: asks for trade-offs, proposes a competing approach, makes the AI defend its choice, then decides. |

Flag separately (not a low score, a different finding): sessions with many
turns caused by the AI repeatedly missing the target. Cause is a thin opening
prompt — that belongs to Nhóm 1.

## Nhóm 3 — Xác minh & tư duy phản biện (Verification)

Evidence of checking, all visible in the dialogue: pasting an error or a
wrong result back, asking for a source, asking for the change to be tested,
reporting what happened when they ran it, contradicting the AI with a fact.

| Score | What it looks like |
|---|---|
| 1 | No sign of checking anywhere. Never contradicts the AI. Results appear to be used as-is. |
| 2 | Only notices problems when something visibly breaks; no proactive checking. |
| 3 | Runs/tests the result on real work, but rarely questions claims or facts. |
| 4 | Routinely verifies before using: runs it, reads the diff, checks a claim, and catches mistakes. |
| 5 | Verification is habitual and targeted — checks the parts most likely to be wrong, asks for sources on factual claims, corrects the AI with evidence. |

An almost-zero correction rate over many sessions is a finding worth naming:
either the tasks were trivial or checking is not happening. Decide which by
reading, and say which.

## Nhóm 4 — Học & chuyển giao kỹ năng (Skill Transfer)

| Score | What it looks like |
|---|---|
| 1 | Pure output consumption. Same task shape, asked the same way, for weeks. Never asks how it works. |
| 2 | Rare "why" questions; prompts on a repeated topic look identical from first session to last. |
| 3 | Asks how things work sometimes; some improvement in prompts on familiar topics. |
| 4 | Regularly asks for the reasoning to reuse it; later prompts on the same topic are visibly sharper and more specific. |
| 5 | Prompts on recurring topics get shorter *and* more precise over time; the user brings their own hypothesis and uses the AI to test it. |

The comparison to make: earliest sessions on a topic versus the most recent
ones on that same topic. Quote both.

## Nhóm 5 — Phù hợp mục đích (Context Fit)

This scores whether the user matches effort to task type.

| Score | What it looks like |
|---|---|
| 1 | Mismatched both ways: one-liners for production decisions, or long ceremony for trivial lookups. |
| 3 | Right register most of the time; some deep tasks handled like quick ones. |
| 5 | Quick tasks are crisp and single-turn; deep tasks reliably get context, iteration, and verification. |

A session that is one turn because that was genuinely enough is evidence
*for* a high score here, never against it.
