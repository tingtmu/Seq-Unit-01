# Proposal

## Why

In the yeast test run (2026-11-01, Codex, `../yeast-bioinfo`), `nerv-init` ran in a folder that already held `input_data/GSE141713/`: a gzipped UMI count matrix, a sample annotation, and the GEO readme. The skill never looked at those files. The user moved them into `data/raw/` and hashed them by hand. The generated sample sheet asked for FASTQ columns that a counts dataset doesn't have, and the design formula named a `batch` column the study doesn't have. Most analyses start after the data has been downloaded, so treating every target as an empty folder adds friction at the very first step. The skill should look first, put the data where the project expects it, and record its provenance. It should ask the user only what the files can't answer.

## What Changes

- **Explore before asking.** Before the interview, `nerv-init` looks at the target folder: file names, sizes, and provider readmes. It proposes the interview answers these settle, such as the assay and whether the inputs are reads or precomputed counts, and asks only the rest. Until the user has said the data is not sensitive, it opens no data or metadata table, not even a header row, because a wide table's header can hold sample identifiers.
- **Annotated plan.** The plan shown before the user's yes is an annotated top-level tree: each folder with a one-line purpose, each data move written as `from → to`, and the add-ons. The flat dry-run file list is not shown unless asked for. The explicit yes stays.
- **Data intake.** After scaffolding and before the commit, the agent:
  - verifies any checksum files that came with the data, at the source, before moving anything;
  - moves raw data found inside the project folder into `data/raw/<delivery>/`, and copies raw data the user points to outside it;
  - puts reference FASTA and annotation files in `data/reference/`;
  - records each file's SHA-256 and source in `data/README.md`;
  - makes that delivery folder read-only.
  `data/raw/` itself stays writable, so a new delivery needs no permission change. In an empty folder, the agent asks the user to put the raw files in `data/raw/<delivery>/` or give their path, and runs the same intake when they say the data is in.
- **The sample sheet fits the data.** The agent builds `config/samples.tsv` from the discovered sample metadata and never invents a column. The smoke tests and the Snakemake sample-sheet check require only `sample_id`; any `fastq_*` columns present are still checked for existing files. The bulk RNA-seq `design.yaml` no longer ships `~ batch + condition`. The formula stays empty until the analysis plan fixes it.
- **Read-only per delivery.** The read-only next step becomes one short sentence. It says the agent makes each delivery read-only after recording its provenance, and that new data goes in a new delivery folder. The chmod and attrib command list goes away.
- **Sensitive data.** When the data is declared sensitive, intake still moves, checksums, and makes each delivery read-only, but never reads data or metadata contents and doesn't fill the sample sheet. Before committing, the agent asks whether to commit `data/README.md`, since it lists raw file names.
- **Generated `data/README.md`.** One folder per delivery, a tool-neutral checksum wording instead of `sha256sum`, and an "Adding a delivery" section that lists the whole intake (verify, place, record, make read-only, update the sample sheet) with the read-only commands, so later sessions follow the same intake without the skill.
- `nerv-init` description and rules: it works in an empty folder or one that already holds raw data. It moves only the data paths the confirmed plan lists, removes only source folders those moves left empty, and still never overwrites.
- `GLOSSARY.md`: new terms **Data intake** and **Delivery**. The word "batch" is avoided because the glossary already uses it in the statistical sense.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-bootstrap`:
  - "Interview before generation": explore first, propose the answers the files settle, show an annotated plan.
  - "Refuse to overwrite an existing project": moving the paths listed in the plan is allowed, and overwriting still is not.
  - "Fresh project passes its own Test command": only `sample_id` is required.
  - "Read-only raw data recommended after scaffolding": per delivery, and one sentence.
  - New requirements: "Explore the target before asking", "Data intake after scaffolding", "Provenance recorded at intake", "Each delivery made read-only after intake", "Raw data requested in an empty folder", "Sensitive data at intake", and "Sample sheet built from the data".

## Impact

- `skills/nerv-init/SKILL.md`: description, rules, a new explore step, the annotated plan, and a data-intake step between scaffolding and the prose.
- `skills/nerv-init/references/interview.md`: assay and the other answers can be proposed from the files; the input type (reads or counts) is noted.
- `skills/nerv-init/scripts/scaffold.py`: the read-only entry in `NEXT_STEPS`.
- Templates:
  - `templates/base/data/README.md` (deliveries, checksums, the next delivery);
  - `templates/addons/bulk-rnaseq/config/design.yaml` (empty formula);
  - `templates/languages/python/tests/test_smoke.py`, `templates/languages/r/tests/test_smoke.R`, and `templates/engines/snakemake/workflow/rules/common.smk` (require `sample_id` only).
- Tests: `tests/test_scaffold.py` (the missing-column test uses `sample_id`, a counts-shaped sheet passes, the new read-only step text) and `tests/test_templates.py` if a template check is needed.
- `GLOSSARY.md`, `README.md` (the `nerv-init` row and install step 2).
- No hook changes. Moving files into `data/raw/` is already allowed by `raw_guard.py`, and `chmod` or `attrib` changes neither size nor modification time, so the raw snapshot reports nothing.
- Out of scope and left to a follow-up change: merging the Codex and Claude Code next steps, the agent setting a missing git identity, and dropping the "fill `config/samples.tsv`" next step.
