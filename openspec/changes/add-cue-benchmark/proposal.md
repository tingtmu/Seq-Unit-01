# Proposal

## Why

Generated projects carry three test-first cues (`docs/principles.md` names red-green-refactor, `scripts/README.md` asks for a failing test before code that decides results, `tests/README.md` says to test the logic that decides results). There is no evidence on whether they change what an agent does or how correct its code is. One Sonnet test run showed test-first behavior, but no run without the cues was done for comparison. `SCOPE.md` says to delete instructions the model already follows by default, so the cues need evidence before we decide to keep, drop, or strengthen them.

How this clears the admission bar:
- The user asked for this measurement.
- It serves a possible deletion, and deleting counts as progress.
- It adds nothing to any skill or generated project, so the "prose before code" test applies to the later cue edit, not to this harness.
- The "observed" item is the open question the earlier TDD run left. That run had no comparison arm, and its ROADMAP row already says to revisit with a later run.

## What Changes

- Add a small A/B benchmark harness under `bench/` in this repo. It is dev tooling, not a skill: nothing under `skills/` changes, and `npx skills` does not ship it.
- Two arms built from the same scaffold answers: **A** is the skeleton as shipped, **B** is the same skeleton with the three test-first cue lines removed by one fixed patch.
- Three hard bioinformatics tasks (difficulty about 7-8 of 10), each with synthetic raw data from a fixed seed, planted traps, a reference implementation, hidden tests, and one mutant per trap:
  - T1: per-sample scRNA-seq QC by MAD outliers from 10x-style matrices.
  - T2: bulk RNA-seq sample sheet and design validation before DESeq2.
  - T3: DE results annotation and significance call.
- Each task also has a follow-up prompt, given in a new session on the same run repo, that tempts a regression of the first behavior.
- A runner that starts each session headless with `claude -p` on Haiku inside its own run repo under `../nerv_all_runs/bench-runs/`:
  - the repo's own `AGENTS.md` is the only project context;
  - user skills, commands, MCP servers, and auto-memory are off;
  - transcripts are kept outside the run repo;
  - a session that changes the shared Python environment or shows leaked context is marked invalid.
- Size: 3 tasks × 2 arms × 3 reps = 18 sessions, plus 18 follow-up sessions. Haiku only, preceded by a 3-session pilot on arm B to check the traps are not too easy.
- A scorer that records, per session:
  - **Outcome:** hidden-test pass rate per trap, silent-wrong result, mutant kill rate of the agent's own tests, regression-free rate after the follow-up.
  - **Cost:** one metric, `total_cost_usd`.
  - **Process:** cue exposure (whether the agent read a cue file before coding), test-first, saw red, out-of-repo access, test-to-code line ratio, hard-rule violation (raw data changed), completion.
  - **Reliability:** pass^3, the share of tasks where all 3 reps pass.
- A results summary with a stated decision rule. The verdict is keep, drop, or strengthen the cues, or "cues not reached" or "inconclusive". The result becomes a `ROADMAP.md` row. Editing the cues themselves is a separate follow-up, outside this change.
- Glossary terms for the new concepts, and a `bench/` entry in the README's Repository layout.

## Capabilities

### New Capabilities

- `cue-benchmark`: an A/B comparison of a generated project with and without a set of template cues. It covers how the arms are built, how sessions are isolated, how tasks and hidden tests are checked for validity, what is measured per session, and how a decision is reported.

### Modified Capabilities

None. The cues being measured are prose that keeps the `project-bootstrap` promise; no requirement changes.

## Impact

- New: `bench/` (task definitions, data generators, reference implementations, hidden tests, mutants, arm patch, runner, scorer, results summary) and `tests/test_bench.py`.
- Changed: `GLOSSARY.md` (new terms) and `README.md` (Repository layout). `ROADMAP.md` (the item and later its result) is local and gitignored, so it is edited but not committed.
- Writes at run time outside this repo: run repos under `../nerv_all_runs/bench-runs/`, session transcripts under `../nerv_all_runs/bench-logs/`, and a dedicated Python environment for the sessions. None of them is committed.
- New dev-only dependencies for the harness and the sessions: `pandas`, `numpy`, `scipy`, `pytest` (pandas and numpy are already in `.venv`).
- Uses API spend for about 39 Haiku sessions. Each session's cost is capped.
- No change to any skill folder, `scaffold.py`, templates, or generated projects.
