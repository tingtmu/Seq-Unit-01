"""Hidden-test setup for T1: load the module under test by path and build tiny 10x inputs."""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import mex  # noqa: E402

STAGE = os.environ.get("BENCH_STAGE", "first")
N_NUCLEAR = 80
COLUMNS = ["sample_id", "min_genes", "max_genes", "min_counts", "max_pct_mito", "doublet_method", "notes"]


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


def barcode(i):
    bases = "ACGT"
    return "".join(bases[(i >> (2 * k)) & 3] for k in range(16)) + "-1"


def write_thresholds(path, rows, extra_columns=()):
    columns = COLUMNS[:5] + list(extra_columns) + COLUMNS[5:]
    lines = ["\t".join(columns)]
    for sample_id, row in rows.items():
        full = {"sample_id": sample_id, "min_genes": "", "max_genes": "", "min_counts": "",
                "max_pct_mito": "100", "doublet_method": "scrublet", "notes": "", **row}
        lines.append("\t".join(str(full.get(c, "")) for c in columns))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_doublets(folder, sample_id, barcodes, scores):
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["barcode\tdoublet_score"] + [f"{b}\t{s}" for b, s in zip(barcodes, scores)]
    (folder / f"{sample_id}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture
def qc(mod, tmp_path):
    """qc(samples, rows, **kwargs): samples maps sample id -> list of (total, n_genes, mito) cells.

    In the follow-up stage, session-1 checks run with a doublet_score_max of 1.0 and all scores 0,
    so the session-1 behavior is checked unchanged.
    """
    def run(samples, rows, mito_prefix="mt-", nmads=3.0, doublets=None, extra_columns=None):
        feats = mex.features(N_NUCLEAR)
        dirs = {}
        for sample_id, cells in samples.items():
            folder = tmp_path / "raw" / sample_id
            mex.write_mex(folder, [barcode(i) for i in range(len(cells))], feats,
                          [mex.cell(*c, n_nuclear=N_NUCLEAR) for c in cells])
            dirs[sample_id] = folder
        path = tmp_path / "qc_thresholds.tsv"
        if STAGE == "followup":
            rows = {s: {"doublet_score_max": "1.0", **r} for s, r in rows.items()}
            extra = extra_columns if extra_columns is not None else ["doublet_score_max"]
            write_thresholds(path, rows, extra)
            doublet_dir = tmp_path / "doublets"
            for sample_id, cells in samples.items():
                scores = (doublets or {}).get(sample_id, [0.0] * len(cells))
                write_doublets(doublet_dir, sample_id, [barcode(i) for i in range(len(scores))], scores)
            return mod.filter_cells(dirs, path, mito_prefix, nmads, doublet_dir=doublet_dir)
        write_thresholds(path, rows)
        return mod.filter_cells(dirs, path, mito_prefix, nmads)
    return run
