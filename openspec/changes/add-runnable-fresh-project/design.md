# Design

## Context

`scaffold.py` builds a project from three layers: `templates/base`, an optional `templates/addons/<assay>`, and `templates/engines/<engine>`. Files are rendered with `{{VAR}}` substitution. The Test command combines the engine's check (`snakemake -n`, or nothing for plain scripts) with one command per language (`pytest tests/`, `Rscript -e "testthat::test_dir('tests')"`). Nothing in the output depends on the languages except that command and some README text. `workflow/rules/common.smk` imports `pandas`. The Snakemake Run command already uses `--use-conda`, so conda is already a prerequisite.

## Goals / Non-Goals

**Goals:**
- Every combination of engine and languages has passing Run and Test commands after one environment-creation command.
- The layers stay DRY (`test_layer_only_contains_differences`).

**Non-Goals:**
- Per-step environments for future rules. `envs/README.md` already says to add one per tool group.
- Checking or installing conda, or running anything during scaffolding.
- Lock files (`conda-lock`, `renv.lock`).

## Decisions

**1. One `envs/workflow.yaml` per engine, with the language dependencies filled in by a variable.**
Each engine layer ships `envs/workflow.yaml` (channels `conda-forge` and `bioconda`; the Snakemake engine adds `snakemake-minimal` and `pandas`; the plain-scripts engine adds no engine tools). A new variable, `{{ENV_DEPENDENCIES}}`, is rendered from the `LANGUAGES` table: `python` and `pytest` for Python, and `r-base` and `r-testthat` for R.
Alternatives: (a) one file per engine × language combination. That makes four files today, more with each engine, and breaks DRY. (b) One environment file per language. That gives two environments to activate, so the single Test command can't run in one shell. Rejected.

**2. A language layer for the smoke tests: `templates/languages/<lang>/`.**
`plan()` adds one layer per chosen language after the engine layer, using the existing layering code. Python ships `tests/test_smoke.py` and R ships `tests/test_smoke.R`. pytest collects only `test_*.py` and testthat runs only `test*.R`, so the two files coexist without conflict.
Alternative: build the test files as strings in `scaffold.py`, the way `.gitignore` is built. Rejected, because templates are the established way to ship files and are easy to review.

**3. The smoke test checks the sample-sheet header with the standard library or base R only.**
Python uses `csv` and R uses `read.delim`, so the test needs no dependency beyond the test runner. Paths resolve from the test file's location (`Path(__file__)` in Python, `testthat::test_path()` in R), so the test passes whichever directory it is run from. The required columns (`sample_id`, `fastq_1`) duplicate `REQUIRED_COLUMNS` in `common.smk`. That is accepted because plain-scripts projects have no `common.smk`, and the test is meant to be replaced by real tests.

**4. Versions pinned exactly, and verified at apply time.**
The pins come from the current conda-forge and bioconda indexes, checked when the change is applied (the test run used snakemake 9.27.1 and pytest 9.2.0). The verification date is recorded in `envs/README.md` "Last major change" of the template. Pins are not taken from memory.

**5. Quick start step 1 becomes literal.**
`conda env create -f envs/workflow.yaml && conda activate {{PROJECT_NAME}}`. The environment `name:` field is the project name, so different projects don't collide. A note says that `mamba` works as a drop-in replacement.

## Risks / Trade-offs

- [Pinned versions go stale] → The pins are a known-good starting point. `envs/README.md` already says to record version changes. Re-checking them joins the recurring release housekeeping in ROADMAP.
- [The project name may not be a valid conda env name] → `validate()` already requires a non-blank `project_name`. Write the env name with spaces replaced by `-`. A bad name fails at `conda env create` with conda's own clear error, and the scaffold doesn't break.
- [CI can't run conda, R, or snakemake] → pytest checks the generated Python smoke test by running it in the repo venv (it uses only the standard library) and checks the environment file contents as text. The R smoke test, `snakemake -n`, and the conda create step are checked by hand once during apply and recorded in the test-run notes, following the AGENTS.md habit for behavior that pytest can't cover.
