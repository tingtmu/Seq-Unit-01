# Tasks

## 1. Terms, roadmap, environment, spike

- [ ] 1.1 Add the new terms to `GLOSSARY.md` with the domain-modeling skill, in a new "Benchmarking the cues" section: **Cue**, **Arm**, **Run repo**, **Trap**, **Hidden test**, **Mutant**, **Silent-wrong result**, and **Follow-up session**, each with a plain definition and an _Avoid_ line. Verify that design.md, the spec, and the later `bench/` code use only these terms (grep for "variant", "treatment", "oracle", and "buggy version", and expect no hits outside _Avoid_ lines).
- [ ] 1.2 Add a `ROADMAP.md` row "Cue benchmark (TDD cues, Haiku)" under "Skills: open design", status `next`, pointing to this change. Verify by reading the row.
- [ ] 1.3 Install `scipy` into `.venv` and create `../nerv_all_runs/bench-venv/` with pinned `pandas==3.1.0`, `numpy==2.5.4`, `scipy`, and `pytest`. Record the exact versions in `bench/README.md`. Verify that `<venv>/Scripts/python -c "import pandas, numpy, scipy, pytest"` succeeds in both.
- [ ] 1.4 Spike on headless isolation. Scaffold a throwaway project in `../nerv_all_runs/bench-spike/` and run one short `claude -p` session with the design's session command, asking the agent to run the Test command. From the stream, record in `bench/README.md`: the `init` event's model, tools, skills, MCP servers, and whether `~/.claude/rules` content loaded; the `total_cost_usd` field in the `result` event; and whether the allowed Bash calls ran without a permission denial. Save a trimmed copy of the stream as `tests/fixtures/bench/stream_spike.jsonl` for the scorer tests. Delete `bench-spike/`. Verify that `bench/README.md` has a dated "Spike" section that answers each point, and adjust the session command in design.md if the spike forces it.

## 2. Arms and run repo build

- [ ] 2.1 Write the tests in `tests/test_bench.py` first: building arm A and arm B for one task in `tmp_path` and diffing them shows only the three cue lines; a `CUE_LINES` entry that doesn't match the template stops the build with an error naming the file and line; the arm B Test command passes before any session; and `generate.py` run twice with the task seed gives byte-identical files. Verify that `.venv/Scripts/python -m pytest tests/test_bench.py` fails (red) because `bench/` doesn't exist yet.
- [ ] 2.2 Write `bench/arms.py` (`CUE_LINES` copied exactly from the three templates) and `bench/build.py` (scaffold with fixed answers and date, fill the project question, sample sheet, config pins, and delivery with its provenance line, make the delivery read-only, run the Test command, apply the arm B patch, commit `baseline` with a repo-local `bench` identity, in the order design.md gives). Verify that the 2.1 tests pass (green).

## 3. Tasks, hidden tests, and mutants

- [ ] 3.1 Add parametrized checks over `bench/tasks/*/` to `tests/test_bench.py`: the reference passes every hidden test, each mutant fails at least one, every trap in `traps.json` names an existing hidden test and mutant, the follow-up reference passes `test_followup.py` and the original `test_task.py`, and `prompt.md`/`followup.md` contain no "test", "testing", "TDD", or "test-first" (case-insensitive). Verify that they fail (red) with no tasks present, or are collected empty and flagged by an explicit "three tasks exist" assert.
- [ ] 3.2 Build T1 `t1-scrna-qc` per design.md: `answers.json`, seeded `generate.py` (four mouse samples in 10x MEX format, one tiny uniform sample where MAD = 0, one 0-count cell, one barcode shared across samples, `qc_thresholds.tsv` with some blank cells), `prompt.md` with the exact signature and rules, `reference.py`, `hidden/test_task.py`, one mutant per trap, and `traps.json`. Verify that the 3.1 checks pass for T1.
- [ ] 3.3 Add the T1 follow-up: doublet score files in the generator, `followup.md`, `reference_followup.py`, and `hidden/test_followup.py`. Verify that the 3.1 checks pass for the T1 follow-up, and that a follow-up mutant which makes the MAD helper two-sided fails `test_task.py`.
- [ ] 3.4 Build T2 `t2-design-check` per design.md: a BOM-headed `samples.tsv` with every trap seeded, `design.yaml` with `~ batch + condition`, a reference level and contrasts, FASTQ stubs under `data/raw/`, the prompt, the reference, hidden tests, mutants, and `traps.json`. Verify that the 3.1 checks pass for T2.
- [ ] 3.5 Add the T2 follow-up: a `layout` column, an optional batch, `followup.md`, the follow-up reference, and hidden tests. Verify that the 3.1 checks pass for it, and that the confounding and duplicate hidden tests are part of the regression set.
- [ ] 3.6 Build T3 `t3-de-annotation` per design.md: a DESeq2-style result (versionless ids, NA padj rows, a padj exactly at alpha, all-zero genes), a GENCODE-style annotation (versioned ids, `_PAR_Y` rows, duplicate symbols, ids missing from the DE table and the reverse), the prompt, the reference, hidden tests, mutants, and `traps.json`. Verify that the 3.1 checks pass for T3.
- [ ] 3.7 Add the T3 follow-up: a `log2FoldChange_shrunk` column, `followup.md`, the follow-up reference, and hidden tests, with a mutant that re-calls significance on the shrunken LFC. Verify that the 3.1 checks pass for it, and that this mutant fails the regression set.

## 4. Runner

- [ ] 4.1 Write the runner tests first in `tests/test_bench.py`:
  - the session plan has 3 reps × 2 arms per task and never puts two sessions of the same arm next to each other within a task;
  - the built command holds the pinned Haiku id, `--setting-sources project`, `--strict-mcp-config`, `stream-json`, `acceptEdits`, the Bash allowlist, the disabled web tools, and the budget cap, with the run repo as cwd and `bench-venv` first on PATH;
  - the context-leak check rejects a run root that has a `CLAUDE.md` or `AGENTS.md` in a parent folder, or holds anything from `bench/tasks/`.

  Verify red.
- [ ] 4.2 Write `bench/runner.py`: `plan`, `pilot` (one arm B session per task), `grid`, and a `followup` step that starts a new session after the first session is scored. It applies the 30-minute limit, saves each session's stream as `session1.jsonl`/`session2.jsonl` in the run repo, and takes the `data/raw/` checksums before and after. Verify that the 4.1 tests pass (green) and that `python bench/runner.py plan` prints the planned 36 sessions without starting any.

## 5. Scorer

- [ ] 5.1 Write the scorer tests first, with stream fixtures in `tests/fixtures/bench/`: the spike stream plus small synthetic streams for test-first, implementation-first, saw red, a limit hit, and a normal end. Cover:
  - test-first and not test-first;
  - saw red, and "unknown" when the pytest output is unparseable;
  - cost taken from the `result` event;
  - a limit hit recorded as not completed and still scored;
  - a changed `data/raw/` checksum recorded as a hard-rule violation;
  - silent-wrong versus crash, using two toy modules;
  - mutant kill rate, with toy agent tests that catch one of two mutants (0.5), and 0 with no new tests;
  - regression-free recorded separately from the follow-up pass rate.

  Verify red.
- [ ] 5.2 Write `bench/score.py`. It runs the hidden tests from `bench/` with the module path in an environment variable (no cache, no bytecode, nothing written into the run repo), computes the per-trap pass rate through `traps.json`, runs mutants in a temp copy, parses the event stream, computes the test-to-code ratio from `git diff baseline`, and appends one row per session to `bench/results/<date>/runs.csv`. Verify that the 5.1 tests pass (green) and that `git status` in a scored fixture repo is clean.

## 6. Summary and docs

- [ ] 6.1 Write the summary tests first: each row of the decision rule in design.md gives its verdict on a synthetic `runs.csv`; a yes/no difference below one run in some task is reported as no difference; a measure better in one task and worse in another is reported as no difference; disagreeing outcome measures give "no difference" for outcome; and the summary states the rule, the row applied, and the thresholds. Verify red.
- [ ] 6.2 Write `bench/summarize.py`. It produces per-task-and-arm tables (outcome, cost, process, pass^3), regression-free over runs whose first session passed (with that count), the raw table, and the verdict, written to `bench/results/<date>/summary.md`. Verify that the 6.1 tests pass (green).
- [ ] 6.3 Write `bench/README.md` (what it measures, the commands for build, pilot, grid, score, and summarize, where run repos go, and the Spike section from 1.4), and add `bench/` to the README's Repository layout. Verify that each command in `bench/README.md` runs as written with `--help` or `plan`, and that no README line names a file that doesn't exist.

## 7. Integration and harness review

- [ ] 7.1 Run the full suite with `.venv/Scripts/python -m pytest` and verify it passes.
- [ ] 7.2 Run the review gate on the harness before spending any sessions: commit (repo identity, Co-Authored-By line, no push), then have a fresh-context reviewer check the commit range against AGENTS.md and this change's spec. Focus on the isolation, the arm diff, and the validity of traps and mutants. Fix and commit the confirmed findings. Verify that the fix commit exists and the suite still passes.

## 8. Pilot

- [ ] 8.1 Run `python bench/runner.py pilot` (3 arm B sessions, no cost cap beyond a generous safety cap noted in the results). Score them. Verify that each pilot has a `runs.csv` row marked `pilot`.
- [ ] 8.2 Act on the pilot:
  - for any task whose pilot passed every hidden test, add at least one harder trap with its hidden test and mutant, and rerun the 3.1 checks;
  - for any pilot that failed from a misunderstood interface, sharpen that prompt;
  - set the cost cap to three times the highest pilot cost.

  Record each change, and the cap, in `bench/results/<date>/summary.md` under "Pilot". Verify that the suite passes after any task change.

## 9. Grid and verdict

- [ ] 9.1 Run `python bench/runner.py grid` (18 first sessions, each followed by its scored follow-up session, 36 in all), in the background. Verify that `runs.csv` holds 36 non-pilot rows, and that any session stopped by a limit is marked and not rerun silently.
- [ ] 9.2 Run `python bench/summarize.py` and read `summary.md`. Spot-check one test-first and one not-test-first verdict against their stream files by hand. Verify that the verdict names the rule row it came from.
- [ ] 9.3 Update the `ROADMAP.md` row with the verdict, the key numbers, and the caveats (Haiku only, 3 reps), set its status to `done`, and add a new row for the follow-up cue edit (keep, drop, or strengthen) if the verdict calls for one. Commit the results and the ROADMAP update. Verify by reading the row and `git log`.

## Workflow follow-up

- Review gate after apply (AGENTS.md Commands): tests, commit, fresh-context reviewer, fix confirmed findings. Task 7.2 covers the harness. Run it once more over the results commit if task 8.2 changed tasks.
- Archive with `/opsx:archive`, then run the review gate again.
- Any edit to the cues themselves is a separate change, or a direct commit if it stays prose that keeps the skill's promise.
