# Design

## Context

`skills/nerv-init/hooks/sync_ratio.py` has two modes:

- **Hook mode** (the default) reads a `Stop` event from stdin, writes a digest to `.git/nerv-sync-state`, and prints `decision: block` once per state.
- **`--report`** prints the out-of-sync folders as JSON and touches no state.

The detection itself, `find_out_of_sync`, is shared by both modes and is already covered by `tests/test_sync_ratio.py`.

`scaffold.py` copies both hook scripts into `.nerv/hooks/`. It does not render anything under `.nerv/`, so the template variables are not applied there. Both adapters wire a `Stop` entry to the script.

Two places name the project path: `skills/sync-ratio/SKILL.md` runs `.nerv/hooks/sync_ratio.py --report`, and `test_scaffold.py` asserts it. Hard rule 1 means `sync-ratio` cannot reach into `nerv-init`'s folder, so it must use the project copy. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- Projects get only the raw-data guard as hooks. `.nerv/hooks/` holds only hooks.
- The report output (JSON shape, out-of-sync rules, threshold override) stays exactly as it is, so the `sync-ratio` flow after step 1 does not change.

**Non-Goals:**
- Touching `raw_guard.py` or its adapter entries.
- Migrating existing projects.

## Decisions

1. **Locations: `skills/nerv-init/scripts/sync_ratio.py` → `.nerv/scripts/sync_ratio.py`.**
   - In this repository the script sits next to `scaffold.py`, under the folder that already holds `nerv-init`'s scripts. A new top-level folder for one file would be over-engineering.
   - In projects, `.nerv/scripts/` mirrors `.nerv/hooks/`: the project owns its copy, and the copy keeps working if the skills are removed.
   - Rejected: shipping the script inside `skills/sync-ratio/`. The user chose to keep it installed by `nerv-init`, and an agent-specific install path (`.claude/skills/` versus `.agents/skills/`) would make the SKILL.md command depend on the agent.
   - One trade-off: `scripts/` in this repository now mixes a scaffold-time tool with a file that gets copied into projects. The module docstring states which one it is.

2. **Report-only means no flag.** The script always prints the report. Hook mode goes away entirely: `run_hook`, `state_path`, `reminder`, `STATE_FILE`, the stdin read, the `hashlib` import, and the `--report` switch.
   - Keeping `--report` as an accepted no-op would be a speculative option.
   - The skill's command changes anyway, because the path changes.

3. **No broad exception guard.** Hard rule 3 (fail open) applies to hooks, and this is no longer one. As now, git failures still produce an empty report, through `git()` returning `None`. Any other error is a crash with a traceback, which is the right signal for a command run on demand.

4. **Adapters lose the whole `Stop` key,** not just its entry. The Codex `description` drops "+ doc-sync". `test_adapters_point_to_project_hooks` keeps working, because every remaining command still points to `.nerv/hooks/`. A new assertion checks that neither adapter has a `Stop` key.

5. **Codex trust step wording.** Drop "and the sync reminder", and name only `.nerv/hooks/raw_guard.py` in the list of hooks to trust. The test changes from asserting "sync reminder" to asserting that it is absent.

6. **Glossary.** Remove the "Sync reminder" term, because nothing produces that message anymore. Change the Angel codename note so it no longer refers to the reminder; it can say "the threat the sync-ratio report finds". "Sync ratio", "Major change", and "Out of sync" stay.

7. **Main spec purposes.** The `doc-sync` and `project-bootstrap` Purpose lines mention the sync reminder. Deltas cannot change a Purpose, so they are edited directly in `openspec/specs/` after archive syncs the requirements. That is a prose-only edit to a main spec.

## Risks / Trade-offs

- **[Risk] Projects scaffolded earlier still run their own `Stop` hook,** and their `sync-ratio` skill (if reinstalled) looks for `.nerv/scripts/sync_ratio.py`, which they don't have. → The skill's "script missing" branch tells the user. The only known project like this is the throwaway test-run project, so no fallback path is added (proposal, out of scope).
- **[Risk] Fewer README updates without the nudge.** → `magi-review` CASPER-3 already checks the "Current state" and "Last major change" sections of significantly changed folders. The next test run will show whether that is enough.
- **[Trade-off] The detection stays as code,** although SCOPE.md prefers prose. → The user chose this. Code keeps the report deterministic and keeps its existing tests.

## Migration Plan

- Ship as one OpenSpec change with commits per concern:
  1. the script and its tests;
  2. scaffold, adapters, and template;
  3. skill docs, README, and glossary.
- Rollback is a revert. No user data or state depends on it.
- The stale `.git/nerv-sync-state` in old projects is harmless and is left alone.
