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

**Ceiling:** T1 and T3 pass-rate outcomes sit at the ceiling (1.00 in both arms in the pilots and the grid), so they cannot show a difference between the arms. A DROP verdict from row 4 partly reflects that ceiling: it says the cues changed behavior without a measurable outcome gain on these tasks, not that they cannot pay on harder ones.
