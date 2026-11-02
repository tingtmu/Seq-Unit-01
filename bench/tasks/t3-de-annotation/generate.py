"""Seeded inputs for T3: a DESeq2 result (lfcThreshold=1, greaterAbs) and a GENCODE v43 gene table."""
from pathlib import Path

import numpy as np
from scipy.stats import norm

SEED = 20261105
N_GENES = 1500
DE_PATH = "data/processed/deseq2/treated_vs_control.tsv"
ANN_PATH = "data/reference/gencode.v43.genes.tsv"
PAR_GENES = 6                 # genes on the X/Y pseudoautosomal regions, listed twice in GENCODE v43
SHARED_SYMBOLS = 8            # pairs of distinct gene ids with the same symbol
DE_ONLY = 12                  # DE ids not in the annotation (retired ids)
ANN_ONLY = 40                 # annotated genes absent from the DE table
TYPES = ["protein_coding"] * 6 + ["lncRNA"] * 3 + ["processed_pseudogene"]


def bh(p):
    """Benjamini-Hochberg adjusted p-values for a 1-d array without NaN."""
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(p)
    out[order] = np.minimum(adjusted, 1.0)
    return out


def de_table(rng):
    ids = [f"ENSG{n:011d}" for n in rng.choice(np.arange(100000, 999999), N_GENES, replace=False)]
    base = np.round(rng.lognormal(5.5, 1.8, N_GENES), 3)
    base[:15] = 0.0                                            # all-zero genes
    lfc = np.round(rng.normal(0, 1.3, N_GENES), 4)
    se = np.round(0.15 + 2.5 / np.sqrt(base + 1), 4)
    stat = np.where(np.abs(lfc) > 1, np.sign(lfc) * (np.abs(lfc) - 1) / se, 0.0)
    pvalue = np.where(np.abs(lfc) > 1, 2 * norm.sf(np.abs(stat)), 1.0)
    filtered = base < 8                                        # independent filtering
    padj = np.full(N_GENES, np.nan)
    padj[~filtered] = bh(pvalue[~filtered])
    for column in (lfc, se, stat, pvalue):                     # DESeq2 gives all-zero genes NA
        column[:15] = np.nan
    candidates = np.where(~filtered & (np.abs(lfc) > 1.5))[0]
    padj[candidates[0]] = 0.05                                 # exactly at alpha
    return ids, base, lfc, se, stat, pvalue, padj


def fmt(x, digits=6):
    return "NA" if np.isnan(x) else f"{x:.{digits}g}"


def shrink(rng, lfc, se):
    """apeglm-like shrinkage: toward 0, more for noisy genes, never across 0."""
    weight = 1 / (1 + (se / 0.25) ** 2) * rng.uniform(0.85, 1.0, len(lfc))
    return np.round(lfc * weight, 4)


def write_de(out, rng, shrunk=False):
    ids, base, lfc, se, stat, pvalue, padj = de_table(rng)
    columns = ["gene_id", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"]
    values = [ids, base, lfc, se, stat, pvalue, padj]
    if shrunk:
        columns.insert(3, "log2FoldChange_shrunk")
        values.insert(3, shrink(np.random.default_rng(SEED + 1), lfc, se))
    lines = ["\t".join(columns)]
    for i in range(N_GENES):
        lines.append("\t".join([ids[i]] + [fmt(v[i]) for v in values[1:]]))
    path = out / DE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return ids


def write_annotation(out, rng, ids):
    rows = []
    annotated = ids[DE_ONLY:]
    extra = [f"ENSG{n:011d}" for n in range(1000, 1000 + ANN_ONLY)]
    for i, gid in enumerate(annotated + extra):
        version = int(rng.integers(1, 20))
        name = f"GENE{i // 2 if i < 2 * SHARED_SYMBOLS else i}"
        chrom = "chrX" if i < 2 * SHARED_SYMBOLS + PAR_GENES and i >= 2 * SHARED_SYMBOLS else f"chr{1 + i % 22}"
        rows.append([f"{gid}.{version}", name, TYPES[i % len(TYPES)], chrom])
        if chrom == "chrX":
            rows.append([f"{gid}.{version}_PAR_Y", name, TYPES[i % len(TYPES)], "chrY"])
    order = rng.permutation(len(rows))
    lines = ["gene_id\tgene_name\tgene_type\tchrom"] + ["\t".join(rows[j]) for j in order]
    path = out / ANN_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def generate(out, stage="first"):
    """Write the stage's inputs under `out`, at their project-relative paths."""
    out = Path(out)
    rng = np.random.default_rng(SEED)
    ids = write_de(out, rng, shrunk=stage == "followup")
    if stage == "first":
        write_annotation(out, rng, ids)
