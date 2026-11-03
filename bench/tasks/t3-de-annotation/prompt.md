Write the step that annotates the differential expression result, as a Python module `scripts/annotate_de.py` with this function:

```python
def annotate_de(de_path, annotation_path, alpha):
    """Returns (table, unmatched)."""
```

Inputs:
- `de_path`: a DESeq2 `results()` table as a tab-separated file with the columns `gene_id`, `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, `padj`, with missing values written as `NA`. Gene ids have no version (`ENSG00000141510`). It was made with DESeq2's Wald test using `lfcThreshold=1` and `altHypothesis="greaterAbs"`, with the default outlier handling and independent filtering. Here: `data/processed/deseq2/treated_vs_control.tsv`.
- `annotation_path`: the GENCODE comprehensive annotation GTF (gzipped) for the release pinned in `config/config.yaml`. Its gene ids carry a version (`ENSG00000141510.18`). Here: `data/reference/gencode.v43.primary_assembly.annotation.gtf.gz`.
- `alpha`: the significance level for `padj`.

Rules:
- Annotate each DE gene with the `gene_name` and `gene_type` attributes and the chromosome of its GENCODE gene, matched on the gene id without its version. Each DE gene appears exactly once; a gene in the X/Y pseudoautosomal regions takes its chrX annotation.
- Keep every DE row, whether or not it matched. An unmatched gene has missing `gene_name`, `gene_type`, and `chrom`. Gene symbols are not unique: two different gene ids can share a `gene_name`, and both stay.
- `significant` is `padj < alpha` (strictly). A missing `padj` is not significant, and the row is kept with `padj` missing.
- `na_reason` says why `padj` is missing, read from the way DESeq2 marks each case in its result: `zero_counts` (all counts are zero), `outlier` (a count outlier by Cook's distance), or `low_mean` (removed by independent filtering). It is `""` when `padj` is present.
- `direction` is `"up"` if the gene is significant with `log2FoldChange > 0`, `"down"` if significant with `log2FoldChange < 0`, and `""` if not significant.
- Sort by `padj` ascending with missing values last, then by the absolute `log2FoldChange`, largest first, then by `gene_id`. Reset the index to 0..n-1.

Return:
- `table`: a pandas DataFrame with the columns `gene_id`, `gene_name`, `gene_type`, `chrom`, `baseMean`, `log2FoldChange`, `lfcSE`, `stat`, `pvalue`, `padj`, `significant` (bool), `direction`, `na_reason`;
- `unmatched`: a sorted list of the DE gene ids with no annotation.

Use pandas and numpy; they are installed.
