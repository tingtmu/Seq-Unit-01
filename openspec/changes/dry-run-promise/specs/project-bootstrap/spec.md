## MODIFIED Requirements

### Requirement: Interview before generation
The bootstrap skill SHALL ask the user about assay type (bulk-rnaseq, scrnaseq, or other), workflow engine, language, compute setup, data sensitivity, and the one-line biological question the project answers. The question MAY be answered `TBD`, which is its default. The skill SHALL ask before creating any file, and SHALL show a summary of the planned structure for confirmation. The summary SHALL contain the planned top-level tree, taken from the scaffold's dry run, and the add-on and engine layers that apply, taken from the interview answers. The dry-run result SHALL list the planned files; it need not list add-ons. When the agent writes the project prose after scaffolding, it SHALL use the question answer rather than invent one.

#### Scenario: User answers the interview
- **WHEN** the user invokes the bootstrap skill in an empty directory
- **THEN** the agent asks the interview questions, shows the planned tree, and creates nothing until the user confirms

#### Scenario: Add-ons named in the plan
- **WHEN** the agent shows the plan for answers with assay `scrnaseq` and engine `snakemake`
- **THEN** it names the scRNA-seq add-on and the Snakemake engine layer from the answers, without inferring them from planned file names

#### Scenario: Dry run lists planned files
- **WHEN** the scaffold runs as a dry run on a target without conflicts
- **THEN** it reports status `planned` and the list of planned files, and writes nothing

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

### Requirement: Refuse to overwrite an existing project
The bootstrap skill SHALL NOT overwrite existing files. If the target directory already holds an AGENTS.md, CLAUDE.md, README.md, or any skeleton folder, it SHALL list the conflicts and ask how to proceed. The scaffold's dry run SHALL report conflicts the same way a real run does, so the agent finds them before the user confirms.

#### Scenario: Non-empty target
- **WHEN** the target already contains `README.md`
- **THEN** the agent reports the conflict and does not modify that file without explicit approval

#### Scenario: Conflicts found by the dry run
- **WHEN** the scaffold runs as a dry run on a target that already contains `README.md` and a `scripts/` folder
- **THEN** it reports status `conflict` with `README.md` and `scripts/` in its conflict list, exits non-zero, and writes nothing

#### Scenario: Agent stops on dry-run conflicts
- **WHEN** the dry run in the plan step reports conflicts
- **THEN** the agent shows the conflict list and asks how to proceed before asking the user to confirm the plan
