"""Reference: per-sample scRNA-seq cell QC, follow-up (Cell Ranger 2 folders, doublet scores, MAD on pct_mito)."""
import gzip
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import mmread

MAD_SCALE = 1.4826
GENE_EXPRESSION = "Gene Expression"
REASON_ORDER = ("low_counts", "low_genes", "high_genes", "high_mito", "doublet")
CELL_COLUMNS = ["cell_id", "sample_id", "barcode", "n_counts", "n_genes", "pct_mito", "keep", "reason"]


def read_table(path, names):
    return pd.read_csv(path, sep="\t", header=None, dtype=str, names=names)


def read_mex(folder):
    """Cell Ranger 3+ (gzipped, features.tsv.gz with a type column) or Cell Ranger 2 (plain, genes.tsv)."""
    folder = Path(folder)
    if (folder / "matrix.mtx.gz").is_file():
        with gzip.open(folder / "matrix.mtx.gz", "rb") as fh:
            matrix = mmread(fh, spmatrix=False).tocsr()
        barcodes = read_table(folder / "barcodes.tsv.gz", ["barcode"])["barcode"].tolist()
        feats = read_table(folder / "features.tsv.gz", ["gene_id", "symbol", "type"])
    else:
        matrix = mmread(folder / "matrix.mtx", spmatrix=False).tocsr()
        barcodes = read_table(folder / "barcodes.tsv", ["barcode"])["barcode"].tolist()
        feats = read_table(folder / "genes.tsv", ["gene_id", "symbol"]).assign(type=GENE_EXPRESSION)
    return matrix, barcodes, feats


def metrics(matrix, feats, mito_prefix):
    genes = (feats["type"] == GENE_EXPRESSION).to_numpy()
    matrix, feats = matrix[genes, :], feats[genes]
    n_counts = np.asarray(matrix.sum(axis=0)).ravel().astype(float)
    n_genes = np.asarray((matrix > 0).sum(axis=0)).ravel().astype(float)
    is_mito = feats["symbol"].str.startswith(mito_prefix).to_numpy()
    mito = np.asarray(matrix[is_mito, :].sum(axis=0)).ravel().astype(float)
    pct_mito = np.divide(100.0 * mito, n_counts, out=np.zeros_like(n_counts), where=n_counts > 0)
    return n_counts, n_genes, pct_mito


def mad_outliers(values, nmads, among, tail, log):
    """One-tailed MAD outliers ("low" or "high"), median and MAD over `among`. None when MAD is 0."""
    x = np.log1p(values) if log else np.asarray(values, dtype=float)
    med = np.median(x[among])
    mad = MAD_SCALE * np.median(np.abs(x[among] - med))
    if mad == 0:
        return None
    if tail == "low":
        return x < med - nmads * mad
    return x > med + nmads * mad


def read_thresholds(path):
    table = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    return {row["sample_id"].strip(): row for _, row in table.iterrows()}


def value(row, column):
    text = str(row.get(column, "")).strip()
    return None if text == "" else float(text)


def lower_filter(values, fixed, nmads, metric, notes, among):
    if fixed is not None:
        return values < fixed
    low = mad_outliers(values, nmads, among, "low", log=True)
    if low is None:
        notes.append(f"mad_zero:{metric}")
        return np.zeros(len(values), dtype=bool)
    return low


def mito_filter(pct_mito, fixed, nmads, notes, among):
    if fixed is not None:
        return pct_mito > fixed
    high = mad_outliers(pct_mito, nmads, among, "high", log=False)
    if high is None:
        notes.append("mad_zero:pct_mito")
        return np.zeros(len(pct_mito), dtype=bool)
    return high


def read_doublet_scores(doublet_dir, sample_id, barcodes):
    path = Path(doublet_dir) / f"{sample_id}.tsv"
    table = pd.read_csv(path, sep="\t", dtype={"barcode": str})
    scores = dict(zip(table["barcode"], table["doublet_score"].astype(float)))
    missing = [b for b in barcodes if b not in scores]
    if missing:
        raise ValueError(f"sample {sample_id}: barcode {missing[0]} has no doublet score in {path}")
    return np.array([scores[b] for b in barcodes])


def reason(i, empty, flags):
    if empty[i]:
        return "empty"
    return ";".join(code for code in REASON_ORDER if flags[code][i])


def filter_sample(sample_id, folder, row, mito_prefix, nmads, doublet_dir):
    matrix, barcodes, feats = read_mex(folder)
    n_counts, n_genes, pct_mito = metrics(matrix, feats, mito_prefix)
    empty = n_counts == 0
    among = ~empty
    notes = []
    max_genes = value(row, "max_genes")
    low_genes = lower_filter(n_genes, value(row, "min_genes"), nmads, "n_genes", notes, among)
    low_counts = lower_filter(n_counts, value(row, "min_counts"), nmads, "n_counts", notes, among)
    flags = {
        "low_counts": low_counts,
        "low_genes": low_genes,
        "high_genes": n_genes > max_genes if max_genes is not None else np.zeros(len(n_genes), dtype=bool),
        "high_mito": mito_filter(pct_mito, value(row, "max_pct_mito"), nmads, notes, among),
        "doublet": read_doublet_scores(doublet_dir, sample_id, barcodes) > value(row, "doublet_score_max"),
    }
    reasons = [reason(i, empty, flags) for i in range(len(barcodes))]
    cells = pd.DataFrame({
        "cell_id": [f"{sample_id}:{b}" for b in barcodes], "sample_id": sample_id, "barcode": barcodes,
        "n_counts": n_counts, "n_genes": n_genes, "pct_mito": pct_mito,
        "keep": [r == "" for r in reasons], "reason": reasons,
    })
    return cells, notes


def filter_cells(matrix_dirs, thresholds, mito_prefix, nmads=3.0, doublet_dir=None):
    rows = read_thresholds(thresholds)
    frames, summary = [], []
    for sample_id, folder in matrix_dirs.items():
        if sample_id not in rows:
            raise ValueError(f"sample {sample_id!r} has no row in {thresholds}")
        cells, notes = filter_sample(sample_id, folder, rows[sample_id], mito_prefix, nmads, doublet_dir)
        frames.append(cells)
        summary.append({"sample_id": sample_id, "n_cells": len(cells), "n_kept": int(cells["keep"].sum()),
                        "notes": ";".join(notes)})
    return pd.concat(frames, ignore_index=True)[CELL_COLUMNS], pd.DataFrame(summary)
