# Proposal

## Why

In the 2026-11-02 test run (`nerv-1102`), the raw-data guard blocked the intake move the user had confirmed. Codex sent the move, a cleanup, and a hash as one multi-line PowerShell script. The guard's shell parser treats newlines as whitespace, so it read the whole script as one `Move-Item` and counted the destination `data/raw/GSE141713` as a source. Codex has no "ask", so this became a hard deny that told the agent not to retry, and intake stopped halfway.

The flaw is the approach, not one bug. Shell parsing is a heuristic: it blocks safe commands (this run) and misses unsafe ones (`python -c "os.remove(...)"`, a Snakemake rule). The user's real concern is raw data being deleted, and agents already respect a clearly stated rule. So the protection becomes a hard rule that names deletion, plus the read-only deliveries nerv-init already sets, plus `magi-review`. On macOS and Linux, read-only stops deletion for any tool. On Windows it stops overwrites and PowerShell or Python deletes, but Git Bash `rm` still deletes read-only files (reproduced on 2026-11-02). There, the hard rule is the only protection, and the docs say so. The user accepted this gap rather than adding another OS mechanism. The guard's friction (a Codex `/hooks` trust step, false denies) is not worth its partial coverage.

## What Changes

- **BREAKING (for generated projects):** nerv-init no longer installs any agent hook. Removed: `.nerv/hooks/raw_guard.py`, `.claude/settings.json`, `.codex/hooks.json`, the raw snapshot and its `.gitignore` line.
- Removed from this repo: `skills/nerv-init/hooks/` (the guard and both adapters) and its tests.
- The next steps drop the "turn on the raw-data guard / `/hooks`" entry. One entry remains: the read-only entry, without its "the guard is best-effort" clause.
- The generated `AGENTS.md` hard rule becomes: "Never delete, move, overwrite, or edit files in `data/raw/`; deliveries there are read-only. Fixes are workflow steps that write to `data/processed/`. When adding a delivery, record its source and checksum in `data/README.md`."
- The `data/README.md` template and README.md state the limit of read-only files on Windows: Git Bash `rm` can still delete them.
- nerv-init's SKILL.md, the `data/README.md` template, the interview mapping, README, and GLOSSARY drop their guard references. Intake still moves deliveries found inside the project. Replacing a file in a read-only delivery is the same flow for every agent: ask, make that delivery writable, then make it read-only again.
- The `raw-data-guard` capability is retired.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `raw-data-guard`: every requirement removed; the capability is retired.
- `project-bootstrap`: no hook installation and no Codex trust step. The hard-rules wording now names deletion. The read-only next step loses its guard clause and becomes the only next step. The read-only-delivery replacement scenario no longer mentions a Codex deny.
- `skill-distribution`: the "Single-source hooks with per-agent adapters" requirement is removed, and "Self-contained skills" no longer mentions installing hooks.
- `doc-sync`: "Detect major changes per folder" places the report script at `.nerv/scripts/` instead of "outside its hooks folder", because generated projects no longer have a hooks folder.

## Impact

- Code: `skills/nerv-init/scripts/scaffold.py` (file plan, `.gitignore`, `NEXT_STEPS`, executable bit for `.nerv/hooks/`, `PYTHON` variable), deleting `skills/nerv-init/hooks/`.
- Templates: `templates/base/AGENTS.md.tmpl`, `templates/base/data/README.md`.
- Skill prose: `skills/nerv-init/SKILL.md`, `skills/nerv-init/references/interview.md`.
- Tests: delete `tests/test_raw_guard.py`; update `tests/test_scaffold.py` and `tests/test_skill_docs.py`.
- Docs: `README.md` (hook section, quick-start Codex step, NERV briefing), `GLOSSARY.md` (retire "Raw-data guard" and "Raw snapshot"; update "Next steps" and "Hard rule").
- Projects created earlier keep their own guard copies, which keep working. No migration is shipped.
- Unchanged: `magi-review` still treats `.claude/settings*.json` and `.codex/hooks.json` as critical agent wiring, since users may add their own hooks there.
