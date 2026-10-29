# Spec Delta

## ADDED Requirements

### Requirement: Codex trust step reported after scaffolding
When the bootstrap skill finishes creating a project, it SHALL tell the user how to trust the project's Codex hooks: start Codex in the project root, run `/hooks`, and trust the nerv hooks. It SHALL say that the raw-data guard and the sync reminder stay off in Codex until the user does this, and that the hooks must be trusted again after `.codex/hooks.json` changes. The step SHALL be reported for every created project, whichever agent the user runs.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the scaffold result lists the Codex trust step among its next steps, naming `/hooks` and stating that the raw-data guard and sync reminder are off in Codex until the hooks are trusted

#### Scenario: Agent relays the step
- **WHEN** the agent summarizes the created project for the user
- **THEN** it shows every next step from the scaffold result, including the Codex trust step, without dropping or shortening any of them

#### Scenario: Nothing created
- **WHEN** the scaffold is a dry run or stops on conflicts
- **THEN** no next steps are reported, because no hooks were installed
