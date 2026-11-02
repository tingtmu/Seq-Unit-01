# data/

## Purpose

Input data. `raw/` holds data exactly as received (immutable). `reference/` holds genome and annotation files. `processed/` holds corrected or derived inputs written by workflow steps.

## Conventions

- Never edit, overwrite, move, or delete files in `raw/`. Fixes are workflow steps that write to `processed/`.
- Each delivery (raw files received together) gets its own folder, `raw/<delivery>/`, with the files as received: no unzipping or renaming.
- Checksum files that came with a delivery (`*.md5`, `md5sum.txt`) are verified before the files go into `raw/`.
- Every raw file is listed in the provenance table below with its source and SHA-256 checksum, computed with any tool the shell offers.
- Each delivery is made read-only once its provenance is recorded. `raw/` itself stays writable, so a new delivery needs no permission change.
- Reference files must match the build and annotation pinned in `config/config.yaml`.
- Large files are git-ignored; this README and the provenance table are tracked.

### Adding a delivery

1. If the delivery came with checksum files, verify them where the data sits. On a mismatch, stop and fetch the files again before they go into `raw/`.
2. Put the files, as received, in a new folder `raw/<delivery>/`, named by the accession the data states, else the folder it arrived in, else the date received.
3. Record each file's provenance in the table below.
4. Make the delivery read-only.
5. Update `config/samples.tsv` from the sample metadata (and, for a count matrix, `counts:` in `config/config.yaml`).

Commands, run from the project root. To make a delivery read-only:

- `chmod -R a-w data/raw/<delivery>` (macOS, Linux, Git Bash on Windows)
- `attrib +R /S data\raw\<delivery>\*` (Windows cmd or PowerShell)

On Windows, read-only files still block overwrites, but Git Bash `rm` and PowerShell `Remove-Item -Force` can delete them, so the hard rule in `AGENTS.md` is the protection there.

To make it writable again, only to replace a broken file, and read-only again after recording the new file:

- `chmod -R u+w data/raw/<delivery>` (macOS, Linux, Git Bash on Windows)
- `attrib -R /S data\raw\<delivery>\*` (Windows cmd or PowerShell)

### Provenance

| File | Source (URL / accession / run) | Received | sha256 |
|------|--------------------------------|----------|--------|

## Current state

<!-- nerv: what data is present. -->
Scaffolded {{DATE}}; no data yet. Put raw files, as received, in `raw/<delivery>/`.

## Last major change

{{DATE}}: created by nerv-init.
