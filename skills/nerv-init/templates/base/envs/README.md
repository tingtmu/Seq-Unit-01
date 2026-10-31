# envs/

## Purpose

Software environment specifications ({{LANGUAGES}}) so every step runs with pinned tool versions.

## Conventions

- One environment file per tool group (e.g. `envs/qc.yaml`), with explicit versions.
- Never rely on tools installed globally on one machine.
- When a tool version changes, note it in "Last major change".

## Current state

<!-- nerv: list environments. -->
- `workflow.yaml`: the tools the Run and Test commands call. Create it before the first run.

## Last major change

{{DATE}}: created by nerv-init; `workflow.yaml` versions pinned as current on conda-forge and bioconda on 2026-10-31.
