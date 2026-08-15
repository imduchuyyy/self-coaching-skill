# Coaching playbook

Pick interventions from the group that scored lowest. Each one must be small
enough to do tomorrow and observable in the next review.

## Nhóm 1 low — thin prompts

- **Four-line opener** for deep tasks: Mục tiêu / Ràng buộc / Bối cảnh /
  Định dạng đầu ra. Four lines, not four paragraphs.
- **Paste the artifact, not the description of it** — the failing test output,
  the actual file, the real email thread.
- **Say who it is for.** "for a junior dev on this repo" changes the answer
  more than any wording tweak.
- **Name what "done" looks like** before starting: the check you will run to
  accept the result.
- **Save one good prompt as a reusable skeleton** for the task shape they
  repeat most (found in their repeated topics).

## Nhóm 2 low — grab and go

- **One mandatory second question** on any deep task: "what would you do
  differently and why", or "what's the weakest part of this".
- **Ask for two options with trade-offs** before accepting an approach.
- **Make the AI state its assumptions** before it starts, and correct them
  then — cheaper than correcting the output.
- If turns are high because of repair loops instead: **stop and restate the
  goal in one message** rather than nudging turn after turn.

## Nhóm 3 low — no verification

- **Decide the check before reading the answer**: run the test, open the file,
  verify the number. Choose it first so the answer cannot talk you out of it.
- **Ask for the source** on any factual or numeric claim, and open it.
- **Ask "what in this is most likely wrong?"** — a cheap targeted audit.
- **Never ship unread.** Read the diff or the text end to end once before it
  leaves the machine.
- For code: **make the AI run the test/build itself** and show the output.

## Nhóm 4 low — no skill transfer

- **Add "và giải thích tại sao"** on tasks in the domain they want to own.
- **Predict first**: write your own answer in one line, then compare with the
  AI's and ask about the gap. This is the fastest learning loop available.
- **Retire a recurring prompt**: after 3 identical requests, ask the AI to
  turn it into a checklist or script so the task stops needing the AI.
- **Escalate difficulty**: on a familiar topic, ask a question that assumes
  the basics instead of re-asking them.

## Nhóm 5 low — wrong register

- **Two-second triage before asking**: is this a lookup, or a decision I'd
  want a colleague to review? Only the second gets the four-line opener.
- **Anything touching production or people is a deep task**, regardless of
  how small the change looks.
- **Do not over-ceremony quick lookups** — a one-line question is the right
  tool and costs nothing.
