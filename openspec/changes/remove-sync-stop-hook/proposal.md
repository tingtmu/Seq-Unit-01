# Proposal

## Why

The 2026-10-30 scope review froze hooks and moved standards to review. The sync Stop hook breaks both decisions: it forces an extra agent turn, and `magi-review` already checks stale READMEs (CASPER-3's "Docs" lens). Removing it is the "deleting counts" route the admission bar allows. The on-demand `sync-ratio` skill stays, so the out-of-sync check stays as well, but only as a report the agent runs when asked, not as a hook.

## What Changes

- **BREAKING (generated projects):** projects created by `nerv-init` no longer get a `Stop` hook. The Claude Code and Codex hook adapters wire only the raw-data guard.
- The doc-sync script becomes report-only. Hook mode goes away: reading the Stop event, the remind-once state file (`.git/nerv-sync-state`), the `decision: block` output, and the `--report` flag, because reporting is now the only mode.
- The script moves out of `hooks/`, since it is no longer a hook. In this repository it moves from `skills/nerv-init/hooks/sync_ratio.py` to `skills/nerv-init/scripts/sync_ratio.py`. `nerv-init` installs it in projects as `.nerv/scripts/sync_ratio.py` instead of `.nerv/hooks/sync_ratio.py`.
- The `sync-ratio` skill runs `.nerv/scripts/sync_ratio.py`. It no longer says that the check runs automatically as a Stop hook, and it drops the note about the remind-once state.
- The scaffold's Codex trust step names only the raw-data guard.
- The generated `AGENTS.md` drops "A hook reminds you once if you forget."
- `README.md`, the `nerv-init` SKILL.md "Hooks installed" list, and `GLOSSARY.md` drop the sync reminder.

Out of scope:
- **Converting `sync-ratio` to a prose-only skill.** The user chose to keep the script, report-only.
- **A fallback for projects scaffolded before this change.** Their `.nerv/hooks/sync_ratio.py` and their `Stop` hook still work, because the project owns its hook version.
- **Changing what counts as a major change, or the `NERV_SYNC_THRESHOLD` override.**
- **The "Small skill wording" ROADMAP item (S3, `git status --short` in step 2).**

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `doc-sync`:
  - The requirement "Non-blocking sync reminder at end of turn" is removed.
  - "Detect major changes per folder" is now an on-demand report, not a hook.
  - "Graceful outside git" changes from a silent hook exit to an empty report.
  - "Manual sync skill" runs the project's report script.
- `project-bootstrap`:
  - "Git initialization and hook installation" installs only the raw-data guard hooks, plus the report script outside the hooks folder.
  - "Codex trust step reported after scaffolding" no longer mentions the sync reminder.

## Impact

- **Code:**
  - `skills/nerv-init/hooks/sync_ratio.py` is removed.
  - `skills/nerv-init/scripts/sync_ratio.py` is new and report-only.
  - `skills/nerv-init/scripts/scaffold.py` changes its copy step and the Codex trust entry in `NEXT_STEPS`.
  - `skills/nerv-init/hooks/adapters/{claude-settings,codex-hooks}.json` lose the `Stop` block and the "doc-sync" in the Codex description.
- **Templates:** `skills/nerv-init/templates/base/AGENTS.md.tmpl`.
- **Skills:** `skills/sync-ratio/SKILL.md` and `skills/nerv-init/SKILL.md`.
- **Tests:**
  - `tests/test_sync_ratio.py` loses the hook-mode tests and points to the new path.
  - `tests/test_scaffold.py` covers the installed paths, adapters without `Stop`, and the trust-step wording.
- **Docs:** `README.md` (skill table, intro, hook table, Codex limits bullet, repository layout) and `GLOSSARY.md` (the "Sync reminder" term and the Angel codename note).
- **No new external schema:** this change only deletes adapter entries and adds none, so no hook schema needs re-checking. The README verification dates stay as they are.
- **Review:** hooks and `scaffold.py` change, so a fresh-context review is required before merging.
