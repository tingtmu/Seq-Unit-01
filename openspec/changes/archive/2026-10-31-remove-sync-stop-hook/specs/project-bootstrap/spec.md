# Spec Delta

## MODIFIED Requirements

### Requirement: Git initialization and hook installation
The bootstrap skill SHALL initialize a git repository with a `.gitignore` suited to bioinformatics data. It SHALL also install the raw-data-guard hooks for each supported agent, and the doc-sync report script outside the project's hooks folder. It SHALL NOT install an end-of-turn (`Stop`) hook.

#### Scenario: Bootstrap completes
- **WHEN** generation finishes
- **THEN** `git status` works in the project, large data paths are ignored, and the hook configurations for Claude Code and Codex exist and point to the shared hook scripts

#### Scenario: No end-of-turn hook
- **WHEN** generation finishes
- **THEN** neither the Claude Code nor the Codex hook configuration has a `Stop` entry, and the doc-sync report script exists in the project but not in its hooks folder

### Requirement: Codex trust step reported after scaffolding
When the bootstrap skill finishes creating a project, it SHALL tell the user how to trust the project's Codex hooks: start Codex in the project root, run `/hooks`, and trust the nerv hooks. It SHALL say that the raw-data guard stays off in Codex until the user does this, and that the hooks must be trusted again after `.codex/hooks.json` changes. The step SHALL be reported for every created project, whichever agent the user runs.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the scaffold result lists the Codex trust step among its next steps, naming `/hooks` and stating that the raw-data guard is off in Codex until the hooks are trusted, and it does not mention a sync reminder

#### Scenario: Agent relays the step
- **WHEN** the agent summarizes the created project for the user
- **THEN** it shows every next step from the scaffold result, including the Codex trust step, without dropping or shortening any of them

#### Scenario: Nothing created
- **WHEN** the scaffold is a dry run or stops on conflicts
- **THEN** no next steps are reported, because no hooks were installed
