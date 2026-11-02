"""Seeded inputs for T1: four mouse 10x samples, QC thresholds, and the follow-up doublet scores."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mex  # noqa: E402

SEED = 20261103
N_NUCLEAR = 800
SAMPLES = {"WT_1": (220, 3200), "WT_2": (180, 1400), "KO_1": (240, 2600), "KO_2": (7, 0)}
CONDITION = {"WT_1": "wildtype", "WT_2": "wildtype", "KO_1": "knockout", "KO_2": "knockout"}
SHARED_BARCODE = "TTTGTCAAGTGACATA-1"
THRESHOLD_COLUMNS = ["sample_id", "min_genes", "max_genes", "min_counts", "max_pct_mito", "doublet_method", "notes"]
THRESHOLDS = {
    "WT_1": ["200", "4000", "500", "15", "scrublet", "fixed after pilot"],
    "WT_2": ["", "", "", "10", "scrublet", "low depth: MAD"],
    "KO_1": ["200", "", "", "15", "scrublet", "counts by MAD"],
    "KO_2": ["", "", "", "20", "scrublet", "few cells captured"],
}
FOLLOWUP_MITO_BLANK = ("WT_2", "KO_1")
DOUBLET_MAX = {"WT_1": "0.25", "WT_2": "0.30", "KO_1": "0.25", "KO_2": "0.30"}


def barcodes(rng, n):
    seqs = set()
    while len(seqs) < n:
        seqs.add("".join(rng.choice(list("ACGT"), 16)) + "-1")
    return sorted(seqs)


def sample_cells(rng, n_cells, depth):
    """Gene counts per cell: log-normal depth, a mito fraction, multinomial over genes."""
    probs = rng.dirichlet(np.full(N_NUCLEAR, 0.3))
    cells = []
    for i in range(n_cells):
        total = int(rng.lognormal(np.log(depth), 0.45))
        if i == 3:
            total = 0
        mito = int(total * min(0.6, rng.beta(2, 40) + (0.3 if i % 37 == 5 else 0)))
        counts = rng.multinomial(total - mito, probs)
        cell = {3 + j: int(c) for j, c in enumerate(counts) if c}
        if mito:
            split = rng.multinomial(mito, [0.6, 0.25, 0.15])
            cell.update({j: int(c) for j, c in enumerate(split) if c})
        cells.append(cell)
    return cells


def tiny_cells():
    """A small uniform sample: most cells identical, so the MAD of counts and genes is 0."""
    same = mex.cell(1500, 600, 30, n_nuclear=N_NUCLEAR)
    return [same] * 5 + [mex.cell(900, 450, 20, n_nuclear=N_NUCLEAR), mex.cell(2600, 700, 40, n_nuclear=N_NUCLEAR)]


def tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join("\t".join(r) + "\n" for r in rows), encoding="utf-8", newline="\n")


def build_samples(rng):
    """{sample id: (barcodes, cells)}; one barcode is shared by WT_1 and KO_1."""
    samples = {}
    for sample_id, (n_cells, depth) in SAMPLES.items():
        codes = barcodes(rng, n_cells)
        cells = sample_cells(rng, n_cells, depth) if depth else tiny_cells()
        if sample_id in ("WT_1", "KO_1"):
            codes[10] = SHARED_BARCODE
        samples[sample_id] = (codes, cells)
    return samples


def first(out, samples):
    feats = mex.features(N_NUCLEAR)
    for sample_id, (codes, cells) in samples.items():
        mex.write_mex(out / "data/raw/delivery-01" / sample_id, codes, feats, cells)
    tsv(out / "config/samples.tsv", [["sample_id", "matrix_dir", "condition"]]
        + [[s, f"data/raw/delivery-01/{s}", CONDITION[s]] for s in SAMPLES])
    tsv(out / "config/qc_thresholds.tsv", [THRESHOLD_COLUMNS] + [[s, *THRESHOLDS[s]] for s in SAMPLES])


def followup(out, rng, samples):
    columns = THRESHOLD_COLUMNS[:5] + ["doublet_score_max"] + THRESHOLD_COLUMNS[5:]
    rows = [columns]
    for s in SAMPLES:
        values = list(THRESHOLDS[s])
        if s in FOLLOWUP_MITO_BLANK:
            values[3] = ""
        rows.append([s, *values[:4], DOUBLET_MAX[s], *values[4:]])
    tsv(out / "config/qc_thresholds.tsv", rows)
    for s, (codes, _) in samples.items():
        scores = np.round(rng.beta(1.2, 9, len(codes)), 4)
        tsv(out / "data/processed/doublets" / f"{s}.tsv",
            [["barcode", "doublet_score"]] + [[b, f"{v:.4f}"] for b, v in zip(codes, scores)])


def generate(out, stage="first"):
    """Write the stage's inputs under `out`, at their project-relative paths."""
    out = Path(out)
    rng = np.random.default_rng(SEED)
    samples = build_samples(rng)
    if stage == "first":
        first(out, samples)
    else:
        followup(out, rng, samples)
