The core changed its sheet, and the checker in `scripts/check_design.py` must handle it. Keep everything it does now unchanged.

The core now sends mixed single- and paired-end runs. The second delivery is in `data/raw/delivery-02/`, and `config/samples.tsv` has been replaced by the new sheet.

1. The sheet may have a `layout` column with the values `SE` or `PE`. When it is present, it decides pairing instead of the "any row has a `fastq_2`" rule: a `PE` row without `fastq_2` is `missing_fastq_2`, an `SE` row with a `fastq_2` is a new error `unexpected_fastq_2` (the id), and any other layout value is a new error `bad_layout` (the id). Without a `layout` column, the current rule holds.
2. The `batch` column may be absent, because the new sheet comes from one run. Then the formula is used without batch: every term that involves `batch` is dropped, and nothing is reported about it. Any other factor that is missing is still `missing_column`.
