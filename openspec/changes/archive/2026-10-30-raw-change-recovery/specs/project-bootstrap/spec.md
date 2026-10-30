# Spec Delta

## ADDED Requirements

### Requirement: Read-only raw data recommended after scaffolding
When scaffolding creates a project, the next steps SHALL recommend, not merely offer, making `data/raw/` read-only at the OS level, with the command for macOS or Linux and for Windows. The step SHALL say to apply it once each batch of raw data is in place and recorded in `data/README.md`, how to undo it before adding the next batch, and that the raw-data guard is best-effort.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include an entry marked "Recommended" that makes `data/raw/` read-only, gives the commands for macOS or Linux and for Windows, and does not call the step optional

#### Scenario: Adding the next batch
- **WHEN** the user reads the read-only step
- **THEN** it says when to apply it (after a batch is in place and recorded) and gives the commands that make `data/raw/` writable again before the next batch is added
