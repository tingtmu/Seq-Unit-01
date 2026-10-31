# Design

## Context

`scaffold.py` builds a project from three layers: `templates/base`, an optional `templates/addons/<assay>`, and `templates/engines/<engine>`. Files are rendered with `{{VAR}}` substitution. The Test command combines the engine's check (`snakemake -n`, or nothing for plain scripts) with one command per language (`pytest tests/`, `Rscript -e "testthat::test_dir('tests')"`). `workflow/rules/common.smk` imports `pandas`. The Snakemake Run command already uses `--use-conda`, so conda is already a prerequisite. `validate()` accepts any non-blank `project_name`, spaces included.

## Goals / Non-Goals

**Goals:**
- Every combination of engine and languages has passing Run and Test commands after one environment-creation command.
- The layers stay DRY, and `test_layer_only_contains_differences` checks every layer kind.

**Non-Goals:**
- Per-step environments for future rules. `envs/README.md` already says to add one per tool group.
- Checking or installing conda or bash, or running anything during scaffolding.
- Lock files (`conda-lock`, `renv.lock`).

## Decisions

**1. One base template `templates/base/envs/workflow.yaml.tmpl`, with the dependencies filled in by a variable.**
The template holds the channels (`conda-forge` and `bioconda`), `name: {{ENV_NAME}}`, and `{{ENV_DEPENDENCIES}}`. `scaffold.py` builds the dependency list from two tables:
- the engine's tools: `snakemake-minimal` and `pandas` for Snakemake, none for plain scripts;
- each language's tools: `python` and `pytest` for Python, `r-base` and `r-testthat` for R.

Alternatives:
- One file per engine. The copies would be near-identical, differing in two lines. Rejected (reviewer finding).
- One file per engine × language. Four files today. Rejected.
- One environment per language. That gives two environments, so the single Test command can't run in one shell. Rejected.

**2. One `ENV_NAME` variable for both the YAML and the README.**
`ENV_NAME` is `project_name` with every run of characters outside `[A-Za-z0-9_.-]` replaced by `-`. Both `workflow.yaml` and the Quick start activate command use it, so the two can't drift apart.

**3. A language layer for the smoke tests: `templates/languages/<lang>/`.**
`plan()` adds one layer per chosen language after the engine layer, using the existing layering code. Python ships `tests/test_smoke.py` and R ships `tests/test_smoke.R`. pytest collects only `test_*.py` and testthat runs only `^test.*\.[rR]$`, so the two files coexist. `LAYERS` in `tests/test_templates.py` gains `"languages"`. GLOSSARY's **Add-on** widens to "assay-, engine-, or language-specific".
Alternative: build the test files as strings in `scaffold.py`, the way `.gitignore` is built. Rejected, because templates are the established way to ship files.

**4. The smoke test checks the sample-sheet header with the standard library or base R only.**
Python uses `csv` with a path built from `Path(__file__)`. R uses `read.delim` with `testthat::test_path("..", "config", "samples.tsv")`. The required columns (`sample_id`, `fastq_1`) duplicate `REQUIRED_COLUMNS` in `common.smk`. That is accepted because plain-scripts projects have no `common.smk`, and the test is meant to be replaced by real tests. Smoke-test sources must not contain `{{UPPER}}` literals, because `render()` raises on unknown variables.

**5. Versions pinned exactly, and verified at apply time.**
The pins come from the current conda-forge and bioconda indexes, checked when the change is applied, not taken from memory. The date is recorded in the template's `envs/README.md` "Last major change".

**6. Quick start step 1 names its prerequisites.**
It names conda (mamba works too), and a POSIX shell (`bash`) for the plain-scripts engine, then gives `conda env create -f envs/workflow.yaml` and `conda activate {{ENV_NAME}}`. The engine-specific shell note goes in the engine's text, not in base.

## Risks / Trade-offs

- [Pinned versions go stale] → The pins are a known-good starting point. Re-checking them joins the recurring release housekeeping in ROADMAP.
- [The largest environment (Snakemake plus both languages) may not solve] → The manual check in tasks 3.1 creates exactly that environment.
- [CI can't run conda, R, or snakemake] → pytest runs the generated Python smoke test in the repo venv and checks the environment file as text. The conda create step, the R smoke test, and `snakemake -n` are checked by hand once and recorded in the test-run notes.
