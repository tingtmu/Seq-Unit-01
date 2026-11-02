# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Git initialization and hook installation`
- TO: `### Requirement: Git initialization without agent hooks`

## MODIFIED Requirements

### Requirement: Hard rules recorded
The generated AGENTS.md SHALL include these hard rules: files in `data/raw/` are never deleted, overwritten, or edited, and deliveries there are read-only; corrections are a workflow step that writes to `data/processed/`; secrets, credentials, and protected/controlled-access data are never committed; and the reference genome build and annotation version are pinned in one place. When the user reports sensitive data, the rules SHALL add stricter handling of that data.

#### Scenario: Sensitive data declared
- **WHEN** the user answers that the project contains human or controlled-access data
- **THEN** AGENTS.md includes the stricter data-handling rules and `.gitignore` excludes the data directories

#### Scenario: Raw data rule names deletion
- **WHEN** the skeleton is generated
- **THEN** the first hard rule in AGENTS.md says never to delete, overwrite, or edit files in `data/raw/`, says deliveries there are read-only, and says to record a new delivery's source and checksum in `data/README.md`

### Requirement: Git initialization without agent hooks
The bootstrap skill SHALL initialize a git repository with a `.gitignore` suited to bioinformatics data and a `.gitattributes` that stores and checks out text files with LF line endings. It SHALL install the doc-sync report script in `.nerv/scripts/`. It SHALL NOT install any agent hook or agent hook configuration.

#### Scenario: Bootstrap completes
- **WHEN** generation finishes
- **THEN** `git status` works in the project, large data paths are ignored, and the doc-sync report script exists at `.nerv/scripts/sync_ratio.py`

#### Scenario: No agent hooks
- **WHEN** generation finishes
- **THEN** the project has no `.nerv/hooks/` folder, no `.claude/settings.json`, and no `.codex/hooks.json`, and `.gitignore` has no raw snapshot entry

#### Scenario: No end-of-turn hook
- **WHEN** generation finishes
- **THEN** no end-of-turn (`Stop`) hook is installed, because the project has no agent hook configuration, and the doc-sync report script exists in `.nerv/scripts/` to run on demand

#### Scenario: Intake move is not blocked
- **WHEN** the agent moves a confirmed delivery from inside the project into `data/raw/<delivery>/`, in a single command or as part of a multi-line script
- **THEN** no project hook intercepts or denies the command

#### Scenario: LF line endings on any platform
- **WHEN** generation finishes and the user adds the files to git on a machine with `core.autocrlf=true`
- **THEN** git reports no line-ending conversion warnings, and the files git checks out, including shell scripts, have LF line endings

### Requirement: Read-only raw data recommended after scaffolding
When scaffolding creates a project, the next steps SHALL include one entry, of at most two sentences, saying that each delivery in `data/raw/` is made read-only once its provenance is recorded and that new data goes in a new delivery folder. The entry SHALL NOT list operating-system commands; the commands that make a delivery read-only or writable again live in the generated `data/README.md`.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include a read-only entry of at most two sentences that names delivery folders under `data/raw/`, contains no `chmod` or `attrib` command, and does not mention a raw-data guard, hooks, or `/hooks`

#### Scenario: Adding the next batch
- **WHEN** the user reads the read-only entry before adding more raw data
- **THEN** it tells them to put the new data in a new delivery folder, so no permissions have to change first

#### Scenario: Windows user in Git Bash
- **WHEN** a user or a later agent session on Windows needs to make a delivery read-only or writable again
- **THEN** the generated `data/README.md` gives the commands for macOS, Linux, or Git Bash on Windows, and for Windows cmd or PowerShell, each labeled with the shells it works in

#### Scenario: Agent relays the step
- **WHEN** the agent summarizes the created project for the user
- **THEN** it shows every next step from the scaffold result, without dropping or shortening any of them

#### Scenario: Nothing created
- **WHEN** the scaffold is a dry run or stops on conflicts
- **THEN** no next steps are reported

### Requirement: First commit after scaffolding
When a project is created, the scaffold result SHALL report whether a git identity (name and email) is set for it, and the next steps SHALL NOT contain a commit entry or any git command. The bootstrap skill SHALL commit the project itself after writing its prose. The commit SHALL contain only the generated files, the installed skill copies, the files data intake filled, and other paths the user approves after the skill lists them. When it cannot commit, its summary SHALL say why in one sentence.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the result reports the git identity as set or missing, and the next steps are exactly one entry: the read-only entry

#### Scenario: Identity already set
- **WHEN** git reports both `user.name` and `user.email` for the project
- **THEN** the plan names the identity the commit will use, the agent does not ask for one, and no next step mentions `git config` or `git commit`

#### Scenario: No git identity on the machine
- **WHEN** git reports no `user.name` or no `user.email` and the user gives a name and email in reply to the plan
- **THEN** the agent sets them with `git config` in the project, without `--global`, commits, and the user's global git configuration is unchanged

#### Scenario: Git unavailable
- **WHEN** scaffolding finishes but git could not be run
- **THEN** the result reports the identity as missing, the next steps hold no git command, and the agent's summary says in one sentence that nothing was committed because git is unavailable

#### Scenario: Agent commits the scaffold
- **WHEN** an identity is set and `git add -A` would include only the generated files, the installed skill copies (`.claude/skills/`, `.agents/skills/`, `skills-lock.json`), and the files data intake filled
- **THEN** the skill commits after writing the prose, reports the commit to the user, and does not ask the user to commit

#### Scenario: Other files in the target
- **WHEN** an identity is set and the target also holds new or changed paths that are neither generated, installed skill copies, nor filled by data intake, including changes already in an existing repository
- **THEN** the skill lists those paths and asks the user whether to include them before it commits

#### Scenario: User declines the other files
- **WHEN** the user answers no to including the other paths
- **THEN** the skill still commits the generated files, the installed skill copies, and the files data intake filled, and the commit contains none of the declined paths, even ones that were already staged

### Requirement: Each delivery made read-only after intake
After a delivery's provenance is recorded, the bootstrap skill SHALL make that delivery's folder read-only at the operating-system level, using a command for the shell it runs in. It SHALL leave `data/raw/` itself writable, so a new delivery can be added without changing any permissions. It SHALL make a delivery writable again only after the user approves replacing files in it.

#### Scenario: Delivery made read-only
- **WHEN** the provenance of `data/raw/GSE141713/` is recorded
- **THEN** the files in that folder are read-only, and a new folder can still be created in `data/raw/`

#### Scenario: Replacing a broken download
- **WHEN** the user reports that a raw file in a read-only delivery is corrupt and must be fetched again
- **THEN** the agent asks before making that delivery writable, changes only that delivery, and makes it read-only again after the new file's provenance is recorded, the same way in every supported agent

## REMOVED Requirements

### Requirement: Codex trust step reported after scaffolding
**Reason**: nerv-init no longer installs hooks, so there is nothing to trust or turn on with `/hooks`.
**Migration**: None. The read-only entry is now the only next step.
