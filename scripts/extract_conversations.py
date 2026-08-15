#!/usr/bin/env python3
"""Extract normalized conversations from local Claude Code history.

Reads ~/.claude/projects/<project-slug>/<session-id>.jsonl and emits a
single JSON document containing only real human/assistant turns, with
tool-result payloads, sidechains and CLI plumbing stripped out.
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter
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
    r"This session is being continued from|<skill|<function_results)",
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
    """Flatten a message content field to plain text, or None."""
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
    """Strip injected tags. Returns (text, slash_command_or_None)."""
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
        text = f"{command} {text}".strip()
    return text, command


def tool_calls(content):
    """Return (names, signatures) for tool_use blocks in a message."""
    if not isinstance(content, list):
        return [], []
    names, signatures = [], []
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        name = block.get("name", "?")
        names.append(name)
        params = block.get("input") or {}
        detail = ""
        if isinstance(params, dict):
            detail = (
                params.get("command")
                or params.get("file_path")
                or params.get("pattern")
                or params.get("url")
                or ""
            )
        signatures.append(f"{name}: {str(detail)[:160]}".strip())
    return names, signatures


def read_session(path, preview_chars, max_user_chars):
    entries = []
    with open(path, "r", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not entries:
        return None

    session = {
        "session_id": os.path.splitext(os.path.basename(path))[0],
        "project": os.path.basename(os.path.dirname(path)),
        "file": path,
        "cwd": None,
        "git_branch": None,
        "started_at": None,
        "ended_at": None,
        "slash_commands": [],
        "tools_used": Counter(),
        "turns": [],
    }
    user_index = 0

    for entry in entries:
        if entry.get("isSidechain"):
            continue
        kind = entry.get("type")
        if kind not in ("user", "assistant"):
            continue
        message = entry.get("message") or {}
        content = message.get("content")
        stamp = parse_ts(entry.get("timestamp"))
        session["cwd"] = session["cwd"] or entry.get("cwd")
        session["git_branch"] = session["git_branch"] or entry.get("gitBranch")
        if stamp:
            iso = stamp.isoformat()
            session["started_at"] = session["started_at"] or iso
            session["ended_at"] = iso

        if kind == "assistant":
            names, signatures = tool_calls(content)
            session["tools_used"].update(names)
            text = block_text(content) or ""
            if not text.strip() and not names:
                continue  # thinking-only block
            session["turns"].append(
                {
                    "role": "assistant",
                    "ts": stamp.isoformat() if stamp else None,
                    "text": text[:preview_chars],
                    "truncated": len(text) > preview_chars,
                    "chars": len(text),
                    "tools": names,
                    "tool_calls": signatures,
                }
            )
            continue

        if is_tool_result(content):
            continue
        raw = block_text(content)
        if not raw or not raw.strip():
            continue
        text, command = clean_user_text(raw)
        if INJECTED_RE.match(text):
            continue
        if command:
            session["slash_commands"].append(command)
        if not text:
            continue
        session["turns"].append(
            {
                "role": "user",
                "ts": stamp.isoformat() if stamp else None,
                "index": user_index,
                "text": text[:max_user_chars],
                "truncated": len(text) > max_user_chars,
                "chars": len(text),
                "words": len(text.split()),
                "is_slash_command": bool(command),
            }
        )
        user_index += 1

    turns = session["turns"]
    session["user_turn_count"] = sum(1 for t in turns if t["role"] == "user")
    session["assistant_turn_count"] = len(turns) - session["user_turn_count"]
    session["tools_used"] = dict(session["tools_used"])
    return session


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
    parser.add_argument("--preview-chars", type=int, default=400)
    parser.add_argument("--max-user-chars", type=int, default=4000)
    parser.add_argument("--out", help="write JSON here instead of stdout")
    args = parser.parse_args()

    pattern = os.path.join(args.root, "*", "*.jsonl")
    paths = sorted(glob.glob(pattern))
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
        session = read_session(path, args.preview_chars, args.max_user_chars)
        if not session:
            continue
        if session["user_turn_count"] < args.min_user_turns:
            continue
        started = parse_ts(session["started_at"])
        if cutoff and (not started or started < cutoff):
            continue
        sessions.append(session)

    sessions.sort(key=lambda s: s["started_at"] or "")
    if args.limit:
        sessions = sessions[-args.limit :]

    document = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": args.root,
        "session_count": len(sessions),
        "user_turn_total": sum(s["user_turn_count"] for s in sessions),
        "sessions": sessions,
    }
    payload = json.dumps(document, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(payload)
        print(
            f"{len(sessions)} sessions, "
            f"{document['user_turn_total']} user turns -> {args.out}"
        )
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
