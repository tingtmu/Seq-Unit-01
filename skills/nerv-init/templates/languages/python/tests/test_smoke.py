"""Smoke test so the Test command passes on a fresh project. Replace it with real tests."""
import csv
from pathlib import Path

SAMPLE_SHEET = Path(__file__).resolve().parents[1] / "config" / "samples.tsv"
REQUIRED_COLUMNS = {"sample_id", "fastq_1"}


def test_sample_sheet_has_required_columns():
    with open(SAMPLE_SHEET, newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh, delimiter="\t"))
    missing = REQUIRED_COLUMNS - set(header)
    assert not missing, f"config/samples.tsv is missing required columns: {sorted(missing)}"
