# project-bootstrap Specification

## Purpose

Bootstraps a new bioinformatics project, from an empty directory or one that already holds raw data, through a short interview, producing a directory skeleton, layered agent/human documentation, read-only raw deliveries, and the raw data taken in with its provenance.

## Requirements

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
The generated AGENTS.md SHALL include these hard rules: files in `data/raw/` are never deleted, moved, overwritten, or edited, and deliveries there are read-only; corrections are a workflow step that writes to `data/processed/`; secrets, credentials, and protected/controlled-access data are never committed; and the reference genome build and annotation version are pinned in one place. When the user reports sensitive data, the rules SHALL add stricter handling of that data.

#### Scenario: Sensitive data declared
- **WHEN** the user answers that the project contains human or controlled-access data
- **THEN** AGENTS.md includes the stricter data-handling rules and `.gitignore` excludes the data directories

#### Scenario: Raw data rule names deletion
- **WHEN** the skeleton is generated
- **THEN** the first hard rule in AGENTS.md says never to delete, move, overwrite, or edit files in `data/raw/`, says deliveries there are read-only, and says to record a new delivery's source and checksum in `data/README.md`

### Requirement: Git initialization without agent hooks
The bootstrap skill SHALL initialize a git repository with a `.gitignore` suited to bioinformatics data and a `.gitattributes` that stores and checks out text files with LF line endings. It SHALL install the doc-sync report script in `.nerv/scripts/`. It SHALL NOT install any agent hook or agent hook configuration.

#### Scenario: Bootstrap completes
- **WHEN** generation finishes
- **THEN** `git status` works in the project, large data paths are ignored, and the doc-sync report script exists at `.nerv/scripts/sync_ratio.py`

#### Scenario: No agent hooks
- **WHEN** generation finishes
- **THEN** the project has no `.nerv/hooks/` folder, no `.claude/settings.json`, and no `.codex/hooks.json`, and `.gitignore` has no raw snapshot entry

#### Scenario: No end-of-turn hook
- **WHEN** generation finishes
- **THEN** no end-of-turn (`Stop`) hook is installed, because the project has no agent hook configuration, and the doc-sync report script exists in `.nerv/scripts/` to run on demand

#### Scenario: Intake move is not blocked
- **WHEN** the agent moves a confirmed delivery from inside the project into `data/raw/<delivery>/`, in a single command or as part of a multi-line script
- **THEN** no project hook intercepts or denies the command

#### Scenario: LF line endings on any platform
- **WHEN** generation finishes and the user adds the files to git on a machine with `core.autocrlf=true`
- **THEN** git reports no line-ending conversion warnings, and the files git checks out, including shell scripts, have LF line endings

### Requirement: Read-only raw data recommended after scaffolding
When scaffolding creates a project, the next steps SHALL include one entry, of at most two sentences, saying that each delivery in `data/raw/` is made read-only once its provenance is recorded and that new data goes in a new delivery folder. The entry SHALL NOT list operating-system commands; the commands that make a delivery read-only or writable again live in the generated `data/README.md`.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the next steps include a read-only entry of at most two sentences that names delivery folders under `data/raw/`, contains no `chmod` or `attrib` command, and does not mention a raw-data guard, hooks, or `/hooks`

#### Scenario: Adding the next batch
- **WHEN** the user reads the read-only entry before adding more raw data
- **THEN** it tells them to put the new data in a new delivery folder, so no permissions have to change first

#### Scenario: Windows user in Git Bash
- **WHEN** a user or a later agent session on Windows needs to make a delivery read-only or writable again
- **THEN** the generated `data/README.md` gives the commands for macOS, Linux, or Git Bash on Windows, and for Windows cmd or PowerShell, each labeled with the shells it works in

#### Scenario: Windows limit stated
- **WHEN** a user reads how deliveries are protected in the generated `data/README.md`
- **THEN** it says that on Windows, read-only files still block overwrites but Git Bash `rm` and PowerShell `Remove-Item -Force` can delete them, so the hard rule is the protection there, and the read-only next step makes no claim that every tool is blocked

#### Scenario: Agent relays the step
- **WHEN** the agent summarizes the created project for the user
- **THEN** it shows every next step from the scaffold result, without dropping or shortening any of them

#### Scenario: Nothing created
- **WHEN** the scaffold is a dry run or stops on conflicts
- **THEN** no next steps are reported

### Requirement: First commit after scaffolding
When a project is created, the scaffold result SHALL report whether a git identity (name and email) is set for it, and the next steps SHALL NOT contain a commit entry or any git command. The bootstrap skill SHALL commit the project itself after writing its prose. The commit SHALL contain only the generated files, the installed skill copies, the files data intake filled, and other paths the user approves after the skill lists them. When it cannot commit, its summary SHALL say why in one sentence.

#### Scenario: Project created
- **WHEN** scaffolding finishes and the project is created
- **THEN** the result reports the git identity as set or missing, and the next steps are exactly one entry: the read-only entry

#### Scenario: Identity already set
- **WHEN** git reports both `user.name` and `user.email` for the project
- **THEN** the plan names the identity the commit will use, the agent does not ask for one, and no next step mentions `git config` or `git commit`

#### Scenario: No git identity on the machine
- **WHEN** git reports no `user.name` or no `user.email` and the user gives a name and email in reply to the plan
- **THEN** the agent sets them with `git config` in the project, without `--global`, commits, and the user's global git configuration is unchanged

#### Scenario: Git unavailable
- **WHEN** scaffolding finishes but git could not be run
- **THEN** the result reports the identity as missing, the next steps hold no git command, and the agent's summary says in one sentence that nothing was committed because git is unavailable

#### Scenario: Agent commits the scaffold
- **WHEN** an identity is set and `git add -A` would include only the generated files, the installed skill copies (`.claude/skills/`, `.agents/skills/`, `skills-lock.json`), and the files data intake filled
- **THEN** the skill commits after writing the prose, reports the commit to the user, and does not ask the user to commit

#### Scenario: Other files in the target
- **WHEN** an identity is set and the target also holds new or changed paths that are neither generated, installed skill copies, nor filled by data intake, including changes already in an existing repository
- **THEN** the skill lists those paths and asks the user whether to include them before it commits

#### Scenario: User declines the other files
- **WHEN** the user answers no to including the other paths
- **THEN** the skill still commits the generated files, the installed skill copies, and the files data intake filled, and the commit contains none of the declined paths, even ones that were already staged

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
- **THEN** the agent asks before making that delivery writable, changes only that delivery, and makes it read-only again after the new file's provenance is recorded, the same way in every supported agent

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

### Requirement: Git identity set for the project only
When no git identity is set, the bootstrap skill SHALL ask the user for a name and email in its plan message and, after `git init`, set exactly those for this project only, never globally and never invented. Without an identity, it SHALL NOT commit.

#### Scenario: No identity given
- **WHEN** no identity is set and the user does not give a name and email
- **THEN** the agent does not invent one and does not commit, and its summary says in one sentence that nothing was committed because git has no identity for the project

### Requirement: Sample sheet and reference pins are not a user step
The next steps SHALL NOT ask the user to fill `config/samples.tsv` or the reference pins in `config/config.yaml`. The bootstrap skill SHALL fill the reference fields that the data's own files state, such as the organism, and leave the others empty rather than guess. When an empty field blocks the project's next run, the summary SHALL name it in one line. When the data is sensitive and the sample sheet was not filled, the summary SHALL say in one line that the user fills it.

#### Scenario: No fill-in entry
- **WHEN** scaffolding finishes and the project is created
- **THEN** no next step mentions `config/samples.tsv` or the reference pins

#### Scenario: Organism stated by the data
- **WHEN** the delivery's readme names the organism but not the genome build
- **THEN** `config/config.yaml` has the organism filled, the genome build left empty, and no invented build

#### Scenario: Sensitive data
- **WHEN** the project holds sensitive data, so the agent did not read the sample metadata
- **THEN** no next step mentions `config/samples.tsv`, and the summary says in one line that the user fills it, because the agent did not read the metadata

### Requirement: Summary points to the analysis
After the next steps, the bootstrap skill's summary SHALL end by inviting the user to say what they want to compare or test, so the conversation moves on to planning the analysis. In an empty folder, the request for raw data SHALL come before this invitation.

#### Scenario: Data in place
- **WHEN** the project is created and its raw data is taken in
- **THEN** the summary's last line asks the user what they want to compare

#### Scenario: No data yet
- **WHEN** the project is created in an empty folder
- **THEN** the summary asks for the raw data first, and then invites the user to say what they want to compare
