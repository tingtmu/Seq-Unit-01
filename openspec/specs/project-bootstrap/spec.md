# project-bootstrap Specification

## Purpose

Bootstraps a new bioinformatics project from an empty directory through a short interview, producing a directory skeleton, layered agent/human documentation, and installed guardrail hooks.

## Requirements

### Requirement: Interview before generation
The bootstrap skill SHALL ask the user about assay type (bulk-rnaseq, scrnaseq, or other), workflow engine, language, compute setup, and data sensitivity. It SHALL do so before creating any file, and SHALL show a summary of the planned structure for confirmation.

#### Scenario: User answers the interview
- **WHEN** the user invokes the bootstrap skill in an empty directory
- **THEN** the agent asks the interview questions, shows the planned tree, and creates nothing until the user confirms

#### Scenario: Defaults offered
- **WHEN** the user has no preference for workflow engine
- **THEN** Snakemake is proposed as the default

### Requirement: Refuse to overwrite an existing project
The bootstrap skill SHALL NOT overwrite existing files. If the target directory already holds an AGENTS.md, CLAUDE.md, README.md, or any skeleton folder, it SHALL list the conflicts and ask how to proceed.

#### Scenario: Non-empty target
- **WHEN** the target already contains `README.md`
- **THEN** the agent reports the conflict and does not modify that file without explicit approval

### Requirement: Shared skeleton with add-ons
The generated project SHALL contain these shared folders, each with its own README: `config/`, `data/` (with `raw/`, `reference/`, `processed/`), `workflow/`, `scripts/`, `notebooks/`, `envs/`, `results/`, `tests/`, and `docs/`. Assay-specific and engine-specific add-ons SHALL be layered on top according to the interview answers.

#### Scenario: Bulk RNA-seq with Snakemake
- **WHEN** the user picks bulk-rnaseq and Snakemake
- **THEN** the shared skeleton is created, `workflow/` follows the Snakemake standard layout, and `config/` contains a place for the design formula and contrasts

#### Scenario: scRNA-seq
- **WHEN** the user picks scrnaseq
- **THEN** the folder READMEs document the object format conventions (.h5ad/.rds), that per-sample QC thresholds are recorded in `config/`, and that integration/batch choices are logged

#### Scenario: Other assay
- **WHEN** the user picks "other" and describes the assay
- **THEN** the shared skeleton is created and the agent adapts README content to the description without adding unrequested folders

### Requirement: Concise AGENTS.md with pointers
The generated `AGENTS.md` SHALL contain only the hard rules, the project's run and test commands, and a map from areas to deeper docs (e.g. "for workflow details read `workflow/README.md`"). Detail SHALL live in the folder READMEs, not in AGENTS.md.

#### Scenario: Agent looks for workflow details
- **WHEN** an agent reads `AGENTS.md`
- **THEN** it finds a path pointer to `workflow/README.md` rather than workflow details inline

### Requirement: CLAUDE.md imports AGENTS.md
The generated `CLAUDE.md` SHALL import `AGENTS.md` via `@AGENTS.md` and SHALL NOT duplicate its content.

#### Scenario: Claude Code session start
- **WHEN** Claude Code loads the project
- **THEN** the AGENTS.md content is loaded through the CLAUDE.md import

### Requirement: Uniform folder README template
Every generated folder README SHALL have the sections Purpose, Conventions, Current state, and Last major change.

#### Scenario: New folder README
- **WHEN** the skeleton is generated
- **THEN** each folder README contains all four sections, filled with content specific to the interview answers

### Requirement: Hard rules recorded
The generated AGENTS.md SHALL include these hard rules: raw data is never modified in place; corrections are a workflow step that writes to `data/processed/`; secrets, credentials, and protected/controlled-access data are never committed; and the reference genome build and annotation version are pinned in one place. When the user reports sensitive data, the rules SHALL add stricter handling of that data.

#### Scenario: Sensitive data declared
- **WHEN** the user answers that the project contains human or controlled-access data
- **THEN** AGENTS.md includes the stricter data-handling rules and `.gitignore` excludes the data directories

### Requirement: Git initialization and hook installation
The bootstrap skill SHALL initialize a git repository with a `.gitignore` suited to bioinformatics data. It SHALL also install the doc-sync and raw-data-guard hooks for each supported agent.

#### Scenario: Bootstrap completes
- **WHEN** generation finishes
- **THEN** `git status` works in the project, large data paths are ignored, and the hook configurations for Claude Code and Codex exist and point to the shared hook scripts
