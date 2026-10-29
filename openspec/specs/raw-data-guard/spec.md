# raw-data-guard Specification

## Purpose

Protects immutable raw data in `data/raw/` from silent modification or deletion by agents, while still allowing new raw data to be added with provenance recorded.

## Requirements

### Requirement: Allow new raw files with provenance nudge
The guard SHALL allow an agent to create a new file under `data/raw/`. After allowing it, the guard SHALL remind the agent to record the file's source and checksum in `data/README.md`.

#### Scenario: Download new batch
- **WHEN** an agent writes a new file `data/raw/batch2/S1_R1.fastq.gz`
- **THEN** the write proceeds and the agent is reminded to record provenance

### Requirement: Require approval to modify or delete existing raw files
The guard SHALL intercept agent actions that modify, overwrite, move, or delete an existing file under `data/raw/`. Where the agent supports asking the user, the guard SHALL request user approval. Otherwise it SHALL deny the action and tell the user how to run it themselves.

#### Scenario: Agent edits an existing raw file in Claude Code
- **WHEN** an agent tries to edit `data/raw/S1_R1.fastq.gz`
- **THEN** the user is prompted to approve or reject the action

#### Scenario: Agent without approval support
- **WHEN** an agent that cannot prompt the user attempts `rm data/raw/S1_R1.fastq.gz`
- **THEN** the action is denied with a message explaining the hard rule and how the user can perform it manually

### Requirement: Best-effort shell detection
The guard SHALL inspect shell commands for common destructive operations that target `data/raw/` (remove, move, in-place edit, output redirection). It SHALL be documented as best-effort, not as a security boundary.

#### Scenario: Redirect overwrite
- **WHEN** an agent runs a command redirecting output with `>` into an existing `data/raw/` file
- **THEN** the guard treats it as a modification requiring approval

#### Scenario: Unrelated command
- **WHEN** an agent runs a command that reads from `data/raw/` without writing to it
- **THEN** the guard allows it without prompting

### Requirement: Fail open on guard errors
If the guard itself errors (e.g. malformed hook input), it SHALL allow the action and write a diagnostic to stderr. It SHALL NOT break the agent session.

#### Scenario: Malformed input
- **WHEN** the hook receives input it cannot parse
- **THEN** the action proceeds and an error message is written to stderr
