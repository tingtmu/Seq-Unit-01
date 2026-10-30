# Proposal

## Why

In the first test run (2026-10-30, finding R3), a misclicked approval let an agent edit an existing raw file, and the change could not be undone. Raw data is git-ignored, the raw snapshot keeps sizes and times but no contents, and nothing told the user that the file's provenance record in `data/README.md` no longer matched it. With real data, the only way back is to fetch the file again from its source. The raw-data guard already detects the change. What's missing is telling the user what the change costs and making the real protection, OS read-only, the normal step instead of an optional one.

## What Changes

- **After-the-fact report:** when existing raw files are modified or removed, the raw-data guard's report also says that their provenance records in `data/README.md` no longer match, and that raw data is not in git, so getting a file back means fetching it again from its source.
- **Approval request (Claude Code):** the "ask" message for changing an existing raw file says that approving cannot be undone, because raw data is not in git. Codex's deny message doesn't change.
- **Provenance reminder:** the reminder for new raw files includes a ready-to-run SHA-256 command for those files, chosen for the user's operating system.
- **Next steps:** the read-only step changes from "Optional" to "Recommended". It also says when to apply it (after each batch is in place and recorded) and how to undo it before adding the next batch.

Out of scope:
- verifying checksums in the hook
- backing up raw contents
- an opt-in deny policy for Claude Code (a separate ROADMAP idea)
- fixing the `attrib` example so it works in Git Bash (part of the "First-run next steps" ROADMAP item)

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `raw-data-guard`:
  - "Allow new raw files with provenance reminder": the reminder includes a SHA-256 command.
  - "Require approval to modify or delete existing raw files": the approval request warns that approval cannot be undone.
  - "Report changes to existing raw files after the fact": the report names the provenance records that no longer match and how to recover.
- `project-bootstrap`: adds the requirement "Read-only raw data recommended after scaffolding". The read-only step is now covered by a spec, as a recommendation with when-to-apply and undo guidance.

## Impact

- `skills/nerv-init/hooks/raw_guard.py`: the message texts and choosing the checksum command. No change to detection or decisions.
- `skills/nerv-init/scripts/scaffold.py`: the read-only entry in `NEXT_STEPS`.
- `tests/test_raw_guard.py`:
  - new tests;
  - `test_script_modifying_raw_file_reported` currently asserts that `data/README.md` is *not* in the report, and must change.
- `tests/test_scaffold.py`: the next-steps test checks "Recommended".
- `README.md`: the "Hooks and their limits" rows for the raw-data guard. No hook adapter changes, so no external schema check is needed.
- Both files change hook or scaffold code, so a fresh-context review is required before merging.
