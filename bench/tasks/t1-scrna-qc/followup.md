The QC step in `scripts/qc_filter.py` needs two additions. Keep everything it does now unchanged.

1. Doublets. `filter_cells` gains a keyword argument, `doublet_dir`: a folder with one file per sample, `<sample_id>.tsv`, with the columns `barcode` and `doublet_score`. Scores for this project are in `data/processed/doublets/`. `config/qc_thresholds.tsv` now has a `doublet_score_max` column. Drop a cell whose score is strictly above its sample's `doublet_score_max`, with the reason code `doublet`, which comes last in the reason order (`low_counts`, `low_genes`, `high_genes`, `high_mito`, `doublet`). A barcode with no score in its sample's file is an error, raised with a message that names the sample and the barcode.

2. `max_pct_mito` may now be blank. A blank means a MAD upper bound on `pct_mito` itself (not on `log1p`), over that sample's cells: drop a cell if `pct_mito > median + nmads * MAD`, with MAD scaled by 1.4826 as before. Only the high side is filtered. If the MAD is 0, apply no mito filter for that sample, and record `mad_zero:pct_mito` in the summary notes.

The new signature is `filter_cells(matrix_dirs, thresholds, mito_prefix, nmads=3.0, doublet_dir=None)`.
