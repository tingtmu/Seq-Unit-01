# Tasks

## 1. Sample sheet requires only `sample_id` (templates and tests)

- [x] 1.1 In `tests/test_scaffold.py`, change `test_python_smoke_test_names_missing_column` to remove `sample_id` and assert that the failure names `sample_id`. Add `test_python_smoke_test_accepts_counts_sheet`: replace the sheet with `sample_id\tcondition\treplicate` and one row, then assert pytest exits 0 (scenario "Sample sheet for precomputed counts"). Run them and confirm they fail (red).
- [x] 1.2 Add pytests that execute the generated `workflow/rules/common.smk` source with a stub `config = {"samples": <path>}` (pandas is in the repo venv). A counts-shaped sheet passes and sets `SAMPLES`. A sheet whose `fastq_1` path does not exist raises `ValueError` naming that file. A sheet without `sample_id` raises naming `sample_id`. Run them and confirm the counts case fails (red).
- [x] 1.3 Set `REQUIRED_COLUMNS` to `{"sample_id"}` in `templates/engines/snakemake/workflow/rules/common.smk` and `templates/languages/python/tests/test_smoke.py`, and to `c("sample_id")` in `templates/languages/r/tests/test_smoke.R`. Verify: `.venv/Scripts/python -m pytest` passes (green).
- [x] 1.4 In `templates/addons/bulk-rnaseq/config/design.yaml`, set `design: ""` with the comment "fix in the analysis plan before looking at results; columns must exist in config/samples.tsv". Add a pytest that a bulk RNA-seq project's `design.yaml` has an empty formula and that neither it nor the template `samples.tsv` header contains `batch` (scenarios "Bulk RNA-seq design left open" and "No invented covariate"). Drop `batch` from the template `config/samples.tsv` header. Verify: the full suite passes.

## 2. Read-only per delivery (scaffold.py and data README)

- [x] 2.1 In `tests/test_scaffold.py`, rewrite the read-only assertions in `test_created_result_lists_next_steps`. The entry is still the last one. It has at most two sentences, names delivery folders under `data/raw/`, says the guard is best-effort and that new data goes in a new delivery folder, and contains no `chmod` or `attrib`. Add a test that the generated `data/README.md` has an "Adding a delivery" section that names `config/samples.tsv` and holds the per-delivery commands `chmod -R a-w data/raw/<delivery>`, `chmod -R u+w data/raw/<delivery>`, `attrib +R /S data\raw\<delivery>\*`, and `attrib -R /S data\raw\<delivery>\*`, each labeled with "Git Bash" or "cmd or PowerShell" in that order, and that neither the read-only entry nor the README uses "lock" as a whole word (regex `\block\b`, so "blocks" doesn't match). Run them and confirm they fail (red).
- [x] 2.2 Replace the read-only entry in `NEXT_STEPS` with the one-sentence text from design decision 5. Keep the entry order and the `identity_missing` order test intact. Verify: the next-steps tests pass.
- [x] 2.3 In `templates/base/data/README.md`:
  - **Conventions:** one folder per delivery (`raw/<delivery>/`, files as received), provider checksum files verified first, SHA-256 recorded without naming a single tool, and each delivery read-only after its provenance is recorded.
  - **"Adding a delivery":** a short subsection listing the whole intake: verify provider checksums where the data sits, put the files in a new `raw/<delivery>/`, record provenance, make it read-only, update `config/samples.tsv` (and `counts:` in `config/config.yaml`). Then the labeled commands to make a delivery read-only and writable again, saying that in Codex the user runs the replacement because the guard denies it.
  - **Current state:** say no data yet, with a pointer to put raw files in `raw/<delivery>/`.
  - Keep the four sections and the provenance table.
  - Verify: the new test from 2.1 and `test_folder_readme_has_four_sections_in_order` pass, and `grep -n sha256sum skills/nerv-init/templates` finds nothing.
- [x] 2.4 In `templates/addons/bulk-rnaseq/data/README.md.append`, add one line: a precomputed count matrix stays in its delivery folder, and its path goes in `config/config.yaml` under `counts:`. Verify: `test_layer_only_contains_differences` passes.
- [x] 2.5 (Found in apply review.) `insert_conventions` in `scaffold.py` puts add-on lines at the end of the Conventions bullets, before any `###` subsection, so the bulk RNA-seq data notes no longer land under the Provenance table. Test: `test_addon_conventions_land_before_subsections`.

## 3. nerv-init skill prose (SKILL.md and interview.md)

- [x] 3.1 In `skills/nerv-init/SKILL.md`:
  - **Description:** works in an empty folder or one that already holds raw data. Keep the first sentence free of EVA terms.
  - **Rules:** "move only the paths the confirmed plan lists; never overwrite".
  - **New first step, Explore:** two levels deep, skipping `.git` and the skill copies; file names, sizes, and provider readmes only, with no data or metadata table opened, not even a header row, before the user confirms the data is not sensitive; classify each item as raw, reference, or other.
  - **Interview:** propose the answers the files settle, say which files settled them, and ask only the rest. The assay is asked only when the files don't show it.
  - **Plan:** an annotated top-level tree (folder plus one-line purpose, moves as `from → to`, add-ons), with the full file list only on request.
  - Verify: `tests/test_skill_docs.py` passes (frontmatter function-first, relays every next step, no `/hooks`, self-contained).
- [x] 3.2 In `SKILL.md`, add a "Data intake" step between Scaffold and Write the prose:
  - verify provider checksum files where the data sits, before moving or copying, and stop that delivery on a mismatch;
  - move in-folder raw data and copy outside data into `data/raw/<delivery>/`, naming it by accession, then arrival folder, then date; references go to `data/reference/`;
  - remove source folders the move left empty with a non-recursive `rmdir` only;
  - ask before a large copy, and offer a move only when the source is on the project's volume;
  - record SHA-256, source ("supplied locally" plus the original path, naming an accession only if the data states it), and the date in `data/README.md`;
  - make the delivery read-only with the command for the agent's shell;
  - fill `config/samples.tsv` from the metadata (only supported columns, FASTQ columns only for reads) and add `counts:` to `config/config.yaml` for a count matrix;
  - sensitive data: still place, checksum, and make read-only, but read no data or metadata contents, leave the sample sheet as the template, and before committing say that `data/README.md` lists raw file names and ask whether to commit it;
  - replacing a file in a read-only delivery: ask first; in Codex, give the user the commands, because the guard denies it.
  
  In the empty-folder case, the Summarize step asks the user to put raw files in `data/raw/<delivery>/` or give a path, and the agent runs the same intake when they reply. Make the Commit step's expected paths include the filled `data/README.md`, `config/samples.tsv`, and `config/config.yaml`. Verify: `tests/test_skill_docs.py` passes, the step reads correctly for the yeast folder, an empty folder, a provider MD5 mismatch, and sensitive data, and the skill says "read-only", not "lock".
- [x] 3.3 In `skills/nerv-init/references/interview.md`, note that answers settled by the files are proposed, not asked, and that the assay has no default only when the files don't show it. Add input type (reads or precomputed counts) to the "How answers map" table as agent-only: it shapes the sample sheet and `counts:` and is not a scaffold key. Verify: `scaffold.py` still rejects unknown keys only as before (`test_invalid_answers_rejected` passes).

## 4. Glossary, README, spec purpose, roadmap

- [x] 4.1 Use the domain-modeling skill to add **Data intake** and **Delivery** to `GLOSSARY.md`. Delivery: _Avoid_ "batch", because the glossary uses it in the statistical sense. Update the **Next steps** entry if its example changes. Verify by reading each term against the spec.
- [x] 4.2 `README.md`: the `nerv-init` row and install step 2 say it explores the folder first, takes in raw data it finds (or asks for it), records provenance, and makes each delivery read-only. Verify by reading against the spec.
- [x] 4.3 Edit the Purpose of `openspec/specs/project-bootstrap/spec.md` directly: from an empty folder *or one that already holds raw data*, and drop the stale "sync reminder" mention. Verify: `openspec validate --specs --strict` passes.
- [x] 4.4 `ROADMAP.md`: set "Data intake" and "Sample sheet fits the data" to `done`. Add a watch item for the next test run, which reruns `../yeast-bioinfo` from a fresh copy and an empty folder. It checks that the agent explores before asking, proposes answers with their evidence, shows the annotated plan, moves only the listed paths, records provenance, makes the delivery read-only, invents no columns, asks for data in the empty folder, and, with sensitive data, opens no table and asks before committing `data/README.md`.

## 5. Integration check

- [x] 5.1 Run the full suite (`.venv/Scripts/python -m pytest`), then `openspec validate add-data-intake --strict`. Both pass.

## Workflow follow-up

- Run the AGENTS.md review gate after propose, after apply, and after archive: tests, a commit, a fresh-context reviewer, and fixes.
- `/opsx:verify`, then `/opsx:archive`. Don't push unless asked.
- Then apply the follow-up change "Shorter next steps, identity set by the agent". It edits the same `NEXT_STEPS`, so apply it after this one.
