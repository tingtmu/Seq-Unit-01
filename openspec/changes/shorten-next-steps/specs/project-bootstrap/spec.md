# Spec Delta

## MODIFIED Requirements

### Requirement: Codex trust step reported after scaffolding
When the bootstrap skill finishes creating a project, its next steps SHALL begin with one entry that turns on the raw-data guard. The entry SHALL name `/hooks`. For Codex, it SHALL say to trust the nerv hooks, that the raw-data guard stays off in Codex until the user does, and that the hooks must be trusted again after `.codex/hooks.json` changes. For Claude Code, it SHALL say to check that the nerv hook is listed and to restart Claude Code in the project root if it is not. The entry SHALL be reported for every created project, whichever agent the user runs.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the first next step names `/hooks`, states that the raw-data guard is off in Codex until the hooks are trusted, says to trust them again after `.codex/hooks.json` changes, gives restarting Claude Code as the fallback, and does not mention a sync reminder

#### Scenario: Agent relays the step
- **WHEN** the agent summarizes the created project for the user
- **THEN** it shows every next step from the scaffold result, including the hook entry, without dropping or shortening any of them

#### Scenario: Nothing created
- **WHEN** the scaffold is a dry run or stops on conflicts
- **THEN** no next steps are reported, because no hooks were installed

### Requirement: First commit after scaffolding
When scaffolding creates a project, the result SHALL report whether a git identity (name and email) is set for the project, and the next steps SHALL NOT contain a commit entry or any git command. The bootstrap skill SHALL commit the project itself after writing its prose. When no identity is set, the skill SHALL ask the user for a name and email in its plan message and, after `git init`, set exactly those for this project only, never globally and never invented. The commit SHALL contain only the generated files, the installed skill copies, the files data intake filled, and other paths the user approves. Before committing, the skill SHALL list any other new or changed path and ask whether to include it. When it cannot commit, its summary SHALL say why in one sentence.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the result reports the git identity as set or missing, and the next steps are exactly two entries: the raw-data guard entry, then the read-only entry

#### Scenario: Identity already set
- **WHEN** git reports both `user.name` and `user.email` for the project
- **THEN** the plan names the identity the commit will use, the agent does not ask for one, and no next step mentions `git config` or `git commit`

#### Scenario: No git identity on the machine
- **WHEN** git reports no `user.name` or no `user.email` and the user gives a name and email in reply to the plan
- **THEN** the agent sets them with `git config` in the project, without `--global`, commits, and the user's global git configuration is unchanged

#### Scenario: No identity given
- **WHEN** no identity is set and the user does not give a name and email
- **THEN** the agent does not invent one and does not commit, and its summary says in one sentence that nothing was committed because git has no identity for the project

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

## REMOVED Requirements

### Requirement: Claude Code hook check reported after scaffolding
**Reason**: Merged into the single raw-data guard entry ("Codex trust step reported after scaffolding"). Two entries about `/hooks` overwhelmed the user in the yeast test run.
**Migration**: The first next step now covers both agents: trust the hooks in Codex, or check that the hook is listed in Claude Code and restart if it is not.

## ADDED Requirements

### Requirement: Sample sheet and reference pins are not a user step
The next steps SHALL NOT ask the user to fill `config/samples.tsv` or the reference pins in `config/config.yaml`. The bootstrap skill SHALL fill the reference fields that the data's own files state, such as the organism, and leave the others empty rather than guess. When an empty field blocks the project's next run, the summary SHALL name it in one line.

#### Scenario: No fill-in entry
- **WHEN** scaffolding finishes and the project is created
- **THEN** no next step mentions `config/samples.tsv` or the reference pins

#### Scenario: Organism stated by the data
- **WHEN** the delivery's readme names the organism but not the genome build
- **THEN** `config/config.yaml` has the organism filled, the genome build left empty, and no invented build

### Requirement: Summary points to the analysis
After the next steps, the bootstrap skill's summary SHALL end by inviting the user to say what they want to compare or test, so the conversation moves on to planning the analysis. In an empty folder, the request for raw data SHALL come before this invitation.

#### Scenario: Data in place
- **WHEN** the project is created and its raw data is taken in
- **THEN** the summary's last line asks the user what they want to compare

#### Scenario: No data yet
- **WHEN** the project is created in an empty folder
- **THEN** the summary asks for the raw data first, and then invites the user to say what they want to compare
