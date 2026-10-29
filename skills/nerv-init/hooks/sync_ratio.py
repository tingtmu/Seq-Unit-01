#!/usr/bin/env python3
"""Doc-sync check: find top-level folders with major changes whose README.md was not updated.

Hook mode (default): reads the agent's Stop-event JSON on stdin. If folders are out of
sync and this exact state has not been reported before, prints a single
{"decision": "block", "reason": ...} so the agent gets one turn to update READMEs.
Works for Claude Code and Codex (same Stop schema). Never blocks twice for one state.

Report mode (--report): prints the out-of-sync folders as JSON and touches no state.

Standard library only. Exits 0 silently outside git or when git is unavailable.
"""
import hashlib
import json
import os
import subprocess
import sys

DEFAULT_THRESHOLD = 30
STATE_FILE = "nerv-sync-state"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def git(cwd, *args):
    """Run git and return stdout, or None if git is missing or the command fails."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except (OSError, ValueError):
        return None
    return result.stdout if result.returncode == 0 else None


def threshold():
    try:
        return int(os.environ.get("NERV_SYNC_THRESHOLD", DEFAULT_THRESHOLD))
    except ValueError:
        return DEFAULT_THRESHOLD


def top_folder(path):
    return path.split("/", 1)[0] if "/" in path else None


def find_out_of_sync(cwd):
    """Return (repo_root, report) where report is a sorted list of out-of-sync folders,
    or (None, []) when cwd is not inside a git repository."""
    root = git(cwd, "rev-parse", "--show-toplevel")
    if root is None:
        return None, []
    root = root.strip()

    status = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames")
    if status is None:
        return None, []
    changed, added_or_deleted = set(), set()
    for entry in filter(None, status.split("\0")):
        code, path = entry[:2], entry[3:]
        changed.add(path)
        if code == "??" or "A" in code or "D" in code:
            added_or_deleted.add(path)

    base = "HEAD" if git(root, "rev-parse", "--verify", "-q", "HEAD") is not None else EMPTY_TREE
    lines = {}
    for entry in filter(None, (git(root, "diff", "--numstat", "-z", "--no-renames", base) or "").split("\0")):
        added, deleted, path = entry.split("\t", 2)
        folder = top_folder(path)
        if folder and added != "-":
            lines[folder] = lines.get(folder, 0) + int(added) + int(deleted)

    folders = {top_folder(p) for p in changed} - {None}
    report = []
    for folder in sorted(folders):
        readme = f"{folder}/README.md"
        if not os.path.isfile(os.path.join(root, folder, "README.md")) or readme in changed:
            continue
        files = sorted(p for p in changed if top_folder(p) == folder)
        major = any(p in added_or_deleted for p in files) or lines.get(folder, 0) > threshold()
        if major:
            report.append({"folder": f"{folder}/", "readme": readme, "files": files})
    return root, report


def state_path(root):
    path = git(root, "rev-parse", "--git-path", STATE_FILE)
    return os.path.join(root, path.strip()) if path else None


def reminder(report):
    items = "\n".join(f"- {r['folder']} -> update {r['readme']}" for r in report)
    return (
        "Doc sync (Boy Scout Rule): these folders changed significantly but their README "
        f"was not updated:\n{items}\n"
        "If warranted, update the 'Current state' and 'Last major change' sections. "
        "Otherwise just stop again; this reminder will not repeat for the same state."
    )


def run_hook(stdin_text):
    """Return the JSON string to print for a Stop event, or None to stay silent."""
    try:
        event = json.loads(stdin_text) if stdin_text.strip() else {}
    except json.JSONDecodeError:
        event = {}
    if event.get("stop_hook_active"):
        return None
    root, report = find_out_of_sync(event.get("cwd") or os.getcwd())
    if root is None:
        return None
    state = state_path(root)
    if not report:
        if state and os.path.exists(state):
            os.remove(state)
        return None
    digest = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
    if state and os.path.exists(state):
        with open(state, encoding="utf-8") as fh:
            if fh.read().strip() == digest:
                return None
    if state:
        with open(state, "w", encoding="utf-8") as fh:
            fh.write(digest)
    return json.dumps({"decision": "block", "reason": reminder(report)})


def main(argv):
    if "--report" in argv:
        _, report = find_out_of_sync(os.getcwd())
        print(json.dumps(report, indent=2))
        return 0
    try:
        output = run_hook(sys.stdin.read())
    except Exception as exc:  # never break the agent session
        print(f"nerv sync_ratio: {exc!r}", file=sys.stderr)
        return 0
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
