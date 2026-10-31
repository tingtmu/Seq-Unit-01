# Tasks

## 1. Environment file

- [ ] 1.1 Look up current versions on conda-forge and bioconda for `snakemake-minimal`, `pandas`, `python`, `pytest`, `r-base`, and `r-testthat`, and record them with today's date. Verify that each pinned version exists in the channel index.
- [ ] 1.2 Write failing tests in `tests/test_scaffold.py`:
  - Snakemake + Python: `envs/workflow.yaml` names snakemake, pandas, and pytest with pinned versions.
  - Plain scripts + R: it names r-base and r-testthat but not snakemake.
  - Both languages: it names pytest and testthat.
  - Project name `Mouse liver RNA`: the YAML `name:` is a valid conda name and equals the name in the README `conda activate` command.

  Verify that the new tests fail.
- [ ] 1.3 Add `templates/base/envs/workflow.yaml.tmpl` and the `ENV_NAME` and `ENV_DEPENDENCIES` variables in `scaffold.py`, built from engine and language tool tables. Verify that the 1.2 tests pass.
- [ ] 1.4 Make README Quick start step 1 name the prerequisites (conda or mamba; `bash` for plain scripts) and give the literal `conda env create -f envs/workflow.yaml` and `conda activate {{ENV_NAME}}` commands. List `workflow.yaml` in the template's `envs/README.md` "Current state", with the pin date in "Last major change". Verify with a scaffold test that asserts both commands appear in the generated `README.md`.

## 2. Smoke test per language

- [ ] 2.1 Extend `LAYERS` in `tests/test_templates.py` to include `"languages"`. Write failing tests:
  - A Python-only scaffold has `tests/test_smoke.py` and no `tests/test_smoke.R`. An R-only scaffold has the reverse.
  - Running `pytest` on the generated project's `tests/` with the repo venv collects at least one test and exits 0.
  - After `fastq_1` is removed from the generated `config/samples.tsv`, the same run fails and its output names `fastq_1`.

  Verify that the new tests fail.
- [ ] 2.2 Add the language layer to `plan()` (`templates/languages/<lang>/`, one per chosen language, after the engine layer). Add `templates/languages/python/tests/test_smoke.py` (standard library `csv`, path from `__file__`) and `templates/languages/r/tests/test_smoke.R` (base R `read.delim`, `testthat::test_path`). Verify that the 2.1 tests, `test_layer_only_contains_differences` for every layer, and the full suite pass.
- [ ] 2.3 Update the template's `tests/README.md` "Current state" to name the smoke test and say to replace it with real tests. Update `skills/nerv-init/references/interview.md` so the `engine` and `languages` rows mention `envs/workflow.yaml` and the smoke test. Widen GLOSSARY **Add-on** to cover language layers. Verify that the full suite passes.

## 3. Integration check and docs

- [ ] 3.1 By hand, outside the repo, scaffold two projects into scratch folders: Snakemake + [python, r] (the full environment and the longest Test chain) and plain scripts + python. In each, run `conda env create -f envs/workflow.yaml`, activate the environment, then run the generated Run and Test commands. Verify that every command exits 0, and record the result in the test-run notes. If conda or R is unavailable on this machine, say so and leave that part unverified.
- [ ] 3.2 Update `README.md` (the `nerv-init` row: it now also ships an environment file and a smoke test) and set the ROADMAP item "Runnable fresh project (minimal)" to done. Verify with `git diff` that both appear in the same commit as the behavior change.

## Workflow follow-up

- Run the review gate (AGENTS.md: tests, commit, fresh-context reviewer) after apply and after archive.
- `/opsx:verify`, then `/opsx:archive`.
