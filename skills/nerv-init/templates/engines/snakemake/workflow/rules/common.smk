import os

import pandas as pd

# Fail fast: validate the sample sheet before any rule runs.
REQUIRED_COLUMNS = {"sample_id", "fastq_1"}

samples = pd.read_csv(config["samples"], sep="\t", dtype=str)
missing_columns = REQUIRED_COLUMNS - set(samples.columns)
if missing_columns:
    raise ValueError(f"{config['samples']} is missing required columns: {sorted(missing_columns)}")
samples = samples.set_index("sample_id", drop=False)
if samples.index.duplicated().any():
    raise ValueError(f"Duplicate sample_id in {config['samples']}: {list(samples.index[samples.index.duplicated()])}")
fastqs = samples.filter(like="fastq_").stack().dropna()
missing_files = [f for f in fastqs if not os.path.exists(f)]
if missing_files:
    raise ValueError(f"FASTQ files listed in {config['samples']} do not exist: {missing_files}")

SAMPLES = list(samples.index)
