"""Hidden checks for the T3 follow-up: a shrunken LFC column, used for direction and ties only."""
from conftest import ann_row, de_row, gene

ANN = [ann_row(1, "TP53"), ann_row(2, "MYC"), ann_row(3, "GAPDH"), ann_row(4, "ACTB")]


def row(table, n):
    return table[table["gene_id"] == gene(n)].iloc[0]


def test_shape(annotate):
    table, _ = annotate([de_row(1, 2.0, 0.01, shrunk=1.4)], ANN)
    assert "log2FoldChange_shrunk" in table.columns and "log2FoldChange" in table.columns
    assert len(table) == 1


def test_shrunk_column_reported(annotate):
    table, _ = annotate([de_row(1, 2.0, 0.01, shrunk=1.4), de_row(2, -2.5, 0.02, shrunk=-1.1)], ANN)
    assert row(table, 1)["log2FoldChange_shrunk"] == 1.4 and row(table, 2)["log2FoldChange_shrunk"] == -1.1


def test_no_post_hoc_lfc_filter(annotate):
    table, _ = annotate([de_row(1, 1.8, 0.01, shrunk=0.6), de_row(2, -1.6, 0.03, shrunk=-0.4)], ANN)
    assert len(table) == 2
    assert bool(row(table, 1)["significant"]) and bool(row(table, 2)["significant"])
    assert [row(table, n)["direction"] for n in (1, 2)] == ["up", "down"]


def test_ties_ranked_by_shrunk(annotate):
    rows = [de_row(1, 3.0, 0.01, shrunk=1.2), de_row(2, 2.0, 0.01, shrunk=1.8), de_row(3, -2.5, 0.01, shrunk=-1.5)]
    table, _ = annotate(rows, ANN)
    assert list(table["gene_id"]) == [gene(2), gene(3), gene(1)]

