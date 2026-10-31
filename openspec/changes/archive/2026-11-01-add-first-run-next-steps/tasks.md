# Tasks

## 1. LF line endings

- [x] 1.1 In `tests/test_scaffold.py`, add a test that a created project has `.gitattributes` containing `* text=auto eol=lf`, and a test that `git -c core.autocrlf=true add -A` in the created project prints no line-ending warning and that `git ls-files --eol` then shows tracked text files with `attr/text=auto eol=lf` (skip if git is unavailable); add `.gitattributes` to the exact top-level set in `test_other_assay_uses_base_only`; verify the new tests fail before the code change
- [x] 1.2 In `scaffold.py`, add a `GITATTRIBUTES` constant and write it in `plan()`; update the module docstring; verify the tests from 1.1 and the full suite pass
- [x] 1.3 List `.gitattributes` in `SKILL.md` step 4, the `any` row of `references/interview.md`, and the `nerv-init` row of `README.md`; verify by reading each line

## 2. Next steps

- [x] 2.1 Update `test_created_result_lists_next_steps`: find steps by content instead of index (except the Codex step at `steps[0]`); assert a Claude Code step naming `/hooks` and restart; assert a commit step with `git config user.email`, `git config --global user.name`, `git config --global user.email`, `git add -A`, `git commit`, and no `&&`; assert the read-only step labels `chmod` with Git Bash and `attrib` with cmd or PowerShell; verify the test fails before the code change
- [x] 2.2 Update `NEXT_STEPS` in `scaffold.py` in the order Codex trust, Claude Code check, first commit, fill config, read-only; verify the full suite passes
- [x] 2.3 Run a scaffold into a scratch folder on Windows, follow the commit step in Git Bash and in PowerShell, and confirm the commands run as written; record the result in the change's commit message

## Workflow follow-up

- Review gate after apply (AGENTS.md), then `/opsx:verify` and `/opsx:archive` with its review gate.
- Mark "First-run next steps" done in `ROADMAP.md`, and add next-run checklist items to the test-run notes: the five next steps relayed in order, a quiet first `git add` on Windows, and the commit succeeding on a machine with no git identity.
