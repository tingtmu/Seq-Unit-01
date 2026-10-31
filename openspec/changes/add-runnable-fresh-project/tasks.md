# Tasks

## 1. Environment file per engine

- [ ] 1.1 Look up current versions on conda-forge and bioconda for `snakemake-minimal`, `pandas`, `python`, `pytest`, `r-base`, and `r-testthat`, and record them with today's date. Verify that each pinned version exists in the channel index.
- [ ] 1.2 Write failing tests in `tests/test_scaffold.py`. For Snakemake with Python, `envs/workflow.yaml` names snakemake, pandas, and pytest with pinned versions. For plain scripts with R, it names r-base and r-testthat but not snakemake. With both languages, it names pytest and testthat. The env `name:` is the project name. Verify that the new tests fail.
- [ ] 1.3 Add `templates/engines/{snakemake,scripts}/envs/workflow.yaml` and the `{{ENV_DEPENDENCIES}}` variable built from the `LANGUAGES` table in `scaffold.py`. Verify that the 1.2 tests and `test_layer_only_contains_differences` pass.
- [ ] 1.4 Make README Quick start step 1 the literal `conda env create -f envs/workflow.yaml` / `conda activate` command (mamba noted), and list `workflow.yaml` in the template's `envs/README.md` "Current state", with the pin date in "Last major change". Verify with a scaffold test that asserts the command appears in the generated `README.md`.

## 2. Smoke test per language

- [ ] 2.1 Write failing tests. A Python-only scaffold has `tests/test_smoke.py` and no `tests/test_smoke.R`. An R-only scaffold has the reverse. Running `pytest` on the generated project's `tests/` with the repo venv collects at least one test and exits 0. After removing `fastq_1` from the generated `config/samples.tsv`, the same run fails and its output names `fastq_1`. Verify that the new tests fail.
- [ ] 2.2 Add the language layer to `plan()` (`templates/languages/<lang>/`, one per chosen language, after the engine layer) and add `templates/languages/python/tests/test_smoke.py` (standard library `csv`, path from `__file__`) and `templates/languages/r/tests/test_smoke.R` (base R `read.delim`, `testthat::test_path`). Verify that the 2.1 tests and the full suite pass.
- [ ] 2.3 Update the template's `tests/README.md` "Current state" to name the smoke test and say to replace it with real tests. Update `skills/nerv-init/references/interview.md` so the `engine` and `languages` rows mention `envs/workflow.yaml` and the smoke test. Verify that the full suite passes, including `test_skill_docs.py`.

## 3. Integration check and docs

- [ ] 3.1 By hand, outside the repo: scaffold Snakemake + Python and plain scripts + R projects into scratch folders, run `conda env create -f envs/workflow.yaml`, then run the generated Run and Test commands in each. Verify that every command exits 0, and record the result in the test-run notes. If conda or R is unavailable on this machine, say so and leave the R check unverified.
- [ ] 3.2 Update `README.md` (the `nerv-init` row: it now also ships an environment file and a smoke test) and set the ROADMAP item "Runnable fresh project (minimal)" to done. Verify with `git diff` that both appear in the same commit as the behavior change.

## Workflow follow-up

- Run the review gate (AGENTS.md: tests, commit, fresh-context reviewer) after propose, after apply, and after archive.
- `/opsx:verify`, then `/opsx:archive`.
