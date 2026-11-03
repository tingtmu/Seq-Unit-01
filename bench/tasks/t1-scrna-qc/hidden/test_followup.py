"""Hidden checks for the T1 follow-up: doublet scores and a MAD upper tail on blank max_pct_mito."""
import numpy as np
import pytest

from conftest import barcode

FIXED = {"min_counts": "1", "min_genes": "1"}


def test_shape(qc):
    cells, summary = qc({"S1": [(1000, 50, 0)] * 3}, {"S1": {**FIXED, "doublet_score_max": "0.5"}})
    for column in ("cell_id", "sample_id", "barcode", "n_counts", "n_genes", "pct_mito", "keep", "reason"):
        assert column in cells.columns, column
    assert len(cells) == 3 and list(summary["sample_id"]) == ["S1"]


def test_doublet_score_strictly_above(qc):
    cells, _ = qc({"S1": [(1000, 50, 0)] * 3}, {"S1": {**FIXED, "doublet_score_max": "0.25"}},
                  doublets={"S1": [0.1, 0.25, 0.3]})
    assert cells["keep"].tolist() == [True, True, False]
    assert cells["reason"].tolist() == ["", "", "doublet"]


def test_doublet_reason_after_others(qc):
    cells, _ = qc({"S1": [(1000, 50, 0), (1000, 50, 500)]},
                  {"S1": {**FIXED, "max_pct_mito": "20", "doublet_score_max": "0.25"}},
                  doublets={"S1": [0.9, 0.9]})
    assert cells["reason"].tolist() == ["doublet", "high_mito;doublet"]


def test_missing_barcode_is_an_error(qc):
    with pytest.raises(Exception) as info:
        qc({"S7": [(1000, 50, 0)] * 3}, {"S7": {**FIXED, "doublet_score_max": "0.5"}},
           doublets={"S7": [0.1, 0.1]})
    assert "S7" in str(info.value) and barcode(2) in str(info.value)


def test_blank_mito_uses_mad_upper_tail(qc):
    sample = [(1000, 50, m) for m in (38, 39, 40, 41, 42)] * 3 + [(1000, 50, 300), (1000, 50, 0)]
    cells, _ = qc({"S1": sample}, {"S1": {**FIXED, "max_pct_mito": ""}})
    high, low = cells.iloc[15], cells.iloc[16]
    assert not high["keep"] and high["reason"] == "high_mito"
    assert low["keep"] and np.isclose(low["pct_mito"], 0)
    assert cells["keep"].sum() == 16


def test_blank_mito_on_raw_percent(qc):
    sample = [(1000, 50, m) for m in (10, 20, 40, 60, 80)] * 3 + [(1000, 50, 150)]
    cells, _ = qc({"S1": sample}, {"S1": {**FIXED, "max_pct_mito": ""}})
    assert cells["reason"].iloc[15] == "high_mito"
    assert cells["keep"].sum() == 15


def test_blank_mito_mad_zero(qc):
    cells, summary = qc({"S1": [(1000, 50, 0)] * 4 + [(1000, 50, 100)]}, {"S1": {**FIXED, "max_pct_mito": ""}})
    assert cells["keep"].all()
    assert "mad_zero:pct_mito" in summary.set_index("sample_id").loc["S1", "notes"].split(";")


def test_mixed_given_and_blank_mito(qc):
    spread = [(1000, 50, m) for m in (38, 39, 40, 41, 42)] * 3
    cells, _ = qc({"GIVEN": spread + [(1000, 50, 60)], "BLANK": spread + [(1000, 50, 60)]},
                  {"GIVEN": {**FIXED, "max_pct_mito": "10"}, "BLANK": {**FIXED, "max_pct_mito": ""}})
    kept = cells.groupby("sample_id")["keep"].sum().to_dict()
    assert kept == {"GIVEN": 16, "BLANK": 15}


def test_blank_mito_ignores_empty_cells(qc):
    sample = [(1000, 50, m) for m in (38, 39, 40, 41, 42)] * 3 + [(1000, 50, 48)] + [(0, 0, 0, 700)] * 8
    cells, _ = qc({"S1": sample}, {"S1": {**FIXED, "max_pct_mito": ""}})
    assert cells["reason"].iloc[15] == "high_mito"
    assert (cells["reason"].iloc[16:] == "empty").all()
    assert cells["keep"].sum() == 15


def test_cell_ranger_2_folder(qc):
    old = [(1000, 50, 100), (400, 30, 0), (0, 0, 0)]
    new = [(1000, 50, 100, 5000), (400, 30, 0, 3000), (0, 0, 0, 800)]
    cells, summary = qc({"OLD": old, "NEW": new}, {s: {"min_counts": "500", "min_genes": "1"} for s in ("OLD", "NEW")},
                        v2=("OLD",))
    for sample_id in ("OLD", "NEW"):
        part = cells[cells["sample_id"] == sample_id]
        assert part["n_counts"].tolist() == [1000, 400, 0] and part["n_genes"].tolist() == [50, 30, 0]
        assert part["reason"].tolist() == ["", "low_counts", "empty"]
        assert part["cell_id"].iloc[0] == f"{sample_id}:{barcode(0)}"
    assert summary.set_index("sample_id")["n_kept"].to_dict() == {"OLD": 1, "NEW": 1}
