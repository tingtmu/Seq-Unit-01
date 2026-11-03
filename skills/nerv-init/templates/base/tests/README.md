# tests/

## Purpose

Tests for analysis scripts and the workflow.

## Conventions

- Run with: `{{TEST_COMMAND}}`
- Use tiny synthetic inputs, built inline or checked into `tests/data/`; never real patient data.
- For logic that decides results, use tiny synthetic inputs with explicit expected outputs. Include negative or boundary cases that distinguish the intended rule from a plausible wrong implementation.
- Don't test styling (colours, labels, themes); test the data a plot or report draws.

## Current state

<!-- nerv: list what is covered. -->
- `test_smoke.*` (one per language): checks that `config/samples.tsv` has its required columns, so the Test command passes on a fresh project. Replace it with real tests.

## Last major change

{{DATE}}: created by nerv-init.
