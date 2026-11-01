# Design

## Context

See proposal.md (Why). Constraints that shape the approach:

- **Hooks are frozen** (`SCOPE.md`). `raw_guard.py` must keep working unchanged. A check of its `check_simple`: moving or copying *into* `data/raw/` is not flagged, because only sources inside raw, or a destination that is an existing raw *file*, count. `chmod` and `attrib` are in no command list, and they change neither size nor modification time, so the raw snapshot reports nothing. A move into raw does trigger the PostToolUse provenance reminder, which the intake step answers anyway.
- **Prose before code** (admission bar 4) and **HUD, not Dummy Plug**. The agent already knows how to list files, read a gzipped header, hash a file, and map columns. The skill only needs to tell it *when* to do these things and *where* the results go.
- **Each skill folder is self-contained** (hard rule 1). Intake guidance lives in `skills/nerv-init/` and in the generated `data/README.md`, never in another skill.
- The smoke tests (`test_smoke.py`, `test_smoke.R`) and `common.smk` hard-code `{"sample_id", "fastq_1"}`. `tests/test_scaffold.py::test_python_smoke_test_names_missing_column` pins `fastq_1`.
- `.gitignore` already ignores `data/raw/*`, so the deliveries never enter git; the provenance table in `data/README.md` does.

## Goals / Non-Goals

**Goals:**
- One user "yes" sets up a folder that already holds data: the skeleton, the data in place, provenance, a read-only delivery, a sample sheet, and the commit.
- The same intake works later, in a new session, without `nerv-init`: the generated `data/README.md` describes it.

**Non-Goals:**
- Adopting a folder that already has its own `README.md`, `scripts/`, or `data/`. The existing conflict flow still applies (ROADMAP: "a way to add an add-on to an existing generated project" stays deferred).
- Downloading data from GEO, SRA, or ENA.
- Inferring biology (condition labels, covariates) beyond what the metadata columns state.
- Next-step consolidation and git identity. Those belong to the follow-up change (ROADMAP "Shorter next steps, identity set by the agent").

## Decisions

### 1. Intake is SKILL.md prose, not a script
The new flow in `SKILL.md`:
- **Step 1, Explore.** List the target, two levels deep, skipping `.git` and the installed skill copies. Read provider readmes, but open no data or metadata table before the user confirms the data is not sensitive. Classify each item as raw data, a reference, or other.
- **Interview, now step 2.** Propose the settled answers and ask only the rest.
- **Plan.** An annotated tree, with moves as `from → to`.
- **Intake, a new step after Scaffold.** Verify provider checksums at the source, move or copy, record SHA-256, make the delivery read-only, and fill the sample sheet and the count-matrix path (not for sensitive data).
- Prose, commit, summary as before. In an empty folder, the summary asks for the data.

*Alternatives:* a `discover.py` format sniffer, or a `scaffold.py --adopt` mode that returns migration actions in the dry run. Both were rejected. They put file-format knowledge in code that needs tests and upkeep, the agent already reads formats better than a sniffer, and neither is needed until prose has failed (bar 4).

### 2. Order: scaffold → intake → prose → commit
- **After scaffold,** so `data/raw/` and `data/README.md` exist to receive the data and the provenance.
- **Before the prose,** so the "Current state" sections describe the data actually present.
- **Before the commit,** so the first commit contains the filled provenance table and sample sheet.

### 3. Move inside, copy outside
- **Data already in the project folder is moved.** On the same volume, a move is a rename: instant, no doubled disk use, and no second "original" that can drift.
- **Data the user points to elsewhere is copied,** with its checksum compared to the source, and the original is left alone. The user may still want it there (a lab share, a downloads folder). A large copy asks first. It offers a move instead only when the source is on the project's volume, where a move is a rename. Across volumes a move is a copy plus a delete: no faster, it would delete the original from a lab share, and PowerShell `Move-Item` can't move a folder across volumes at all.
- Source folders left empty by a move are removed with a non-recursive remove (`rmdir`), never `rm -r` or `Remove-Item -Recurse`, so a folder that still holds anything stays. Other user files stay where they are.

### 4. A delivery is the unit of raw data
- **Folder name:** the accession the data's own files state (`GSE141713`). Otherwise the folder name it arrived in. Otherwise the receive date (`2026-11-01`).
- **Files stay as received,** with no unzipping or renaming.
- **Why a new term:** `GLOSSARY.md` gains **Delivery** ("raw files received together, in their own `data/raw/<delivery>/` folder") and **Data intake**. "Batch" is avoided, because the glossary already uses it in the statistical sense (batch confounded with condition).

### 5. Read-only per delivery; the commands live in `data/README.md`
- **What becomes read-only:** the agent runs, for its own shell, `chmod -R a-w data/raw/<delivery>` (macOS, Linux, Git Bash) or `attrib +R /S data\raw\<delivery>\*` (cmd or PowerShell). The commands that make it writable again are `chmod -R u+w data/raw/<delivery>` and `attrib -R /S data\raw\<delivery>\*`, with `/S` so files in subfolders are included.
- **Vocabulary:** the glossary lists "lock" under _Avoid_ for the raw-data guard, so the skill and templates say "read-only" and "writable again".
- **What stays open:** `data/raw/` itself, so a new delivery is just a new folder.
- **Where the commands are documented:** the generated `data/README.md` gains a short "Adding a delivery" section. It lists the whole intake (verify provider checksums, a new delivery folder, record provenance, make it read-only, update `config/samples.tsv` and `counts:`) and these commands, labeled by shell. The section is the HUD for later sessions, when `nerv-init` is no longer loaded.
- **Replacing a file in Codex:** the raw-data guard denies overwriting an existing raw file in Codex (it can't ask), so there the agent gives the user the commands to make the delivery writable, replace the file, and make it read-only again.
- **Next step:** the read-only entry in `NEXT_STEPS` shrinks to: "Each delivery in `data/raw/` is made read-only once its provenance is recorded, because the raw-data guard is best-effort; put new data in a new delivery folder (`data/README.md` has the commands)."
- *Alternative:* making all of `data/raw/` read-only, as today. Rejected: every new delivery would need two permission changes, the friction the user objected to.

### 6. Checksums: provider files first, at the source, then SHA-256 by any tool
- If the delivery has MD5 or SHA files (`*.md5`, `md5sum.txt`, `MD5.txt`, common from sequencing cores and ENA), the agent verifies them where the data sits, before moving or copying. A mismatch stops that delivery's intake with the files still outside `data/raw/`. A corrupt file is never recorded as raw data, and re-fetching it never needs to overwrite a raw file, which the guard would deny in Codex.
- SHA-256 is then computed with whatever the shell offers. Long hashes may run in the background.
- The template stops naming `sha256sum`, which doesn't exist in PowerShell; the hook's reminder already gives the OS-specific command.

### 7. The sample sheet requires only `sample_id`
- **The checks:** `common.smk`, `test_smoke.py`, and `test_smoke.R` require `{"sample_id"}`. `common.smk` keeps checking files in whatever `fastq_*` columns exist (already its behavior).
- **The template:** `config/samples.tsv` keeps its FASTQ-shaped header for the empty-folder case. When metadata is found, the agent rewrites it.
- **Count matrices:** a precomputed matrix's path goes in `config/config.yaml` under a `counts:` key, added by the agent only when one exists, so the template doesn't grow a key most projects won't use.
- **Design formula:** `design.yaml` ships `design: ""`, with the comment "fix in the analysis plan before looking at results; columns must exist in config/samples.tsv".
- **Testing `common.smk`:** a pytest runs its source with a stub `config` dict (pandas is in the repo venv), covering the counts-shaped sheet and the missing-FASTQ case without installing Snakemake.

### 8. Sensitive data: no table contents before the answer, and none at all if sensitive
- Exploration happens before the sensitivity answer, so it reads only file names, sizes, and provider readmes. Header rows are excluded: a wide count matrix's header is its sample IDs, and a VCF `#CHROM` line lists the samples, either of which may be a patient identifier.
- When the data is sensitive, intake still places, checksums, and makes each delivery read-only, but never reads data or metadata contents, so no sample-level value enters the prompt (the generated sensitive hard rule). The sample sheet stays the template for the user to fill.
- In sensitive mode, `.gitignore` still tracks `data/README.md` and `config/samples.tsv` (`test_sensitive_adds_rules_and_ignores`). Raw file names can be identifiers, so the agent asks before committing `data/README.md`. The `.gitignore` itself doesn't change: tracking the provenance table is the default the user can decline.

## Risks / Trade-offs

- **The agent classifies a non-raw file as raw, or misses one.** → Every move is listed in the plan the user confirms, and other files stay in place.
- **A read-only delivery confuses a later tool or a user,** for example `git clean`, deleting the project, or a tool that writes an index beside the reads. → `data/README.md` documents making it writable again. Indexes already belong in `data/reference/` by convention. The summary says the delivery is read-only.
- **On Windows, `chmod` in Git Bash only sets the read-only attribute on files.** → It matches the existing spec labels. The folder itself stays creatable, which is what we want.
- **Agent behavior is not pytested** (SCOPE: no prose-grepping tests). → The behavior scenarios (explore, propose answers, annotated plan, intake, empty-folder request, no invented columns) are checked in the next test run, which reruns the yeast folder and an empty folder, and recorded in ROADMAP as a watch item.
- **The provenance reminder fires during intake.** → Expected and harmless: the agent is recording provenance in the same step.

## Migration Plan

Existing generated projects are unaffected: their `common.smk` and smoke tests keep requiring `fastq_1` until the user edits them. No rollback is needed beyond reverting the commit.
