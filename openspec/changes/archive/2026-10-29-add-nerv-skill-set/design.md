# Design

## Context

This repo (`Seq-Unit-01`) is greenfield. It contains only OpenSpec tooling, in `.claude/` and `.agents/`, which shows the user works with several agents. The skill set built here is published publicly under the `tingtmu` GitHub account and installed into individual projects; nothing is installed globally. See proposal.md for motivation and the specs for required behavior.

Prior art reviewed: addyosmani/agent-skills, obra/superpowers, and tingtmu/review-slices. None of them uses majority voting. superpowers v6.0.0 (PR #1717) merged two per-task reviewers into one because the number of dispatches drove cost: about half the spend was coordination, and the extra reviewer re-read the same diff. That finding shapes the escalating-level review design.

## Goals / Non-Goals

**Goals:**
- Each skill works on its own once copied into a project. No runtime dependency on this repo.
- One hook implementation shared by every supported agent.
- The parts that can be built deterministically (folder tree, hook wiring, .gitignore) are built by a script and can be tested. The parts that depend on judgment (README prose, AGENTS.md tailoring) are written by the agent.

**Non-Goals:**
- No templates for assays beyond bulk-rnaseq and scrnaseq in v1. "Other" adapts the shared skeleton.
- Shipping a Nextflow layout in v1 is not a goal. The interview offers Snakemake or plain scripts; for Nextflow, the agent adapts `workflow/` and records that choice in its README.
- No per-project configuration of review levels, beyond what the default table covers.
- No global installation, and no publishing to a skills marketplace beyond the GitHub repo.
- The raw-data guard is not a security boundary.

## Decisions

### D1. Repo layout: one folder per self-contained skill

```
skills/
  nerv-init/
    SKILL.md
    references/interview.md        questions, defaults, how answers map to add-ons
    scripts/scaffold.py            deterministic tree, gitignore, git init, hook install
    templates/
      base/                        shared skeleton + README templates (4-section)
      addons/bulk-rnaseq/  addons/scrnaseq/
      engines/snakemake/   engines/scripts/
      AGENTS.md.tmpl  CLAUDE.md  README.md.tmpl
    hooks/                         canonical hook scripts + per-agent adapters
      sync_ratio.py  raw_guard.py
      adapters/claude-settings.json  adapters/codex-hooks.json
  sync-ratio/
    SKILL.md                       on-demand review; calls the project copy of sync_ratio.py
  magi-review/
    SKILL.md
    references/levels.md  seat-briefs.md  receiving-feedback.md
tests/                             pytest for scaffold.py and hook scripts
README.md  LICENSE
```
- **Why:** The `npx skills` CLI installs whole skill folders. If a skill depends on a sibling skill, it breaks when installed alone (spec: Self-contained skills).
- **Alternative rejected:** a top-level `hooks/` directory shared by all skills. It is cleaner in this repo but fails when a skill is installed on its own.

### D2. Hooks are copied into the project at bootstrap

`scaffold.py` copies the hook scripts to `<project>/.nerv/hooks/` and writes the adapter configs: `.claude/settings.json` and `.codex/hooks.json`. Each adapter points to `.nerv/hooks/*.py`. The `sync-ratio` skill runs that same project copy.

- **Why:** Hooks must keep working even if the skill folder is removed or updated, and the project should own the hook version it was created with.
- **Alternative rejected:** pointing hooks at the installed skill folder. Those paths differ between agents and install methods.

### D3. Hybrid generation: script for structure, agent for prose

- `scaffold.py` takes the interview answers as JSON and does the mechanical work:
  - creates the folders;
  - copies the template READMEs and hooks;
  - writes the `.gitignore`;
  - runs `git init`;
  - refuses to overwrite and lists any conflicts.
- The agent then fills in the template placeholders and adapts the text for the chosen assay and engine. For an "other" assay, the agent writes that content itself.
- **Why:** The overwrite refusal and the shape of the tree can be tested. README text depends on the project and benefits from the agent's judgment.
- **Alternative rejected:** agent-only generation. It is not reproducible and the overwrite rule can't be tested.
- **Alternative rejected:** a full template engine such as cookiecutter. It adds a dependency and is more than v1 needs.

### D4. AGENTS.md: about 60 lines recommended, 200-line hard ceiling

- **Recommended size:** about 60 lines. The template aims for this.
- **Hard ceiling:** 150-200 lines. Growth past the recommended size is allowed when the project needs it.
- **Over the ceiling:** content should move into folder READMEs or `docs/`, and AGENTS.md keeps a path pointer to it.
- Only the 200-line ceiling is enforced.

- AGENTS.md contains three things:
  - the hard rules;
  - the run and test commands;
  - a table that maps each area to its doc path.
- Soft principles are not listed in AGENTS.md. Instead they are built into the skills and templates:
  - Planning-first and small slices: the interview shows the plan and asks for confirmation before generating.
  - Zero-trust review: magi-review.
  - Fail fast: the Conventions section of `config/README` says to validate the sample sheet first.
  - Boy Scout: the sync-ratio hook.
  - KISS/YAGNI: the scaffold creates no folders the user didn't ask for.
- AGENTS.md has a single line pointing to `docs/principles.md`, which keeps the full list for humans.
- **Why:** Agents already know the generic principles. AGENTS.md is loaded in every session, so every line costs context each time.

### D5. sync_ratio.py mechanics

- Runs `git status --porcelain` and `git diff --numstat HEAD`, which covers staged and unstaged changes plus untracked files. Changes are grouped by top-level folder; only folders that have a `README.md` count.
- A folder counts as having a major change when a file was added or deleted, or when more than 30 lines changed in total. The threshold can be changed with the environment variable `NERV_SYNC_THRESHOLD`.
- A folder is out of sync when it has a major change and its `README.md` is not among the changed files.
- **Remind once:** the script hashes the sorted out-of-sync report and stores the hash in `.git/nerv-sync-state`. If the current hash matches the stored one, it exits silently.
- **Claude Code adapter (Stop event):**
  - If `stop_hook_active` is true, the script exits 0 and does nothing. This prevents a reminder loop.
  - Otherwise it returns `{"decision":"block","reason":"<reminder>"}`, which gives the agent one more turn.
- **Codex adapter:** uses the equivalent stop event and output. The exact schema is confirmed against Codex docs during implementation (see Open Questions).
- **Why one continuation:** that is the only way a Stop hook can put text in front of the agent. The "remind once" hash and `stop_hook_active` together guarantee at most one continuation (spec: doc-sync).

### D6. raw_guard.py mechanics

- **PreToolUse on file-write tools.**
  - If the target path resolves inside `data/raw/` and the file already exists, the guard returns "ask" in Claude Code. In agents without an "ask" decision, it returns deny with instructions.
  - If the file is new, the guard allows the write.
- **PostToolUse on new files:** adds context reminding the agent to record provenance and a checksum in `data/README.md`.
- **PreToolUse on shell commands:** applies regex heuristics for `rm`, `mv`, `sed -i`, `truncate`, and `>`/`>>` redirects whose target is under `data/raw/`. A match is treated as a modification.
- **Paths:** normalized with `os.path.realpath` relative to the project root, which handles `..` and Windows separators.
- **Fail-open:** if the guard hits an exception, it writes the error to stderr and allows the action (spec: Fail open).
  - **Why:** a broken guard must not break every session.
  - **Trade-off:** a bug in the guard can let a write through. Defense in depth covers this: `nerv-init` suggests making `data/raw` read-only at the OS level and records checksums.

### D7. magi-review structure

- **`levels.md`** holds the default path/size table:
  - TRIVIAL: Markdown outside AGENTS.md and CLAUDE.md, under 50 lines.
  - CRITICAL: anything under `workflow/`, `config/`, `envs/`, or `data/`; statistics code under `scripts/` or `notebooks/` (DE, clustering, normalization); hook files; AGENTS.md; CLAUDE.md.
  - STANDARD: everything else.
- **`seat-briefs.md`** holds one brief per seat, plus a merged brief for STANDARD. Every brief requires:
  - fresh context, read-only access, and the diff range;
  - "assume it is wrong and show how it fails";
  - running the cheapest relevant check, without re-running the full suite;
  - the finding tags (Blocker, Fix, Nit, Pre-existing), at most 3 Nits, and a word cap;
  - the "Cannot verify" and "Declined to judge" lists.
- **Vote aggregation:** CONDITIONAL counts as APPROVE when its required fixes are applied. If they are not applied, it counts as REJECT. BALTHASAR's hard-rule REJECT is a veto.
- **`receiving-feedback.md`** sets the author's rules: verify every finding, no performative agreement, at most one scoped re-review, and an explicit ruling when the author and a reviewer still disagree.
- **Model choice:** seats inherit the session model. Each brief notes that CRITICAL seats should use the strongest available model.
- **Sources:**
  - Seat persona names: Evangelion's MAGI.
  - Mechanics: review-slices (tags, prompt-injection rule, never lower the level), superpowers (fresh brief, distrust the author's report, receiving rules, fewer dispatches), and addyosmani (a fix required for Critical findings, skip rule for tiny changes).

### D8. Repo-local GitHub identity

- This repo sets `user.name`/`user.email` with `git config --local`.
- Pushes use `GH_TOKEN` for `tingtmu`, or `gh auth switch` immediately before pushing.
- The global gh and git configuration is left untouched.
- This happens at publish time and is not part of the skill set.

## Risks / Trade-offs

- [`npx skills` CLI behavior or flags change] → Check the CLI's current documentation during implementation, and keep the degit/manual fallback documented and tested.
- [Hook schemas differ between agents or change over time] → Keep adapters thin and logic in the Python scripts; record verified schema versions in a comment in each adapter.
- [Shell regex in raw_guard misses indirect writes] → Document it as best-effort; recommend OS read-only permissions and checksums.
- [The sync nudge becomes noise on large refactors] → The threshold can be changed, the reminder fires once per state, and the hook never blocks twice.
- [Majority vote outvotes a correct minority finding] → All seats' findings are always reported. Hard-rule findings veto. The vote only decides the verdict, not which findings are shown.
- [Template text drifts between the bulk and sc add-ons] → Add-ons contain only what differs from the base templates, so there is no duplication.
- [Windows path and shell differences] → Hooks are written in Python with no bash dependency; tests run on Windows.

## Migration Plan

Not applicable. This is a new repository with no existing users.

## Open Questions

- The exact Codex hook event names and output schema for stop and pre-tool-use. Confirm them against current Codex docs when writing `adapters/codex-hooks.json`. This changes only the adapter file, not the design.
- Final public repo name, for example `nerv-skills` or `seq-unit-01`. It is only needed for the install command in README.md.
