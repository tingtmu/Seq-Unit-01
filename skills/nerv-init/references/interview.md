# nerv-init interview

Ask these in one short round (group them; don't interrogate one by one). Offer the default in brackets and accept it if the user has no preference.

| # | Question | Answers key | Allowed values | Default |
|---|----------|-------------|----------------|---------|
| 1 | Project name? | `project_name` | short text | name of the target folder |
| 2 | Assay type? | `assay` | `bulk-rnaseq`, `scrnaseq`, `other` | none: must ask |
| 2b | (only if other) Describe the assay in a sentence (e.g. "ATAC-seq, paired-end, mouse"). | `assay_description` | text | none |
| 3 | Workflow engine? | `engine` | `snakemake`, `scripts` | `snakemake` |
| 4 | Analysis language(s)? | `languages` | list of `python`, `r` | `["python"]` |
| 5 | Where will it run? (laptop, lab server, Slurm HPC, cloud) | `compute` | short text | `local` |
| 6 | Does the project hold human or controlled-access data (dbGaP, EGA, patient samples)? | `sensitive` | `true` / `false` | `false` |

If the user wants Nextflow: choose `scripts`, then after scaffolding replace `workflow/run_all.sh` with a Nextflow layout and record that choice in `workflow/README.md`. No Nextflow template ships in v1.

## Answers JSON

```json
{
  "project_name": "tumor-scrna",
  "assay": "scrnaseq",
  "assay_description": "",
  "engine": "snakemake",
  "languages": ["python", "r"],
  "compute": "Slurm HPC",
  "sensitive": true
}
```

`scaffold.py` validates this and exits 2 with a message if a value is invalid. Optional `date` (YYYY-MM-DD) overrides today's date in the READMEs.

## How answers map to the generated project

| Answer | Effect |
|--------|--------|
| any | Shared skeleton: `config/ data/{raw,reference,processed}/ workflow/ scripts/ notebooks/ envs/ results/ tests/ docs/`, each with a 4-section README; `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), `README.md`; `.gitignore`; `git init`; hooks in `.nerv/hooks/` wired via `.claude/settings.json` and `.codex/hooks.json`; the doc-sync report in `.nerv/scripts/` |
| `assay: bulk-rnaseq` | Add-on: `config/design.yaml` (design formula, contrasts, thresholds); DE conventions in `config/`, `scripts/`, `data/`, `results/` READMEs |
| `assay: scrnaseq` | Add-on: `config/qc_thresholds.tsv` (per-sample QC); object format (`.h5ad`/`.rds`) conventions in `results/` and `notebooks/` READMEs; `docs/integration-log.md` for integration/batch choices |
| `assay: other` | Base only; you adapt README text to `assay_description` without adding folders |
| `engine: snakemake` | `workflow/Snakefile`, `workflow/rules/common.smk` (validates the sample sheet); run `snakemake --use-conda --cores 4`; test adds `snakemake -n`; `envs/workflow.yaml` pins snakemake and pandas; README names conda as the prerequisite |
| `engine: scripts` | `workflow/run_all.sh`; run `bash workflow/run_all.sh`; README names conda and `bash` as prerequisites |
| `languages` | Test command: `pytest tests/` for python, `testthat` for r; language named in `scripts/` and `envs/` READMEs; `envs/workflow.yaml` pins python and pytest, or r-base and r-testthat; smoke test `tests/test_smoke.py` or `tests/test_smoke.R` checks the sample-sheet columns |
| `compute` | Shown in `AGENTS.md` and `README.md`; you add scheduler notes (e.g. a Snakemake Slurm profile) to `workflow/README.md` if relevant |
| `sensitive: true` | Extra hard rules in `AGENTS.md`; `.gitignore` also excludes everything else under `data/` and all of `results/` except READMEs, plus VCFs |
