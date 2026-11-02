# Tasks

## 1. Tests first (scaffold output)

- [x] 1.1 In `tests/test_scaffold.py`, replace `test_adapters_point_to_project_hooks`, `test_adapters_have_no_stop_hook`, `test_guard_pre_and_post_matchers_cover_same_tools`, and `test_installed_guard_finds_project_root` with one `test_no_agent_hooks`. It checks that a created project has no `.nerv/hooks/`, `.claude/settings.json`, or `.codex/hooks.json`, that `.gitignore` has no `raw-snapshot` line, and that `.nerv/scripts/sync_ratio.py` exists. Also remove `.claude` and `.codex` from the exact top-level set in `test_other_assay_uses_base_only` (around line 77). This covers the scenarios "No agent hooks", "No end-of-turn hook", and "Intake move is not blocked". Verify both fail against the current scaffold.
- [x] 1.2 Update the next-step tests: `assert_two_user_steps` becomes a one-step check (the read-only entry, with no git command and no `config/samples.tsv`), and `test_created_result_lists_next_steps` drops its guard assertions and the `"best-effort" in read_only` assertion. The read-only entry must still be at most two sentences, name `data/raw/` and "new delivery folder", contain no `chmod` or `attrib`, and must not contain "guard", "hook", or `/hooks`. Verify they fail against the current `NEXT_STEPS`.
- [x] 1.3 Drop `.nerv/hooks/raw_guard.py` from the expected file lists (`test_scaffold.py` around lines 36 and 97, and the tracked-files assertion with its `check-ignore .nerv/raw-snapshot.json` around line 386). Add an assertion that the first hard rule in the generated `AGENTS.md` contains "Never delete, move, overwrite, or edit files in `data/raw/`", "read-only", and the clause about recording source and checksum in `data/README.md` (scenario "Raw data rule names deletion"). Verify the new assertion fails.
- [x] 1.4 Delete `tests/test_raw_guard.py`. In `tests/test_skill_docs.py`, keep `test_nerv_init_relays_every_next_step`, but change the `/hooks` assertion so SKILL.md mentions neither `/hooks` nor "raw-data guard". Verify it fails on the current SKILL.md.

## 2. Remove the guard from the scaffold

- [x] 2.1 In `skills/nerv-init/scripts/scaffold.py`, stop planning `.nerv/hooks/raw_guard.py`, `.claude/settings.json`, and `.codex/hooks.json`. Remove `HOOKS`, the `.nerv/*raw-snapshot*` line in `GITIGNORE`, the `.nerv/hooks/` executable-bit branch, and the `PYTHON` variable. Update the module docstring. Verify with `grep -n "hook\|PYTHON\|snapshot" skills/nerv-init/scripts/scaffold.py`, which should only find the "not a hook" wording, if any.
- [x] 2.2 Replace `NEXT_STEPS` with the single read-only entry from design.md ("Each delivery in `data/raw/` is made read-only once its provenance is recorded; put new data in a new delivery folder (`data/README.md` has the commands and their limits)."). Verify the group 1 next-step tests pass, and that the entry contains neither "no tool" nor "cannot be deleted".
- [x] 2.3 Delete `skills/nerv-init/hooks/` (the `raw_guard.py` script, `adapters/`, `__pycache__`). Verify `test_skill_folder_is_self_contained` still passes and the folder is gone.
- [x] 2.4 Update `skills/nerv-init/templates/base/AGENTS.md.tmpl` hard rule 1 to the approved wording. Then run `.venv/Scripts/python -m pytest tests/test_scaffold.py tests/test_templates.py` and verify group 1's tests pass, including `test_agents_md_size`.

## 3. Templates and skill prose

- [x] 3.1 In `skills/nerv-init/templates/base/data/README.md`, drop the hook sentence from the first Conventions bullet and the "In Codex, the raw-data guard denies…" line. Add one line under the read-only commands: on Windows, read-only files still block overwrites, but Git Bash `rm` can delete them, so the hard rule is the protection there (scenario "Windows limit stated"). Add a test in `tests/test_templates.py` (or `test_scaffold.py`) asserting that the generated `data/README.md` mentions Git Bash `rm` deleting read-only files. Write it before the edit and verify it fails first. Verify with `grep -n -i "hook\|guard" skills/nerv-init/templates/` (no hits).
- [x] 3.2 In `skills/nerv-init/SKILL.md`: step 5 no longer lists hooks or adapters; the "Replacing a file later" bullet drops its Codex sentence; step 9 drops "the hooks installed" and the sentence about the raw-data guard staying off in Codex; and the "## Hooks installed" section is removed. Verify with `grep -n -i "hook\|guard" skills/nerv-init/SKILL.md` (no hits) and `tests/test_skill_docs.py` passing.
- [x] 3.3 In `skills/nerv-init/references/interview.md`, remove "hooks in `.nerv/hooks/`…" and the adapter files from the "any" row of the mapping table. Verify that grep finds no "hook" left in that file.

## 4. User-facing docs and glossary

- [x] 4.1 In `README.md`: change the intro to "A hard rule and read-only deliveries protect raw data" (or similar) and drop "Hook logic is Python 3 standard library only". Change the NERV briefing so the AT Field is the read-only deliveries. Remove the quick-start "Codex only: run `/hooks`" bullet, the paragraph about nerv-init installing the raw-data guard, and the `hooks/{raw_guard.py,adapters/}` entry in the repository layout. Change the Requirements line to the scaffold only. Replace "Hooks and their limits" with a short "Raw data protection" section covering the hard rule, read-only deliveries, and the Windows attribute limit, and fix the table-of-contents link. Verify with `grep -n -i "hook\|guard" README.md`: only the sync-ratio "not a hook" wording, if any, should remain.
- [x] 4.2 In `GLOSSARY.md`: remove "Raw-data guard" and "Raw snapshot"; move the AT Field codename to "Delivery"; replace the Codex-trust example in "Next steps" and update the "Hard rule" example to deletion. Verify with `grep -n -i "guard\|snapshot\|hooks" GLOSSARY.md` (no hits except _Avoid_ lists).

## 5. Specs and local notes

- [x] 5.1 Edit the Purpose of `openspec/specs/project-bootstrap/spec.md` directly: replace "the installed raw-data guard" with "read-only raw deliveries". Verify with `openspec validate --specs --strict`.
- [x] 5.2 Update the local, gitignored notes directly. In `AGENTS.md`: remove the "Hooks are frozen" scope bullet and hard rules 2 to 4, renumber, and drop the hook mentions in "Verify external schemas", "Review with fresh eyes", "Fail fast at boundaries", and the "Where to look" README row. In `SCOPE.md`: rewrite the "Hooks are frozen" constraint as "no agent hooks" and prune the "Not planned" rows that only applied to the guard. In `ROADMAP.md`: add this item as shipped, with a link to the 2026-11-02 test run, and mark "Hook interpreter on macOS/Linux" as moot. Verify each file with a grep for "hook".

## 6. Integration check

- [x] 6.1 Run the full suite `.venv/Scripts/python -m pytest` and verify that everything passes. Then run `grep -rn -i "raw_guard\|raw-data guard\|raw snapshot" --include=*.py --include=*.md --include=*.json skills tests README.md GLOSSARY.md` and verify there are no hits.
- [x] 6.2 Dry-run the scaffold with sample answers into a scratch folder (`scaffold.py --answers - --target <scratch> --dry-run`) and verify the planned `files` list has no `.nerv/hooks/`, `.claude/`, or `.codex/` path.

## Workflow follow-up

- Review gate after apply: run the tests, commit, then have a fresh-context reviewer check the commit range against `AGENTS.md` and this change's specs.
- `/opsx:verify`, then `/opsx:archive`. `retire_capabilities: true` makes archive delete the `raw-data-guard` main spec; afterwards, run `openspec validate --specs --strict`.
- Next test run: confirm intake moves a delivery without any hook involvement in both Claude Code and Codex, and record the result in that run's notes.
