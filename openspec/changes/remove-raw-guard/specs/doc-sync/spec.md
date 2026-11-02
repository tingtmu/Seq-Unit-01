# Spec Delta

## MODIFIED Requirements

### Requirement: Detect major changes per folder
The doc-sync check SHALL use git to find which top-level documented folders have major changes since the last commit, counting both uncommitted and staged changes. A change is major if it adds or deletes a file, or if it changes more lines than a configurable threshold. The check SHALL run only on demand, as a report script installed in the project at `.nerv/scripts/`; it SHALL NOT run as an agent hook.

#### Scenario: New script added
- **WHEN** a new file is added under `scripts/` and `scripts/README.md` is unchanged
- **THEN** the check reports `scripts/` as out of sync

#### Scenario: Minor edit
- **WHEN** a few lines change in one existing file, below the threshold
- **THEN** the check reports nothing for that folder

#### Scenario: README already updated
- **WHEN** a folder has major changes and its README was also modified
- **THEN** the check does not report that folder

#### Scenario: Report output
- **WHEN** the report script runs in a project where `scripts/` is out of sync
- **THEN** it prints a JSON list with one entry per out-of-sync folder, giving the folder, its README path, and the changed files, and it writes no state file
