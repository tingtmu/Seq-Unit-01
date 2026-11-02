Write the step that annotates the differential expression result, as a Python module `scripts/annotate_de.py` with this function:

```python
def annotate_de(de_path, annotation_path, alpha):
    """Returns (table, unmatched)."""
```

Inputs:
- `de_path`: a DESeq2 result as a tab-separated file with the columns `gene_id`, `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, `padj`, with missing values written as `NA`. Gene ids have no version (`ENSG00000141510`). It was made with DESeq2's Wald test using `lfcThreshold=1` and `altHypothesis="greaterAbs"`. Here: `data/processed/deseq2/treated_vs_control.tsv`.
- `annotation_path`: a gene table derived from GENCODE (the release pinned in `config/config.yaml`), tab-separated, with the columns `gene_id`, `gene_name`, `gene_type`, `chrom`. Its gene ids carry a version (`ENSG00000141510.18`). Genes in the X/Y pseudoautosomal regions are listed twice, once with an id ending in `_PAR_Y` for the chrY copy. Here: `data/reference/gencode.v43.genes.tsv`.
- `alpha`: the significance level for `padj`.

Rules:
- Match a DE gene to the annotation on the gene id without its version. Ignore the `_PAR_Y` rows, so each DE gene gets the annotation of its non-`_PAR_Y` row and appears once.
- Keep every DE row, whether or not it matched. An unmatched gene has missing `gene_name`, `gene_type`, and `chrom`. Gene symbols are not unique: two different gene ids can share a `gene_name`, and both stay.
- `significant` is `padj < alpha` (strictly). A missing `padj` (independent filtering, or a gene with all-zero counts) is not significant, and the row is kept with `padj` missing.
- `direction` is `"up"` if the gene is significant with `log2FoldChange > 0`, `"down"` if significant with `log2FoldChange < 0`, and `""` if not significant.
- Sort by `padj` ascending with missing values last, then by the absolute `log2FoldChange`, largest first, then by `gene_id`. Reset the index to 0..n-1.

Return:
- `table`: a pandas DataFrame with the columns `gene_id`, `gene_name`, `gene_type`, `chrom`, `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, `padj`, `significant` (bool), `direction`;
- `unmatched`: a sorted list of the DE gene ids with no annotation.

Use pandas and numpy; they are installed.
