# project-bootstrap Specification

## Purpose

Bootstraps a new bioinformatics project from an empty directory through a short interview, producing a directory skeleton, layered agent/human documentation, and installed hooks (the raw-data guard and the sync reminder).

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

### Requirement: Read-only raw data recommended after scaffolding
When scaffolding creates a project, the next steps SHALL recommend, not merely offer, making `data/raw/` read-only at the OS level, with the command for macOS or Linux and for Windows. The step SHALL say to apply it once each batch of raw data is in place and recorded in `data/README.md`, how to undo it before adding the next batch, and that the raw-data guard is best-effort.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include an entry marked "Recommended" that makes `data/raw/` read-only, gives the commands for macOS or Linux and for Windows, and does not call the step optional

#### Scenario: Adding the next batch
- **WHEN** the user reads the read-only step
- **THEN** it says when to apply it (after a batch is in place and recorded) and gives the commands that make `data/raw/` writable again before the next batch is added

### Requirement: Environment for the Run and Test commands
The generated project SHALL include one environment file in `envs/` with pinned versions. Creating that environment SHALL provide the engine and test tools that the Run and Test commands call for the chosen engine and languages. The README Quick start SHALL name the prerequisites the environment does not provide (conda, and a POSIX shell for plain scripts) and give the exact commands that create and activate the environment, using the same environment name the file declares.

#### Scenario: Snakemake with Python
- **WHEN** the user picks Snakemake and Python
- **THEN** `envs/` contains one environment file that pins Snakemake, the packages the generated workflow imports, and pytest, and README Quick start step 1 is the command that creates it

#### Scenario: Plain scripts with R
- **WHEN** the user picks plain scripts and R
- **THEN** the environment file pins R and testthat and does not include Snakemake

#### Scenario: Both languages
- **WHEN** the user picks Python and R
- **THEN** the one environment file provides both pytest and testthat

#### Scenario: Project name with spaces
- **WHEN** the project name is `Mouse liver RNA`
- **THEN** the environment file declares a valid conda environment name, and the Quick start activate command uses that same name

### Requirement: Fresh project passes its own Test command
The generated project SHALL include, for each chosen language, one smoke test in `tests/` that the Test command collects and that passes on the unmodified scaffold. The smoke test SHALL check a property of the generated project: that the sample sheet has its required columns. It SHALL use no real data.

#### Scenario: Python project tested on day one
- **WHEN** the user picks Python and runs `pytest tests/` in the fresh project with the environment active
- **THEN** at least one test is collected and pytest exits 0

#### Scenario: R project tested on day one
- **WHEN** the user picks R and runs the testthat Test command in the fresh project with the environment active
- **THEN** at least one test runs and the command exits 0

#### Scenario: Sample sheet loses a required column
- **WHEN** a user removes the `fastq_1` column from `config/samples.tsv`
- **THEN** the smoke test fails and names the missing column

#### Scenario: Language not chosen
- **WHEN** the user picks only Python
- **THEN** `tests/` has no R smoke test
