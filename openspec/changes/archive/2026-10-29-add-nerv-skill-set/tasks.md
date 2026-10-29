# Tasks

## 1. Repo setup

- [x] 1.1 Run `git init`, set the repo-local `user.name`/`user.email` for `tingtmu` (`git config --local`), and add `.gitignore` and LICENSE. Verify: `git config --local --list` shows the tingtmu identity, and the global config is unchanged.
- [x] 1.2 Create the `skills/nerv-init`, `skills/sync-ratio`, `skills/magi-review`, and `tests/` folders following design D1, and set up pytest. Verify: `python -m pytest` runs and collects 0 tests without errors.

## 2. Hook scripts (shared logic)

- [x] 2.1 Implement `skills/nerv-init/hooks/sync_ratio.py` per D5:
  - per-folder major-change detection from git;
  - out-of-sync check;
  - remind-once hash in `.git/nerv-sync-state`;
  - silent exit outside git.

  Verify with pytest on temporary git repos, covering the doc-sync scenarios: new script, minor edit, README already updated, repeated stop, no git.
- [x] 2.2 Add Claude Code Stop-event handling to `sync_ratio.py` (honors `stop_hook_active` and returns a single block reason). Verify with a pytest that feeds sample hook JSON and checks for one continuation at most.
- [x] 2.3 Implement `skills/nerv-init/hooks/raw_guard.py` per D6:
  - new file: allow;
  - existing file: ask (or deny with instructions where "ask" isn't supported);
  - shell-command heuristics;
  - realpath normalization;
  - fail-open to stderr.

  Verify with pytest covering every raw-data-guard scenario, including Windows-style paths and malformed input.
- [x] 2.4 Add the PostToolUse provenance reminder for new files under `data/raw/`. Verify with a pytest that sample input produces context naming `data/README.md`.

## 3. Agent adapters

- [x] 3.1 Check the current Claude Code hook schema (PreToolUse "ask" decision, Stop `decision/reason`, PostToolUse context) using Context7/docs, then write `hooks/adapters/claude-settings.json`. Verify: the JSON parses, and a manual run in a scratch project triggers the guard's ask prompt and one sync reminder.
- [x] 3.2 Check the current Codex hooks schema (`.codex/hooks.json` events and output), resolving the design Open Question, then write `hooks/adapters/codex-hooks.json`. Record the verified schema source in the README. Verify: the JSON parses, and a manual Codex run in a scratch project fires both hooks (or the gap is documented if Codex lacks an equivalent event).

## 4. nerv-init

- [x] 4.1 Write `templates/base/` per the project-bootstrap spec:
  - folder READMEs with the 4-section template (Purpose / Conventions / Current state / Last major change);
  - `AGENTS.md.tmpl` (hard rules, run/test commands, path map; aim for about 60 lines);
  - `CLAUDE.md` (`@AGENTS.md`);
  - `README.md.tmpl`;
  - `docs/principles.md` with the user's principle list.

  Verify: a test checks every README template has all 4 sections and that AGENTS.md.tmpl is 200 lines or fewer, with about 60 recommended and not enforced.
- [x] 4.2 Write `templates/addons/bulk-rnaseq`, `templates/addons/scrnaseq`, `templates/engines/snakemake` (standard Snakemake layout), and `templates/engines/scripts`, each containing only what differs from base. Verify: a test confirms no add-on file duplicates a base file verbatim.
- [x] 4.3 Implement `scripts/scaffold.py` (answers JSON → tree, template copy, .gitignore, git init, hooks copied to `.nerv/hooks/`, adapters installed, overwrite refusal with a conflict list). Verify with pytest:
  - bulk+snakemake, sc+scripts, and other answers each produce the expected trees;
  - a non-empty target reports conflicts and changes nothing;
  - `git status` works in the output;
  - data paths are ignored;
  - the sensitive-data answer adds the stricter ignores.
- [x] 4.4 Write `references/interview.md` (questions, defaults with Snakemake as the default engine, the answers JSON schema, and how answers map to add-ons) and `SKILL.md`:
  - a description stating what the skill does in plain words in the first sentence;
  - flow: interview → show the planned tree → confirm → scaffold → agent fills README/AGENTS prose → summary;
  - an "other assay" adaptation guide.

  Verify: dry-run the skill in an empty scratch directory with Claude Code, confirming no files are written before confirmation and the result matches the spec scenarios.

## 5. sync-ratio skill

- [x] 5.1 Write `skills/sync-ratio/SKILL.md`: it runs the project's `.nerv/hooks/sync_ratio.py` in report mode, lists out-of-sync folders, and drafts edits limited to the Current state and Last major change sections for approval. Add a report-mode CLI flag to `sync_ratio.py` with a test. Verify: in a scaffolded scratch project, add a script and invoke the skill; it proposes a `scripts/README.md` update.

## 6. magi-review

- [x] 6.1 Write `references/levels.md`: the default level table and escalation rules (D7). Verify: the table classifies each code-review spec scenario (docs-only → TRIVIAL, workflow edit → CRITICAL) when walked through manually and recorded in the PR description.
- [x] 6.2 Write `references/seat-briefs.md`: the STANDARD merged brief plus the MELCHIOR-1, BALTHASAR-2, and CASPER-3 briefs. Each includes the finding format, tags, Cannot-verify and Declined lists, the read-only and prompt-injection rules, and the bioinformatics checks for MELCHIOR. Verify: each brief contains every finding-format field required by the spec.
- [x] 6.3 Write `references/receiving-feedback.md` and `SKILL.md`:
  - level selection;
  - dispatch (1 reviewer or 3 parallel seats);
  - vote aggregation with CONDITIONAL handling and the BALTHASAR veto;
  - the report showing the tally;
  - the single scoped re-review.

  Verify: run magi-review in a scratch project on (a) a seeded diff with a hardcoded credential, which must REJECT via veto, and (b) a docs-only diff, which must be TRIVIAL and dispatch no reviewer.

## 7. Distribution and docs

- [x] 7.1 Write the repo `README.md`:
  - what each skill does, with the EVA name explained;
  - `npx skills add tingtmu/Seq-Unit-01` install;
  - degit/manual fallback;
  - supported agents and hook limitations, with raw_guard marked as best-effort.

  Check current `npx skills` CLI docs before documenting flags. Verify: both install methods, followed as written in a fresh scratch directory, make the skills available at project level only.
- [x] 7.2 End-to-end check in a fresh scratch directory: install → `/nerv-init` (scrnaseq, Snakemake, both languages) → edit a workflow rule → stop (one sync reminder) → try to edit a raw file (ask prompt) → `/magi-review` (CRITICAL, three seats, tally shown). Verify: every step behaves as the specs describe, and any deviation is recorded.

## Workflow follow-up

- Decide the final public repo name, create it under `tingtmu`, and push using the repo-local identity (`GH_TOKEN` or `gh auth switch`).
- Run `/opsx:verify`, then archive the change.
