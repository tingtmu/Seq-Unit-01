"""Hidden checks for T1 session 1: filter_cells(matrix_dirs, thresholds, mito_prefix, nmads=3.0)."""
import numpy as np

from conftest import barcode

FIXED_GENES = {"min_genes": "1"}
SPREAD = [(c, 50, 0) for c in (900, 950, 1000, 1050, 1100)] * 3


def by_barcode(cells, sample_id, i):
    return cells[(cells["sample_id"] == sample_id) & (cells["barcode"] == barcode(i))].iloc[0]


def test_shape(qc):
    cells, summary = qc({"S1": SPREAD, "S2": SPREAD[:5]}, {"S1": {}, "S2": FIXED_GENES})
    for column in ("cell_id", "sample_id", "barcode", "n_counts", "n_genes", "pct_mito", "keep", "reason"):
        assert column in cells.columns, column
    for column in ("sample_id", "n_cells", "n_kept", "notes"):
        assert column in summary.columns, column
    assert len(cells) == 20
    assert set(cells["keep"].unique()) <= {True, False}


def test_metrics_per_cell(qc):
    cells, _ = qc({"S1": [(1000, 40, 100), (500, 20, 0)]}, {"S1": {"min_counts": "1", "min_genes": "1"}})
    first, second = by_barcode(cells, "S1", 0), by_barcode(cells, "S1", 1)
    assert (first["n_counts"], first["n_genes"]) == (1000, 40)
    assert np.isclose(first["pct_mito"], 10.0)
    assert (second["n_counts"], second["n_genes"], second["pct_mito"]) == (500, 20, 0)


def test_per_sample_thresholds(qc):
    deep = [(c, 50, 0) for c in (9000, 9500, 10000, 10500, 11000)] * 6
    shallow = [(c, 50, 0) for c in (800, 900, 1000, 1100, 1200)] * 2
    cells, _ = qc({"DEEP": deep, "SHALLOW": shallow}, {"DEEP": FIXED_GENES, "SHALLOW": FIXED_GENES})
    assert cells["keep"].all(), cells.loc[~cells["keep"], ["cell_id", "reason"]]


def test_mad_on_log_scale(qc):
    cells, _ = qc({"S1": [(c, 50, 0) for c in (300, 600, 1000, 1600, 3000)] * 3 + [(60, 50, 0)]},
                  {"S1": FIXED_GENES})
    low = by_barcode(cells, "S1", 15)
    assert not low["keep"] and low["reason"] == "low_counts"
    assert cells["keep"].sum() == 15


def test_mad_is_normal_scaled(qc):
    counts = [int(round(np.expm1(x))) for x in (6.8, 6.9, 7.0, 7.1, 7.2)] * 3 + [int(round(np.expm1(6.65)))]
    cells, _ = qc({"S1": [(c, 50, 0) for c in counts]}, {"S1": FIXED_GENES})
    assert cells["keep"].all(), cells.loc[~cells["keep"], ["n_counts", "reason"]]


def test_mad_zero_sample(qc):
    tiny = [(100, 50, 0)] * 5 + [(60, 50, 0), (300, 50, 0)]
    cells, summary = qc({"TINY": tiny}, {"TINY": FIXED_GENES})
    assert cells["keep"].all()
    notes = summary.set_index("sample_id").loc["TINY", "notes"]
    assert "mad_zero:n_counts" in notes.split(";")


def test_low_tail_only(qc):
    cells, _ = qc({"S1": SPREAD + [(20000, 50, 0)]}, {"S1": FIXED_GENES})
    assert by_barcode(cells, "S1", 15)["keep"]
    assert cells["keep"].all()


def test_mito_prefix_matched_on_symbol(qc):
    sample = [(1000, 50, 0)] * 5 + [(1000, 50, 500)]
    cells, _ = qc({"S1": sample}, {"S1": {"min_counts": "1", "min_genes": "1", "max_pct_mito": "20"}})
    high = by_barcode(cells, "S1", 5)
    assert np.isclose(high["pct_mito"], 50.0)
    assert not high["keep"] and high["reason"] == "high_mito"
    assert cells["keep"].sum() == 5


def test_blank_threshold_means_mad(qc):
    sample = [(c, g, 0) for c, g in zip((900, 950, 1000, 1050, 1100), (40, 45, 50, 55, 60))] * 3
    sample += [(100, 50, 0), (1000, 5, 0)]
    cells, _ = qc({"S1": sample}, {"S1": {}})
    assert by_barcode(cells, "S1", 15)["reason"] == "low_counts"
    assert by_barcode(cells, "S1", 16)["reason"] == "low_genes"
    assert cells["keep"].sum() == 15


def test_zero_count_cell(qc):
    cells, _ = qc({"S1": SPREAD + [(0, 0, 0, 400)]}, {"S1": FIXED_GENES})
    empty = by_barcode(cells, "S1", 15)
    assert empty["n_counts"] == 0 and empty["pct_mito"] == 0
    assert not empty["keep"] and empty["reason"] == "empty"
    assert cells["pct_mito"].notna().all()


def test_antibody_counts_are_not_genes(qc):
    sample = [(1000, 50, 100, 6000), (500, 40, 0, 4000), (1000, 50, 0, 0)]
    cells, _ = qc({"S1": sample}, {"S1": {"min_counts": "800", "min_genes": "45", "max_genes": "60"}})
    first, second = by_barcode(cells, "S1", 0), by_barcode(cells, "S1", 1)
    assert (first["n_counts"], first["n_genes"]) == (1000, 50) and np.isclose(first["pct_mito"], 10.0)
    assert first["keep"]
    assert second["reason"] == "low_counts;low_genes"


def test_empty_cells_left_out_of_mad(qc):
    sample = SPREAD + [(700, 50, 0)] + [(0, 0, 0, 900)] * 8
    cells, summary = qc({"S1": sample}, {"S1": FIXED_GENES})
    assert by_barcode(cells, "S1", 15)["reason"] == "low_counts"
    assert (cells["reason"].iloc[16:] == "empty").all()
    assert cells["keep"].sum() == 15
    assert summary.set_index("sample_id").loc["S1", "n_kept"] == 15


def test_bounds_computed_independently(qc):
    sample = SPREAD + [(500, 30, 0)] * 6 + [(750, 50, 0)]
    cells, _ = qc({"S1": sample}, {"S1": {"min_genes": "40"}})
    assert by_barcode(cells, "S1", 21)["keep"]
    assert (cells["reason"].iloc[15:21] == "low_counts;low_genes").all()
    assert cells["keep"].sum() == 16


def test_cell_ids_unique_across_samples(qc):
    cells, summary = qc({"S1": SPREAD, "S2": SPREAD}, {"S1": FIXED_GENES, "S2": FIXED_GENES})
    assert cells["cell_id"].is_unique and len(cells) == 30
    assert by_barcode(cells, "S2", 0)["cell_id"] == f"S2:{barcode(0)}"
    assert summary.set_index("sample_id")["n_cells"].to_dict() == {"S1": 15, "S2": 15}


def test_fixed_thresholds_inclusive(qc):
    sample = [(1000, 50, 0), (999, 50, 0), (1000, 51, 0), (1000, 50, 100), (1000, 50, 101)]
    cells, summary = qc({"S1": sample},
                        {"S1": {"min_counts": "1000", "min_genes": "1", "max_genes": "50", "max_pct_mito": "10"}})
    assert cells["keep"].tolist() == [True, False, False, True, False]
    assert cells["reason"].tolist() == ["", "low_counts", "high_genes", "", "high_mito"]
    assert summary.set_index("sample_id").loc["S1", "n_kept"] == 2


def test_several_reasons_in_order(qc):
    cells, _ = qc({"S1": [(500, 60, 100)]},
                  {"S1": {"min_counts": "1000", "min_genes": "1", "max_genes": "50", "max_pct_mito": "10"}})
    assert cells["reason"].tolist() == ["low_counts;high_genes;high_mito"]
