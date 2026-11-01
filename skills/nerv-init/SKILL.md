---
name: nerv-init
description: Set up a new bioinformatics sequencing project (bulk RNA-seq, scRNA-seq, or other assays) from an empty directory. Runs a short interview, then generates the folder skeleton, a concise AGENTS.md/CLAUDE.md with hard rules, per-folder READMEs, git, and a raw-data guard hook. Use when the user wants to start, bootstrap, or scaffold a new analysis project.
---

# nerv-init: bootstrap a sequencing project

NERV builds the base the Evas launch from; this skill builds the base an analysis project grows from.

## Rules

- Write nothing before the user confirms the planned tree.
- Never overwrite existing files. If the scaffold reports conflicts, show them and ask how to proceed (different directory, or the user moves the files). Do not delete or rename the user's files yourself.
- Do not add folders the user did not ask for (KISS/YAGNI).

## Flow

1. **Interview.** Ask the questions in `references/interview.md` in one message. Propose the defaults (Snakemake engine, Python, local compute, not sensitive, project question `TBD`). Assay type has no default: ask.
2. **Plan.** Build the answers JSON and run a dry run, passing the JSON on stdin. `<skill-dir>` is the folder containing this SKILL.md:
   ```
   python <skill-dir>/scripts/scaffold.py --answers - --target . --dry-run
   ```
   Use `python3` if `python` is not available. If the result's `status` is `conflict`, show its `conflicts` list and stop to ask how to proceed. If it is `planned`, there are no conflicts: show the planned top-level tree from `files`, and name the add-ons that apply (assay, engine, and language layers). Take the add-ons from your answers, using the table "How answers map to the generated project" in `references/interview.md`; do not guess them from file names.
3. **Confirm.** Wait for an explicit yes. Adjust the answers and repeat step 2 if the user changes anything.
4. **Scaffold.** Run the same command without `--dry-run`. It creates the tree, `.gitignore`, `.gitattributes` (LF line endings), `git init`, copies hooks to `.nerv/hooks/` and the doc-sync report to `.nerv/scripts/`, and installs `.claude/settings.json` and `.codex/hooks.json`.
5. **Write the prose.** Replace every `<!-- nerv: ... -->` comment with project-specific text:
   - The project question in `AGENTS.md` and `README.md` comes from the `question` answer. If it is `TBD`, write `TBD`; never invent a question.
   - `AGENTS.md`: the one-line project question. Keep the file about 60 lines and never above 200; move detail into folder READMEs and link it.
   - `README.md`: what the project answers and its status.
   - Each folder README: fill "Conventions" and "Current state" for this assay, engine, and language. Keep all four sections.
   - Do not copy folder details into `AGENTS.md`; it only points to them.
6. **Commit.** Only if the scaffold result's `git_identity` is `set`; if it is `missing`, skip this step, because `next_steps` tells the user how to set an identity and commit. Never set or invent an identity yourself.
   - List what changed: `git status --porcelain --untracked-files=all`. Compare the paths with the result's `files`. Expected extras are the installed skill copies: the `skills` folders under `.claude` and `.agents`, and `skills-lock.json`.
   - If any other path is new or changed (including changes the user had already staged), list those paths and ask whether to include them. Wait for the answer.
   - Stage and commit by explicit path, as two separate commands, where `<paths>` is the generated files, the skill copies, and any paths the user approved:
     ```
     git add -- <paths>
     git commit -m "nerv-init scaffold" -- <paths>
     ```
     The paths after `--` keep declined or already-staged paths out of the commit. If the user declines the other paths, still commit the rest.
   - If the commit fails, show git's error to the user and continue; do not retry with a different identity.
7. **Summarize.** Report the created tree, the hooks installed, and the commit (its short hash, or why there is none). Then show the user every entry of `next_steps` from the scaffold result, in order and word for word. Do not drop or shorten any of them: the first one says which safety hooks stay off in Codex until the user trusts them.

## "Other" assay

The scaffold creates only the shared skeleton. Using `assay_description`, adapt the READMEs yourself:
- `config/README.md`: the assay's key parameters (e.g. peak caller settings for ATAC-seq, variant filters for WGS) and where they live in `config/config.yaml`.
- `data/README.md`: expected raw formats and any assay-specific reference files (e.g. blacklists, known-sites VCFs).
- `scripts/README.md` and `results/README.md`: the main analysis steps and outputs.
- Add files only when the user asks or the assay cannot work without them; record any addition in that folder's "Last major change".

## Hooks installed

- `.nerv/hooks/raw_guard.py`: new files in `data/raw/` are allowed with a reminder to record provenance in `data/README.md`, however they were written; changing or deleting existing raw files asks the user (Claude Code) or is denied with instructions (Codex), and raw files changed some other way, such as by a script, are reported after the fact. Best-effort, not a security boundary.
