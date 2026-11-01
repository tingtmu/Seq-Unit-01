# Tasks

## 1. Two next-step entries (scaffold.py)

- [x] 1.1 In `tests/test_scaffold.py`, rewrite the next-steps tests:
  - `test_created_result_lists_next_steps`: exactly two entries. The first names `/hooks`, "project root" for Codex, "raw-data guard", "off in Codex until", "again after any change to `.codex/hooks.json`", and a Claude Code restart, with no sync mention. The second is the read-only entry.
  - `test_identity_set_leaves_commit_to_agent` and `test_identity_missing_keeps_commit_step`, the latter renamed to `test_identity_missing_has_no_git_step`: the same two entries, `git_identity` reported, and no entry contains `git config`, `git commit`, `git add`, or `config/samples.tsv`.
  - `test_git_unavailable_reports_identity_missing`: `git: "unavailable"`, `git_identity: "missing"`, and no git command in any entry.
  - Run them and confirm they fail (red).
- [x] 1.2 In `scaffold.py`:
  - merge the Codex and Claude Code entries into the hook entry from design decision 3;
  - delete the samples entry, `COMMIT_STEP`, `COMMIT_STEP_AFTER`, and the conditional in `next_steps()`, leaving it to return the two entries;
  - keep `git_identity` in the result.
  - Verify: `.venv/Scripts/python -m pytest` passes (green).

## 2. Agent sets a project-only identity (SKILL.md)

- [x] 2.1 In `skills/nerv-init/SKILL.md`:
  - **Explore:** check `git config user.name` and `git config user.email` in the target.
  - **Plan:** name the identity the commit will use, or, if it is missing, ask for a name and email in the same message.
  - **Commit:** if `git_identity` is `missing` and the user gave a name and email, run `git config user.name "<name>"` and `git config user.email "<email>"` in the project as separate commands, never with `--global`, and repeat back what was set. Then commit as before. The expected paths add the files data intake filled.
  - Replace "Never set or invent an identity yourself" with "Never invent an identity or set it globally".
  - **Summarize:** if nothing was committed, say why in one sentence.
  - Keep `/hooks` out of SKILL.md.
  - Verify: `tests/test_skill_docs.py` passes, and the step reads correctly for identity set, identity given, no identity given, and git unavailable.

## 3. Pins and forward pointer (SKILL.md)

- [x] 3.1 In the `SKILL.md` data-intake step, fill the reference fields in `config/config.yaml` that the data's own files state, leave the others empty, and never guess a build. In Summarize, name in one line an empty field that blocks the next run; for sensitive data, say in one line that the user fills `config/samples.tsv` because the agent did not read the metadata; and end with an invitation to say what to compare; in an empty folder, the data request comes first. Name no other skill. Verify: `tests/test_skill_docs.py` passes (self-contained), and the summary order reads correctly for the yeast case and the empty-folder case.

## 4. Docs and roadmap

- [x] 4.1 In the `nerv-init` row of `README.md`, say that it asks for a git name and email if none is set, saves them for the project only, and makes the first commit. Remove "its next steps give the commands to set one". Update any README text that lists the next steps. Verify by reading against the spec.
- [x] 4.2 In `GLOSSARY.md`, check the **Next steps** entry (its example is "trusting the Codex hooks") and update it only if it no longer matches. Verify by reading.
- [x] 4.3 In `ROADMAP.md`, set "Shorter next steps, identity set by the agent" to `done`. Extend the test-run watch item: the agent asks for an identity only when it is missing, sets it project-only, commits, and ends the summary with the invitation to compare.

## 5. Integration check

- [x] 5.1 Run the full suite (`.venv/Scripts/python -m pytest`), then `openspec validate shorten-next-steps --strict`. Both pass.

## Workflow follow-up

- Apply only after `add-data-intake` is applied, because both edit `NEXT_STEPS` and `test_scaffold.py`.
- Run the AGENTS.md review gate after propose, after apply, and after archive.
- `/opsx:verify`, then `/opsx:archive`. Don't push unless asked.
