# Spec Delta

## Purpose

Defines how the skill set is packaged, installed into a single project, and made usable across multiple coding agents from one source of truth.

## ADDED Requirements

### Requirement: Project-level installation
The skill set SHALL be installable into one project with a single `npx skills add tingtmu/Seq-Unit-01` command. The repo README SHALL document a fallback that copies the files without Node. Installation SHALL NOT require a global install.

#### Scenario: Install via skills CLI
- **WHEN** a user runs the documented install command in an empty project directory
- **THEN** the three skills are available to the agent in that project only

#### Scenario: Fallback install
- **WHEN** a user without Node follows the documented fallback
- **THEN** the same skill files end up in the project's agent skill directories

### Requirement: Self-contained skills
Each skill SHALL contain everything it needs at runtime: its instructions, references, templates, and hook scripts. It SHALL NOT depend on files elsewhere in this repo.

#### Scenario: Only nerv-init installed
- **WHEN** only the bootstrap skill is copied into a project
- **THEN** it can generate the full skeleton and install the hooks

### Requirement: Single-source hooks with per-agent adapters
Hook logic SHALL live in one set of scripts that use only the Python 3 standard library. Each supported agent (Claude Code and Codex at minimum) SHALL get a thin configuration that points to those scripts.

#### Scenario: Same behavior across agents
- **WHEN** the raw-data guard runs under Claude Code and under Codex
- **THEN** both invoke the same script and apply the same decision logic, differing only in how the decision is reported to the agent

### Requirement: Approachable EVA naming
Each skill name SHALL use an Evangelion term. Its description SHALL say in plain bioinformatics terms what the skill does and when to use it, so the agent can trigger it without knowing the reference.

#### Scenario: Description clarity
- **WHEN** a user unfamiliar with Evangelion reads the skill list
- **THEN** each description states its function (e.g. "set up a new bioinformatics project") in its first sentence
