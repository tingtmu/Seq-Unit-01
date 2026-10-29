#!/usr/bin/env python3
"""Raw-data guard: protect existing files under data/raw/.

PreToolUse: creating a new raw file is allowed; modifying, overwriting, moving or deleting
an existing one needs human approval ("ask" in Claude Code; "deny" with instructions in
agents without an ask decision, e.g. Codex).
PostToolUse: after a new raw file is written, remind the agent to record provenance.

Usage: raw_guard.py --agent claude|codex   (hook JSON on stdin)

Best-effort, not a security boundary: shell detection is a heuristic. On any internal
error the guard writes to stderr and allows the action (fail open).
Standard library only.
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

RAW_PARTS = ("data", "raw")
SEPARATORS = {";", "&&", "||", "|", "&", "\n"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
DELETE_CMDS = {"rm", "unlink", "shred", "truncate", "remove-item", "del", "erase", "ri", "clear-content"}
MOVE_CMDS = {"mv", "cp", "move-item", "copy-item", "move", "copy"}
WRITE_CMDS = {"set-content", "add-content", "out-file"}
WRAPPERS = {"sudo", "command", "env", "nohup", "time"}
INPLACE = re.compile(r"^(-i|-[a-zA-Z]*i[a-zA-Z.]*|--in-place.*)$")
PATCH_LINE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$", re.MULTILINE)

RULE = "Hard rule: raw data in data/raw/ is never modified in place; corrections are a workflow step writing to data/processed/."
PROVENANCE = ("New raw file(s) added: {files}. Record each file's source (URL/accession or instrument run), "
              "download date, and checksum (e.g. sha256sum) in data/README.md.")


def project_root():
    env = os.environ.get("NERV_PROJECT_ROOT")
    return Path(env) if env else Path(__file__).resolve().parents[2]  # <root>/.nerv/hooks/


class Guard:
    def __init__(self, root, cwd):
        self.root = os.path.normcase(os.path.realpath(root))
        self.cwd = cwd or str(root)

    def raw_path(self, path):
        """Return the absolute path if it lies in data/raw/ (or is data/raw itself), else None."""
        if not path:
            return None
        full = os.path.realpath(os.path.join(self.cwd, os.path.expanduser(path)))
        try:
            rel = os.path.relpath(os.path.normcase(full), self.root)
        except ValueError:  # different drive on Windows
            return None
        parts = Path(rel).parts
        return full if tuple(parts[:2]) == RAW_PARTS else None

    def existing_raw(self, path):
        full = self.raw_path(path)
        return full if full and os.path.isfile(full) else None

    # --- PreToolUse -----------------------------------------------------------------
    def check_tool(self, tool, tool_input):
        """Return a list of protected paths this tool call would modify."""
        tool_input = tool_input if isinstance(tool_input, dict) else {}
        if tool in ("Write", "Edit", "MultiEdit"):
            hit = self.existing_raw(tool_input.get("file_path"))
            return [hit] if hit else []
        if tool == "NotebookEdit":
            hit = self.existing_raw(tool_input.get("notebook_path"))
            return [hit] if hit else []
        command = tool_input.get("command")
        if isinstance(command, list):  # some agents send argv
            command = " ".join(shlex.quote(c) for c in command)
        if not isinstance(command, str):
            return []
        if tool == "apply_patch" or command.lstrip().startswith("*** Begin Patch"):
            return self.check_patch(command)
        if tool in ("Bash", "PowerShell", "shell", "exec_command"):
            return self.check_shell(command)
        return []

    def check_patch(self, patch):
        hits = []
        for action, path in PATCH_LINE.findall(patch):
            full = self.existing_raw(path.strip()) if action == "Add" else self.raw_path(path.strip())
            if full:
                hits.append(full)
        return hits

    def check_shell(self, command):
        hits = []
        for words in split_commands(command):
            hits += self.check_simple(words)
        return hits

    def check_simple(self, words):
        hits, args = [], []
        i = 0
        while i < len(words):  # pull out redirect targets
            if words[i] in REDIRECTS and i + 1 < len(words):
                hit = self.existing_raw(words[i + 1])
                if hit:
                    hits.append(hit)
                i += 2
                continue
            args.append(words[i])
            i += 1
        while args and (args[0] in WRAPPERS or re.match(r"^\w+=", args[0])):
            args = args[1:]
        if not args:
            return hits
        name = os.path.basename(args[0]).lower()
        operands = [a for a in args[1:] if not a.startswith("-")]
        if name in DELETE_CMDS or (name in ("sed", "perl") and any(INPLACE.match(a) for a in args[1:])):
            hits += [p for p in map(self.raw_path, operands) if p]
        elif name in MOVE_CMDS and operands:
            if name in ("mv", "move-item", "move"):  # copy only reads its sources
                hits += [p for p in map(self.raw_path, operands[:-1]) if p]
            dest = self.existing_raw(operands[-1])
            if dest:
                hits.append(dest)
        elif name in WRITE_CMDS or name == "tee":
            hits += [p for p in map(self.existing_raw, operands) if p]
        return hits

    # --- PostToolUse ----------------------------------------------------------------
    def new_raw_files(self, tool, tool_input, tool_response):
        tool_input = tool_input if isinstance(tool_input, dict) else {}
        if tool == "Write":
            if isinstance(tool_response, dict) and tool_response.get("type") == "update":
                return []
            path = self.raw_path(tool_input.get("file_path"))
            return [path] if path else []
        command = tool_input.get("command")
        if tool == "apply_patch" and isinstance(command, str):
            return [p for a, f in PATCH_LINE.findall(command) if a == "Add" for p in [self.raw_path(f.strip())] if p]
        return []


def split_commands(command):
    """Split a shell command line into simple commands (lists of words). Heuristic."""
    command = command.replace("\\", "/")  # Windows paths; escapes are rare in practice
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes
        tokens = re.findall(r"[;&|<>]+|[^\s;&|<>]+", command)
    words, result = [], []
    for token in tokens:
        if token in SEPARATORS:
            result.append(words)
            words = []
        else:
            words.append(token)
    result.append(words)
    return [w for w in result if w]


def relative(paths, root):
    return ", ".join(sorted({Path(os.path.relpath(p, root)).as_posix() for p in paths}))


def decide(event, agent, root):
    """Return the JSON-serialisable hook output, or None to allow silently."""
    guard = Guard(root, event.get("cwd"))
    name = event.get("hook_event_name")
    tool = event.get("tool_name", "")
    if name == "PostToolUse":
        new = guard.new_raw_files(tool, event.get("tool_input"), event.get("tool_response"))
        if not new:
            return None
        return {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                       "additionalContext": PROVENANCE.format(files=relative(new, root))}}
    if name != "PreToolUse":
        return None
    hits = guard.check_tool(tool, event.get("tool_input"))
    if not hits:
        return None
    files = relative(hits, root)
    if agent == "claude":
        reason = f"This would modify or delete existing raw data ({files}). {RULE} Approve only if intended."
        decision = "ask"
    else:
        reason = (f"Blocked: this would modify or delete existing raw data ({files}). {RULE} "
                  "Do not retry or work around this. Write corrected output to data/processed/ via a "
                  "workflow step instead. If the user really wants this raw file changed, tell them the "
                  "exact command so they can run it themselves outside the agent.")
        decision = "deny"
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": reason}}


def main(argv):
    agent = argv[argv.index("--agent") + 1] if "--agent" in argv[:-1] else "claude"
    try:
        event = json.loads(sys.stdin.read())
        if not isinstance(event, dict):
            raise ValueError("hook input is not a JSON object")
        output = decide(event, agent, project_root())
    except Exception as exc:  # fail open: a broken guard must not break the session
        print(f"nerv raw_guard: allowing action after internal error: {exc!r}", file=sys.stderr)
        return 0
    if output:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
