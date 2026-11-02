The DE result in `data/processed/deseq2/treated_vs_control.tsv` has been re-delivered with one more column, `log2FoldChange_shrunk` (apeglm shrinkage), between `log2FoldChange` and `lfcSE`. Update `scripts/annotate_de.py` and keep everything else it does unchanged:

- Report `log2FoldChange_shrunk` in the table, right after `log2FoldChange`.
- Use `log2FoldChange_shrunk` instead of `log2FoldChange` for `direction` and for the absolute fold-change tie-break in the sort order.
- Keep significance from `padj` alone, because the fold-change threshold was already tested in DESeq2 (`lfcThreshold=1`).
