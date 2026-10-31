# Spec Delta

## ADDED Requirements

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
