# self-coaching

A Claude Code skill that reviews how effectively you use AI.

It reads your own local Claude Code chat history, judges it against five
metric families, and returns a scored report: what you already do well, where
you lose value, and a small number of habit changes to try next. Every score
is backed by a quote from your own conversations.

The skill is the evaluator. There is no scoring script and no heuristic that
assigns points — the agent reads the actual dialogue and judges it, because
the things that matter here (was that follow-up a real challenge, or just
"continue"?) cannot be counted with a regex.

## What it measures

| Group | Question it answers |
|---|---|
| 1. Input Quality | Do your requests state a goal, constraints, and a desired output format, or are they a few vague words? |
| 2. Interaction Depth | After the first answer, do you dig deeper and push back, or take the output and leave? |
| 3. Verification | Do you check what the AI produced — run it, source it, contradict it — or accept it as-is? |
| 4. Skill Transfer | Do you ask why and how so you can do it yourself next time, or only collect artifacts? |
| 5. Context Fit | Do you match effort to task type? |

Group 5 is applied first and governs the rest. A quick lookup answered in one
turn is correct behaviour, and Groups 1 to 4 are scored only on the deep tasks
where depth was actually warranted. Without that step, an assessment like this
punishes efficient behaviour, which is the most common way it goes wrong.

## Requirements

- Claude Code, with existing chat history under `~/.claude/projects/`
- Python 3.9 or newer, standard library only. No dependencies to install.

## Install

Clone the repo, then link it into your personal skills directory:

```bash
git clone <this-repo> ~/Documents/self-coaching-agent
mkdir -p ~/.claude/skills
ln -sfn ~/Documents/self-coaching-agent ~/.claude/skills/self-coaching
```

A symlink is recommended over a copy: edits to the repo take effect in the
next session with no reinstall. To install a fixed copy instead:

```bash
mkdir -p ~/.claude/skills/self-coaching
cp -R SKILL.md scripts references ~/.claude/skills/self-coaching/
```

For a single project rather than your whole account, use
`<project>/.claude/skills/self-coaching` as the target instead.

The directory name must be `self-coaching`, matching the `name` field in
`SKILL.md`.

Verify the install:

```bash
ls ~/.claude/skills/self-coaching/
python3 ~/.claude/skills/self-coaching/scripts/extract_conversations.py \
  --since-days 7 --user-only | head -20
```

Skills are discovered when a session starts, so start a new Claude Code
session before testing. If the skill does not appear, run `/doctor` — a
malformed `SKILL.md` frontmatter is the usual cause.

## Use

In a new session, either invoke it directly:

```
/self-coaching
```

or ask for it in plain language, in any language you use:

```
review how well I use AI
```

The agent extracts your recent conversations, reads them, scores the five
groups, and prints a report: a metrics table, evidence-backed strengths and
gaps, a rewrite of one of your own weak prompts, and three habits to try with
the signal that should move for each.

The report is written in whatever language your prompts are in, and quotes
your words untranslated. The skill files themselves are English.

## The extraction script

`scripts/extract_conversations.py` is the only script. It reads
`~/.claude/projects/<project-slug>/<session-id>.jsonl` and prints the chat as
a plain transcript.

It exists because raw transcripts are mostly not conversation. In a typical
history, over 90 percent of the entries typed as `user` are tool results, not
things a human wrote. The script keeps only real dialogue and drops tool
calls, tool results, sidechains, thinking blocks, slash commands with no
arguments, hook and harness notices, and injected skill instructions that
would otherwise read as human turns.

```bash
python3 scripts/extract_conversations.py --since-days 30 --out /tmp/chat.txt
```

| Flag | Effect |
|---|---|
| `--root PATH` | History location, default `~/.claude/projects` |
| `--project SUBSTR` | Only projects whose folder name contains SUBSTR |
| `--since-days N` | Only sessions started within the last N days |
| `--limit N` | Keep only the N most recent sessions |
| `--min-user-turns N` | Drop sessions with fewer real user turns |
| `--user-only` | Print only what you wrote, not the replies |
| `--max-user-chars N` | Clip long user turns, default 4000 |
| `--max-ai-chars N` | Clip long AI replies, default 800 |
| `--out PATH` | Write the transcript to a file |

Output format, one block per session:

```
========================================================================
[3/26] -Users-you-Documents-project
session a2ac72c8-8129-48a9-9223-d955fc6e2405  started 2026-08-05 06:49  4 user turns
========================================================================

--- USER 06:49 ---
add long/short option on journal, make sure new fields doesn't break
production database when migrated

--- AI 06:50 ---
...
```

The script is also useful on its own, outside the skill, for reading back what
you actually asked over the last month.

## Notes on scope

Thirty days of history is usually 15 to 30 sessions and a transcript of a few
thousand lines, which the agent reads in full. If that is too much context,
narrow it with `--limit` or `--since-days`. Below roughly eight sessions the
sample is too small for scores to mean much, and the skill is instructed to
say so rather than produce confident numbers.

## Privacy

Everything runs locally against files already on your machine. Nothing is
uploaded. The skill is instructed to keep extracts in a scratchpad directory
rather than your repositories, to quote only the short snippets needed as
evidence, and never to publish or send transcript contents anywhere unless you
ask for it.

Your history may contain secrets, client names, and private code. Review the
report before sharing it.

## Layout

```
SKILL.md                          Skill definition and workflow
scripts/extract_conversations.py  Transcript extraction
references/rubric.md              1-5 scoring bands per group
references/playbook.md            Interventions keyed to the weakest group
references/report_template.md     Output shape for the report
```
