"""Reference: annotate DESeq2 results with GENCODE genes and call significance (session 1)."""
import re

import numpy as np
import pandas as pd

ANNOTATION_COLUMNS = ["gene_name", "gene_type", "chrom"]
DE_COLUMNS = ["baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj"]
GTF_COLUMNS = ["chrom", "source", "feature", "start", "end", "score", "strand", "frame", "attributes"]
ATTRIBUTE = re.compile(r'(\S+) "([^"]*)"')


def attributes(text):
    return dict(ATTRIBUTE.findall(text))


def read_annotation(path):
    gtf = pd.read_csv(path, sep="\t", comment="#", header=None, names=GTF_COLUMNS, dtype=str)
    genes = gtf[gtf["feature"] == "gene"]
    attrs = [attributes(a) for a in genes["attributes"]]
    ann = pd.DataFrame({"gene_id": [a["gene_id"] for a in attrs], "gene_name": [a["gene_name"] for a in attrs],
                        "gene_type": [a["gene_type"] for a in attrs], "chrom": genes["chrom"].to_numpy()})
    ann = ann[~ann["gene_id"].str.endswith("_PAR_Y")].copy()
    ann["gene_id"] = ann["gene_id"].str.split(".").str[0]
    return ann[["gene_id", *ANNOTATION_COLUMNS]]


def na_reasons(table):
    """Why padj is NA, as DESeq2 marks it: all-zero counts, a Cook's outlier, or independent filtering."""
    zero = table["baseMean"] == 0
    outlier = ~zero & table["pvalue"].isna()
    low_mean = ~zero & table["pvalue"].notna() & table["padj"].isna()
    return np.select([zero, outlier, low_mean], ["zero_counts", "outlier", "low_mean"], default="")


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
    table["na_reason"] = na_reasons(table)
    table = rank(table)
    return table[["gene_id", *ANNOTATION_COLUMNS, *DE_COLUMNS, "significant", "direction", "na_reason"]], unmatched
