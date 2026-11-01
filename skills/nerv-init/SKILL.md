---
name: nerv-init
description: Set up a new bioinformatics sequencing project (bulk RNA-seq, scRNA-seq, or other assays) in an empty folder or one that already holds raw data. Looks at the folder first, runs a short interview, then generates the folder skeleton, a concise AGENTS.md/CLAUDE.md with hard rules, per-folder READMEs, git, and a raw-data guard hook, and takes in the raw data with its provenance. Use when the user wants to start, bootstrap, or scaffold a new analysis project.
---

# nerv-init: bootstrap a sequencing project

NERV builds the base the Evas launch from; this skill builds the base an analysis project grows from.

## Rules

- Write nothing before the user confirms the planned tree.
- Never overwrite existing files. If the scaffold reports conflicts, show them and ask how to proceed (different directory, or the user moves the files).
- Move only the data paths the confirmed plan lists, and remove only source folders those moves left empty. Do not move, rename, or delete any other user file.
- Do not add folders the user did not ask for (KISS/YAGNI).

## Flow

1. **Explore.** List the target two levels deep, skipping `.git` and the installed skill copies (`.claude/skills`, `.agents`, `skills-lock.json`). Look at file names and sizes, and read provider readmes (GEO, ENA, or sequencing-core notes). Until the user has said the data is not sensitive, open no data or metadata table, not even its header row: a wide table's header can hold sample identifiers. Classify each item as raw data, a reference (genome FASTA, annotation GTF/GFF), or other. Other files stay where they are. A top-level `data/` (or any skeleton folder) is a conflict the dry run reports; ask the user to rename or move it first.
2. **Interview.** Ask the questions in `references/interview.md` in one message. First propose the answers the files settle, such as the assay and whether the inputs are reads or precomputed counts, and say which files settled each one. Ask only the rest, proposing the defaults (Snakemake engine, Python, local compute, not sensitive, project question `TBD`). Ask the assay when the files don't show it; never guess it.
3. **Plan.** Build the answers JSON and run a dry run, passing the JSON on stdin. `<skill-dir>` is the folder containing this SKILL.md:
   ```
   python <skill-dir>/scripts/scaffold.py --answers - --target . --dry-run
   ```
   Use `python3` if `python` is not available. If the result's `status` is `conflict`, show its `conflicts` list and stop to ask how to proceed. If it is `planned`, show an annotated top-level tree:
   - each top-level folder from `files`, with a one-line purpose;
   - each data move or copy as `from → to`, such as `input_data/GSE141713/ → data/raw/GSE141713/`, and reference files going to `data/reference/`;
   - the add-ons that apply (assay, engine, and language layers). Take them from your answers, using the table "How answers map to the generated project" in `references/interview.md`; do not guess them from file names.

   Show the full file list only if the user asks for it.
4. **Confirm.** Wait for an explicit yes. Adjust the answers and repeat step 3 if the user changes anything.
5. **Scaffold.** Run the same command without `--dry-run`. It creates the tree, `.gitignore`, `.gitattributes` (LF line endings), `git init`, copies hooks to `.nerv/hooks/` and the doc-sync report to `.nerv/scripts/`, and installs `.claude/settings.json` and `.codex/hooks.json`.
6. **Data intake.** For each delivery (raw files received together) in the confirmed plan:
   - **Verify provider checksums first.** If the delivery has checksum files (`*.md5`, `md5sum.txt`, `MD5.txt`, `*.sha256`), verify them where the data sits, before moving or copying. On a mismatch, stop this delivery: name the mismatched files and leave them outside `data/raw/`.
   - **Place it.** Folder name: the accession the data's own files state (`GSE141713`), else the folder it arrived in, else today's date. Move raw data found inside the project folder into `data/raw/<delivery>/`; copy raw data the user points to outside it, leave the original in place, and check each copy's SHA-256 against its source. Files stay as received: no unzipping or renaming. References go to `data/reference/`.
   - **Large copies.** If a copy would take long or use a lot of disk space, ask first. Offer a move instead only when the source is on the project's volume, where a move is a rename; never move data off another volume or a shared drive.
   - **Clean up.** Remove a source folder only if the moves left it empty, with a non-recursive remove (`rmdir`); never `rm -r` or `Remove-Item -Recurse`.
   - **Record provenance** in the table in `data/README.md`: each file's path, SHA-256 (any tool the shell offers; long hashes may run in the background), the date received, and its source. Write "supplied locally" plus the original path; name an accession only if the data states it, and never claim a download URL you did not use.
   - **Make the delivery read-only** with the command for your shell, from `data/README.md` ("Adding a delivery"). Leave `data/raw/` itself writable.
   - **Sample sheet** (not for sensitive data). Rewrite `config/samples.tsv` from the sample metadata: one row per sample, a `sample_id` column, and only columns the metadata supports. Never invent one, such as `batch`. Add FASTQ columns (`fastq_1`, `fastq_2`, paths under `data/raw/<delivery>/`) only for reads. For a count matrix, add `counts: <path>` to `config/config.yaml`.
   - **Sensitive data.** Still verify, place, record checksums, and make the delivery read-only, but read no data or metadata contents and leave `config/samples.tsv` as the template for the user to fill.
   - **Replacing a file later** in a read-only delivery: ask first, make only that delivery writable, and make it read-only again after recording the new file. In Codex the raw-data guard denies the replacement, so give the user the commands instead.

   If exploration found no raw data, skip this step; step 9 asks for the data.
7. **Write the prose.** Replace every `<!-- nerv: ... -->` comment with project-specific text:
   - The project question in `AGENTS.md` and `README.md` comes from the `question` answer. If it is `TBD`, write `TBD`; never invent a question.
   - `AGENTS.md`: the one-line project question. Keep the file about 60 lines and never above 200; move detail into folder READMEs and link it.
   - `README.md`: what the project answers and its status.
   - Each folder README: fill "Conventions" and "Current state" for this assay, engine, and language, describing the data actually present. Keep all four sections.
   - Do not copy folder details into `AGENTS.md`; it only points to them.
8. **Commit.** Only if the scaffold result's `git_identity` is `set`; if it is `missing`, skip this step, because `next_steps` tells the user how to set an identity and commit. Never set or invent an identity yourself.
   - List what changed: `git status --porcelain --untracked-files=all`. Compare the paths with the result's `files`; the generated files include `data/README.md`, `config/samples.tsv`, and `config/config.yaml` as intake filled them. Expected extras are the installed skill copies: the `skills` folders under `.claude` and `.agents`, and `skills-lock.json`.
   - If any other path is new or changed (including changes the user had already staged), list those paths and ask whether to include them. Wait for the answer.
   - Stage and commit by explicit path, as two separate commands, where `<paths>` is the generated files, the skill copies that `git status` listed (leave out any that don't exist, or `git add` fails), and any paths the user approved:
     ```
     git add -- <paths>
     git commit -m "nerv-init scaffold" -- <paths>
     ```
     The paths after `--` keep declined or already-staged paths out of the commit. If the user declines the other paths, still commit the rest.
   - Sensitive data: before committing, say that `data/README.md` lists the raw file names, which can be identifiers, and ask whether to commit it. If the user declines, leave it out of `<paths>`.
   - If `git add` or `git commit` fails, show git's error to the user and continue; do not retry with a different identity.
9. **Summarize.** Report the created tree, the hooks installed, the deliveries taken in and made read-only, and the commit (its short hash, or why there is none). If no raw data was found, ask the user to put the raw files, as received, in `data/raw/<delivery>/` or give their path; when they say the data is in, run step 6 for it, then commit the updated `data/README.md`, `config/samples.tsv`, and `config/config.yaml` as in step 8. Then show the user every entry of `next_steps` from the scaffold result, in order and word for word. Do not drop or shorten any of them: the first one says which safety hooks stay off in Codex until the user trusts them.

## "Other" assay

The scaffold creates only the shared skeleton. Using `assay_description`, adapt the READMEs yourself:
- `config/README.md`: the assay's key parameters (e.g. peak caller settings for ATAC-seq, variant filters for WGS) and where they live in `config/config.yaml`.
- `data/README.md`: expected raw formats and any assay-specific reference files (e.g. blacklists, known-sites VCFs).
- `scripts/README.md` and `results/README.md`: the main analysis steps and outputs.
- Add files only when the user asks or the assay cannot work without them; record any addition in that folder's "Last major change".

## Hooks installed

- `.nerv/hooks/raw_guard.py`: new files in `data/raw/` are allowed with a reminder to record provenance in `data/README.md`, however they were written; changing or deleting existing raw files asks the user (Claude Code) or is denied with instructions (Codex), and raw files changed some other way, such as by a script, are reported after the fact. Best-effort, not a security boundary.
