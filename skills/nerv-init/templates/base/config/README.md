# config/

## Purpose

Everything that parameterizes a run: the sample sheet, analysis parameters, and the pinned reference genome build and annotation version.

## Conventions

- `config/config.yaml` is the single place where the reference build and annotation version are set. Code reads them from here.
- `config/samples.tsv` has one row per sample. Validate the sample sheet first: a run fails fast on missing required columns, duplicate IDs, or listed files that do not exist.
- Change parameters here, not in code. Record why a parameter changed in "Last major change".
<!-- nerv: list the sample sheet columns and what each means. -->

## Current state

<!-- nerv: which samples and parameters are configured now. -->
Scaffolded {{DATE}}; sample sheet not yet filled.

## Last major change

{{DATE}}: created by nerv-init.
