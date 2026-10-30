# Tasks

## 1. Raw-data guard messages

- [x] 1.1 In `tests/test_raw_guard.py`, add tests that fail now:
  - (a) For two new raw files, the provenance reminder contains a SHA-256 command naming both files. Test the per-OS choice (`linux` → `sha256sum`, `darwin` → `shasum -a 256`, `win32` → `Get-FileHash -Algorithm SHA256`) by importing the module and calling the helper with an explicit platform. Add one hook-run test for the current platform.
  - (b) A modified raw file's report says that its provenance record in `data/README.md` no longer matches and that recovery means fetching the file again from its source. Cover a removed file the same way.
  - (c) The Claude Code "ask" reason says that approving cannot be undone because raw data is not in git. The Codex "deny" reason is unchanged.
  - Update `test_script_modifying_raw_file_reported`: it asserts that `data/README.md` is *not* in the report. Replace that check with one that the new-file reminder text is absent.
  - Verify that the new tests fail with `.venv/Scripts/python -m pytest tests/test_raw_guard.py`.
- [x] 1.2 In `skills/nerv-init/hooks/raw_guard.py`:
  - add a checksum-command helper that takes the file list and the platform (default `sys.platform`). On Linux and macOS it quotes paths with `shlex.quote`. On Windows it single-quotes and comma-joins them, and uses `Get-FileHash -LiteralPath … | Format-List Hash, Path`;
  - append its command to `PROVENANCE`;
  - add the provenance-mismatch sentence to `CHANGED`;
  - add the cannot-be-undone sentence to the Claude "ask" reason.
  - Update the module docstring if its summary changes. Use standard library only; on errors the hook still fails open.
  - Verify that the 1.1 tests and the full suite pass with `.venv/Scripts/python -m pytest`.
- [x] 1.3 Update `README.md` "Hooks and their limits", the raw-data guard rows and limits bullet: the reminder includes a checksum command, the after-the-fact report names the provenance mismatch, and the approval request warns that it can't be undone. Update the raw-data guard paragraph near the top if it describes these messages, and the `nerv-init` SKILL.md hook bullet only if its wording becomes wrong. Verify by reading the diff: no hook adapter changed, so the verification date stays as it is.

## 2. Read-only next step

- [x] 2.1 In `tests/test_scaffold.py`, extend `test_created_result_lists_next_steps` so that it fails now:
  - the read-only entry contains "Recommended" and not "Optional";
  - it gives both `chmod` and `attrib` commands;
  - it gives both undo commands (`u+w`, `attrib -R`);
  - it says to apply the step after a batch is recorded in `data/README.md`.
  - Verify that it fails with `.venv/Scripts/python -m pytest tests/test_scaffold.py`.
- [x] 2.2 Rewrite the read-only entry of `NEXT_STEPS` in `skills/nerv-init/scripts/scaffold.py` as described in design decision 4. Keep its position and leave the `attrib` quoting as it is. Verify that the 2.1 test and the full suite pass.
- [x] 2.3 If `README.md` or `skills/nerv-init/SKILL.md` describes the read-only step as optional, update that wording. Verify with `grep -n -i "optional" README.md skills/nerv-init/SKILL.md`.

## 3. Review and integration

- [x] 3.1 Get a fresh-context review of the `raw_guard.py` and `scaffold.py` diffs, which the repo requires for changes to hooks and `scaffold.py`. Give the reviewer the code and the spec deltas, not this design's conclusions. Verify each finding before acting on it, and confirm that the full suite passes after the accepted fixes.
- [x] 3.2 Run `openspec validate raw-change-recovery --strict` and verify that it passes.
- [x] 3.3 Set the "Raw change recovery" row in `ROADMAP.md` to done. Verify by reading the row.

## Workflow follow-up

- Run `/opsx:verify`, then `/opsx:archive` after review.
- Commit once per concern (guard messages, then the next step, then docs), and push only when the user asks.
- Optionally re-run Prompt 2 steps 1–4 in `../nerv-testrun` after a fresh `npx skills add`, to see the new messages in a live session.
