"""Seeded inputs for T3: a DESeq2 result (lfcThreshold=1, greaterAbs) and a GENCODE v43 GTF."""
import gzip
from pathlib import Path

import numpy as np
from scipy.stats import norm

SEED = 20261105
N_GENES = 1500
DE_PATH = "data/processed/deseq2/treated_vs_control.tsv"
ANN_PATH = "data/reference/gencode.v43.primary_assembly.annotation.gtf.gz"
OUTLIERS = 9                  # Cook's outliers: pvalue and padj NA, at any baseMean
PAR_GENES = 6                 # genes on the X/Y pseudoautosomal regions, listed twice in GENCODE v43
SHARED_SYMBOLS = 8            # pairs of distinct gene ids with the same symbol
DE_ONLY = 12                  # DE ids not in the annotation (retired ids)
ANN_ONLY = 40                 # annotated genes absent from the DE table
TAB, NL = chr(9), chr(10)
GTF_HEADER = ["##description: evidence-based annotation of the human genome (GRCh38), version 43 (Ensembl 109)",
              "##provider: GENCODE", "##contact: gencode-help@ebi.ac.uk", "##format: gtf", "##date: 2023-02-16"]
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
    outlier = np.zeros(N_GENES, dtype=bool)
    outlier[rng.choice(np.arange(15, N_GENES), OUTLIERS, replace=False)] = True
    pvalue[outlier] = np.nan
    tested = ~filtered & ~outlier
    padj = np.full(N_GENES, np.nan)
    padj[tested] = bh(pvalue[tested])
    for column in (lfc, se, stat, pvalue):                     # DESeq2 gives all-zero genes NA
        column[:15] = np.nan
    candidates = np.where(tested & (np.abs(lfc) > 1.5))[0]
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


def gtf_gene(gene_id, name, kind, chrom, start):
    """A gene line, then one transcript and its exon, as GENCODE writes them."""
    tx_id = "ENST" + gene_id[4:]
    gene_attrs = f'gene_id "{gene_id}"; gene_type "{kind}"; gene_name "{name}"; level 2;'
    tx_attrs = (f'gene_id "{gene_id}"; transcript_id "{tx_id}"; gene_type "{kind}"; gene_name "{name}"; '
                f'transcript_type "{kind}"; transcript_name "{name}-201"; level 2; tag "basic";')
    rows = [("gene", gene_attrs, start + 4000), ("transcript", tx_attrs, start + 4000),
            ("exon", tx_attrs + " exon_number 1;", start + 600)]
    return [TAB.join([chrom, "HAVANA", f, str(start), str(end), ".", "+", ".", a]) for f, a, end in rows]


def write_annotation(out, rng, ids):
    genes = []
    annotated = ids[DE_ONLY:]
    extra = [f"ENSG{n:011d}" for n in range(1000, 1000 + ANN_ONLY)]
    for i, gid in enumerate(annotated + extra):
        version = int(rng.integers(1, 20))
        name = f"GENE{i // 2 if i < 2 * SHARED_SYMBOLS else i}"
        chrom = "chrX" if i < 2 * SHARED_SYMBOLS + PAR_GENES and i >= 2 * SHARED_SYMBOLS else f"chr{1 + i % 22}"
        genes.append((f"{gid}.{version}", name, TYPES[i % len(TYPES)], chrom))
        if chrom == "chrX":
            genes.append((f"{gid}.{version}_PAR_Y", name, TYPES[i % len(TYPES)], "chrY"))
    lines = list(GTF_HEADER)
    for j in rng.permutation(len(genes)):
        lines += gtf_gene(*genes[j], start=11869 + 7000 * int(j))
    path = out / ANN_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress((NL.join(lines) + NL).encode("utf-8"), mtime=0))


def generate(out, stage="first"):
    """Write the stage's inputs under `out`, at their project-relative paths."""
    out = Path(out)
    rng = np.random.default_rng(SEED)
    ids = write_de(out, rng, shrunk=stage == "followup")
    if stage == "first":
        write_annotation(out, rng, ids)
