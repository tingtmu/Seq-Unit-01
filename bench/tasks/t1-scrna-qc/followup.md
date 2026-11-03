The QC step in `scripts/qc_filter.py` needs three additions. Keep everything it does now unchanged.

1. A second delivery, `data/raw/delivery-02/`, holds two samples the core re-ran with Cell Ranger 2. Its folders use the older layout: `matrix.mtx`, `barcodes.tsv`, and `genes.tsv` (gene id and symbol, no feature type column), none of them gzipped. `matrix_dirs` can now mix both layouts. `config/samples.tsv` and `config/qc_thresholds.tsv` list the new samples.

2. Doublets. `filter_cells` gains a keyword argument, `doublet_dir`: a folder with one file per sample, `<sample_id>.tsv`, with the columns `barcode` and `doublet_score`. Scores for this project are in `data/processed/doublets/`. `config/qc_thresholds.tsv` now has a `doublet_score_max` column. Drop a cell whose score is strictly above its sample's `doublet_score_max`, with the reason code `doublet`, which comes last in the reason order (`low_counts`, `low_genes`, `high_genes`, `high_mito`, `doublet`). A barcode with no score in its sample's file is an error, raised with a message that names the sample and the barcode.

3. `max_pct_mito` may now be blank. A blank means a MAD upper bound on `pct_mito` itself (not on `log1p`): drop a cell if `pct_mito > median + nmads * MAD`, with the median and the scaled MAD taken over the same cells as the other bounds. Only the high side is filtered. If the MAD is 0, apply no mito filter for that sample, and record `mad_zero:pct_mito` in the summary notes.

The new signature is `filter_cells(matrix_dirs, thresholds, mito_prefix, nmads=3.0, doublet_dir=None)`.
