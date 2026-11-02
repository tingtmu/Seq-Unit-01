"""Reference: check a bulk RNA-seq sample sheet and design before DESeq2 (session 1)."""
from collections import namedtuple
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

Problem = namedtuple("Problem", "severity code sample_id message")
BASE_COLUMNS = ("sample_id", "fastq_1")


def error(code, sample_id, message):
    return Problem("error", code, sample_id, message)


def read_sheet(path):
    sheet = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    sheet.columns = [c.strip() for c in sheet.columns]
    return sheet.apply(lambda column: column.str.strip())


def design_factors(formula):
    terms = [t.strip() for t in str(formula).strip().lstrip("~").split("+")]
    return [t for t in terms if t and t != "1"]


def check_columns(sheet, factors):
    return [error("missing_column", None, f"column {c!r} is missing from the sample sheet")
            for c in (*BASE_COLUMNS, *factors) if c not in sheet.columns]


def check_duplicates(sheet):
    counts = sheet["sample_id"].value_counts()
    return [error("duplicate_sample", s, f"sample_id {s!r} occurs {n} times") for s, n in counts.items() if n > 1]


def paired_rows(sheet):
    """Rows that must have fastq_2: all rows, if any row has one."""
    if "fastq_2" not in sheet.columns or not (sheet["fastq_2"] != "").any():
        return sheet.iloc[0:0]
    return sheet


def check_pairs(sheet):
    rows = paired_rows(sheet)
    return [error("missing_fastq_2", r.sample_id, "paired-end sample has no fastq_2")
            for r in rows.itertuples() if r.fastq_2 == ""]


def check_files(sheet, raw_dir):
    problems = []
    for row in sheet.itertuples():
        for column in ("fastq_1", "fastq_2"):
            name = getattr(row, column, "")
            if column == "fastq_1" and name == "":
                problems.append(error("missing_fastq", row.sample_id, "fastq_1 is empty"))
            elif name and not (Path(raw_dir) / name).is_file():
                problems.append(error("missing_fastq", row.sample_id, f"{column} {name!r} not found in {raw_dir}"))
    return problems


def check_levels(sheet, factors):
    problems = []
    for factor in factors:
        spellings = {}
        for level in sheet[factor].unique():
            spellings.setdefault(level.lower(), set()).add(level)
        for forms in spellings.values():
            if len(forms) > 1:
                problems.append(error("level_case_conflict", None,
                                      f"{factor} levels differ only by case: {sorted(forms)}"))
    return problems


def check_rank(sheet, factors):
    columns = [np.ones(len(sheet))]
    for factor in factors:
        levels = sorted(sheet[factor].unique())
        columns += [(sheet[factor] == level).to_numpy(dtype=float) for level in levels[1:]]
    matrix = np.column_stack(columns)
    if np.linalg.matrix_rank(matrix) < matrix.shape[1]:
        return [error("confounded", None, f"design {' + '.join(factors)} is not full rank")]
    return []


def check_named_levels(sheet, design):
    problems = []
    named = [(f, lvl, "reference level") for f, lvl in (design.get("reference_level") or {}).items()]
    for name, (factor, numerator, denominator) in (design.get("contrasts") or {}).items():
        named += [(factor, numerator, f"contrast {name}"), (factor, denominator, f"contrast {name}")]
    for factor, level, where in named:
        if factor in sheet.columns and str(level).strip() not in set(sheet[factor]):
            problems.append(error("missing_level", None, f"{where}: {factor} level {level!r} not in the sheet"))
    return problems


def check_replicates(sheet, design):
    factors = {c[0] for c in (design.get("contrasts") or {}).values()} | set(design.get("reference_level") or {})
    problems = []
    for factor in sorted(f for f in factors if f in sheet.columns):
        counts = sheet[factor].value_counts()
        for level, n in counts.items():
            if n == 1:
                sample = sheet.loc[sheet[factor] == level, "sample_id"].iloc[0]
                problems.append(Problem("warning", "single_replicate", sample,
                                        f"{factor} level {level!r} has one replicate"))
    return problems


def check_design(samples_path, design_path, raw_dir):
    sheet = read_sheet(samples_path)
    design = yaml.safe_load(Path(design_path).read_text(encoding="utf-8")) or {}
    factors = design_factors(design.get("design", ""))
    problems = check_columns(sheet, factors)
    if any(c not in sheet.columns for c in BASE_COLUMNS):
        return problems
    present = [f for f in factors if f in sheet.columns]
    problems += check_duplicates(sheet)
    problems += check_pairs(sheet)
    problems += check_files(sheet, raw_dir)
    problems += check_levels(sheet, present)
    if present == factors:
        problems += check_rank(sheet, factors)
    problems += check_named_levels(sheet, design)
    problems += check_replicates(sheet, design)
    return problems
