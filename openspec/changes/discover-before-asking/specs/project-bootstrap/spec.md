# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: First commit reported after scaffolding`
- TO: `### Requirement: First commit after scaffolding`

## MODIFIED Requirements

### Requirement: First commit after scaffolding
When scaffolding creates a project, the result SHALL report whether a git identity (name and email) is set for the project. If one is set, the next steps SHALL NOT include a commit step, and the bootstrap skill SHALL commit the project itself after writing its prose, so later changes can be diffed against it. The commit SHALL contain only the generated files, the installed skill copies, and other paths the user approves. Before committing, the skill SHALL list any other new or changed path in the target and ask whether to include it. If no identity is set, the next steps SHALL tell the user to set one, giving the commands for a name and an email, and then to commit. Each command SHALL be given separately, not chained with `&&`, so it runs in Windows PowerShell 5.1.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the result reports the git identity as set or missing, and the next steps include Codex trust, `/hooks` in Claude Code, filling `config/samples.tsv` and the reference pins, and making `data/raw/` read-only, in that order

#### Scenario: Identity already set
- **WHEN** scaffolding finishes and git reports both `user.name` and `user.email` for the project
- **THEN** the result reports the identity as set, the next steps are exactly the four user-only entries (Codex trust, `/hooks`, `config/samples.tsv`, read-only `data/raw/`), and no next step mentions `git config` or `git commit`

#### Scenario: No git identity on the machine
- **WHEN** scaffolding finishes and git reports no `user.name` or no `user.email` for the project
- **THEN** the result reports the identity as missing, and the next steps include a commit entry that gives `git config` commands for `user.name` and `user.email` before `git add -A` and `git commit`, each as a separate command

#### Scenario: Git unavailable
- **WHEN** scaffolding finishes but git could not be run
- **THEN** the result reports the identity as missing and keeps the commit entry, so the user still learns how to commit once git works

#### Scenario: Agent commits the scaffold
- **WHEN** the identity is set and `git add -A` would include only the generated files and the installed skill copies (`.claude/skills/`, `.agents/skills/`, `skills-lock.json`)
- **THEN** the skill commits after writing the prose, reports the commit to the user, and does not ask the user to commit

#### Scenario: Other files in the target
- **WHEN** the identity is set and the target also holds new or changed paths that are neither generated nor installed skill copies, including changes already in an existing repository
- **THEN** the skill lists those paths and asks the user whether to include them before it commits

#### Scenario: User declines the other files
- **WHEN** the user answers no to including the other paths
- **THEN** the skill still commits the generated files and the installed skill copies, and the commit contains none of the declined paths, even ones that were already staged
