# Proposal

## Why

Starting a bioinformatics project with an AI agent today means re-typing the same structure, rules, and guardrails every time. Even then, the agent only gets context from one root README that drifts out of date. We want a reusable, agent-agnostic skill set. It should set up a sequencing project from zero with layered documentation: a short AGENTS.md that points to folder READMEs. Hooks keep those READMEs current, and the skill set adds a review process tuned to bioinformatics risks (reproducibility, provenance, statistical validity).

## What Changes

- New public skill set repo (GitHub, `tingtmu` account). Skills use Neon Genesis Evangelion names that still describe what they do:
  - **`nerv-init`**: interviews the user, then generates the project. The interview covers assay type (bulk-rnaseq, scrnaseq, or other), workflow engine (Snakemake by default), language (R/Python/both), compute setup, and whether the data is sensitive. The generated project has:
    - a shared directory skeleton plus add-ons for the chosen assay type;
    - `git init`;
    - a short `AGENTS.md` with hard rules and pointers to deeper docs, and a `CLAUDE.md` that imports it with `@AGENTS.md`;
    - a root `README.md` and a README in each main folder;
    - the hooks wired up for each supported agent.
  - **`sync-ratio`**: a skill plus a Stop hook. It finds major changes in a folder (from git diff) where that folder's README was not updated, and reminds the agent once (Boy Scout Rule). It never blocks.
  - **`magi-review`**: review at escalating levels:
    - TRIVIAL: skipped.
    - STANDARD: one reviewer applying three lenses.
    - CRITICAL: three independent seats vote:
      - MELCHIOR-1: scientific validity.
      - BALTHASAR-2: safety and hard rules.
      - CASPER-3: craftsmanship and spec.

    A 2/3 majority decides, and BALTHASAR alone can veto on hard-rule violations.
  - **Raw-data guard hook**: new files in `data/raw/` are allowed, with a reminder to record their provenance. Changes to or deletion of existing raw files need human approval. Agents that can't ask the user get a denial with instructions instead.
- Rules have two levels. Hard rules are a short list in AGENTS.md and are enforced where possible. Soft principles (the user's AI-assisted and classic SE principles) are built into the skill instructions and templates rather than listed in full.
- Install per project with `npx skills add tingtmu/Seq-Unit-01`. Copying with degit is the documented fallback. Nothing is installed globally on this machine.

## Capabilities

### New Capabilities
- `project-bootstrap`: the interview and generating the project: skeleton plus assay/engine add-ons, AGENTS.md/CLAUDE.md/README hierarchy, folder README template, git init, hook installation.
- `doc-sync`: finding major per-folder changes where the folder README was not updated, and reminding the agent without blocking (skill + hook).
- `code-review`: choosing the review level, single-pass three-lens review, three-seat voting with veto, finding format and severity tags, and the rules for handling feedback.
- `raw-data-guard`: protecting `data/raw/`: allow new files with a provenance reminder, require approval before changing or deleting existing ones.
- `skill-distribution`: how the skill set is laid out, installed per project, and made usable across agents (Claude Code, Codex) from one source.

### Modified Capabilities
<!-- none: no existing specs -->

## Impact

- New files in this repo: `skills/` (three SKILL.md files with references and templates), `hooks/` (stdlib Python scripts plus per-agent adapter configs), the repo README, and tests.
- Runtime dependencies in projects that use the skill set: Python 3 (standard library only) for the hooks, git, and optionally Node (for `npx skills`).
- External: a public GitHub repo under `tingtmu`; this repo's git config is local and does not touch the global gh/git identity.
