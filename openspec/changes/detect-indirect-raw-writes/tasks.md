# Tasks

## 1. Snapshot diff in the raw-data guard

- [x] 1.1 Write failing tests in `tests/test_raw_guard.py` for each spec scenario: a new file from a Bash PostToolUse gives a provenance reminder; a second unrelated call gives no repeat; a file modified or removed by a "script" (changed on disk between calls) is reported; a read-only command gives no output; a corrupt `.nerv/raw-snapshot.json` fails open with stderr and no message; `.gitkeep` is ignored; Codex `Bash` PostToolUse also reminds. Update the existing PostToolUse tests so the file really exists on disk. Verify that the new tests fail for the expected reason.
- [x] 1.2 In `skills/nerv-init/hooks/raw_guard.py`, replace `new_raw_files` with a stat walk of `data/raw/` (follow dir symlinks, skip `.gitkeep`), a diff against `.nerv/raw-snapshot.json` (missing means empty), an atomic save, and one `additionalContext` message for new and changed files. Update the module docstring. Verify with `.venv/Scripts/python -m pytest tests/test_raw_guard.py`.
- [x] 1.3 Add the term for the snapshot to `GLOSSARY.md` (domain-modeling skill) and use it in the code and the message text. Verify that the term is used consistently across `raw_guard.py`, README, and the spec.

## 2. Wiring and scaffold

- [x] 2.1 Re-verify the Claude Code PostToolUse schema (matcher, `additionalContext`) and the Codex PostToolUse schema for `Bash` against current docs/source (Context7 or `openai/codex`). Note the findings for README. Verify that the sources are cited with today's date.
- [x] 2.2 Widen the PostToolUse matchers: `claude-settings.json` to `Write|Edit|MultiEdit|NotebookEdit|Bash|PowerShell`, `codex-hooks.json` to `^(apply_patch|Bash)$`. Add a test in `tests/test_scaffold.py` that the Pre and Post matchers cover the same tools. Verify it passes.
- [x] 2.3 Add `.nerv/raw-snapshot.json` to `GITIGNORE` in `scaffold.py`. Extend a scaffold test so a generated project ignores it (`git check-ignore`). Verify it passes.

## 3. Docs

- [x] 3.1 Update `README.md`: the hook table's provenance row (all write tools, including shell), a new note that changes to existing raw files are reported after the fact, limitation line 68 (indirect writes now reported, not prevented, mtime-preserving writes missed), removal of the "Codex shell-written files get no provenance reminder" limitation, and the schema verification date. Verify with `tests/test_skill_docs.py`.
- [x] 3.2 Update the hook summary in `skills/nerv-init/SKILL.md` and the `data/README.md` template's convention line if its wording no longer matches. Verify that the full suite passes: `.venv/Scripts/python -m pytest`.
- [x] 3.3 In `ROADMAP.md`, mark "Guard cannot see indirect writes" and "Codex shell-written files get no provenance reminder" as done (or rewrite the first one to say it's detected, not prevented). Verify that both rows show the new status.

## 4. Review

- [x] 4.1 Get a fresh-context review of the `raw_guard.py` and adapter changes (AGENTS.md: hooks need review). Verify each finding before acting on it. The task is done when every confirmed finding is fixed and the full suite passes.

## 5. House rule

- [x] 5.1 (Done early, 2026-10-29.) Add a one-line Development habit to the local `AGENTS.md`: don't over-engineer; follow YAGNI and KISS. Verify that the line is present (AGENTS.md is gitignored, so it isn't committed).

## Workflow follow-up

- Run `/opsx:verify`, then `/opsx:archive` to sync the `raw-data-guard` delta into the main spec.
