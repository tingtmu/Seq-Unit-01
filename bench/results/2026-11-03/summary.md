# Cue benchmark summary

Haiku only, 3 reps per arm: a self-test, not statistical significance. The raw table is below.

## Verdict

**DROP (cues don't pay)**

Row applied: 4
- Inputs: exposed True, A high True, B high False, A vs B test-first +1, outcome +0, test-first runs did better False
- Cost (A vs B, lower is better): +0

Without flagged sessions: **DROP (cues don't pay)** (row 4)
- Inputs: exposed True, A high True, B high False, A vs B test-first +1, outcome +0, test-first runs did better False

## Decision rule

Rows are checked top to bottom; the first that matches applies.

| # | Condition | Verdict |
|---|-----------|---------|
| 1 | A not exposed | CUES NOT REACHED |
| 2 | A high and B high | DROP (default behavior) |
| 3 | A > B and outcome: A better | KEEP |
| 4 | A > B and outcome: no difference or A worse | DROP (cues don't pay) |
| 5 | A low and B low and test-first runs did better | STRENGTHEN (weak: observational) |
| 6 | A low and B low | DROP |
| 7 | otherwise | INCONCLUSIVE |

Thresholds for "different": yes/no measures differ by at least one run per task, in the same direction in every task; rates by at least 0.10 pooled, same direction in every task; cost by at least 25% pooled, same direction in every task. High compliance is test-first in at least 6 of 9 runs (2/3) per arm. Exposed means at least half of arm A's first sessions read a cue file before coding. Test-first runs did better means their mean hidden pass rate beats the other runs by at least 0.10, with at least 3 runs in each group. Outcome is the hidden pass rate, the regression-free rate, and the silent-wrong rate; if they disagree, outcome is no difference.

## Per task and arm

First sessions; regression-free counts only runs whose first session passed every hidden test (n in brackets). pass^3: all reps passed every hidden test.

| Task | Arm | Runs | Pass rate | pass^3 | Silent-wrong | Regression-free (n) | Kill rate | Cost USD (unknown) | Exposed | Test-first | Saw red | Test/code | Out-of-repo | Hard rule |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| t1-scrna-qc | A | 3 | 1.00 | True | 0.00 | 1.00 (3) | 0.62 | 0.03 (0) | 3/3 | 3/3 | 3/3 | 1.00 | 3 | 0 |
| t1-scrna-qc | B | 3 | 1.00 | True | 0.00 | 1.00 (3) | 0.31 | 0.02 (0) | 3/3 | 0/3 | 2/3 | 0.41 | 3 | 0 |
| t2-design-check | A | 3 | 1.00 | True | 0.00 | 1.00 (3) | 0.56 | 0.03 (0) | 3/3 | 2/3 | 3/3 | 0.86 | 3 | 0 |
| t2-design-check | B | 3 | 0.99 | False | 0.33 | 1.00 (2) | 0.25 | 0.02 (0) | 3/3 | 0/3 | 3/3 | 0.65 | 1 | 0 |
| t3-de-annotation | A | 3 | 1.00 | True | 0.00 | 1.00 (3) | 0.46 | 0.01 (0) | 3/3 | 3/3 | 2/3 | 1.31 | 2 | 0 |
| t3-de-annotation | B | 3 | 1.00 | True | 0.00 | 1.00 (3) | 0.82 | 0.01 (0) | 3/3 | 0/3 | 1/3 | 0.83 | 1 | 0 |

## Invalid sessions

None.

## Flagged sessions (out-of-repo access)

- t1-scrna-qc-B-pilot session 1: /tmp/insp.py, C:/Tingwei/test_claude/personal_proj/nerv_all_runs/bench-runs/t1-scrna-qc-B-pilot/../insp_tmp.py, C:/Tingwei/test_claude/personal_proj/nerv_all_runs/bench-runs/insp_tmp.py, /
- t3-de-annotation-B-pilot session 1: ~, /_PAR_Y/, /tmp/annotated_check.tsv, /tmp/unmatched_check.txt
- t1-scrna-qc-A-r1 session 1: /features.tsv.gz
- t1-scrna-qc-B-r1 session 1: /tmp/peek.py, /, /features.tsv.gz
- t1-scrna-qc-B-r2 session 2: /
- t1-scrna-qc-A-r2 session 2: /
- t1-scrna-qc-A-r3 session 2: /, C:\Tingwei\test_claude\personal_proj\nerv_all_runs\bench-runs\check_real_qc.py
- t1-scrna-qc-B-r3 session 1: /features.tsv.gz
- t2-design-check-A-r1 session 1: /
- t2-design-check-A-r1 session 2: /tmp/edit_tests.py, ~, C:/Tingwei/test_claude/personal_proj/nerv_all_runs/bench-runs/edit_tests.py, C:/Tingwei/test_claude/personal_proj/nerv_all_runs/bench-runs
- t2-design-check-A-r3 session 2: ~
- t2-design-check-B-r3 session 2: ~
- t3-de-annotation-B-r2 session 1: ~, /PAR_Y/, /tmp/annotated_check.tsv
- t3-de-annotation-A-r2 session 1: /
- t3-de-annotation-A-r3 session 1: ~, /PAR_Y/

## Pilot

**Pilot 1** (first task versions, default effort; rows in `pilot1-runs.csv`): all three arm B sessions passed every hidden test (T1 9/9 traps, T2 10/10, T3 7/7), at $0.014–0.029 per session. No session was test-first.

**Changes after pilot 1 (task 8.2, commits a599e64 and ed9a5a0):**
- T1: CITE-seq antibody features (RNA metrics count gene expression only); barcodes with no gene UMIs get the reason `empty` and are left out of the MAD bounds; all bounds come from the same cells, independent of each other. The follow-up adds two Cell Ranger 2 folders, so the shared reader changes.
- T2: two-factor interactions in the rank check; R `make.names` collisions; one FASTQ named twice, also when written differently; a contrast on a factor outside the formula; the BOM and stray-space hints removed from the prompt. In the follow-up, every term involving batch is dropped.
- T3: the annotation is the GENCODE v43 GTF (gene, transcript, and exon rows); a new `na_reason` column follows DESeq2's NA conventions (zero counts, Cook's outlier, low mean).
- Sessions run with `--effort low`.

**Pilot 2** (redesigned tasks, `--effort low`; rows below):
- T1: 12/12 traps; no tests written.
- T2: 14/15 traps (missed `contrast_factor_in_formula`); 148 test lines, but they import the agent's own helper `make_names`, so none count toward the kill rate.
- T3: 9/9 traps; 11/13 mutants killed; saw red.
- None was test-first, and all three read a cue file (`scripts/README.md`).
- Out-of-repo flags: real ones (scratch files in `/tmp` and in `bench-runs/`), and also false positives from awk syntax (`~`, `/_PAR_Y/`, a bare `/`).

**No more trap rounds, and no cost cap** (user's decision after pilot 2). T1 and T3 passed every hidden test twice, so the difference between the arms is expected in the process measures (test-first, mutant kill rate) and in follow-up regressions, not in first-session pass rates. A cap at three times the pilot cost ($0.07) could cut off arm A sessions that write tests first, so the grid runs uncapped; the 30-minute limit stays.

- t1-scrna-qc-B-pilot: pass rate 1.00, cost 0.01
- t2-design-check-B-pilot: pass rate 0.96, cost 0.02
- t3-de-annotation-B-pilot: pass rate 1.00, cost 0.02

## Raw table

| run | session | completed | limit | cost_usd | hidden_pass_rate | traps_passed | silent_wrong | regression_free | mutant_kill_rate | exposed | test_first | saw_red | test_code_ratio | hard_rule_violation | invalid | out_of_repo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| t1-scrna-qc-A-r1 | 1 | True | - | 0.03 | 1.00 | 12 | False | - | 0.60 | True | True | True | 1.10 | False | - | /features.tsv.gz |
| t1-scrna-qc-A-r1 | 2 | True | - | 0.04 | 1.00 | 8 | False | True | 0.25 | True | False | False | 1.02 | False | - | - |
| t1-scrna-qc-B-r1 | 1 | True | - | 0.03 | 1.00 | 12 | False | - | 0.47 | True | False | True | 0.60 | False | - | /tmp/peek.py, /, /features.tsv.gz |
| t1-scrna-qc-B-r1 | 2 | True | - | 0.03 | 1.00 | 8 | False | True | 0.12 | True | False | False | 0.84 | False | - | - |
| t1-scrna-qc-B-r2 | 1 | True | - | 0.02 | 1.00 | 12 | False | - | 0.47 | True | False | True | 0.63 | False | - | - |
| t1-scrna-qc-B-r2 | 2 | True | - | 0.03 | 1.00 | 8 | False | True | 0.25 | True | False | True | 1.20 | False | - | / |
| t1-scrna-qc-A-r2 | 1 | True | - | 0.03 | 1.00 | 12 | False | - | 0.60 | True | True | True | 1.12 | False | - | - |
| t1-scrna-qc-A-r2 | 2 | True | - | 0.03 | 1.00 | 8 | False | True | 0.12 | True | True | True | 1.38 | False | - | / |
| t1-scrna-qc-A-r3 | 1 | True | - | 0.03 | 1.00 | 12 | False | - | 0.67 | True | True | True | 0.78 | False | - | - |
| t1-scrna-qc-A-r3 | 2 | True | - | 0.04 | 1.00 | 8 | False | True | 0.12 | False | False | unknown | 1.33 | False | - | /, C:\Tingwei\test_claude\personal_proj\nerv_all_runs\bench-runs\check_real_qc.py |
| t1-scrna-qc-B-r3 | 1 | False | - | 0.01 | 1.00 | 12 | False | - | 0.00 | True | False | False | 0.00 | False | - | /features.tsv.gz |
| t1-scrna-qc-B-r3 | 2 | True | - | 0.03 | 1.00 | 8 | False | True | 0.38 | True | False | False | 1.34 | False | - | - |
| t2-design-check-A-r1 | 1 | True | - | 0.03 | 1.00 | 15 | False | - | 0.84 | True | True | True | 0.93 | False | - | / |
| t2-design-check-A-r1 | 2 | True | - | 0.03 | 1.00 | 8 | False | True | 1.00 | True | True | True | 2.64 | False | - | /tmp/edit_tests.py, ~, C:/Tingwei/test_claude/personal_proj/nerv_all_runs/bench-runs/edit_tests.py, C:/Tingwei/test_claude/personal_proj/nerv_all_runs/bench-runs |
| t2-design-check-B-r1 | 1 | True | - | 0.03 | 0.96 | 14 | True | - | 0.00 | True | False | True | 0.78 | False | - | - |
| t2-design-check-B-r1 | 2 | True | - | 0.01 | 1.00 | 8 | True | False | 0.00 | False | False | True | 2.17 | False | - | - |
| t2-design-check-B-r2 | 1 | True | - | 0.04 | 1.00 | 15 | False | - | 0.74 | True | False | True | 0.56 | False | - | - |
| t2-design-check-B-r2 | 2 | True | - | 0.02 | 1.00 | 8 | False | True | 0.88 | True | False | unknown | 2.53 | False | - | - |
| t2-design-check-A-r2 | 1 | True | - | 0.03 | 1.00 | 15 | False | - | 0.84 | True | True | True | 0.85 | False | - | - |
| t2-design-check-A-r2 | 2 | True | - | 0.02 | 1.00 | 8 | False | True | 1.00 | True | True | True | 2.05 | False | - | - |
| t2-design-check-A-r3 | 1 | True | - | 0.03 | 1.00 | 15 | False | - | 0.00 | True | False | True | 0.80 | False | - | - |
| t2-design-check-A-r3 | 2 | True | - | 0.02 | 1.00 | 8 | False | True | 0.00 | True | True | True | 2.82 | False | - | ~ |
| t2-design-check-B-r3 | 1 | True | - | 0.03 | 1.00 | 15 | False | - | 0.00 | True | False | True | 0.61 | False | - | - |
| t2-design-check-B-r3 | 2 | True | - | 0.02 | 1.00 | 8 | False | True | 0.00 | False | False | unknown | 1.88 | False | - | ~ |
| t3-de-annotation-A-r1 | 1 | True | - | 0.02 | 1.00 | 9 | False | - | 0.38 | True | True | True | 1.35 | False | - | - |
| t3-de-annotation-A-r1 | 2 | True | - | 0.01 | 1.00 | 6 | False | True | 0.00 | False | False | False | 3.78 | False | - | - |
| t3-de-annotation-B-r1 | 1 | True | - | 0.02 | 1.00 | 9 | False | - | 0.77 | True | False | unknown | 0.93 | False | - | - |
| t3-de-annotation-B-r1 | 2 | True | - | 0.00 | 1.00 | 6 | False | True | 0.50 | False | False | False | 1.14 | False | - | - |
| t3-de-annotation-B-r2 | 1 | True | - | 0.02 | 1.00 | 9 | False | - | 0.77 | True | False | True | 0.76 | False | - | ~, /PAR_Y/, /tmp/annotated_check.tsv |
| t3-de-annotation-B-r2 | 2 | True | - | 0.01 | 1.00 | 6 | False | True | 0.67 | False | False | True | 2.75 | False | - | - |
| t3-de-annotation-A-r2 | 1 | True | - | 0.02 | 1.00 | 9 | False | - | 0.77 | True | True | True | 1.41 | False | - | / |
| t3-de-annotation-A-r2 | 2 | True | - | 0.01 | 1.00 | 6 | False | True | 0.67 | False | False | False | 6.17 | False | - | - |
| t3-de-annotation-A-r3 | 1 | True | - | 0.02 | 1.00 | 9 | False | - | 0.23 | True | True | False | 1.17 | False | - | ~, /PAR_Y/ |
| t3-de-annotation-A-r3 | 2 | True | - | 0.01 | 1.00 | 6 | False | True | 0.00 | False | False | False | 3.00 | False | - | - |
| t3-de-annotation-B-r3 | 1 | True | - | 0.01 | 1.00 | 9 | False | - | 0.92 | True | False | False | 0.81 | False | - | - |
| t3-de-annotation-B-r3 | 2 | True | - | 0.01 | 1.00 | 6 | False | True | 1.00 | False | False | False | 5.00 | False | - | - |
