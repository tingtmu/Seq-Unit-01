"""Reference: annotate DESeq2 results with GENCODE genes and call significance (session 1)."""
import numpy as np
import pandas as pd

ANNOTATION_COLUMNS = ["gene_name", "gene_type", "chrom"]
DE_COLUMNS = ["baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"]


def read_annotation(path):
    ann = pd.read_csv(path, sep="\t", dtype=str)
    ann = ann[~ann["gene_id"].str.endswith("_PAR_Y")].copy()
    ann["gene_id"] = ann["gene_id"].str.split(".").str[0]
    return ann[["gene_id", *ANNOTATION_COLUMNS]]


def call(table, alpha):
    significant = (table["padj"] < alpha).fillna(False).astype(bool)
    direction = np.where(table["log2FoldChange"] > 0, "up", "down")
    return significant, np.where(significant, direction, "")


def rank(table):
    order = table.assign(_na=table["padj"].isna(), _abs=-table["log2FoldChange"].abs())
    order = order.sort_values(["_na", "padj", "_abs", "gene_id"], kind="mergesort")
    return order.drop(columns=["_na", "_abs"]).reset_index(drop=True)


def annotate_de(de_path, annotation_path, alpha):
    de = pd.read_csv(de_path, sep="\t", dtype={"gene_id": str})
    ann = read_annotation(annotation_path)
    table = de.merge(ann, on="gene_id", how="left", validate="many_to_one")
    unmatched = sorted(table.loc[table["gene_name"].isna(), "gene_id"])
    table["significant"], table["direction"] = call(table, alpha)
    table = rank(table)
    return table[["gene_id", *ANNOTATION_COLUMNS, *DE_COLUMNS, "significant", "direction"]], unmatched
