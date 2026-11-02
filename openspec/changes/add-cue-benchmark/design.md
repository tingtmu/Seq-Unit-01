# Design

## Context

- The cues under test are three template lines, found by reading the templates:
  - `skills/nerv-init/templates/base/docs/principles.md`: "**Test-driven (red-green-refactor).** Write a failing test on tiny synthetic data, make it pass, then clean up."
  - `skills/nerv-init/templates/base/scripts/README.md`: "Before writing code that decides results (filters, thresholds, joins, sample-sheet checks), write a failing test first; see `tests/README.md`. Exploratory notebooks are exempt until their code moves here."
  - `skills/nerv-init/templates/base/tests/README.md`: "Test the logic that decides results: filters, thresholds, statistics."
- They are prose. No `project-bootstrap` requirement promises them, so a later keep, drop, or strengthen edit is a direct commit (AGENTS.md rule 2), unless it changes a skill promise.
- Two other test cues sit outside these templates: `yashima-blueprint` step 6 ("boundary tests first") and the CASPER-3 brief in `magi-review`. The tasks never invoke those skills, so they stay out of scope.
- `scaffold.py --answers FILE --target DIR` builds a generated project with no interview. It is deterministic given a fixed `date`. Engine `scripts` with language `python` gives the Test command `pytest tests/` and no snakemake dependency.
- None of the parent folders of `personal_proj/nerv_all_runs/` holds a `CLAUDE.md` or `AGENTS.md` (checked 2026-11-03).
- None of the cues is in the generated `AGENTS.md`. `CLAUDE.md` is only `@AGENTS.md`, which links to the three cue files without quoting them. An agent reaches a cue only if it opens one of those files. That is how real users meet the cues too, so the benchmark keeps it and measures exposure rather than moving the cues.
- `claude --help` (2.1.316) offers `-p`, `--model`, `--output-format stream-json`, `--setting-sources`, `--strict-mcp-config`, `--disable-slash-commands` ("Disable all skills and commands"), `--max-budget-usd`, `--permission-mode`, `--allowedTools`, `--disallowedTools`, and `--no-session-persistence`. `--bare` is not used: it turns off CLAUDE.md auto-discovery (the path a real session takes to `AGENTS.md`) and accepts only API-key auth.
- The user rules in `~/.claude/rules/` contain no test-first text (grep, 2026-11-03). User skills do: `~/.claude/skills/diagnosing-bugs` has "failing test" steps, and `~/.claude/skills/tdd` is a symlink that loads again if its target is reinstalled. So skills are disabled, not merely tolerated.
- `../nerv_all_runs/` already holds earlier runs, including `nerv-tdd-run` (a Sonnet TDD run), and an agent with Bash can read any path. Isolation is therefore enforced where the CLI allows it and detected where it doesn't.
- `ROADMAP.md` and `SCOPE.md` are gitignored (local), so they are edited but never committed.
- The bulk add-on's `config/design.yaml` says LFC thresholds are tested, not post-hoc filtered. T3 follows that convention, so its correct answer does not contradict the project the agent sits in.

## Goals / Non-Goals

**Goals:**
- One decision (keep, drop, or strengthen the three cues), read from a small A/B run that is cheap to repeat after a later cue edit.
- Hard, realistic tasks where carelessness gives plausible but wrong numbers.
- A harness that can't leak the answer into a session.

**Non-Goals:**
- Statistical significance. Three reps per arm is a self-test. The summary says so, and the decision rule compensates with direction and size thresholds.
- Other models. The run is Haiku only, so the verdict holds for Haiku. Whether it transfers to Sonnet or Opus stays an open question in the ROADMAP row.
- Measuring `yashima-blueprint` or `magi-review` cues.
- R tasks, Snakemake, or a reusable eval framework. The harness serves these three tasks.

## Decisions

### Layout

```
Seq-Unit-01/bench/                      versioned, not shipped by npx skills
  README.md                             how to run each step
  arms.py                               CUE_LINES: (file, exact line) removed for arm B
  build.py                              scaffold + project question + data + baseline commit [+ arm B patch]
  runner.py                             plan (interleaved), session command, follow-up
  score.py                              hidden tests, mutants, event stream, raw checksum -> one row
  summarize.py                          tables + decision rule -> summary.md
  tasks/<task>/
    answers.json  prompt.md  followup.md  generate.py (seeded data)
    reference.py  reference_followup.py
    hidden/test_task.py  hidden/test_followup.py  hidden/conftest.py (loads the module by path)
    mutants/<trap>.py                   one per trap
    traps.json                          trap -> hidden test ids + mutant ids
  results/<date>/runs.csv  summary.md   committed

personal_proj/nerv_all_runs/
  bench-venv/                           pinned pandas, numpy, scipy, pytest for sessions and scoring
  bench-runs/<task>-<arm>-r<n>/         one run repo per run (two sessions each), not committed
  bench-logs/<task>-<arm>-r<n>/         session1.jsonl, session2.jsonl, checksums, package sets
```

The harness lives here rather than in `nerv_all_runs/` so its tests run in this repo's suite and it changes through OpenSpec. `bench-runs/`, `bench-logs/`, and `bench-venv/` are siblings, so none is a parent folder of a run repo. The follow-up session can't find session 1's transcript in its own repo, and the hidden material lives in a different tree altogether.

Alternative rejected: copying hidden tests into the run repo after the session and deleting them afterwards. Loading the module by path from outside is simpler and leaves nothing behind for the follow-up session to find.

### Building a run repo

1. Run `scaffold.py` with the task's `answers.json` and a fixed `date` (engine `scripts`, language `python`, compute `local`, sensitive `false`).
2. Fill the parts `nerv-init`'s agent steps would fill, the same way in both arms:
   - the project-question comment in `AGENTS.md` and `README.md`;
   - `config/samples.tsv` and `config/config.yaml` (organism and build) for the task;
   - the delivery under `data/raw/` from `generate.py`, with its provenance line in `data/README.md`, made read-only.
3. Arm B only: remove each `CUE_LINES` entry. Fail if an exact line is missing.
4. Run the Test command. It must pass, then commit `baseline` with a repo-local identity (`bench`).

The arm patch comes last, so the A/B diff is exactly the cue lines. `test_bench.py` checks this by building both arms in `tmp_path` and diffing them.

### Session command

```
claude -p "<prompt.md>" --model claude-haiku-5-5 --setting-sources project
       --strict-mcp-config --disable-slash-commands --output-format stream-json --verbose
       --permission-mode acceptEdits
       --allowedTools "Bash(python:*)" "Bash(pytest:*)" "Bash(git:*)" "Bash(ls:*)" "Bash(cat:*)"
       --disallowedTools WebSearch WebFetch "Bash(pip:*)" "Bash(python -m pip:*)"
       --max-budget-usd <cap> --no-session-persistence  [+ the auto-memory switch found in the spike]
cwd = run repo; stdout -> bench-logs/<run>/sessionN.jsonl
env: PATH starts with bench-venv; PYTHONDONTWRITEBYTECODE=1; PIP_NO_INDEX=1; timeout 30 min
```

- **Settings, MCP, skills.** `--setting-sources project` keeps user settings out. `--strict-mcp-config` with no config means no MCP servers. `--disable-slash-commands` turns off skills and commands; generated projects install none, so neither arm loses anything. The runner reads the stream's `init` event. If any skill, command, MCP server, or user rule appears there, the session is invalid and is not scored. The spike (task 1.4) confirms the command gives a clean `init`.
- **Auto-memory.** Auto-memory would let session 2 read notes from session 1. The spike finds the switch that turns it off in `-p` mode and adds it to the command. Independently, after every session the runner checks the agent memory folder for the run repo's path; any file there makes the run invalid (spec "Hidden material out of reach").
- **Permissions.** `acceptEdits` with a short Bash allowlist lets the agent edit and test, while edits outside the run repo still need a permission that headless mode cannot grant. Rejected: `bypassPermissions`, which would let a session write anywhere.
- **Package changes.** Pip is denied, and with `PIP_NO_INDEX=1` it can't fetch anything. The runner records `pip freeze` of `bench-venv` before and after each session. Any change makes the run invalid, and the runner restores the environment from the pinned list before the next session.
- **Reading outside the repo.** `python:*` and `cat:*` can still read outside the repo. That can't be blocked without losing realism, so the scorer flags any tool input that names an absolute path outside the run repo or climbs out with `..`. The summary lists the flagged sessions.
- **Web tools** are off because the hidden tests are public in this repo.
- **Model, cap, follow-up.** The model id is pinned, and the scorer records the model the `init` event reports. The cost cap is set after the pilot, to three times the highest pilot cost. The follow-up is the same command with `followup.md`, after the first session is scored and the follow-up inputs are staged. `--no-session-persistence` and a new process make it a new conversation.

### Staging a follow-up

`stage_followup(run)` runs in this order, and only then starts session 2:
1. Copy the task's follow-up inputs from `generate.py` into the run repo. New raw files go to a new delivery `data/raw/delivery-02/`, with a provenance line appended to `data/README.md`, made read-only. Derived inputs (doublet scores, a re-run DE table) go under `data/processed/`.
2. Record the base for session 2's diff: the tree hash of a temp copy with every file staged (`git add -A` in the copy). Nothing is committed in the run repo.
3. Take the `data/raw/` checksum and the package set.

### Tasks and traps

Every prompt names the module path, the function signature, the inputs, and the output columns, and states each rule exactly (inclusive or strict, NA handling). Traps test carelessness, not guessing. Prompts never mention tests.

**T1 `t1-scrna-qc`** (assay `scrnaseq`, mouse). `scripts/qc_filter.py: filter_cells(matrix_dirs, thresholds, mito_prefix, nmads=3.0) -> (cells, summary)`. The inputs are four samples in 10x MEX format (`matrix.mtx.gz`, `barcodes.tsv.gz`, `features.tsv.gz` with gene id, symbol, type) and `config/qc_thresholds.tsv`, which uses the template columns. The prompt states the meaning of each column:
- `min_counts` and `min_genes`: a value is a fixed lower bound (inclusive keep, `>=`). A blank means a per-sample MAD lower bound on log1p of the metric: drop if below median − nmads × MAD.
- `max_genes`: a value is a fixed upper bound (inclusive keep, `<=`). A blank means no upper filter.
- `max_pct_mito`: always given in session 1. Drop if strictly above it.

The prompt also states the reason codes.

| Trap | Careless version (mutant) |
|---|---|
| per-sample thresholds | median/MAD over all cells pooled |
| log scale | MAD on raw counts |
| MAD scaled by 1.4826 (normal-consistent) | unscaled MAD |
| MAD = 0 in a tiny, uniform sample: no MAD filter, reason recorded | everything off the median dropped |
| one-sided (low) tails for counts and genes | two-sided, dropping high-count cells |
| mito prefix from the argument (`mt-`), matched on the symbol column | hardcoded `MT-`, or matched on gene id |
| blank threshold cell is "use MAD", not 0 | blank read as 0 (filter off) |
| 0-count cell: pct_mito defined as 0, cell dropped by the counts filter | division by zero, NaN kept |
| same barcode in two samples: cell id is `sample_id:barcode` | barcodes collide in the output |

Follow-up: "`qc_thresholds.tsv` gains a `doublet_score_max` column, and `max_pct_mito` may now be blank. When it is blank, use a per-sample MAD upper tail on pct_mito. Also drop cells whose score in `data/processed/doublets/<sample>.tsv` is strictly above `doublet_score_max`. A barcode missing from the scores file is an error, raised with the sample and barcode." The staged thresholds file adds the column and blanks `max_pct_mito` for two samples. The bait is that reusing the one-sided MAD helper for an upper tail tempts making it two-sided, which breaks the counts filter. `hidden/test_followup.py` checks the new behavior. Regression is the original `test_task.py`, rerun against the inputs extended with doublet scores (passing on the follow-up reference).

**T2 `t2-design-check`** (assay `bulk-rnaseq`, human). `scripts/check_design.py: check_design(samples_path, design_path, raw_dir) -> list[Problem]` with `Problem(severity, sample_id, message)`. It collects every problem and raises on none. The inputs are a core-delivered `config/samples.tsv` with a BOM header, and `config/design.yaml` with formula `~ batch + condition`, a reference level, and contrasts.

| Trap | Careless version (mutant) |
|---|---|
| all problems reported, not just the first | returns at the first error |
| duplicate `sample_id` after stripping whitespace | compares raw strings |
| paired project: a row with empty `fastq_2` is an error | checks only `fastq_1` |
| FASTQ path missing under `raw_dir` is an error | not checked |
| level names stripped; levels equal ignoring case but not exactly are an error | silently case-folds, or treats `"Control "` as a new level |
| batch fully confounded with condition (design matrix not full rank) is an error | checks only that the columns exist |
| reference level or contrast level absent from the data is an error | not checked |
| a condition level with one replicate is a warning, not an error | error, or ignored |
| UTF-8 BOM in the header | `﻿sample_id` reported as a missing column |

Follow-up: "the core now sends mixed single- and paired-end runs with a `layout` column (`SE`/`PE`), and `batch` may be absent (then the formula is `~ condition`)." Regression: the confounding and duplicate checks must still fire, and the paired check must apply to `PE` rows.

**T3 `t3-de-annotation`** (assay `bulk-rnaseq`, human). `scripts/annotate_de.py: annotate_de(de_path, annotation_path, alpha) -> (table, unmatched)`. The inputs are:
- a DESeq2 result made with `lfcThreshold=1, altHypothesis="greaterAbs"`: versionless `gene_id`, `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, `padj`;
- a GENCODE-derived annotation: versioned `gene_id`, `gene_name`, `gene_type`, `chrom`, including `_PAR_Y` rows.

The generator keeps the DE table consistent with that test. A gene with |LFC| ≤ 1 has `pvalue` 1, so every significant gene has |LFC| > 1.

T3's `config/config.yaml` pins GRCh38 and **GENCODE v43**, because releases 25 to 43 mark chrY PAR genes with `_PAR_Y`, while v44 and later give them their own ids ([GENCODE FAQ](https://www.gencodegenes.org/pages/faq.html)). The planted annotation then agrees with the project's own pin.

Significance is `padj < alpha`. The table is sorted by padj ascending with NA last, then by |log2FC| descending, then by `gene_id`.

| Trap | Careless version (mutant) |
|---|---|
| version stripped on the annotation side only | joins on raw ids (nothing matches) |
| `_PAR_Y` rows don't duplicate genes after stripping | `split(".")` gives two rows for one gene |
| left join: every DE row kept, unmatched counted | inner join silently drops genes |
| NA padj (independent filtering, all-zero genes) is not significant and is kept | dropped, or compared as significant |
| boundary: padj equal to alpha is not significant | `<=` |
| duplicate gene symbols keyed on id | deduplicated by `gene_name` |
| sort order with NA last and ties broken | NA first, or unstable ties |

Follow-up: "the DE table is re-delivered with a `log2FoldChange_shrunk` column (apeglm). Report it, use it for `direction` and for ranking ties, and keep significance from padj alone, because the threshold was already tested in DESeq2." Shrinkage pulls some significant genes below |LFC| 1, so the trap "no post-hoc LFC filter" is real here (mutant: drops significant genes whose shrunken |LFC| < 1). It is therefore a follow-up trap, not a session-1 trap: on an `lfcThreshold=1` result, that filter can't change anything. Regression: NA and boundary handling unchanged.

Every prompt lists the statistical phrases it may use (for example "Wald test" in T3) as `allowed_phrases` in the task folder. The wording check removes those before it looks for software-testing words.

Each trap names at least one hidden test and one mutant in `traps.json`. `test_bench.py` checks the reference and mutant behavior (the spec's "Valid hidden tests and mutants").

### Scoring

- Hidden tests run with `bench-venv` python from `bench/`, with an environment variable giving the agent module's path. Nothing is written into the run repo (`-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`). Pass rate is overall and per trap through `traps.json`.
- **Silent-wrong:** the function returned output of the documented shape, and a value test failed. A raise counts as a plain failure.
- **Mutant kill rate:**
  1. Copy the run repo to a temp dir and put the task's reference at the module path.
  2. Run the agent's `tests/` (smoke test excluded). The eligible tests are those that pass there. A test that fails or errors on import against the reference (for example, it imports one of the agent's private helpers) is not eligible.
  3. Swap in each mutant in turn. A mutant is killed if any eligible test fails.
  4. With no eligible test, the kill rate is 0, and the record says why.
- **Event stream:**
  - `exposed` is a `Read`, or a `cat`/`python` Bash call, naming one of the three cue files before the first write to the module. The files read are recorded.
  - `test-first` compares the first `Write`/`Edit` to a new `tests/` file with the first write to the module.
  - `saw red` is a pytest Bash call reporting `failed` or `error` after the first new test and before the first all-passed summary.
  - `out-of-repo` lists tool inputs with absolute paths outside the run repo or a `..` that climbs out of it.
  - `completed` means it ended normally and the last pytest call passed.
  - Cost is the `total_cost_usd` of the final `result` event. If the runner killed the session at the time limit, there is no such event, and cost is recorded as unknown. Pooled cost excludes unknowns, and the summary gives their count.
- **Hard-rule violation:** compare SHA-256 sums of `data/raw/` before and after each session.
- **Test-to-code ratio:** run `git add -A` in the scorer's temp copy, then `git diff --cached --numstat` against `baseline` for session 1, or against the post-session-1 tree hash for session 2. The ratio is lines added under `tests/` over lines added under `scripts/`. Untracked files therefore count, whether or not the agent committed.

### Order and size

- Pilot: one arm B session per task, before the cost cap is set. It is not counted.
- Grid: for each task, rep 1 to 3, alternating which arm goes first (`A1 B1 | B2 A2 | A3 B3`, an ABBA counterbalance that balances linear drift better than strict ABAB), giving 18 runs and 36 sessions.
- Sessions run one at a time (simplest, and no rate-limit noise), in the background.

### Decision rule

Measures: compliance is the test-first rate. Outcome is the hidden-test pass rate, the regression-free rate, and the silent-wrong rate. Cost is total USD.

Thresholds for "different" (the summary states them):
- yes/no measures: at least one run per task, in the same direction in all three tasks;
- rates: at least 0.10 pooled, same direction in all three tasks;
- cost: at least 25% pooled, same direction in all three tasks.

Definitions:
- **High** compliance means test-first in at least 6 of 9 runs, pooled per arm. **Low** is not high.
- **A > B** means test-first differs by the yes/no threshold, in A's favor.
- **Exposed** means at least half of arm A's first sessions read a cue file before coding.
- **Test-first runs did better** (pooled across arms, observational) means their mean hidden pass rate beats that of the other runs by at least 0.10, with at least 3 runs in each group.

Rows are checked top to bottom, and the first that matches applies:

```
 #  condition                                                      verdict
 -- ------------------------------------------------------------   ----------------------------------
 1  A not exposed                                                  CUES NOT REACHED (the links in
                                                                   AGENTS.md aren't followed; next step
                                                                   is to move one line into AGENTS.md
                                                                   or drop the cues)
 2  A high and B high                                              DROP (default behavior)
 3  A > B and outcome: A better                                    KEEP
 4  A > B and outcome: no difference or A worse                    DROP (cues don't pay)
 5  A low and B low and test-first runs did better                 STRENGTHEN (weak: observational)
 6  A low and B low                                                DROP
 7  otherwise (e.g. B > A, or A high but A > B fails in one task)  INCONCLUSIVE
```

If several outcome measures disagree (for example, A has a better pass rate but a worse regression-free rate), the verdict is "no difference" for outcome. Hard-rule violations, invalid runs, out-of-repo flags, and over-testing are reported beside the verdict, not inside it.

## Risks / Trade-offs

- [Three reps can't separate small effects.] → Thresholds need agreement in all three tasks. The summary states the limit and keeps the raw table.
- [Haiku may wander into `conda env create` from the generated README and burn its budget.] → `bench-venv` is first on PATH, so `pytest tests/` works directly. The cost cap stops runaways, and such sessions are recorded as not completed rather than rerun.
- [User rules, skills, or plugins leak in despite the flags.] → Spike 1.4 confirms a clean `init` event. In the grid, any session whose `init` lists one is invalid and not scored, because a user skill such as `diagnosing-bugs` carries its own test-first steps.
- [The cues sit one link away from `AGENTS.md`, so Haiku may never read them.] → Exposure is measured, and verdict row 1 ("cues not reached") stops a null result from being read as "cues don't help".
- [Some agent tests target private helpers, which skews the kill rate.] → Eligibility is judged on the reference module, and import failures are excluded (spec "Mutant kill rate").
- [The pytest summary-line parsing for "saw red" is a heuristic.] → It is tested on recorded stream fixtures, and the scorer falls back to "unknown" rather than guessing.
- [Traps too easy or too hard.] → A pilot that passes everything means harder traps. A pilot that fails every test because of an interface misunderstanding means the prompt is sharpened before the grid, and the change is noted in the results.
- [A follow-up depends on session 1's state, so a broken session 1 makes the follow-up meaningless.] → The follow-up still runs. The summary reports regression-free only over runs whose session 1 passed the original hidden tests, and gives that count.
- [Hidden tests are public in this repo, and other runs' solutions sit in sibling folders.] → Web tools are off, streams live outside the run repos, and any out-of-repo path in a tool input is flagged. A flagged session stays in the raw table, and the summary gives the verdict with and without flagged sessions.

## Migration Plan

None. This is new dev tooling, and rollback is deleting `bench/`. Run repos and `bench-venv` are disposable.

## Open Questions

- The exact per-session cost cap. It is set from the pilot (three times the highest pilot cost) and recorded in the results.
