Write the cell QC step for this project as a Python module, `scripts/qc_filter.py`, with this function:

```python
def filter_cells(matrix_dirs, thresholds, mito_prefix, nmads=3.0):
    """Returns (cells, summary)."""
```

Inputs:
- `matrix_dirs`: a dict from sample id to a folder in 10x Genomics MEX format (`matrix.mtx.gz`, `barcodes.tsv.gz`, and `features.tsv.gz` with the columns gene id, gene symbol, feature type). The delivery is in `data/raw/delivery-01/`, one folder per sample, listed in `config/samples.tsv`.
- `thresholds`: the path to a thresholds table in the format of `config/qc_thresholds.tsv`, one row per sample.
- `mito_prefix`: the prefix that marks mitochondrial genes, matched case-sensitively against the gene symbol. This project is mouse, so it is called with `"mt-"`.
- `nmads`: the number of MADs for MAD-based bounds.

Per cell, compute `n_counts` (total UMIs), `n_genes` (genes with at least one UMI), and `pct_mito` (100 × mitochondrial UMIs / `n_counts`; a cell with 0 UMIs has `pct_mito` 0).

The thresholds apply per sample, using that sample's row:
- `min_counts`, `min_genes`: a number is a fixed lower bound, and a cell is kept if its value is `>=` the bound. A blank cell means a MAD lower bound, computed over that sample's cells only, on `log1p` of the metric: drop a cell if `log1p(value) < median - nmads * MAD`, where MAD is the median absolute deviation scaled by 1.4826. Only the low side is filtered. If the MAD is 0, apply no MAD filter for that metric in that sample, and record it in the summary notes as `mad_zero:n_counts` or `mad_zero:n_genes`.
- `max_genes`: a number is a fixed upper bound (keep if `<=`). A blank means no upper filter.
- `max_pct_mito`: always given. Drop a cell if `pct_mito` is strictly above it.

Return two pandas DataFrames:
- `cells`: one row per cell in the input, kept or not, with the columns `cell_id` (`<sample_id>:<barcode>`, since the same barcode can occur in two samples), `sample_id`, `barcode`, `n_counts`, `n_genes`, `pct_mito`, `keep` (bool), and `reason`: an empty string for a kept cell, otherwise every failed filter among `low_counts`, `low_genes`, `high_genes`, `high_mito`, in that order, joined by `;`.
- `summary`: one row per sample with `sample_id`, `n_cells`, `n_kept`, and `notes` (the `mad_zero:...` entries joined by `;`, or an empty string).

A sample in `matrix_dirs` with no row in the thresholds table is an error. Use pandas, numpy, and scipy; they are installed.
