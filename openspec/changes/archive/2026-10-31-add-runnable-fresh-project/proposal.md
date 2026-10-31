# Proposal

## Why

A freshly generated project can't run its own Run and Test commands. In the first test run (2026-10-30, findings 11 and 12), `envs/` held only a README, so neither `snakemake` nor `pytest` could be installed from the project. With the tools installed by hand, `pytest tests/` still exited 5 ("no tests ran"), which made the Test command fail. An agent told to "make the tests pass" begins by chasing a failure that the scaffold itself created. This change provides the umbilical cable: a fresh project whose commands pass on day one.

## What Changes

- Each project gets one environment file, `envs/workflow.yaml`, a conda environment with pinned versions, generated from a single template. It provides the engine's tools and the test runner for every chosen language: `pytest` for Python and `testthat` for R. For the Snakemake engine it also provides `pandas`, which `workflow/rules/common.smk` needs. Conda, and bash for plain scripts, stay prerequisites, and Quick start names them.
- Each chosen language ships one smoke test in `tests/`: `tests/test_smoke.py` for Python and `tests/test_smoke.R` for R. The test checks that `config/samples.tsv` has the required columns, so the Test command collects at least one passing test.
- README Quick start step 1 becomes a concrete command (`conda env create -f envs/workflow.yaml`, then activate it). The "Current state" sections of `envs/README.md` and `tests/README.md` list what was generated.
- Nothing else. Finding 13 (next steps for Claude Code and the first commit) belongs to the separate "First-run next steps" item. No env-check script, no extra environments, and no Run/Test commands executed during scaffolding.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `project-bootstrap`: adds a requirement that a generated project ships an environment providing its Run and Test tools, plus a smoke test so its Test command passes before any analysis code exists.

## Impact

- `skills/nerv-init/templates/base/envs/workflow.yaml.tmpl` (new)
- `skills/nerv-init/templates/languages/{python,r}/tests/test_smoke.*` (new language layer)
- `skills/nerv-init/scripts/scaffold.py`: add the language layer to `plan()` and the `ENV_NAME` and `ENV_DEPENDENCIES` variables
- `GLOSSARY.md`: **Add-on** covers language layers
- `skills/nerv-init/templates/base/README.md.tmpl`, `envs/README.md`, `tests/README.md`
- `skills/nerv-init/references/interview.md`: the answer-to-output map for `engine` and `languages`
- `tests/test_scaffold.py`, `tests/test_templates.py` (the DRY check covers the language layer)
- `README.md` (user-facing): what a generated project contains
- `ROADMAP.md`: mark the item done when it ships
- Users need conda (or mamba) to create the environment. The Snakemake Run command (`--use-conda`) already assumed this.
