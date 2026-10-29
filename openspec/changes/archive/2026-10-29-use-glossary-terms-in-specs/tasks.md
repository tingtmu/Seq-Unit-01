# Tasks

## 1. Purpose wording (direct edits to main specs)

- [x] 1.1 In `openspec/specs/doc-sync/spec.md`, change "nudging the agent" in the Purpose to "reminding the agent"; verify `grep -i nudg openspec/specs/doc-sync/spec.md` matches only the requirement name that the archive renames
- [x] 1.2 In `openspec/specs/project-bootstrap/spec.md`, change "installed guardrail hooks" in the Purpose to "installed hooks (the raw-data guard and the sync reminder)"; verify `grep -i guardrail openspec/specs/` returns nothing

## 2. Requirement renames (spec deltas)

- [x] 2.1 Confirm the RENAMED deltas in `specs/doc-sync/spec.md` and `specs/raw-data-guard/spec.md` match the current main-spec headers exactly; verify `openspec validate use-glossary-terms-in-specs --strict` passes
- [x] 2.2 Run the full test suite with `.venv/Scripts/python -m pytest` and verify every test passes (no test reads spec requirement names, so none should change)

## 3. Roadmap

- [x] 3.1 Mark "Make the OpenSpec specs use the glossary terms" as done in `ROADMAP.md`; verify the item no longer reads `candidate`

## Workflow follow-up

- Archive the change with `/opsx:archive`, which applies the two requirement renames to the main specs.
- After archiving, verify that `grep -ri nudg openspec/specs/` returns nothing.
