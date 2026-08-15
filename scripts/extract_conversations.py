#!/usr/bin/env python3
"""Print the chat between the user and the AI from local Claude Code history.

Reads ~/.claude/projects/<project-slug>/<session-id>.jsonl and prints a
readable transcript of what was actually said. Tool calls, tool results,
sidechains, thinking blocks and CLI plumbing are dropped.
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

DEFAULT_ROOT = os.path.expanduser("~/.claude/projects")

# Wrapper tags the CLI injects into the user channel; not human typing.
NOISE_TAGS = (
    "system-reminder",
    "local-command-caveat",
    "local-command-stdout",
    "local-command-stderr",
    "bash-input",
    "bash-stdout",
    "bash-stderr",
    "task-notification",
    "user-prompt-submit-hook",
)
NOISE_RE = re.compile(
    r"<(%s)>.*?</\1>" % "|".join(NOISE_TAGS), re.DOTALL | re.IGNORECASE
)
COMMAND_NAME_RE = re.compile(r"<command-name>(.*?)</command-name>", re.DOTALL)
ANY_TAG_ONLY_RE = re.compile(r"^<[a-z-]+>.*</[a-z-]+>$", re.DOTALL)

# Text the harness injects into the user channel (skills, hooks, tools).
INJECTED_RE = re.compile(
    r"^(Base directory for this skill|Skill '|Caveat: The messages below|"
    r"\[Request interrupted|API Error|The user (?:doesn't|opened|sent)|"
    r"This session is being continued from|<skill|<function_results|"
    r"Browser tools are not available|Tool .* is not available|"
    r"The following deferred tools)",
    re.IGNORECASE,
)


def parse_ts(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def block_text(content):
    """Flatten a message content field to plain text, or None.

    Only `text` blocks are read, so tool_use and thinking never appear.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        return "".join(parts) if parts else None
    return None


def is_tool_result(content):
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content
    )


def clean_user_text(raw):
    """Strip injected tags, keeping any slash command the user typed."""
    command = None
    match = COMMAND_NAME_RE.search(raw)
    if match:
        command = match.group(1).strip()
    text = NOISE_RE.sub("", raw)
    if command:
        # Keep only the args the user typed after the command name.
        text = COMMAND_NAME_RE.sub("", text)
        text = re.sub(
            r"<command-message>.*?</command-message>", "", text, flags=re.DOTALL
        )
        text = re.sub(r"</?command-[a-z]+>", "\n", text)
        text = text.replace(command, " ")
    text = re.sub(r"</?command-[a-z]+>", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if ANY_TAG_ONLY_RE.match(text):
        text = ""
    if command:
        # A bare command with no arguments is a UI action, not a prompt.
        text = f"{command} {text}".strip() if text else ""
    return text


def clip(text, limit):
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + " […]"


def read_session(path, max_user_chars, max_ai_chars):
    """Return one session as a list of {role, ts, text} turns."""
    session = {
        "session_id": os.path.splitext(os.path.basename(path))[0],
        "project": os.path.basename(os.path.dirname(path)),
        "started_at": None,
        "ended_at": None,
        "turns": [],
    }

    with open(path, "r", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("isSidechain"):
                continue
            kind = entry.get("type")
            if kind not in ("user", "assistant"):
                continue

            content = (entry.get("message") or {}).get("content")
            if is_tool_result(content):
                continue
            raw = block_text(content)
            if not raw or not raw.strip():
                continue  # tool-call-only or thinking-only message

            if kind == "user":
                text = clean_user_text(raw)
                if not text or INJECTED_RE.match(text):
                    continue
                text = clip(text, max_user_chars)
            else:
                text = clip(raw, max_ai_chars)
            if not text:
                continue

            stamp = parse_ts(entry.get("timestamp"))
            if stamp:
                iso = stamp.isoformat()
                session["started_at"] = session["started_at"] or iso
                session["ended_at"] = iso
            session["turns"].append(
                {
                    "role": kind,
                    "ts": stamp.isoformat() if stamp else None,
                    "text": text,
                }
            )

    session["user_turn_count"] = sum(
        1 for t in session["turns"] if t["role"] == "user"
    )
    return session


def format_session(session, index, total):
    started = (session["started_at"] or "")[:16].replace("T", " ")
    lines = [
        "=" * 72,
        f"[{index}/{total}] {session['project']}",
        f"session {session['session_id']}  started {started}  "
        f"{session['user_turn_count']} user turns",
        "=" * 72,
        "",
    ]
    for turn in session["turns"]:
        stamp = (turn["ts"] or "")[11:16]
        who = "USER" if turn["role"] == "user" else "AI"
        lines.append(f"--- {who} {stamp} ---")
        lines.append(turn["text"])
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument(
        "--project", help="only projects whose folder name contains this"
    )
    parser.add_argument(
        "--since-days", type=int, help="only sessions started within N days"
    )
    parser.add_argument(
        "--min-user-turns",
        type=int,
        default=1,
        help="drop sessions with fewer real user turns",
    )
    parser.add_argument(
        "--limit", type=int, help="keep only the N most recent sessions"
    )
    parser.add_argument(
        "--max-user-chars", type=int, default=4000, help="clip long user turns"
    )
    parser.add_argument(
        "--max-ai-chars", type=int, default=800, help="clip long AI replies"
    )
    parser.add_argument(
        "--user-only",
        action="store_true",
        help="print only what the user wrote",
    )
    parser.add_argument("--out", help="write the transcript here")
    args = parser.parse_args()

    paths = sorted(glob.glob(os.path.join(args.root, "*", "*.jsonl")))
    if args.project:
        paths = [p for p in paths if args.project in os.path.dirname(p)]
    if not paths:
        print(f"no transcripts under {args.root}", file=sys.stderr)
        return 1

    cutoff = None
    if args.since_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=args.since_days)

    sessions = []
    for path in paths:
        session = read_session(path, args.max_user_chars, args.max_ai_chars)
        if session["user_turn_count"] < args.min_user_turns:
            continue
        started = parse_ts(session["started_at"])
        if cutoff and (not started or started < cutoff):
            continue
        if args.user_only:
            session["turns"] = [
                t for t in session["turns"] if t["role"] == "user"
            ]
        sessions.append(session)

    sessions.sort(key=lambda s: s["started_at"] or "")
    if args.limit:
        sessions = sessions[-args.limit :]

    total = len(sessions)
    body = "\n".join(
        format_session(s, i, total) for i, s in enumerate(sessions, 1)
    )
    turn_count = sum(s["user_turn_count"] for s in sessions)
    footer = f"\n{total} sessions, {turn_count} user turns\n"

    if args.out:
        with open(args.out, "w") as handle:
            handle.write(body + footer)
        print(f"{total} sessions, {turn_count} user turns -> {args.out}")
    else:
        print(body + footer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
