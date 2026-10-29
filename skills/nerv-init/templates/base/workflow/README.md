# workflow/

## Purpose

The pipeline that turns `data/` + `config/` into `results/`. Every result must be produced here, not by hand.

## Conventions

- Steps read parameters from `config/`; no hardcoded paths or reference versions.
- Each step declares its software environment from `envs/`.
- Raw data is read-only input; corrected data is written to `data/processed/`.

## Current state

<!-- nerv: list the implemented steps. -->
Scaffolded {{DATE}}; no steps implemented yet.

## Last major change

{{DATE}}: created by nerv-init.
