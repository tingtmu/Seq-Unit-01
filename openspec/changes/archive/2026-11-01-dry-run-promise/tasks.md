# Tasks

## 1. Dry run reports conflicts

- [x] 1.1 Add `test_dry_run_reports_conflicts` to `tests/test_scaffold.py`: with `README.md` ("mine\n") and a `scripts/` folder in `tmp_path`, `scaffold.scaffold(answers(), tmp_path, dry_run=True)` returns code 1, `status == "conflict"`, `conflicts == ["README.md", "scripts/"]`, no `files` key, and the directory still holds only those two entries with `README.md` unchanged. It pins existing behavior, so it passes without code changes; confirm it fails if the `dry_run` check is moved above the conflict check, then revert that probe. Verify with `.venv/Scripts/python -m pytest tests/test_scaffold.py`.
- [x] 1.2 Extend `test_dry_run_writes_nothing` to assert `result["status"] == "planned"`. Verify with the same command.

## 2. Skill prose

- [x] 2.1 Rewrite the last two sentences of `skills/nerv-init/SKILL.md` step 2 so they say: if the result's `status` is `conflict`, show its `conflicts` list and stop to ask; if it is `planned`, there are no conflicts, so show the top-level tree from `files` and name the add-ons that apply (assay, engine, and language layers), taken from the answers using the answer-to-output table in `references/interview.md`, not guessed from file names. Keep step 3 unchanged. Verify `.venv/Scripts/python -m pytest tests/test_skill_docs.py` passes and the description's first sentence is unchanged.

## 3. Integration

- [x] 3.1 Run the full suite with `.venv/Scripts/python -m pytest`; all tests pass. Run `openspec validate dry-run-promise --strict`; it passes.

## Workflow follow-up

- Review gate after propose and after apply: commit, then a fresh-context reviewer checks the commit range against AGENTS.md and this change's spec.
- Record in the next test run's notes whether the agent named the add-ons from the answers and handled a dry-run conflict as step 2 says.
- Archive, then mark the ROADMAP item `done`.
