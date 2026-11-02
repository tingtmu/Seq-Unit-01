# skill-distribution Specification

## Purpose

Defines how the skill set is packaged, installed into a single project, and made usable across multiple coding agents from one source of truth.

## Requirements

### Requirement: Project-level installation
The skill set SHALL be installable into one project with a single `npx skills add tingtmu/Seq-Unit-01` command. The repo README SHALL document a fallback that copies the files without Node. Installation SHALL NOT require a global install.

#### Scenario: Install via skills CLI
- **WHEN** a user runs the documented install command in an empty project directory
- **THEN** the four skills are available to the agent in that project only

#### Scenario: Fallback install
- **WHEN** a user without Node follows the documented fallback
- **THEN** the same skill files end up in the project's agent skill directories

### Requirement: Self-contained skills
Each skill SHALL contain everything it needs at runtime: its instructions, references, templates, and scripts. It SHALL NOT depend on files elsewhere in this repo.

#### Scenario: Only nerv-init installed
- **WHEN** only the bootstrap skill is copied into a project
- **THEN** it can generate the full skeleton, including the doc-sync report script

### Requirement: Approachable EVA naming
Each skill name SHALL use an Evangelion term. Its description SHALL say in plain bioinformatics terms what the skill does and when to use it, so the agent can trigger it without knowing the reference.

#### Scenario: Description clarity
- **WHEN** a user unfamiliar with Evangelion reads the skill list
- **THEN** each description states its function (e.g. "set up a new bioinformatics project") in its first sentence
