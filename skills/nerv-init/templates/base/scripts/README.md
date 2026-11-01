# scripts/

## Purpose

Analysis code ({{LANGUAGES}}) called by the workflow: QC, normalization, statistics, plotting.

## Conventions

- Scripts take inputs and outputs as arguments (or from the workflow); no hardcoded paths.
- Set and record random seeds for anything stochastic.
- One script, one job. Shared helpers go in a clearly named module.
- Statistical choices (test, correction, thresholds) are stated in the script header and in this README.
- Before writing code that decides results (filters, thresholds, joins, sample-sheet checks), write a failing test first; see `tests/README.md`. Exploratory notebooks are exempt until their code moves here.

## Current state

<!-- nerv: list scripts and what they do. -->
Scaffolded {{DATE}}; no scripts yet.

## Last major change

{{DATE}}: created by nerv-init.
