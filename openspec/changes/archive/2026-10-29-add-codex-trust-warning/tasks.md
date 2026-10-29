# Tasks

## 1. Verify Codex trust behavior

- [x] 1.1 Check against the current Codex source or docs (Context7 or `openai/codex`) that project hooks are skipped until they are trusted, that `/hooks` is still the command to trust them, and that a change to `.codex/hooks.json` requires trusting them again. Verify by writing down what you found, with its source, before writing any step text. If the behavior differs, stop and update proposal.md and the spec first.

## 2. Next steps in the scaffold result

- [x] 2.1 In `tests/test_scaffold.py`, add tests that fail now: a created project's result has `next_steps`, a non-empty list of strings; the first entry names `/hooks` and says the raw-data guard and sync reminder are off in Codex until the hooks are trusted, and it mentions trusting them again after `.codex/hooks.json` changes; the list also covers `config/samples.tsv` and making `data/raw/` read-only; dry-run and conflict results have no `next_steps`. Verify the new tests fail with `.venv/Scripts/python -m pytest tests/test_scaffold.py`.
- [x] 2.2 In `skills/nerv-init/scripts/scaffold.py`, add a `NEXT_STEPS` constant (Codex trust step first, then samples and reference pins, then making `data/raw/` read-only) and include it as a list in the `created` result. Verify that the 2.1 tests and the full suite pass with `.venv/Scripts/python -m pytest`.

## 3. Skill and user docs

- [x] 3.1 Rewrite `skills/nerv-init/SKILL.md` step 6 to report the created tree and installed hooks, then show every entry of the scaffold result's `next_steps`, without shortening them. Remove its hand-written copy of the next-steps bullets so the list exists only in `scaffold.py`. Verify by reading the file: nothing in SKILL.md refers to a file outside `skills/nerv-init/`, and `test_skill_frontmatter_states_function_first` still passes.
- [x] 3.2 Update `README.md` "Hooks and their limits": the Codex trust bullet says `nerv-init` now prints this step after scaffolding, and the verification sentence lists the Codex trust check with today's date. Verify by reading the diff.
- [x] 3.3 Add **Next steps** to `GLOSSARY.md` under "Setting up a project": the follow-up actions the scaffold reports to the user after it creates a project. Verify that the term is used the same way in SKILL.md, the spec delta, and the code.

## 4. Review and integration

- [x] 4.1 Get a fresh-context review of the `scaffold.py` change, as the repo requires for changes to `scaffold.py`, and verify each finding before acting on it. Verify that all accepted findings are fixed and the full suite passes.
- [x] 4.2 Run `openspec validate add-codex-trust-warning --strict` and verify it passes.
- [x] 4.3 Set the Codex trust warning row in `ROADMAP.md` to done. Verify by reading the row.

## Workflow follow-up

- Run `/opsx:verify`, then `/opsx:archive` after review.
- Commit once per concern (code and tests, then docs), and push only when the user asks.
