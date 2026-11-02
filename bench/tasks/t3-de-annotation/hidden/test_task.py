"""Hidden checks for T3 session 1: annotate_de(de_path, annotation_path, alpha) -> (table, unmatched)."""
import pandas as pd

from conftest import ann_row, de_row, gene

ANN = [ann_row(1, "TP53"), ann_row(2, "MYC"), ann_row(3, "GAPDH"), ann_row(4, "ACTB"), ann_row(5, "EGFR")]


def row(table, n):
    return table[table["gene_id"] == gene(n)].iloc[0]


def test_shape(annotate):
    table, unmatched = annotate([de_row(1, 2.0, 0.01), de_row(2, 0.5, 0.9)], ANN)
    for column in ("gene_id", "gene_name", "gene_type", "chrom", "baseMean", "log2FoldChange", "lfcSE",
                   "stat", "pvalue", "padj", "significant", "direction"):
        assert column in table.columns, column
    assert len(table) == 2 and list(unmatched) == []


def test_versions_stripped_on_annotation(annotate):
    table, _ = annotate([de_row(1, 2.0, 0.01), de_row(2, -1.5, 0.02)], ANN)
    assert row(table, 1)["gene_name"] == "TP53" and row(table, 2)["gene_name"] == "MYC"
    assert row(table, 1)["gene_id"] == gene(1)


def test_par_y_rows_do_not_duplicate(annotate):
    ann = ANN + [ann_row(6, "CSF2RA", 14, chrom="chrX"), ann_row(6, "CSF2RA", 14, chrom="chrY", suffix="_PAR_Y")]
    table, unmatched = annotate([de_row(6, 2.5, 0.001), de_row(1, 2.0, 0.01)], ann)
    assert len(table) == 2 and table["gene_id"].is_unique
    assert row(table, 6)["chrom"] == "chrX" and unmatched == []


def test_left_join_keeps_unmatched(annotate):
    table, unmatched = annotate([de_row(1, 2.0, 0.01), de_row(99, 3.0, 0.001)], ANN)
    assert len(table) == 2
    assert pd.isna(row(table, 99)["gene_name"]) and bool(row(table, 99)["significant"])
    assert list(unmatched) == [gene(99)]
    assert gene(5) not in set(table["gene_id"])


def test_na_padj_kept_and_not_significant(annotate):
    table, _ = annotate([de_row(1, 2.0, 0.01), de_row(3, 0.0, "NA", base=0.0), de_row(4, 3.0, "NA", base=2.0)], ANN)
    assert len(table) == 3
    for n in (3, 4):
        assert pd.isna(row(table, n)["padj"])
        assert not bool(row(table, n)["significant"]) and row(table, n)["direction"] == ""


def test_padj_equal_to_alpha_not_significant(annotate):
    table, _ = annotate([de_row(1, 2.0, 0.05), de_row(2, 2.0, 0.0499)], ANN, alpha=0.05)
    assert not bool(row(table, 1)["significant"]) and bool(row(table, 2)["significant"])


def test_duplicate_symbols_keyed_on_id(annotate):
    ann = ANN + [ann_row(7, "PINX1"), ann_row(8, "PINX1", gene_type="lncRNA")]
    table, _ = annotate([de_row(7, 2.0, 0.01), de_row(8, -2.0, 0.02)], ann)
    assert len(table) == 2
    assert set(table["gene_type"]) == {"protein_coding", "lncRNA"}


def test_direction(annotate):
    table, _ = annotate([de_row(1, 2.0, 0.01), de_row(2, -2.0, 0.01), de_row(3, 0.4, 0.9)], ANN)
    assert [row(table, n)["direction"] for n in (1, 2, 3)] == ["up", "down", ""]


def test_sort_order(annotate):
    rows = [de_row(5, 1.5, "NA"), de_row(4, 2.0, 0.01), de_row(3, -3.0, 0.01), de_row(2, 1.5, 0.001),
            de_row(1, 2.0, 0.01)]
    table, _ = annotate(rows, ANN)
    assert list(table["gene_id"]) == [gene(2), gene(3), gene(1), gene(4), gene(5)]
    assert list(table.index) == list(range(5))
