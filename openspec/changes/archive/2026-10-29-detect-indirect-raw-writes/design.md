# Design

## Context

`raw_guard.py` handles PreToolUse (ask or deny before a direct write) and PostToolUse (a provenance reminder). Today PostToolUse finds new raw files by parsing each tool's input: Write's `tool_response.type` and the `*** Add File:` lines of `apply_patch`. The adapters wire PostToolUse only for `Write` (Claude) and `apply_patch` (Codex). Hooks must use only the standard library, run cross-platform, and fail open. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- One PostToolUse code path that reports new, modified, and removed raw files, whatever tool caused them.
- Keep each hook run fast enough for a 10 s timeout on large raw folders.

**Non-Goals:**
- Preventing indirect writes (read-only locking), content hashing, checksum manifests.
- Matching a PostToolUse report to the PreToolUse decision that approved it.
- Detecting changes made outside the agent between tool calls (they show up at the next tool call, which is acceptable).

## Decisions

**Snapshot diff replaces per-tool parsing.** After a covered tool call, walk `data/raw/`, record `(relative path -> [size, mtime_ns])`, and diff it against the saved snapshot. Added paths go into the provenance reminder. Paths that changed or disappeared go into the change report. Then save the new snapshot. The old `new_raw_files` parsing is deleted rather than kept beside the diff, so there's a single source of truth. If both ran, a Write followed by a Bash call would produce a duplicate reminder.
_Alternative:_ keep the parsing and add the diff only for shell tools. Rejected because there would be two mechanisms and they would need deduplication.

**Size + mtime, no hashing.** `os.stat` per file is cheap. sha256 over FASTQ files is minutes per file. Writes that keep mtime and size (`cp -p`, `touch -r` over a same-size file) slip through, which the best-effort spec accepts.

**Snapshot at `<project>/.nerv/raw-snapshot.json`, gitignored.** It goes next to the hooks under `project_root()`, which is the root the guard already resolves.
_Alternative:_ the git dir via `git rev-parse --git-path`, like `sync_ratio`. Rejected for this hook because it would cost a git subprocess on every file-edit or shell call, and outside git the provenance reminder (which works without git today) would stop. Scaffold adds `.nerv/raw-snapshot.json` to the generated `.gitignore`.

**A missing snapshot means an empty baseline.** A new project has an empty `data/raw/`, so its first raw file is reported as new, which is correct. A project that already holds data and copies in the new hook gets one reminder that lists its existing files. That's acceptable, and needs no special first-run logic. A corrupt or unreadable snapshot is reported to stderr and replaced with the current state, with no message to the agent (fail open).

**Ignore `.gitkeep`.** Scaffold puts it in `data/raw/`. It isn't raw data.

**Follow directory symlinks** (`os.walk(followlinks=True)`). Raw data is often linked in from shared storage, and an unfollowed link would hide every file under it.

**One message, through `additionalContext`.** Both agents already accept `hookSpecificOutput.additionalContext` on PostToolUse. That's how the provenance reminder works today. New and changed files go into one message, and the guard prints nothing when both lists are empty. The change wording is neutral ("if the user did not approve this, stop and tell them"), so a change the user just approved through PreToolUse only produces a redundant line.

**Matchers.** Claude PostToolUse uses the same matcher as PreToolUse (`Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell`), and Codex uses `^(apply_patch|Bash)$`. Both schemas get re-verified against current docs before the adapters are edited, and the date goes into README.md.

**Atomic save.** The snapshot is written to a temp file in `.nerv/`, then `os.replace` puts it in place, so parallel tool calls never read a half-written file.

## Risks / Trade-offs

- [Walking a large or network-mounted `data/raw/` is slow] → stat only, no reads. If the hook times out the agent continues (fail open), and the next run diffs against the last saved snapshot, so nothing is lost permanently.
- [Two parallel tool calls race on the snapshot] → atomic replace. At worst one change is reported twice or by the other call. It's never lost silently, because the diff is always against the last saved state.
- [mtime-preserving rewrites are missed] → documented as best-effort. The README still recommends OS read-only permissions and checksums for real protection.
- [A change the user just approved is reported again] → neutral wording. The cost is one extra line.

## Migration Plan

Existing generated projects keep their own hook copies and are unaffected. To adopt the change, a project copies the new `raw_guard.py` and adapters. The first run reports existing raw files once as new.
