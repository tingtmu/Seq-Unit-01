# Spec Delta

## MODIFIED Requirements

### Requirement: Detect major changes per folder
The doc-sync check SHALL use git to find which top-level documented folders have major changes since the last commit, counting both uncommitted and staged changes. A change is major if it adds or deletes a file, or if it changes more lines than a configurable threshold. The check SHALL run only on demand, as a report script installed in the project outside its hooks folder; it SHALL NOT run as an agent hook.

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

### Requirement: Graceful outside git
The doc-sync check SHALL report no out-of-sync folders and exit with success when the project is not a git repository or git is unavailable.

#### Scenario: No git
- **WHEN** the report script runs in a directory without a git repository
- **THEN** it prints an empty JSON list and exits with success

### Requirement: Manual sync skill
The doc-sync skill SHALL let a user or agent ask for a sync review on demand. The review runs the project's report script, reports every out-of-sync folder, and proposes concrete README edits, limited to the Current state and Last major change sections.

#### Scenario: On-demand check
- **WHEN** the user invokes the doc-sync skill
- **THEN** the agent lists out-of-sync folders and drafts README updates for approval

#### Scenario: Report script missing
- **WHEN** the user invokes the doc-sync skill in a project without the report script
- **THEN** the agent tells the user that the project was not set up with nerv-init and stops

## REMOVED Requirements

### Requirement: Non-blocking sync reminder at end of turn
**Reason**: Hooks are frozen and standards are enforced at review (2026-10-30 scope review). The Stop hook forced an extra agent turn, and `magi-review` already checks that significantly changed folders have updated READMEs.
**Migration**: Run the `sync-ratio` skill on demand, or rely on `magi-review`. Projects scaffolded before this change keep their own `Stop` hook until the user removes it from `.claude/settings.json` and `.codex/hooks.json`.
