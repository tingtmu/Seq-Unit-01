The sequencing core sent the first delivery (`data/raw/delivery-01/`) and its sample sheet, now in `config/samples.tsv`. Before anything goes to DESeq2, write a checker for the sample sheet and the design, as a Python module `scripts/check_design.py` with this function:

```python
def check_design(samples_path, design_path, raw_dir):
    """Returns a list of Problem."""
```

- `samples_path`: a tab-separated sample sheet with the columns `sample_id`, `fastq_1`, `fastq_2`, and the design factors. It comes from the core's spreadsheet export, so it may start with a UTF-8 byte order mark and may have stray spaces around values.
- `design_path`: a design file in the format of `config/design.yaml` (`design` formula, `reference_level`, `contrasts` as `name: [factor, numerator, denominator]`). The formula is additive main effects only, such as `~ batch + condition`.
- `raw_dir`: the folder that FASTQ paths in the sheet are relative to (`data/raw` in this project).

`Problem` is a namedtuple defined in the module: `Problem(severity, code, sample_id, message)`, where `severity` is `"error"` or `"warning"`, `code` is one of the codes below, `sample_id` is the sample's id (with spaces stripped) or `None` when the problem is not about one sample, and `message` is a readable explanation.

Strip spaces from column names and from every value before checking. Then report every problem, not just the first:
- `missing_column` (error, `None`): a column the checks need (`sample_id`, `fastq_1`, or a factor in the formula) is absent. Without `sample_id` or `fastq_1`, report only this.
- `duplicate_sample` (error, the id): a `sample_id` that occurs more than once. One problem per duplicated id.
- `missing_fastq_2` (error, the id): the sheet is paired-end if any row has a `fastq_2`; then every row needs one.
- `missing_fastq` (error, the id): `fastq_1` is empty, or a `fastq_1` or `fastq_2` path does not exist under `raw_dir`. One problem per missing file.
- `level_case_conflict` (error, `None`): two levels of a factor that are equal ignoring case but not exactly (`Control` and `control`). Do not merge them.
- `confounded` (error, `None`): the design matrix of the formula (intercept plus one indicator column per non-first level of each factor) is not full rank, for example batch fully confounded with condition.
- `missing_level` (error, `None`): a reference level or a contrast level that no row has.
- `single_replicate` (warning, the id of that sample): a level of a factor used in a contrast or a reference level that only one sample has.

A clean sheet gives an empty list. The function never raises for problems in the sheet; it returns them. Use pandas, numpy, and PyYAML; they are installed.
