# scripts/

## Purpose

Analysis code ({{LANGUAGES}}) called by the workflow: QC, normalization, statistics, plotting.

## Conventions

- Scripts take inputs and outputs as arguments (or from the workflow); no hardcoded paths.
- Set and record random seeds for anything stochastic.
- One script, one job. Shared helpers go in a clearly named module.
- Statistical choices (test, correction, thresholds) are stated in the script header and in this README.

## Current state

<!-- nerv: list scripts and what they do. -->
Scaffolded {{DATE}}; no scripts yet.

## Last major change

{{DATE}}: created by nerv-init.
