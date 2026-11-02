# Proposal

## Why

Generated projects carry three test-first cues (`docs/principles.md` names red-green-refactor, `scripts/README.md` asks for a failing test before code that decides results, `tests/README.md` says to test the logic that decides results). There is no evidence on whether they change what an agent does or how correct its code is. One Sonnet test run showed test-first behavior, but no run without the cues was done for comparison. `SCOPE.md` says to delete instructions the model already follows by default, so the cues need evidence before we decide to keep, drop, or strengthen them.

## What Changes

- Add a small A/B benchmark harness under `bench/` in this repo. It is dev tooling, not a skill: nothing under `skills/` changes, and `npx skills` does not ship it.
- Two arms built from the same scaffold answers: **A** is the skeleton as shipped, **B** is the same skeleton with the three test-first cue lines removed by one fixed patch.
- Three hard bioinformatics tasks (difficulty about 7-8 of 10), each with synthetic raw data from a fixed seed, planted traps, a reference implementation, hidden tests, and one mutant per trap:
  - T1: per-sample scRNA-seq QC by MAD outliers from 10x-style matrices.
  - T2: bulk RNA-seq sample sheet and design validation before DESeq2.
  - T3: DE results annotation and significance call.
- Each task also has a follow-up prompt, given in a new session on the same run repo, that tempts a regression of the first behavior.
- A runner that starts each session headless with `claude -p` on Haiku inside its own run repo under `../nerv_all_runs/bench-runs/`. The repo's own `AGENTS.md` is the only project context, and no hidden test or mutant is reachable from the run folder.
- Size: 3 tasks × 2 arms × 3 reps = 18 sessions, plus 18 follow-up sessions. Haiku only, preceded by a 3-session pilot on arm B to check the traps are not too easy.
- A scorer that records, per session:
  - **Outcome:** hidden-test pass rate per trap, silent-wrong result, mutant kill rate of the agent's own tests, regression-free rate after the follow-up.
  - **Cost:** one metric, `total_cost_usd`.
  - **Process:** test-first, saw red, test-to-code line ratio, hard-rule violation (raw data changed), completion.
  - **Reliability:** pass^3, the share of tasks where all 3 reps pass.
- A results summary with a stated decision rule (keep, drop, or strengthen the cues). The result becomes a `ROADMAP.md` row. Editing the cues themselves is a separate follow-up, outside this change.
- Glossary terms for the new concepts, and a `bench/` entry in the README's Repository layout.

## Capabilities

### New Capabilities

- `cue-benchmark`: an A/B comparison of a generated project with and without a set of template cues. It covers how the arms are built, how sessions are isolated, how tasks and hidden tests are checked for validity, what is measured per session, and how a decision is reported.

### Modified Capabilities

None. The cues being measured are prose that keeps the `project-bootstrap` promise; no requirement changes.

## Impact

- New: `bench/` (task definitions, data generators, reference implementations, hidden tests, mutants, arm patch, runner, scorer, results summary) and `tests/test_bench.py`.
- Changed: `GLOSSARY.md` (new terms), `README.md` (Repository layout), `ROADMAP.md` (the item and later its result).
- Writes at run time outside this repo: run repos under `../nerv_all_runs/bench-runs/` and a dedicated Python environment for the sessions. Neither is committed.
- New dev-only dependencies for the harness and the sessions: `pandas`, `numpy`, `scipy`, `pytest` (pandas and numpy are already in `.venv`).
- Uses API spend for about 39 Haiku sessions. Each session's cost is capped.
- No change to any skill folder, `scaffold.py`, templates, or generated projects.
