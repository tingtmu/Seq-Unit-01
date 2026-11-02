# Spec Delta

## REMOVED Requirements

### Requirement: Allow new raw files with provenance reminder
**Reason**: The raw-data guard is retired. Recording provenance is part of data intake (`project-bootstrap`, "Provenance recorded at intake") and of the generated hard rule and `data/README.md` steps, so an agent adding a delivery is told to record it without a hook.
**Migration**: None needed. Projects created earlier keep their own copy of the guard, which keeps working; delete `.nerv/hooks/`, `.codex/hooks.json`, and the nerv entries in `.claude/settings.json` to remove it.

### Requirement: Require approval to modify or delete existing raw files
**Reason**: The approval was triggered by shell parsing, which blocked a confirmed intake move in Codex (no "ask", so a hard deny) and still missed deletions through scripts. The generated hard rule forbids deleting, moving, overwriting, or editing raw files. Read-only deliveries enforce it at the operating-system level, except on Windows, where Git Bash `rm` can still delete read-only files; that gap is accepted and documented.
**Migration**: Raw data is protected by the hard rule in `AGENTS.md`, read-only deliveries, and `magi-review`.

### Requirement: Best-effort shell detection
**Reason**: Heuristic shell parsing gave false positives (a multi-line script read as one command) and misses (`python -c`, workflow rules). It is the source of the friction this change removes.
**Migration**: None.

### Requirement: Report changes to existing raw files after the fact
**Reason**: An after-the-fact report cannot undo a deletion, and keeping it would keep the hook files, both adapters, and the Codex trust step. Read-only deliveries prevent the change instead.
**Migration**: None.

### Requirement: Fail open on guard errors
**Reason**: No guard remains to fail.
**Migration**: None.
