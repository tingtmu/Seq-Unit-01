# Spec Delta

## MODIFIED Requirements

### Requirement: Interview before generation
The bootstrap skill SHALL ask the user about assay type (bulk-rnaseq, scrnaseq, or other), workflow engine, language, compute setup, data sensitivity, and the one-line project question, except answers it proposes from the explored files. The question MAY be answered `TBD`, which is its default. The skill SHALL ask before creating any file, and SHALL show the annotated plan for confirmation. The project prose written after scaffolding SHALL use the question answer, never an invented one.

#### Scenario: User answers the interview
- **WHEN** the user invokes the bootstrap skill in an empty directory
- **THEN** the agent asks the interview questions, shows the annotated plan, and creates nothing until the user confirms

#### Scenario: Add-ons named in the plan
- **WHEN** the agent shows the plan for answers with assay `scrnaseq`, engine `snakemake`, and language `python`
- **THEN** it names the scRNA-seq, Snakemake, and Python add-ons from the answers, without inferring them from planned file names

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
The bootstrap skill SHALL NOT overwrite existing files. If the target directory already holds an AGENTS.md, CLAUDE.md, README.md, or any skeleton folder, it SHALL list the conflicts and ask how to proceed. The scaffold's dry run SHALL report conflicts as a real run does, before the user confirms. The skill SHALL NOT move, rename, or delete the user's files, except the data moves (raw and reference) listed in the plan the user confirmed, and removing source folders those moves left empty.

#### Scenario: Non-empty target
- **WHEN** the target already contains `README.md`
- **THEN** the agent reports the conflict and does not modify that file without explicit approval

#### Scenario: Conflicts found by the dry run
- **WHEN** the scaffold runs as a dry run on a target that already contains `README.md` and a `scripts/` folder
- **THEN** it reports status `conflict` with `README.md` and `scripts/` in its conflict list, exits non-zero, and writes nothing

#### Scenario: Agent stops on dry-run conflicts
- **WHEN** the dry run in the plan step reports conflicts
- **THEN** the agent shows the conflict list and asks how to proceed before asking the user to confirm the plan

#### Scenario: Data folder outside the skeleton
- **WHEN** the target holds only `input_data/GSE141713/` with raw files
- **THEN** the dry run reports no conflict, and the raw files move only after the user confirms a plan that lists the move

#### Scenario: Other user files left in place
- **WHEN** the target also holds a user file that is not raw data, such as `analysis.R`
- **THEN** the skill leaves it where it is and does not move, rename, or delete it

### Requirement: Read-only raw data recommended after scaffolding
When scaffolding creates a project, the next steps SHALL include one entry, of at most two sentences, saying that each delivery in `data/raw/` is made read-only once its provenance is recorded, that new data goes in a new delivery folder, and that the raw-data guard is best-effort. The entry SHALL NOT list operating-system commands; the commands that make a delivery read-only or writable again live in the generated `data/README.md`.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include a read-only entry of at most two sentences that names delivery folders under `data/raw/` and contains no `chmod` or `attrib` command

#### Scenario: Adding the next batch
- **WHEN** the user reads the read-only entry before adding more raw data
- **THEN** it tells them to put the new data in a new delivery folder, so no permissions have to change first

#### Scenario: Windows user in Git Bash
- **WHEN** a user or a later agent session on Windows needs to make a delivery read-only or writable again
- **THEN** the generated `data/README.md` gives the commands for macOS, Linux, or Git Bash on Windows, and for Windows cmd or PowerShell, each labeled with the shells it works in

### Requirement: Fresh project passes its own Test command
The generated project SHALL include, for each chosen language, one smoke test in `tests/` that the Test command collects and that passes on the unmodified scaffold. The smoke test SHALL check a property of the generated project: that the sample sheet has its required column, `sample_id`. It SHALL use no real data. The Snakemake sample-sheet check SHALL require only `sample_id`, and SHALL check that the files in any `fastq_*` columns present exist.

#### Scenario: Python project tested on day one
- **WHEN** the user picks Python and runs `pytest tests/` in the fresh project with the environment active
- **THEN** at least one test is collected and pytest exits 0

#### Scenario: R project tested on day one
- **WHEN** the user picks R and runs the testthat Test command in the fresh project with the environment active
- **THEN** at least one test runs and the command exits 0

#### Scenario: Sample sheet loses a required column
- **WHEN** a user removes the `sample_id` column from `config/samples.tsv`
- **THEN** the smoke test fails and names the missing column

#### Scenario: Sample sheet for precomputed counts
- **WHEN** `config/samples.tsv` has the columns `sample_id`, `condition`, and `replicate` and no FASTQ columns
- **THEN** the smoke test passes, and the Snakemake sample-sheet check accepts the sheet

#### Scenario: Listed FASTQ file missing
- **WHEN** the sample sheet lists a `fastq_1` path that does not exist
- **THEN** the Snakemake sample-sheet check fails and names the missing file

#### Scenario: Language not chosen
- **WHEN** the user picks only Python
- **THEN** `tests/` has no R smoke test

## ADDED Requirements

### Requirement: Annotated plan before confirmation
Before creating any file, the bootstrap skill SHALL show an annotated plan and wait for confirmation. The plan SHALL be a top-level tree from the scaffold's dry run: each top-level folder with a one-line purpose, each planned data move as its source and destination paths, and the add-ons that apply (assay, engine, and language layers), taken from the interview answers. The full file list SHALL be shown only on request. The dry-run result SHALL list the planned files; it need not list add-ons.

#### Scenario: Annotated plan
- **WHEN** the agent shows the plan for a folder whose raw data will move from `input_data/GSE141713/` to `data/raw/GSE141713/`
- **THEN** the plan shows each top-level folder with a one-line purpose, shows that move with both paths, names the add-ons, and does not list every planned file

### Requirement: Explore the target before asking
Before asking the interview questions, the bootstrap skill SHALL inspect the target folder: file names, sizes, and provider readmes. It SHALL propose the interview answers these settle, such as the assay and whether the inputs are reads or precomputed counts, and ask only the rest. Until the user confirms the data is not sensitive, it SHALL NOT read the contents of data or metadata tables, header rows included, because a wide table's header can hold sample identifiers.

#### Scenario: Folder holds precomputed counts
- **WHEN** the target holds a gzipped gene-count matrix, a sample annotation, and a readme that describes RNA-seq UMI counts
- **THEN** the agent proposes bulk RNA-seq with precomputed counts as the starting point, says which file names and readme it based this on, and asks only the questions they do not settle

#### Scenario: Assay not clear from the files
- **WHEN** the files do not show which assay produced them
- **THEN** the agent asks for the assay type and does not guess it

#### Scenario: Sensitivity not yet answered
- **WHEN** the agent explores a folder before the user has said whether the data is sensitive
- **THEN** it reads only file names, sizes, and readmes, and opens no data or metadata table, not even its header row

### Requirement: Data intake after scaffolding
When the confirmed plan lists raw data, the bootstrap skill SHALL, after scaffolding and before the first commit, put each delivery in its own folder `data/raw/<delivery>/` with the files as received. It SHALL move raw data found inside the project folder and copy raw data the user points to outside it. Reference sequences and annotations SHALL go in `data/reference/`. It SHALL move or copy only the paths the plan lists, and remove only empty source folders, never recursively.

#### Scenario: Raw data inside the project folder
- **WHEN** the confirmed plan moves `input_data/GSE141713/` to `data/raw/GSE141713/`
- **THEN** after scaffolding the three files are in `data/raw/GSE141713/` with their original names and content, and `input_data/GSE141713/` no longer holds them

#### Scenario: Raw data outside the project folder
- **WHEN** the user points to raw files in another folder, such as a downloads folder or a lab share
- **THEN** the agent copies them into `data/raw/<delivery>/` and leaves the originals in place

#### Scenario: Reference files delivered with the data
- **WHEN** the data includes a genome FASTA or an annotation GTF
- **THEN** the plan places them in `data/reference/`, not in `data/raw/`

#### Scenario: Very large copy
- **WHEN** a copy would take long enough, or use enough disk space, to matter to the user
- **THEN** the agent asks before copying, and offers to move the files instead only when the source is on the same volume as the project; it never moves data off another volume or a shared drive

### Requirement: Provenance recorded at intake
For each file taken in, the bootstrap skill SHALL record in `data/README.md` its path, its source, the date received, and its SHA-256 checksum. The source SHALL be an accession or URL only when the data's own files state it; otherwise it SHALL say the data was supplied locally and give the original path. When the delivery includes provider checksum files, the skill SHALL verify them at the source, before moving or copying anything. After a copy, each copy's checksum SHALL match its source.

#### Scenario: Provenance recorded
- **WHEN** a delivery's files are in `data/raw/GSE141713/`
- **THEN** `data/README.md` lists each file with its source, the date received, and its SHA-256 checksum

#### Scenario: Accession stated by the data
- **WHEN** the delivery's readme names the GEO series GSE141713
- **THEN** the source names GSE141713 and says it was supplied locally, without claiming a download URL the agent did not use

#### Scenario: Provider checksum mismatch
- **WHEN** a delivery includes an MD5 file and a listed file does not match it
- **THEN** the agent stops that delivery's intake before moving or copying it, names the mismatched files, and leaves the delivery where it was, outside `data/raw/`

### Requirement: Each delivery made read-only after intake
After a delivery's provenance is recorded, the bootstrap skill SHALL make that delivery's folder read-only at the operating-system level, using a command for the shell it runs in. It SHALL leave `data/raw/` itself writable, so a new delivery can be added without changing any permissions. It SHALL make a delivery writable again only after the user approves replacing files in it.

#### Scenario: Delivery made read-only
- **WHEN** the provenance of `data/raw/GSE141713/` is recorded
- **THEN** the files in that folder are read-only, and a new folder can still be created in `data/raw/`

#### Scenario: Replacing a broken download
- **WHEN** the user reports that a raw file in a read-only delivery is corrupt and must be fetched again
- **THEN** the agent asks before making that delivery writable, changes only that delivery, and makes it read-only again after the new file's provenance is recorded; where the raw-data guard denies the replacement (Codex), the agent gives the user the commands to run instead

### Requirement: Raw data requested in an empty folder
When exploration finds no raw data, the bootstrap skill SHALL, after scaffolding, ask the user to put the raw files, as received, in `data/raw/<delivery>/` or to give their path. When the user says the data is in place, the skill SHALL run the same intake: provenance, read-only delivery, and sample sheet.

#### Scenario: Empty folder
- **WHEN** the bootstrap skill runs in an empty folder and the project is created
- **THEN** the agent's summary asks the user to put their raw data in `data/raw/<delivery>/` or give its path

#### Scenario: Data added later
- **WHEN** the user says the raw data is in `data/raw/run1/`
- **THEN** the agent records its provenance, makes `data/raw/run1/` read-only, and fills the sample sheet from its metadata

#### Scenario: Data added in a later session
- **WHEN** an agent without the bootstrap skill loaded reads the generated `data/README.md` before adding a delivery
- **THEN** its "Adding a delivery" section lists the whole intake: verify provider checksums, put the files in a new delivery folder, record provenance, make the folder read-only, and update `config/samples.tsv`

### Requirement: Sensitive data at intake
When the user declares the data sensitive, intake SHALL still move or copy each delivery, record its checksums, and make it read-only, but the skill SHALL NOT read the contents of data or metadata files and SHALL NOT fill the sample sheet. Before the first commit, it SHALL say that `data/README.md` lists raw file names and ask whether to commit it.

#### Scenario: Sensitive delivery
- **WHEN** the user answers that the data is sensitive and confirms the plan
- **THEN** the delivery is in `data/raw/<delivery>/` with checksums recorded and made read-only, `config/samples.tsv` is left as the template, and no data or metadata rows were read

#### Scenario: Provenance table before commit
- **WHEN** the project holds sensitive data and the agent is about to commit
- **THEN** it tells the user that `data/README.md` lists raw file names and commits it only if the user agrees

### Requirement: Sample sheet built from the data
When discovered metadata describes the samples and the data is not sensitive, the bootstrap skill SHALL fill `config/samples.tsv` from it: one row per sample, a `sample_id` column, and only columns the metadata supports. FASTQ path columns SHALL appear only when reads are present. The path of a precomputed count matrix SHALL be recorded in `config/config.yaml`. The bulk RNA-seq add-on SHALL ship an empty design formula, for the analysis plan to fix.

#### Scenario: Precomputed counts
- **WHEN** the delivery holds a count matrix and a sample annotation with the columns `sample`, `var_name`, and `repeat_id`
- **THEN** `config/samples.tsv` has one row per annotated sample, a `sample_id` column, columns mapped from the annotation, no FASTQ columns, and `config/config.yaml` names the count matrix path

#### Scenario: No invented covariate
- **WHEN** the sample metadata has no batch information
- **THEN** neither `config/samples.tsv` nor `config/design.yaml` names a `batch` column

#### Scenario: Reads delivered
- **WHEN** the delivery holds paired FASTQ files and a sample sheet that maps them to samples
- **THEN** `config/samples.tsv` lists each sample's `fastq_1` and `fastq_2` paths under `data/raw/<delivery>/`

#### Scenario: Bulk RNA-seq design left open
- **WHEN** the user picks bulk RNA-seq
- **THEN** the generated `config/design.yaml` has an empty design formula, with a comment saying the analysis plan fixes it before results are seen
