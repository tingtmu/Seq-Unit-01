#!/usr/bin/env python3
"""Raw-data guard: protect existing files under data/raw/.

PreToolUse: creating a new raw file is allowed; modifying, overwriting, moving or deleting
an existing one needs human approval ("ask" in Claude Code; "deny" with instructions in
agents without an ask decision, e.g. Codex).
PostToolUse: compare data/raw/ with the raw snapshot (.nerv/raw-snapshot.json: each file's
size and modification time), then save the new one. New raw files get a provenance reminder
with a SHA-256 command for this OS, whatever tool or command wrote them. Existing raw files
that were modified or removed are reported after the fact, with a note that their provenance
records no longer match; nothing is blocked or undone.

Usage: raw_guard.py --agent claude|codex   (hook JSON on stdin)

Best-effort, not a security boundary: shell detection is a heuristic, and writes that keep
a file's size and modification time are missed. On any internal
error the guard writes to stderr and allows the action (fail open).
Standard library only.
"""
import json
import os
import re
import shlex
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

RAW_PARTS = ("data", "raw")
SNAPSHOT_PARTS = (".nerv", "raw-snapshot.json")
MAX_LISTED = 20  # keep the message short when many raw files change at once
SEPARATORS = {";", "&&", "||", "|", "&", "\n"}
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
DELETE_CMDS = {"rm", "unlink", "shred", "truncate", "remove-item", "del", "erase", "ri", "clear-content"}
MOVE_CMDS = {"mv", "cp", "move-item", "copy-item", "move", "copy"}
WRITE_CMDS = {"set-content", "add-content", "out-file"}
WRAPPERS = {"sudo", "command", "env", "nohup", "time"}
INPLACE = re.compile(r"^(-i|-[a-zA-Z]*i[a-zA-Z.]*|--in-place.*)$")
PATCH_LINE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$", re.MULTILINE)

RULE = "Hard rule: raw data in data/raw/ is never modified in place; corrections are a workflow step writing to data/processed/."
NOT_IN_GIT = "raw data is not in git"
PROVENANCE = ("New raw file(s) added: {files}. Record each file's source (URL/accession or instrument run), "
              "download date, and SHA-256 checksum in data/README.md. Checksum command: {command}")
CHANGED = ("Raw files changed since the last raw snapshot: {files}. If the user did not approve this, "
           "stop and tell them now. Their provenance records in data/README.md no longer match, and "
           f"because {NOT_IN_GIT}, recovering a file means fetching it again from its source. " + RULE)
CHECKSUM_TOOLS = {"darwin": "shasum -a 256", "win32": "Get-FileHash -Algorithm SHA256"}  # others: sha256sum


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


def raw_snapshot(root):
    """Map each file under data/raw/ (relative posix path) to [size, mtime_ns].

    A folder that cannot be listed raises instead of reading as "all files removed"
    (e.g. a stale network mount), so the last good raw snapshot is kept.
    """
    raw = Path(root, *RAW_PARTS)
    if not os.path.lexists(raw):
        return {}
    snapshot, seen = {}, set()

    def fail(exc):
        raise exc

    for folder, dirs, names in os.walk(raw, followlinks=True, onerror=fail):
        seen.add(os.path.realpath(folder))
        dirs[:] = [d for d in dirs if os.path.realpath(os.path.join(folder, d)) not in seen]  # symlink loops
        for name in names:
            if name == ".gitkeep":
                continue
            path = os.path.join(folder, name)
            with suppress(FileNotFoundError):  # removed mid-walk, or a broken symlink
                st = os.stat(path)
                snapshot[Path(os.path.relpath(path, root)).as_posix()] = [st.st_size, st.st_mtime_ns]
    return snapshot


def load_snapshot(path):
    """Return the saved raw snapshot, {} if there is none yet. Raise ValueError if it is corrupt.

    Other OSErrors (e.g. Windows locking it during a parallel save) propagate, so the run
    fails open without overwriting it.
    """
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(saved, dict):
        raise ValueError("raw snapshot is not a JSON object")
    return saved


def save_snapshot(path, snapshot):
    """Write atomically, so a parallel hook run never reads a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".raw-snapshot-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(snapshot, f)
        os.replace(tmp, path)
    except BaseException:
        with suppress(OSError):
            os.unlink(tmp)
        raise


def raw_changes(root):
    """Diff data/raw/ against the raw snapshot and save the new one. Return the hook message or None."""
    path = Path(root, *SNAPSHOT_PARTS)
    try:  # load before walking, so a parallel run's newer save never makes a file look removed
        saved = load_snapshot(path)
    except ValueError as exc:
        print(f"nerv raw_guard: replacing corrupt raw snapshot: {exc!r}", file=sys.stderr)
        saved = None
    current = raw_snapshot(root)
    save_snapshot(path, current)
    if saved is None:
        return None
    added = sorted(current.keys() - saved.keys())
    changed = sorted([f"{p} (modified)" for p in current.keys() & saved.keys() if current[p] != saved[p]]
                     + [f"{p} (removed)" for p in saved.keys() - current.keys()])
    messages = []
    if added:
        messages.append(PROVENANCE.format(files=listing(added), command=checksum_command(added[:MAX_LISTED])))
    if changed:
        messages.append(CHANGED.format(files=listing(changed)))
    return " ".join(messages) or None


def listing(items):
    extra = len(items) - MAX_LISTED
    return ", ".join(items[:MAX_LISTED]) + (f", and {extra} more" if extra > 0 else "")


def checksum_command(files, platform=sys.platform):
    """Return a SHA-256 command for these project-relative files, in the platform's usual shell."""
    if platform == "win32":  # -LiteralPath: -Path would read [ ] as wildcards and silently match nothing
        quoted = ", ".join("'" + f.replace("'", "''") + "'" for f in files)
        return f"{CHECKSUM_TOOLS[platform]} -LiteralPath {quoted} | Format-List Hash, Path"
    return f"{CHECKSUM_TOOLS.get(platform, 'sha256sum')} {' '.join(map(shlex.quote, files))}"


def relative(paths, root):
    return ", ".join(sorted({Path(os.path.relpath(p, root)).as_posix() for p in paths}))


def decide(event, agent, root):
    """Return the JSON-serialisable hook output, or None to allow silently."""
    name = event.get("hook_event_name")
    if name == "PostToolUse":
        message = raw_changes(root)
        return message and {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}
    if name != "PreToolUse":
        return None
    hits = Guard(root, event.get("cwd")).check_tool(event.get("tool_name", ""), event.get("tool_input"))
    if not hits:
        return None
    files = relative(hits, root)
    if agent == "claude":
        reason = f"This would modify or delete existing raw data ({files}). {RULE} Approving cannot be undone: {NOT_IN_GIT}. Approve only if intended."
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
