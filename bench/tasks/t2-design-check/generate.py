"""Seeded inputs for T2: a core-delivered sample sheet with every trap, a design, and FASTQ stubs."""
import gzip
from pathlib import Path

import numpy as np

SEED = 20261104
BOM = b"\xef\xbb\xbf"
DESIGN = """\
# Differential expression design. Fix the formula and contrasts BEFORE looking at results.
design: "~ batch + condition"   # columns must exist in config/samples.tsv
reference_level:
  condition: control

contrasts:
  # name: [factor, numerator, denominator]
  treated_vs_control: [condition, treated, control]
  knockout_vs_control: [condition, knockout, control]

thresholds:
  padj: 0.05
  lfc: 1                        # log2 fold-change threshold tested (not post-hoc filtered)
"""
# sample_id, fastq_1, fastq_2, condition, batch: as the core sent it, traps included
FIRST = [
    ("CTL_1", "d1/CTL_1_R1.fastq.gz", "d1/CTL_1_R2.fastq.gz", "control", "run1"),
    ("CTL_2", "d1/CTL_2_R1.fastq.gz", "d1/CTL_2_R2.fastq.gz", "control ", "run2"),     # stripped: fine
    ("CTL_3", "d1/CTL_3_R1.fastq.gz", "d1/CTL_3_R2.fastq.gz", "Control", "run1"),      # case conflict
    ("TRT_1", "d1/TRT_1_R1.fastq.gz", "d1/TRT_1_R2.fastq.gz", "treated", "run1"),
    ("TRT_2", "d1/TRT_2_R1.fastq.gz", "", "treated", "run2"),                          # no fastq_2
    ("TRT_3", "d1/TRT_3_R1.fastq.gz", "d1/TRT_3_R2.fastq.gz", "treated", "run2"),
    ("TRT_3 ", "d1/TRT_3b_R1.fastq.gz", "d1/TRT_3b_R2.fastq.gz", "treated", "run1"),   # duplicate id
    ("KO_1", "d1/KO_1_R1.fastq.gz", "d1/KO_1_R2.fastq.gz", "knockout", "run3"),
    ("KO-2", "d1/KO-2_R1.fastq.gz", "d1/KO-2_R2.fastq.gz", "knockout", "run3"),         # KO.2 in R
    ("KO.2", "d1/KO.2_R1.fastq.gz", "d1/KO-2_R2.fastq.gz", "knockout", "run1"),         # R2 pasted from KO-2
]
MISSING = {"d1/TRT_1_R2.fastq.gz"}                                                     # not delivered
FOLLOWUP_NEW = [
    ("TRT_4", "d2/TRT_4.fastq.gz", "", "SE", "treated"),
    ("TRT_5", "d2/TRT_5.fastq.gz", "d2/TRT_5_R2.fastq.gz", "SE", "treated"),           # SE with fastq_2
    ("KO_2", "d2/KO_2.fastq.gz", "", "SE", "knockout"),
    ("KO_3", "d2/KO_3_R1.fastq.gz", "", "PE", "knockout"),                             # PE without fastq_2
]


def fastq(rng, n_reads=8):
    lines = []
    for i in range(n_reads):
        seq = "".join(rng.choice(list("ACGT"), 50))
        lines += [f"@read{i}", seq, "+", "I" * 50]
    return gzip.compress(("\n".join(lines) + "\n").encode(), mtime=0)


def write_sheet(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join("\t".join(r) + "\n" for r in [header, *rows])
    path.write_bytes(BOM + text.replace("\n", "\r\n").encode("utf-8"))


def rel(name):
    """Sheet paths are relative to data/raw/, so they start with the delivery folder."""
    return name.replace("d1/", "delivery-01/").replace("d2/", "delivery-02/")


def stubs(out, rng, names):
    for name in sorted(names):
        path = out / "data/raw" / rel(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(fastq(rng))


def generate(out, stage="first"):
    """Write the stage's inputs under `out`, at their project-relative paths."""
    out = Path(out)
    if stage == "first":
        stubs(out, np.random.default_rng(SEED), {n for r in FIRST for n in r[1:3] if n} - MISSING)
        write_sheet(out / "config/samples.tsv", ["sample_id", "fastq_1", "fastq_2", "condition", "batch"],
                    [(s, rel(a), rel(b), c, bt) for s, a, b, c, bt in FIRST])
        (out / "config/design.yaml").write_text(DESIGN, encoding="utf-8", newline="\n")
        return
    stubs(out, np.random.default_rng(SEED + 1), {n for r in FOLLOWUP_NEW for n in r[1:3] if n})
    rows = [(s, rel(a), rel(b), "PE", c) for s, a, b, c, _ in FIRST]
    rows += [(s, rel(a), rel(b), layout, c) for s, a, b, layout, c in FOLLOWUP_NEW]
    write_sheet(out / "config/samples.tsv", ["sample_id", "fastq_1", "fastq_2", "layout", "condition"], rows)
