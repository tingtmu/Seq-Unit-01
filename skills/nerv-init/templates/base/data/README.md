# data/

## Purpose

Input data. `raw/` holds data exactly as received (immutable). `reference/` holds genome and annotation files. `processed/` holds corrected or derived inputs written by workflow steps.

## Conventions

- Never edit, overwrite, move, or delete files in `raw/`. Fixes are workflow steps that write to `processed/`. A hook asks for approval before any change to an existing raw file.
- Every raw file is listed in the provenance table below with its source and checksum (`sha256sum`).
- Reference files must match the build and annotation pinned in `config/config.yaml`.
- Large files are git-ignored; this README and the provenance table are tracked.

### Provenance

| File | Source (URL / accession / run) | Received | sha256 |
|------|--------------------------------|----------|--------|

## Current state

<!-- nerv: what data is present. -->
Scaffolded {{DATE}}; no data yet.

## Last major change

{{DATE}}: created by nerv-init.
