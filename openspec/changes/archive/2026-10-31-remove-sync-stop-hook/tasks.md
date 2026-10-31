# Tasks

## 1. Report-only sync script

- [x] 1.1 Update `tests/test_sync_ratio.py` so that it fails now:
  - point `SCRIPT` to `NERV_INIT / "scripts" / "sync_ratio.py"`;
  - delete the hook-mode tests (`stop()` helper, `test_stop_reminds_once_per_state`, `test_stop_hook_active_never_blocks`, `test_state_cleared_when_in_sync`, `test_cli_one_continuation_at_most`, `test_malformed_stdin_uses_cwd`);
  - rewrite the CLI tests to call the script with no arguments. Check that a project with `scripts/` out of sync prints the expected JSON list and writes no `.git/nerv-sync-state`. Check that an in-sync repo and a directory without git both print `[]` and exit 0;
  - keep the detection tests (`folders()`) as they are.

  Verify that the tests fail with `.venv/Scripts/python -m pytest tests/test_sync_ratio.py`.
- [x] 1.2 Move the script with `git mv skills/nerv-init/hooks/sync_ratio.py skills/nerv-init/scripts/sync_ratio.py`, then make it report-only (design decisions 2 and 3):
  - remove `run_hook`, `state_path`, `reminder`, `STATE_FILE`, the `hashlib` import, the stdin read, and the `--report` switch;
  - `main` prints the report;
  - rewrite the docstring to say that it is the on-demand doc-sync report that `nerv-init` copies into projects as `.nerv/scripts/sync_ratio.py`.

  Verify that the 1.1 tests pass.
- [x] 1.3 Update `skills/sync-ratio/SKILL.md`:
  - the command becomes `python .nerv/scripts/sync_ratio.py`, without `--report`;
  - the "missing" check names `.nerv/scripts/sync_ratio.py`;
  - drop "The same check runs automatically as a Stop hook";
  - drop the note "Report mode never changes the hook's remind-once state".

  Verify with `grep -n -i "hook\|--report" skills/sync-ratio/SKILL.md` (no matches) and with the `tests/test_skill_docs.py` tests passing.
- [x] 1.4 Update `GLOSSARY.md` (design decision 6):
  - remove the "Sync reminder" term;
  - change the Angel codename note so it no longer mentions the reminder.

  Verify with `grep -n -i "sync reminder" GLOSSARY.md` (no matches).

## 2. Scaffold and adapters without the Stop hook

- [x] 2.1 Update `tests/test_scaffold.py` so that it fails now:
  - `assert_common` expects `.nerv/scripts/sync_ratio.py` and asserts that `.nerv/hooks/sync_ratio.py` does not exist;
  - add a test that neither adapter (the files in this repository and the copies in the scaffolded project) has a `Stop` key;
  - `test_created_result_lists_next_steps` asserts that "sync reminder" and `sync_ratio.py` are *not* in the trust step, and that "raw-data guard" and "off in Codex until" still are;
  - add a test that runs the installed `.nerv/scripts/sync_ratio.py` in a scaffolded project and gets valid JSON.

  Verify that the tests fail with `.venv/Scripts/python -m pytest tests/test_scaffold.py`.
- [x] 2.2 In `skills/nerv-init/scripts/scaffold.py`:
  - copy only `raw_guard.py` into `.nerv/hooks/`;
  - copy `sync_ratio.py` from the scaffold's own folder into `.nerv/scripts/sync_ratio.py`;
  - rewrite the Codex entry in `NEXT_STEPS` so it names only the raw-data guard and `.nerv/hooks/raw_guard.py`.

  Verify that the 2.1 tests pass.
- [x] 2.3 Remove the `Stop` block from `skills/nerv-init/hooks/adapters/claude-settings.json` and `codex-hooks.json`, and drop "+ doc-sync" from the Codex `description`. Verify that both files still parse (`.venv/Scripts/python -m json.tool <file>`) and that the 2.1 adapter test passes.
- [x] 2.4 In `skills/nerv-init/templates/base/AGENTS.md.tmpl`, delete "A hook reminds you once if you forget." Verify that `tests/test_templates.py` passes and that `grep -rn -i "hook reminds" skills/` has no matches.
- [x] 2.5 Update the docs that describe hooks:
  - `skills/nerv-init/SKILL.md`: remove the `sync_ratio.py` bullet from "Hooks installed";
  - `README.md`: in the intro, hooks no longer keep READMEs current. Remove the Stop-hook sentence from the `sync-ratio` row. Remove the "README sync reminder" row from the hook table. Remove "and sync reminder" from the Codex limits bullet. Update the repository layout so `scripts/` holds `scaffold.py` and `sync_ratio.py`, and `hooks/` holds `raw_guard.py` and `adapters/`.

  Verify with `grep -rn -i "sync reminder\|stop hook\|hooks/sync_ratio" README.md skills/` (no matches). The verification dates stay as they are, because no adapter schema was added.

## 3. Review and integration

- [x] 3.1 Run the full suite with `.venv/Scripts/python -m pytest` and verify that every test passes.
- [x] 3.2 Get a fresh-context review of the `scaffold.py`, adapter, and `sync_ratio.py` diffs, which the repo requires for changes to hooks and `scaffold.py`. Give the reviewer the code and the spec deltas, not this design's conclusions. Verify each finding before acting on it, and confirm that the full suite passes after the accepted fixes.
- [x] 3.3 Run `openspec validate remove-sync-stop-hook --strict` and verify that it passes.
- [x] 3.4 Set the "Remove the sync Stop hook" row in `ROADMAP.md` to done. Verify by reading the row.

## Workflow follow-up

- Run `/opsx:verify`, then `/opsx:archive` after review.
- After archiving, edit the Purpose lines of `openspec/specs/doc-sync/spec.md` and `openspec/specs/project-bootstrap/spec.md` so they no longer mention the sync reminder (design decision 7).
- Commit once per concern (the script, then scaffold and adapters, then docs), and push only when the user asks.
