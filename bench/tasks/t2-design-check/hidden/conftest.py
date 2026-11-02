"""Hidden-test setup for T2: load the module under test by path and write small sheets and designs."""
import importlib.util
import os
import sys
from pathlib import Path

import pytest
import yaml

COLUMNS = ["sample_id", "fastq_1", "fastq_2", "condition", "batch"]


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


def paired(sample_id, condition, batch, **over):
    row = {"sample_id": sample_id, "fastq_1": f"{sample_id.strip()}_R1.fastq.gz",
           "fastq_2": f"{sample_id.strip()}_R2.fastq.gz", "condition": condition, "batch": batch}
    return {**row, **over}


CLEAN = [paired("C1", "control", "b1"), paired("C2", "control", "b2"), paired("C3", "control", "b1"),
         paired("T1", "treated", "b1"), paired("T2", "treated", "b2"), paired("T3", "treated", "b2")]
DESIGN = {"design": "~ batch + condition", "reference_level": {"condition": "control"},
          "contrasts": {"treated_vs_control": ["condition", "treated", "control"]},
          "thresholds": {"padj": 0.05, "lfc": 1}}


@pytest.fixture
def check(mod, tmp_path):
    """check(rows, design=DESIGN, columns=COLUMNS, bom=True, missing=()) -> list of problems."""
    def run(rows, design=None, columns=None, bom=True, missing=()):
        columns = columns or [c for c in COLUMNS if any(c in r for r in rows)]
        raw = tmp_path / "raw"
        raw.mkdir(exist_ok=True)
        for row in rows:
            for key in ("fastq_1", "fastq_2"):
                name = row.get(key, "")
                if name and name not in missing:
                    (raw / name).write_bytes(b"@r1\nACGT\n+\nIIII\n")
        lines = ["\t".join(columns)] + ["\t".join(r.get(c, "") for c in columns) for r in rows]
        text = "\n".join(lines) + "\n"
        sheet = tmp_path / "samples.tsv"
        sheet.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        design_path = tmp_path / "design.yaml"
        design_path.write_text(yaml.safe_dump(design or DESIGN, sort_keys=False), encoding="utf-8")
        return mod.check_design(sheet, design_path, raw)
    return run


def found(problems):
    return {(p.severity, p.code, p.sample_id) for p in problems}
