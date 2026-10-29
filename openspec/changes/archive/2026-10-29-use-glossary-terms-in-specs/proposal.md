# Proposal

## Why

`GLOSSARY.md` is the vocabulary that code, docs, and specs must use. Three spec passages still use terms it lists under _Avoid_: "nudge" in two requirement names and in the `doc-sync` Purpose (the glossary term is **Sync reminder**), and "guardrail" in the `project-bootstrap` Purpose (the glossary term is **Hard rule**). The shipped docs and hook code already say "reminder", so the specs are the odd ones out. Fixing this now means later deltas against these requirements don't copy the old wording.

## What Changes

- Rename `doc-sync` requirement "Non-blocking nudge at end of turn" to "Non-blocking sync reminder at end of turn".
- Rename `raw-data-guard` requirement "Allow new raw files with provenance nudge" to "Allow new raw files with provenance reminder".
- Reword the `doc-sync` Purpose: "nudging the agent" becomes "reminding the agent".
- Reword the `project-bootstrap` Purpose: "installed guardrail hooks" becomes "installed hooks (the raw-data guard and the sync reminder)".

Requirement bodies and scenarios do not change, and no behavior changes.

Out of scope:
- Other context-dependent words the glossary lists under _Avoid_ ("agent", "reviewer", "prompt", "block", "scaffold", "convention") where the specs use them in a different sense than the avoided one, consistent with the glossary's own definitions.
- An automated test for _Avoid_ terms. These words are context-dependent, so a word-match test would mostly flag false positives.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `doc-sync`: requirement "Non-blocking nudge at end of turn" renamed to "Non-blocking sync reminder at end of turn" (name only).
- `raw-data-guard`: requirement "Allow new raw files with provenance nudge" renamed to "Allow new raw files with provenance reminder" (name only).

`project-bootstrap` changes only in its Purpose, which is edited directly in the main spec rather than through a delta.

## Impact

- `openspec/specs/doc-sync/spec.md`, `openspec/specs/raw-data-guard/spec.md`: requirement names (through archive) and the `doc-sync` Purpose (direct edit).
- `openspec/specs/project-bootstrap/spec.md`: Purpose (direct edit).
- `ROADMAP.md` (local): mark the glossary item done.
- No change to code, hooks, tests, templates, or `README.md`. No test reads spec requirement names.
