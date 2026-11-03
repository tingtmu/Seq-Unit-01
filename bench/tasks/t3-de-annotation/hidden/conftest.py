"""Hidden-test setup for T3: load the module under test by path and write small DE tables and GTFs."""
import gzip
import importlib.util
import os
import sys
from pathlib import Path

import pytest

STAGE = os.environ.get("BENCH_STAGE", "first")
DE_COLUMNS = ["gene_id", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"]
GTF_HEADER = ["##description: evidence-based annotation of the human genome (GRCh38), version 43 (Ensembl 109)",
              "##provider: GENCODE", "##contact: gencode-help@ebi.ac.uk", "##format: gtf", "##date: 2023-02-16"]


def load_module():
    path = Path(os.environ["BENCH_MODULE"])
    spec = importlib.util.spec_from_file_location("module_under_check", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def mod():
    return load_module()


def gene(n):
    return f"ENSG{n:011d}"


def de_row(n, lfc, padj, base=500.0, shrunk=None, outlier=False):
    """A DESeq2 row tested with lfcThreshold=1: |LFC| <= 1 gives pvalue 1.

    NA padj follows DESeq2: baseMean 0 means all-zero counts (LFC, SE, stat, pvalue NA too);
    `outlier` is a Cook's outlier (pvalue NA); otherwise NA padj is independent filtering.
    """
    se = 0.3
    stat = 0.0 if abs(lfc) <= 1 else (abs(lfc) - 1) / se * (1 if lfc > 0 else -1)
    pvalue = 1.0 if abs(lfc) <= 1 else (0.2 if padj == "NA" else min(1.0, float(padj) / 2))
    if outlier:
        pvalue, padj = "NA", "NA"
    row = {"gene_id": gene(n), "baseMean": base, "log2FoldChange": lfc, "lfcSE": se, "stat": stat,
           "pvalue": pvalue, "padj": padj}
    if base == 0:
        row.update({"log2FoldChange": "NA", "lfcSE": "NA", "stat": "NA", "pvalue": "NA", "padj": "NA"})
    if shrunk is not None:
        row["log2FoldChange_shrunk"] = shrunk
    return row


def ann_row(n, name, version=5, gene_type="protein_coding", chrom="chr1", suffix=""):
    return {"gene_id": f"{gene(n)}.{version}{suffix}", "gene_name": name, "gene_type": gene_type, "chrom": chrom}


def gtf_lines(rows):
    """GENCODE-style GTF: a gene line, then one transcript and one exon line per gene."""
    lines = list(GTF_HEADER)
    for i, r in enumerate(rows):
        gid, kind, name = r["gene_id"], r["gene_type"], r["gene_name"]
        gene_attrs = f'gene_id "{gid}"; gene_type "{kind}"; gene_name "{name}"; level 2;'
        tx_attrs = (f'gene_id "{gid}"; transcript_id "ENST{gid[4:]}"; gene_type "{kind}"; gene_name "{name}"; '
                    f'transcript_type "{kind}"; transcript_name "{name}-201"; level 2; tag "basic";')
        start = 10000 + 5000 * i
        for feature, attrs, end in (("gene", gene_attrs, start + 3000), ("transcript", tx_attrs, start + 3000),
                                    ("exon", tx_attrs + " exon_number 1;", start + 400)):
            lines.append("\t".join([r["chrom"], "HAVANA", feature, str(start), str(end), ".", "+", ".", attrs]))
    return lines


def write(path, rows, columns):
    lines = ["\t".join(columns)] + ["\t".join(str(r.get(c, "NA")) for c in columns) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gtf(path, rows):
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(gtf_lines(rows)) + "\n")


@pytest.fixture
def annotate(mod, tmp_path):
    """annotate(de_rows, ann_rows, alpha=0.05). In the follow-up stage, a shrunken LFC equal to the
    unshrunken one is added where a row has none, so session-1 behavior is checked unchanged."""
    def run(de_rows, ann_rows, alpha=0.05):
        columns = list(DE_COLUMNS)
        if STAGE == "followup" or any("log2FoldChange_shrunk" in r for r in de_rows):
            de_rows = [{"log2FoldChange_shrunk": r["log2FoldChange"], **r} for r in de_rows]
            columns.insert(3, "log2FoldChange_shrunk")
        write(tmp_path / "de.tsv", de_rows, columns)
        write_gtf(tmp_path / "gencode.v43.annotation.gtf.gz", ann_rows)
        return mod.annotate_de(tmp_path / "de.tsv", tmp_path / "gencode.v43.annotation.gtf.gz", alpha)
    return run
