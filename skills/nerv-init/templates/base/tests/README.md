# tests/

## Purpose

Tests for analysis scripts and the workflow.

## Conventions

- Run with: `{{TEST_COMMAND}}`
- Use tiny synthetic inputs, built inline or checked into `tests/data/`; never real patient data.
- Test the logic that decides results: filters, thresholds, statistics.
- Don't test styling (colours, labels, themes); test the data a plot or report draws.

## Current state

<!-- nerv: list what is covered. -->
- `test_smoke.*` (one per language): checks that `config/samples.tsv` has its required columns, so the Test command passes on a fresh project. Replace it with real tests.

## Last major change

{{DATE}}: created by nerv-init.
