"""Seeded inputs for T1: four mouse 10x samples (two CITE-seq), QC thresholds, and the follow-up
delivery (two Cell Ranger 2 samples) with doublet scores."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mex  # noqa: E402

SEED = 20261103
N_NUCLEAR = 800
N_ADT = 4
# sample: (cells, depth, antibody panel, delivery, Cell Ranger 2 layout)
SAMPLES = {
    "WT_1": (220, 3200, False, "delivery-01", False),
    "WT_2": (180, 1400, False, "delivery-01", False),
    "KO_1": (240, 2600, True, "delivery-01", False),
    "KO_2": (7, 0, True, "delivery-01", False),
}
FOLLOWUP_SAMPLES = {
    "WT_3": (160, 1800, False, "delivery-02", True),
    "KO_3": (150, 2000, False, "delivery-02", True),
}
CONDITION = {"WT_1": "wildtype", "WT_2": "wildtype", "KO_1": "knockout", "KO_2": "knockout",
             "WT_3": "wildtype", "KO_3": "knockout"}
SHARED_BARCODE = "TTTGTCAAGTGACATA-1"
THRESHOLD_COLUMNS = ["sample_id", "min_genes", "max_genes", "min_counts", "max_pct_mito", "doublet_method", "notes"]
THRESHOLDS = {
    "WT_1": ["200", "4000", "500", "15", "scrublet", "fixed after pilot"],
    "WT_2": ["", "", "", "10", "scrublet", "low depth: MAD"],
    "KO_1": ["200", "", "", "15", "scrublet", "counts by MAD; CITE-seq panel"],
    "KO_2": ["", "", "", "20", "scrublet", "few cells captured; CITE-seq panel"],
    "WT_3": ["", "", "", "", "scrublet", "Cell Ranger 2 rerun"],
    "KO_3": ["150", "", "", "", "scrublet", "Cell Ranger 2 rerun"],
}
FOLLOWUP_MITO_BLANK = ("WT_2", "KO_1")
DOUBLET_MAX = {"WT_1": "0.25", "WT_2": "0.30", "KO_1": "0.25", "KO_2": "0.30", "WT_3": "0.25", "KO_3": "0.25"}


def barcodes(rng, n):
    seqs = set()
    while len(seqs) < n:
        seqs.add("".join(rng.choice(list("ACGT"), 16)) + "-1")
    return sorted(seqs)


def sample_cells(rng, n_cells, depth, n_adt):
    """Gene counts per cell: log-normal depth, a mito fraction, multinomial over genes.

    With an antibody panel, every barcode has antibody counts, and a few barcodes were called
    on antibodies alone (no gene UMIs).
    """
    probs = rng.dirichlet(np.full(N_NUCLEAR, 0.3))
    cells = []
    for i in range(n_cells):
        total = int(rng.lognormal(np.log(depth), 0.45))
        if i == 3 or (n_adt and i % 23 == 7):
            total = 0
        mito = int(total * min(0.6, rng.beta(2, 40) + (0.3 if i % 37 == 5 else 0)))
        counts = rng.multinomial(total - mito, probs)
        cell = {3 + j: int(c) for j, c in enumerate(counts) if c}
        if mito:
            split = rng.multinomial(mito, [0.6, 0.25, 0.15])
            cell.update({j: int(c) for j, c in enumerate(split) if c})
        if n_adt:
            tags = rng.multinomial(int(rng.lognormal(np.log(3 * depth), 0.5)), np.full(n_adt, 1 / n_adt))
            cell.update({3 + N_NUCLEAR + k: int(c) for k, c in enumerate(tags) if c})
        cells.append(cell)
    return cells


def tiny_cells():
    """A small uniform sample: most cells identical, so the MAD of counts and genes is 0."""
    def one(total, genes, mito):
        return mex.cell(total, genes, mito, n_nuclear=N_NUCLEAR, adt=2400, n_adt=N_ADT)
    return [one(1500, 600, 30)] * 5 + [one(900, 450, 20), one(2600, 700, 40)]


def tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join("\t".join(r) + "\n" for r in rows), encoding="utf-8", newline="\n")


def build_samples(rng, samples):
    """{sample id: (barcodes, cells)}; one barcode is shared by WT_1 and KO_1."""
    built = {}
    for sample_id, (n_cells, depth, panel, _, _) in samples.items():
        codes = barcodes(rng, n_cells)
        cells = sample_cells(rng, n_cells, depth, N_ADT if panel else 0) if depth else tiny_cells()
        if sample_id in ("WT_1", "KO_1"):
            codes[10] = SHARED_BARCODE
        built[sample_id] = (codes, cells)
    return built


def write_samples(out, specs, built):
    for sample_id, (codes, cells) in built.items():
        _, _, panel, delivery, v2 = specs[sample_id]
        feats = mex.features(N_NUCLEAR, N_ADT if panel else 0)
        mex.write_mex(out / "data/raw" / delivery / sample_id, codes, feats, cells, v2=v2)


def sample_sheet(out, specs):
    tsv(out / "config/samples.tsv", [["sample_id", "matrix_dir", "condition"]]
        + [[s, f"data/raw/{specs[s][3]}/{s}", CONDITION[s]] for s in specs])


def first(out, built):
    write_samples(out, SAMPLES, built)
    sample_sheet(out, SAMPLES)
    tsv(out / "config/qc_thresholds.tsv", [THRESHOLD_COLUMNS] + [[s, *THRESHOLDS[s]] for s in SAMPLES])


def followup(out, rng, built):
    new = build_samples(rng, FOLLOWUP_SAMPLES)
    write_samples(out, FOLLOWUP_SAMPLES, new)
    specs = {**SAMPLES, **FOLLOWUP_SAMPLES}
    sample_sheet(out, specs)
    columns = THRESHOLD_COLUMNS[:5] + ["doublet_score_max"] + THRESHOLD_COLUMNS[5:]
    rows = [columns]
    for s in specs:
        values = list(THRESHOLDS[s])
        if s in FOLLOWUP_MITO_BLANK:
            values[3] = ""
        rows.append([s, *values[:4], DOUBLET_MAX[s], *values[4:]])
    tsv(out / "config/qc_thresholds.tsv", rows)
    for s, (codes, _) in {**built, **new}.items():
        scores = np.round(rng.beta(1.2, 9, len(codes)), 4)
        tsv(out / "data/processed/doublets" / f"{s}.tsv",
            [["barcode", "doublet_score"]] + [[b, f"{v:.4f}"] for b, v in zip(codes, scores)])


def generate(out, stage="first"):
    """Write the stage's inputs under `out`, at their project-relative paths."""
    out = Path(out)
    rng = np.random.default_rng(SEED)
    built = build_samples(rng, SAMPLES)
    if stage == "first":
        first(out, built)
    else:
        followup(out, rng, built)
