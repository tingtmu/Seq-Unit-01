# Spec Delta

## MODIFIED Requirements

### Requirement: Interview before generation
The bootstrap skill SHALL ask the user about assay type (bulk-rnaseq, scrnaseq, or other), workflow engine, language, compute setup, data sensitivity, and the one-line biological question the project answers. The question MAY be answered `TBD`, which is its default. The skill SHALL ask before creating any file, and SHALL show a summary of the planned structure for confirmation. When the agent writes the project prose after scaffolding, it SHALL use the question answer rather than invent one.

#### Scenario: User answers the interview
- **WHEN** the user invokes the bootstrap skill in an empty directory
- **THEN** the agent asks the interview questions, shows the planned tree, and creates nothing until the user confirms

#### Scenario: Defaults offered
- **WHEN** the user has no preference for workflow engine
- **THEN** Snakemake is proposed as the default

#### Scenario: Project question answered
- **WHEN** the user gives a one-line biological question in the interview
- **THEN** the agent writes that question into the generated `AGENTS.md` and `README.md`

#### Scenario: Project question not yet known
- **WHEN** the user answers `TBD` or gives no question
- **THEN** the generated `AGENTS.md` and `README.md` show the question as `TBD`, and the agent does not make one up

#### Scenario: Scaffold accepts the question answer
- **WHEN** the answers passed to the scaffold include a `question` key
- **THEN** the scaffold validates the answers and generates the project as it would without that key
