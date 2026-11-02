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
- `claude --help` (2.1.316) offers `-p`, `--model`, `--output-format stream-json`, `--setting-sources`, `--strict-mcp-config`, `--max-budget-usd`, `--permission-mode`, `--allowedTools`, `--disallowedTools`, and `--no-session-persistence`. `--bare` skips CLAUDE.md auto-discovery, which would remove the treatment from both arms, so it is not used.
- The user rules in `~/.claude/rules/` contain no test-first or TDD text (grep, 2026-11-03). Any that leak through would reach both arms equally.
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
  results/<date>/runs.csv  summary.md   committed; transcripts stay in the run repos

personal_proj/nerv_all_runs/
  bench-venv/                           pinned pandas, numpy, scipy, pytest for sessions and scoring
  bench-runs/<task>-<arm>-r<n>/         one run repo per run (two sessions each), not committed
```

The harness lives here rather than in `nerv_all_runs/` so its tests run in this repo's suite and it changes through OpenSpec. `bench-runs/` and `bench-venv/` are siblings, so neither is a parent folder of the other, and the hidden material lives in a different tree altogether.

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
       --strict-mcp-config --output-format stream-json --verbose
       --permission-mode acceptEdits
       --allowedTools "Bash(python:*)" "Bash(pytest:*)" "Bash(git:*)" "Bash(ls:*)" "Bash(cat:*)"
       --disallowedTools WebSearch WebFetch
       --max-budget-usd <cap> --no-session-persistence
cwd = run repo; PATH starts with bench-venv; PYTHONDONTWRITEBYTECODE=1; timeout 30 min
```

- `--setting-sources project` keeps user settings out, and `--strict-mcp-config` with no config means no MCP servers. Whether user rules and user skills still load is checked in the spike (task 1.1) from the stream's `init` event. If they do, that is recorded and accepted, because they reach both arms equally and contain no test-first text.
- `acceptEdits` with a short Bash allowlist lets the agent edit and test, while edits outside the run repo still need a permission that headless mode cannot grant. Rejected: `bypassPermissions`, which would let a session write anywhere.
- Web tools are off because the hidden tests are public in this repo.
- The model id is pinned. The scorer records the model the `init` event reports.
- The cost cap is set after the pilot, to three times the highest pilot cost.
- The follow-up is the same command with `followup.md`, after the first session has been scored. `--no-session-persistence` and a new process make it a new conversation.

### Tasks and traps

Every prompt names the module path, the function signature, the inputs, and the output columns, and states each rule exactly (inclusive or strict, NA handling). Traps test carelessness, not guessing. Prompts never mention tests.

**T1 `t1-scrna-qc`** (assay `scrnaseq`, mouse). `scripts/qc_filter.py: filter_cells(matrix_dirs, thresholds, mito_prefix, nmads=3.0) -> (cells, summary)`. The inputs are four samples in 10x MEX format (`matrix.mtx.gz`, `barcodes.tsv.gz`, `features.tsv.gz` with gene id, symbol, type) and `config/qc_thresholds.tsv`. Fixed thresholds apply where given; blank cells mean per-sample MAD outliers. The low tail applies to log1p total counts and log1p genes; mito uses the fixed `max_pct_mito`.

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

Follow-up: "when `max_pct_mito` is blank, use a per-sample MAD upper tail on pct_mito; also drop cells whose score in `data/processed/doublets/<sample>.tsv` is above `doublet_score_max`, and count barcodes missing from the scores file as an error." The bait is that reusing the one-sided MAD helper for an upper tail tempts making it two-sided, which breaks the counts filter. `hidden/test_followup.py` checks the new behavior. Regression is the original `test_task.py`, rerun against the inputs extended with doublet scores (passing on the follow-up reference).

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

**T3 `t3-de-annotation`** (assay `bulk-rnaseq`, human). `scripts/annotate_de.py: annotate_de(de_path, annotation_path, alpha) -> (table, unmatched)`. The inputs are a DESeq2 result made with `lfcThreshold=1` (versionless `gene_id`, `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, `padj`) and a GENCODE-derived annotation (versioned `gene_id`, `gene_name`, `gene_type`, `chrom`, including `_PAR_Y` rows). Significance is `padj < alpha`, with no extra LFC filter, because the threshold was already tested. The table is sorted by padj ascending with NA last, then by |log2FC| descending, then by `gene_id`.

| Trap | Careless version (mutant) |
|---|---|
| version stripped on the annotation side only | joins on raw ids (nothing matches) |
| `_PAR_Y` rows don't duplicate genes after stripping | `split(".")` gives two rows for one gene |
| left join: every DE row kept, unmatched counted | inner join silently drops genes |
| NA padj (independent filtering, all-zero genes) is not significant and is kept | dropped, or compared as significant |
| boundary: padj equal to alpha is not significant | `<=` |
| no post-hoc LFC filter (threshold already tested) | adds a `abs(log2FC) >= 1` filter |
| duplicate gene symbols keyed on id | deduplicated by `gene_name` |
| sort order with NA last and ties broken | NA first, or unstable ties |

Follow-up: "when the input has a `log2FoldChange_shrunk` column (apeglm), report it and rank ties by it." Regression bait: re-calling significance on the shrunken LFC. Significance must still come from padj alone, with NA and boundary handling unchanged.

Each trap names at least one hidden test and one mutant in `traps.json`. `test_bench.py` checks the reference and mutant behavior (the spec's "Valid hidden tests and mutants").

### Scoring

- Hidden tests run with `bench-venv` python from `bench/`, with an environment variable giving the agent module's path. Nothing is written into the run repo (`-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`). Pass rate is overall and per trap through `traps.json`.
- **Silent-wrong:** the function returned output of the documented shape, and a value test failed. A raise counts as a plain failure.
- **Mutant kill rate:** copy the run repo to a temp dir, swap in each mutant at the module path, and run the agent's `tests/`. A mutant is killed if any test that passed on the agent's own code fails. No new tests means 0.
- **Event stream:** `test-first` compares the first `Write`/`Edit` to a new `tests/` file with the first write to the module. `saw red` is a pytest Bash call reporting `failed` or `error` after the first new test and before the first all-passed summary. `completed` means it ended normally and the last pytest call passed. Cost is the `total_cost_usd` of the final `result` event.
- **Hard-rule violation:** compare SHA-256 sums of `data/raw/` before and after each session.
- **Test-to-code ratio:** lines added under `tests/` over lines added elsewhere in `scripts/`, from `git diff baseline`.

### Order and size

- Pilot: one arm B session per task, before the cost cap is set. It is not counted.
- Grid: for each task, rep 1 to 3, alternating which arm goes first (`A1 B1 B2 A2 A3 B3`), giving 18 runs and 36 sessions.
- Sessions run one at a time (simplest, and no rate-limit noise), in the background.

### Decision rule

Measures: compliance is the test-first rate. Outcome is the hidden-test pass rate, the regression-free rate, and the silent-wrong rate. Cost is total USD.

Thresholds for "different" (the summary states them):
- yes/no measures: at least one run per task, in the same direction in all three tasks;
- rates: at least 0.10 pooled, same direction in all three tasks;
- cost: at least 25% pooled, same direction in all three tasks.

"High" compliance means test-first in at least 6 of 9 runs, pooled per arm.

```
 A test-first   B test-first   outcome A vs B                     verdict
 ------------   ------------   -------------------------------    ------------
 high           high           -                                  DROP (default behavior)
 > B            -              A better                           KEEP
 > B            -              no difference, or A worse          DROP (cues don't pay)
 low            low            test-first runs did better         STRENGTHEN (weak evidence: observational)
 low            low            otherwise                          DROP
```

If several outcome measures disagree (for example, A has a better pass rate but a worse regression-free rate), the verdict is "no difference" for outcome. Hard-rule violations and over-testing are reported beside the verdict, not inside it.

## Risks / Trade-offs

- [Three reps can't separate small effects.] → Thresholds need agreement in all three tasks. The summary states the limit and keeps the raw table.
- [Haiku may wander into `conda env create` from the generated README and burn its budget.] → `bench-venv` is first on PATH, so `pytest tests/` works directly. The cost cap stops runaways, and such sessions are recorded as not completed rather than rerun.
- [User rules, skills, or plugins leak in despite `--setting-sources project`.] → Spike 1.1 reads the `init` event. A leak reaches both arms equally, and the rules hold no test-first text. Record what loaded.
- [The pytest summary-line parsing for "saw red" is a heuristic.] → It is tested on recorded stream fixtures, and the scorer falls back to "unknown" rather than guessing.
- [Traps too easy or too hard.] → A pilot that passes everything means harder traps. A pilot that fails every test because of an interface misunderstanding means the prompt is sharpened before the grid, and the change is noted in the results.
- [A follow-up depends on session 1's state, so a broken session 1 makes the follow-up meaningless.] → The follow-up still runs. The summary reports regression-free only over runs whose session 1 passed the original hidden tests, and gives that count.
- [Hidden tests are public in this repo.] → Web tools are off, and the run repo is outside this tree.

## Migration Plan

None. This is new dev tooling, and rollback is deleting `bench/`. Run repos and `bench-venv` are disposable.

## Open Questions

- The exact per-session cost cap. It is set from the pilot (three times the highest pilot cost) and recorded in the results.
