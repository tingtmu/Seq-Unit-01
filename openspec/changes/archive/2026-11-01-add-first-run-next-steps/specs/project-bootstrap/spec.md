# Spec Delta

## MODIFIED Requirements

### Requirement: Git initialization and hook installation
The bootstrap skill SHALL initialize a git repository with a `.gitignore` suited to bioinformatics data and a `.gitattributes` that stores and checks out text files with LF line endings. It SHALL also install the raw-data-guard hooks for each supported agent, and the doc-sync report script outside the project's hooks folder. It SHALL NOT install an end-of-turn (`Stop`) hook.

#### Scenario: Bootstrap completes
- **WHEN** generation finishes
- **THEN** `git status` works in the project, large data paths are ignored, and the hook configurations for Claude Code and Codex exist and point to the shared hook scripts

#### Scenario: No end-of-turn hook
- **WHEN** generation finishes
- **THEN** neither the Claude Code nor the Codex hook configuration has a `Stop` entry, and the doc-sync report script exists in the project but not in its hooks folder

#### Scenario: LF line endings on any platform
- **WHEN** generation finishes and the user adds the files to git on a machine with `core.autocrlf=true`
- **THEN** git reports no line-ending conversion warnings, and the files git checks out, including shell scripts and hook scripts, have LF line endings

### Requirement: Read-only raw data recommended after scaffolding
When scaffolding creates a project, the next steps SHALL recommend, not merely offer, making `data/raw/` read-only at the OS level, with the command for macOS, Linux, or Git Bash on Windows and the command for Windows cmd or PowerShell, each labeled with the shells it works in. The step SHALL say to apply it once each batch of raw data is in place and recorded in `data/README.md`, how to undo it before adding the next batch, and that the raw-data guard is best-effort.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include an entry marked "Recommended" that makes `data/raw/` read-only, gives the commands for macOS or Linux and for Windows, and does not call the step optional

#### Scenario: Adding the next batch
- **WHEN** the user reads the read-only step
- **THEN** it says when to apply it (after a batch is in place and recorded) and gives the commands that make `data/raw/` writable again before the next batch is added

#### Scenario: Windows user in Git Bash
- **WHEN** a Windows user reads the read-only step and works in Git Bash
- **THEN** the step labels the `chmod` commands as working in Git Bash and the `attrib` commands as working in cmd or PowerShell

## ADDED Requirements

### Requirement: Claude Code hook check reported after scaffolding
When scaffolding creates a project, the next steps SHALL tell the user to run `/hooks` in Claude Code to confirm that the nerv hook is listed, and to restart Claude Code in the project root if it is not. This step SHALL come after the Codex trust step.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include a Claude Code entry that names `/hooks` and restarting as the fallback, and the Codex trust step is still the first entry

### Requirement: First commit reported after scaffolding
When scaffolding creates a project, the next steps SHALL tell the user to commit the generated project, so later changes can be diffed against it. The step SHALL first tell the user to check that a git identity is set and give the commands that set a name and email if it is not. Each command SHALL be given separately, not chained with `&&`, so it runs in Windows PowerShell 5.1.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include a commit entry that names `git config user.email` as the identity check, gives `git config` commands for `user.name` and `user.email`, and gives `git add -A` and `git commit` as separate commands

#### Scenario: No git identity on the machine
- **WHEN** a user with no git identity follows the commit step in order
- **THEN** they set the identity before running `git commit`, so the commit does not fail with "Author identity unknown"
