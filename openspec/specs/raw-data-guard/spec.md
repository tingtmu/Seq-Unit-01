# raw-data-guard Specification

## Purpose

Protects immutable raw data in `data/raw/` from silent modification or deletion by agents, while still allowing new raw data to be added with provenance recorded.

## Requirements

### Requirement: Allow new raw files with provenance reminder
The guard SHALL allow an agent to create a new file under `data/raw/`. After any agent file-edit or shell tool call that leaves a new file under `data/raw/`, the guard SHALL remind the agent to record the file's source and checksum in `data/README.md`, whatever tool or command created it. The reminder SHALL include a command that computes the SHA-256 checksum of the new files and works on the user's operating system.

#### Scenario: Download new batch
- **WHEN** an agent writes a new file `data/raw/batch2/S1_R1.fastq.gz`
- **THEN** the write proceeds and the agent is reminded to record provenance

#### Scenario: New raw file written by a shell command
- **WHEN** an agent runs a shell command, such as a download script, that creates `data/raw/batch3/S5_R1.fastq.gz`
- **THEN** after the command the agent is reminded to record provenance for that file

#### Scenario: Reminder given once per file
- **WHEN** a new raw file has already triggered a reminder and a later tool call does not touch it
- **THEN** the later tool call produces no reminder for that file

#### Scenario: Reminder includes a checksum command
- **WHEN** new raw files `data/raw/batch2/S1_R1.fastq.gz` and `data/raw/batch2/S1_R2.fastq.gz` trigger a reminder
- **THEN** the reminder contains one SHA-256 command naming both files: `sha256sum` on Linux, `shasum -a 256` on macOS, and `Get-FileHash -Algorithm SHA256` on Windows

### Requirement: Require approval to modify or delete existing raw files
The guard SHALL intercept agent actions that modify, overwrite, move, or delete an existing file under `data/raw/`. Where the agent supports asking the user, the guard SHALL request user approval, and the request SHALL state that approving cannot be undone because raw data is not in version control. Otherwise it SHALL deny the action and tell the user how to run it themselves.

#### Scenario: Agent edits an existing raw file in Claude Code
- **WHEN** an agent tries to edit `data/raw/S1_R1.fastq.gz`
- **THEN** the user is prompted to approve or reject the action

#### Scenario: Approval request warns that it cannot be undone
- **WHEN** the user is prompted to approve a change to `data/raw/S1_R1.fastq.gz`
- **THEN** the prompt says that the change cannot be undone because raw data is not in git

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

### Requirement: Report changes to existing raw files after the fact
After any agent file-edit or shell tool call, the guard SHALL report each existing file under `data/raw/` that was modified or removed since the last check, and tell the agent to stop and inform the user if the user did not approve the change. The report SHALL also state that the provenance records of those files in `data/README.md` no longer match, and that recovering a file means fetching it again from its source because raw data is not in version control. The report SHALL NOT block or undo the action. Detection SHALL compare file size and modification time only, and SHALL be documented as best-effort.

#### Scenario: Script modifies a raw file
- **WHEN** an agent runs `python scripts/fix_headers.py` and the script rewrites `data/raw/S1_R1.fastq.gz`
- **THEN** after the command the agent receives a message naming `data/raw/S1_R1.fastq.gz` as modified and telling it to stop and inform the user if this was not approved

#### Scenario: Report names the provenance mismatch and recovery
- **WHEN** an approved edit or a script modifies `data/raw/S1_R1.fastq.gz`
- **THEN** the message says that its provenance record in `data/README.md` no longer matches, and that recovering the original means fetching it again from its source

#### Scenario: Raw file removed indirectly
- **WHEN** a shell command removes `data/raw/S2_R1.fastq.gz` without naming it on the command line
- **THEN** after the command the agent receives a message naming that file as removed

#### Scenario: Command that does not touch raw data
- **WHEN** an agent runs a command that only reads `data/raw/` or writes elsewhere
- **THEN** the guard produces no message

#### Scenario: Raw snapshot cannot be read or saved
- **WHEN** the raw snapshot is unreadable or cannot be written
- **THEN** the action proceeds, a diagnostic is written to stderr, and the session is not broken

### Requirement: Fail open on guard errors
If the guard itself errors (e.g. malformed hook input), it SHALL allow the action and write a diagnostic to stderr. It SHALL NOT break the agent session.

#### Scenario: Malformed input
- **WHEN** the hook receives input it cannot parse
- **THEN** the action proceeds and an error message is written to stderr
