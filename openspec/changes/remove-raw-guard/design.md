# Design

## Context

See proposal.md (Why). Today, raw data is protected in three layers:

1. A **hard rule** in the generated `AGENTS.md`. It says only "never modify raw data in place", so deletion is not named.
2. **Read-only deliveries.** nerv-init runs `chmod -R a-w` or `attrib +R /S` on each delivery after recording its provenance (`project-bootstrap`, "Each delivery made read-only after intake").
3. The **raw-data guard** (`skills/nerv-init/hooks/raw_guard.py`, about 300 lines, plus two adapters). It has an exact-path check for Write/Edit/apply_patch, a heuristic shell parser for Bash/PowerShell, and a PostToolUse snapshot diff.

`scaffold.py` copies the guard into `.nerv/hooks/`, writes `.claude/settings.json` and `.codex/hooks.json` (both only wire the guard), git-ignores `.nerv/*raw-snapshot*`, marks `.nerv/hooks/` files executable, and fills a `{{PYTHON}}` variable used only by the Claude adapter. `NEXT_STEPS` has two entries: the `/hooks` trust step and the read-only entry. The read-only entry justifies itself with "because the raw-data guard is best-effort".

## Goals / Non-Goals

**Goals:**
- Generated projects carry no agent hooks. Raw data is protected by layers 1 and 2, and `magi-review` checks it at review time.
- Remove every place where the guard is code, configuration, prose, or a term. No leftover that promises a guard.

**Non-Goals:**
- Migrating projects created earlier. Their guard copies keep working, and the removed-requirement text in the `raw-data-guard` delta says how to delete them by hand.
- Changing `magi-review`. It still lists `.claude/settings*.json` and `.codex/hooks.json` as CRITICAL agent wiring. Those paths still matter when users add their own hooks, and the `.nerv/hooks/` entry is harmless for older projects.
- Changing data intake. Moving deliveries found inside the project stays the default.

## Decisions

**Remove the whole guard, not only its shell parser.** The user chose this after considering alternatives:
- *Fix the newline bug only.* This leaves a heuristic that will misfire again on other shell syntax, and in Codex any misfire is a hard deny.
- *Keep only the PostToolUse snapshot alarm.* It cannot undo a deletion, which is the user's main concern. Keeping it means keeping the hook script, both adapters, the git-ignored snapshot, and the Codex `/hooks` trust step.
- *Keep the exact-path Write/Edit check.* Those tools cannot delete files, so the check doesn't address deletion, and it still needs the whole hook installation.

**Write no `.claude/settings.json` or `.codex/hooks.json`.** Both files only carried the guard. Writing empty ones would add files with no purpose and would conflict with settings the user creates later.

**Drop the `{{PYTHON}}` variable and the `.nerv/hooks/` executable bit.** The Claude adapter was their only user. `.nerv/scripts/sync_ratio.py` stays. It is run as `python .nerv/scripts/sync_ratio.py` and never needed the executable bit.

**One next step.** `NEXT_STEPS` keeps only the read-only entry, rewritten to drop the guard clause. Proposed text: "Each delivery in `data/raw/` is made read-only once its provenance is recorded, so no tool can delete or overwrite it; put new data in a new delivery folder (`data/README.md` has the commands)." The text stays in `NEXT_STEPS`, the single source the glossary names.

**Hard-rule wording** (approved by the user): "Never delete, overwrite, or edit files in `data/raw/`; deliveries there are read-only. Fixes are workflow steps that write to `data/processed/`. When adding a delivery, record its source and checksum in `data/README.md`." It names deletion first because that is the failure the user fears. The `data/README.md` convention "Never edit, overwrite, move, or delete files in `raw/`" stays, minus its hook sentence. Moving raw files out of a delivery still breaks provenance paths. Moving originals *into* `data/raw/` is intake, not a change to raw files.

**Glossary.** Retire "Raw-data guard" and "Raw snapshot". The AT Field codename moves to "Delivery": a read-only delivery is now the barrier around raw data. "Next steps" stops using Codex trust as its example. "Hard rule" keeps its definition, with its example updated to "never deleting raw data".

**Spec housekeeping.** The `project-bootstrap` Purpose names "the installed raw-data guard". Deltas cannot change a Purpose, so the task list edits the main spec's Purpose directly, as OpenSpec instructs. After archive removes every `raw-data-guard` requirement, the empty capability folder `openspec/specs/raw-data-guard/` is deleted.

**Local repo files.** `AGENTS.md` (hard rules 2 to 4 and "Hooks are frozen"), `SCOPE.md`, and `ROADMAP.md` are gitignored notes, not OpenSpec artifacts, so they are edited directly during apply.

## Risks / Trade-offs

- [An agent ignores the rule and forces a delete, e.g. `Remove-Item -Force` or `chmod u+w` then `rm`] → Forcing is a deliberate, visible act against an explicit hard rule. The guard never covered every path either (`python -c`, workflow rules). `magi-review` flags changes that weaken protection.
- [The Windows read-only attribute is weaker than POSIX permissions: forced removals succeed, and Git Bash `rm` may clear the attribute] → Accepted. On macOS and Linux, `chmod -R a-w` removes write permission from the delivery folder, so its files cannot be deleted at all. The test run that motivated this change was on Windows, and its failure was a false block, not a deletion.
- [No reminder to record provenance when raw files are added later, outside intake] → The hard rule and the `data/README.md` "Adding a delivery" steps both say to record source and checksum.
- [Between placing a delivery and making it read-only, it is writable] → The gap is inside one nerv-init intake step, done by the same agent following the same instructions.

## Migration Plan

Ship as one commit series through the review gate, update README in the same change, then archive. Rollback is `git revert` of the apply commit. Existing generated projects are not touched.
