#!/usr/bin/env python3
"""Doc-sync report: find top-level folders with major changes whose README.md was not updated.

Prints the out-of-sync folders as a JSON list and changes nothing. This is not a hook:
nerv-init copies it into projects as .nerv/scripts/sync_ratio.py, and the sync-ratio
skill runs it on demand. Prints [] outside git or when git is unavailable.

Standard library only.
"""
import json
import os
import subprocess
import sys

DEFAULT_THRESHOLD = 30
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


def main():
    _, report = find_out_of_sync(os.getcwd())
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
