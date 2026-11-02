# bench: cue benchmark

Dev tooling for the `add-cue-benchmark` change. It is not a skill, and `npx skills` does not ship it.

## What it measures

It asks whether the three test-first cues in generated projects (`arms.py`, `CUE_LINES`) change what Haiku does, and how correct its code is. Arm A is the project as shipped. Arm B is the same project with the three cue lines removed. Each of three tasks (`tasks/t1-scrna-qc`, `tasks/t2-design-check`, `tasks/t3-de-annotation`) runs 3 reps per arm, and each run has two sessions: the task, then a follow-up session that tempts a regression. Per session, `score.py` records outcome (hidden-test pass rate per trap, silent-wrong result, mutant kill rate of the agent's own tests, regression-free), cost (`total_cost_usd`), and process (cue exposure, test-first, saw red, out-of-repo access, test-to-code ratio, raw data changed). `summarize.py` applies the decision rule from the change's design.md and gives a verdict: keep, drop, strengthen, cues not reached, or inconclusive.

Each task folder is described in `taskdef.py`. A mutant is the reference with exact text replacements (`mutants.json`), so it can't drift from the reference.

## Commands

Run from the repo root with the repo venv.

- Build one run repo: `.venv/Scripts/python bench/build.py bench/tasks/t1-scrna-qc A ../nerv_all_runs/bench-runs/t1-scrna-qc-A-r1`
- Plan (prints the 36 sessions, starts nothing): `.venv/Scripts/python bench/runner.py plan`
- Pilot, one arm B session per task: `.venv/Scripts/python bench/runner.py pilot`
- Grid, every planned run with its follow-up session: `.venv/Scripts/python bench/runner.py grid --cap USD`, with USD three times the highest pilot cost
- Score one session again: `.venv/Scripts/python bench/score.py t1-scrna-qc-A-r1 1`
- Summarize: `.venv/Scripts/python bench/summarize.py` (default: the newest `bench/results/<date>/runs.csv`)

Run repos go to `../nerv_all_runs/bench-runs/<task>-<arm>-r<n>/`, and streams, checksums, and package sets to `../nerv_all_runs/bench-logs/<task>-<arm>-r<n>/`. Neither is committed. Results go to `bench/results/<date>/runs.csv` and `summary.md`, which are committed.

## Environments

- `.venv` (this repo): runs the harness and its tests. `scipy 1.18.1` and `PyYAML 6.0.3` were added for the task references.
- `../nerv_all_runs/bench-venv/`: the one Python environment the sessions and the hidden tests use. It was created with Python 3.15.2. Its exact package set is `bench-venv.txt`, which the runner diffs and restores from:
  `pandas==3.1.0`, `numpy==2.5.4`, `scipy==1.18.1`, `pytest==9.2.0`, `PyYAML==6.0.3` (T2 reads `config/design.yaml`), plus their dependencies.

## Spike (2026-11-03)

One throwaway project (bulk, scripts, python) in `../nerv_all_runs/bench-spike/`, with Claude Code 2.1.316 on `claude-haiku-5-5` and the design's session command. The trimmed stream is `tests/fixtures/bench/stream_spike.jsonl`. The spike folder and its memory folder were deleted afterwards.

- **`init` event:** model `claude-haiku-5-5`; `skills: []`, `slash_commands: []`, `mcp_servers: []`. Tools are the built-in set (Bash, Read, Write, Edit, Glob, Grep, Task, ...). `plugins` lists only built-in plugins (`...@builtin`), which every session has, so they don't count as a leak. Agents are the built-ins only.
- **User rules:** not loaded. Asked to quote any instruction that mentions Context7, r-btw, or `coding-style.md` (all of them in `~/.claude/rules/`), the agent found none.
- **Auto-memory:** `-p` mode has no CLI flag for it. Without a switch, `init` reports `memory_paths.auto` and the agent wrote `MEMORY.md` and a note into `~/.claude/projects/<path>/memory/`. With the environment variable `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `memory_paths` is absent, the agent has no memory directory, and no `~/.claude/projects/<path>/` folder is created. The runner sets this variable for every session.
- **Cost:** the final `result` event carries `total_cost_usd` (0.0033 for the spike).
- **Permissions:** `pytest tests/` ran without a prompt. `pip install requests` was denied. A compound command (`pytest tests/ 2>&1; echo ...`) is also denied, because `echo` isn't allowlisted. The agent retried with the plain command. Denials appear in the stream as `system/permission_denied` events and in `result.permission_denials`.
- **Stdin:** `claude -p` waits 3 s for stdin when none is redirected, so the runner closes stdin.
- **Out-of-repo reads:** asked about memory, the agent ran `ls ~/.claude` and a `Glob` on `C:/Users`. This is the case the scorer's out-of-repo flag exists for.
