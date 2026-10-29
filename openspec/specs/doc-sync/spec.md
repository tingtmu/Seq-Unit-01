# doc-sync Specification

## Purpose

Keeps per-folder README files in sync with the code and data they describe by detecting major changes without a matching README update and reminding the agent to apply the Boy Scout Rule.

## Requirements

### Requirement: Detect major changes per folder
The doc-sync check SHALL use git to find which top-level documented folders have major changes since the last commit, counting both uncommitted and staged changes. A change is major if it adds or deletes a file, or if it changes more lines than a configurable threshold.

#### Scenario: New script added
- **WHEN** a new file is added under `scripts/` and `scripts/README.md` is unchanged
- **THEN** the check reports `scripts/` as out of sync

#### Scenario: Minor edit
- **WHEN** a few lines change in one existing file, below the threshold
- **THEN** the check reports nothing for that folder

#### Scenario: README already updated
- **WHEN** a folder has major changes and its README was also modified
- **THEN** the check does not report that folder

### Requirement: Non-blocking sync reminder at end of turn
When an agent finishes a turn, the doc-sync hook SHALL show the agent a short reminder listing each out-of-sync folder and its README path. It SHALL NOT keep the agent from finishing: it MAY ask for at most one extra turn per unchanged out-of-sync state, and the agent decides whether to update the READMEs.

#### Scenario: Out-of-sync folder at stop
- **WHEN** the agent stops and `workflow/` is out of sync
- **THEN** the agent receives one reminder naming `workflow/README.md`, and its next attempt to stop is allowed whether or not it updated the README

#### Scenario: Repeated stop without changes
- **WHEN** the agent stops again with the same out-of-sync state
- **THEN** no second reminder is shown

### Requirement: Graceful outside git
The doc-sync hook SHALL exit silently with success when the project is not a git repository or git is unavailable.

#### Scenario: No git
- **WHEN** the hook runs in a directory without a git repository
- **THEN** it produces no output and does not interrupt the agent

### Requirement: Manual sync skill
The doc-sync skill SHALL let a user or agent ask for a sync review on demand. The review reports every out-of-sync folder and proposes concrete README edits, limited to the Current state and Last major change sections.

#### Scenario: On-demand check
- **WHEN** the user invokes the doc-sync skill
- **THEN** the agent lists out-of-sync folders and drafts README updates for approval
