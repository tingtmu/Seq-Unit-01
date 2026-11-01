# Tasks

## 1. Identity check and conditional commit step (scaffold.py)

- [ ] 1.1 In `tests/test_scaffold.py`, add a fixture that isolates git config (`GIT_CONFIG_GLOBAL` set to a temp file, `GIT_CONFIG_NOSYSTEM=1`), with and without `user.name`/`user.email`. Add tests for scenarios "Identity already set" (result has `git_identity: "set"`, and no step contains `git config` or `git commit`) and "No git identity on the machine" (result has `git_identity: "missing"`, and the commit step keeps its commands in order, with no `&&`). Run the tests and confirm they fail (red).
- [ ] 1.2 Add a test for "Git unavailable": monkeypatch `git_init` (or the git call) so it fails, and assert `git_identity: "missing"` and that the commit step is present. Run it and confirm it fails (red).
- [ ] 1.3 Change `test_created_result_lists_next_steps` to run with the identity missing, so it still checks the order Codex trust → Claude Code → commit → `samples.tsv` → read-only. Add a check to the identity-set path that the remaining steps are exactly the four user-only steps, in order (scenario "Project created").
- [ ] 1.4 In `scaffold.py`, remove the commit entry from `NEXT_STEPS` and keep its text as a separate constant. Add the identity check after `git_init`. Build `next_steps` with the commit step inserted after the Claude Code entry only when the identity is missing. Add `git_identity` to the `created` result. Verify: `.venv/Scripts/python -m pytest` passes (green).

## 2. Agent commits the scaffold (SKILL.md)

- [ ] 2.1 In `skills/nerv-init/SKILL.md`, add a step between "Write the prose" and "Summarize". If `git_identity` is `set`, list the paths with `git status --porcelain --untracked-files=all` and compare them with `files`. Paths under `.claude/skills/`, `.agents/skills/`, or `skills-lock.json` are expected. List any other path and ask before including it. Then run `git add -A` and `git commit -m "nerv-init scaffold"` as separate commands. If the commit fails, show git's error. Never invent an identity. Make the summary step report the commit. Keep `/hooks` out of SKILL.md. Verify: `tests/test_skill_docs.py` passes, and the step reads correctly for both `set` and `missing`.

## 3. Principles template

- [ ] 3.1 In `skills/nerv-init/templates/base/docs/principles.md`, replace the "Ask, don't guess" bullet with "**Explore before asking.** Answer what the files, git, and environment can tell you; ask only about intent or ambiguity they can't resolve." Verify: `grep -rn "Ask, don't guess" skills/` finds nothing, and the full test suite passes.

## 4. Docs and roadmap

- [ ] 4.1 In the `nerv-init` row of `README.md`'s skills table, say that it makes the first commit when a git identity is already set, and otherwise lists the commands to set one. Verify by reading the row against the spec.
- [ ] 4.2 Set the status of "Discover before asking" in `ROADMAP.md` to `done`, and add a test-run watch item: in the next test run, check that the agent commits after writing the prose, and asks about extra files.

## Workflow follow-up

- Run the AGENTS.md review gate after propose, after apply, and after archive: tests, a commit, a fresh-context reviewer, and fixes.
- `/opsx:verify`, then `/opsx:archive`. Don't push unless asked.
