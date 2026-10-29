# Spec Delta

## MODIFIED Requirements

### Requirement: Allow new raw files with provenance nudge
The guard SHALL allow an agent to create a new file under `data/raw/`. After any agent file-edit or shell tool call that leaves a new file under `data/raw/`, the guard SHALL remind the agent to record the file's source and checksum in `data/README.md`, whatever tool or command created it.

#### Scenario: Download new batch
- **WHEN** an agent writes a new file `data/raw/batch2/S1_R1.fastq.gz`
- **THEN** the write proceeds and the agent is reminded to record provenance

#### Scenario: New raw file written by a shell command
- **WHEN** an agent runs a shell command, such as a download script, that creates `data/raw/batch3/S5_R1.fastq.gz`
- **THEN** after the command the agent is reminded to record provenance for that file

#### Scenario: Reminder given once per file
- **WHEN** a new raw file has already triggered a reminder and a later tool call does not touch it
- **THEN** the later tool call produces no reminder for that file

## ADDED Requirements

### Requirement: Report changes to existing raw files after the fact
After any agent file-edit or shell tool call, the guard SHALL report each existing file under `data/raw/` that was modified or removed since the last check, and tell the agent to stop and inform the user if the user did not approve the change. The report SHALL NOT block or undo the action. Detection SHALL compare file size and modification time only, and SHALL be documented as best-effort.

#### Scenario: Script modifies a raw file
- **WHEN** an agent runs `python scripts/fix_headers.py` and the script rewrites `data/raw/S1_R1.fastq.gz`
- **THEN** after the command the agent receives a message naming `data/raw/S1_R1.fastq.gz` as modified and telling it to stop and inform the user if this was not approved

#### Scenario: Raw file removed indirectly
- **WHEN** a shell command removes `data/raw/S2_R1.fastq.gz` without naming it on the command line
- **THEN** after the command the agent receives a message naming that file as removed

#### Scenario: Command that does not touch raw data
- **WHEN** an agent runs a command that only reads `data/raw/` or writes elsewhere
- **THEN** the guard produces no message

#### Scenario: Raw snapshot cannot be read or saved
- **WHEN** the raw snapshot is unreadable or cannot be written
- **THEN** the action proceeds, a diagnostic is written to stderr, and the session is not broken
