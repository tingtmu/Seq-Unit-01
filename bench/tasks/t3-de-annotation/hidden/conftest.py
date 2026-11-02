"""Hidden-test setup for T3: load the module under test by path and write small DE and annotation tables."""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

STAGE = os.environ.get("BENCH_STAGE", "first")
DE_COLUMNS = ["gene_id", "baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"]
ANN_COLUMNS = ["gene_id", "gene_name", "gene_type", "chrom"]


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


def de_row(n, lfc, padj, base=500.0, shrunk=None):
    """A DESeq2 row tested with lfcThreshold=1: |LFC| <= 1 gives pvalue 1."""
    pvalue = "NA" if padj == "NA" else (1.0 if abs(lfc) <= 1 else min(1.0, float(padj) / 2))
    row = {"gene_id": gene(n), "baseMean": base, "log2FoldChange": lfc, "lfcSE": 0.3,
           "stat": 0.0 if abs(lfc) <= 1 else (abs(lfc) - 1) / 0.3 * (1 if lfc > 0 else -1),
           "pvalue": pvalue, "padj": padj}
    if shrunk is not None:
        row["log2FoldChange_shrunk"] = shrunk
    return row


def ann_row(n, name, version=5, gene_type="protein_coding", chrom="chr1", suffix=""):
    return {"gene_id": f"{gene(n)}.{version}{suffix}", "gene_name": name, "gene_type": gene_type, "chrom": chrom}


def write(path, rows, columns):
    lines = ["\t".join(columns)] + ["\t".join(str(r.get(c, "NA")) for c in columns) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        write(tmp_path / "annotation.tsv", ann_rows, ANN_COLUMNS)
        return mod.annotate_de(tmp_path / "de.tsv", tmp_path / "annotation.tsv", alpha)
    return run
