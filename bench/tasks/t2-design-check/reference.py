"""Reference: check a bulk RNA-seq sample sheet and design before DESeq2 (session 1)."""
import posixpath
import re
from collections import namedtuple
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

Problem = namedtuple("Problem", "severity code sample_id message")
BASE_COLUMNS = ("sample_id", "fastq_1")
R_RESERVED = {"if", "else", "repeat", "while", "function", "for", "next", "break", "TRUE", "FALSE", "NULL",
              "Inf", "NaN", "NA", "NA_integer_", "NA_real_", "NA_character_", "NA_complex_", "in"}


def error(code, sample_id, message):
    return Problem("error", code, sample_id, message)


def read_sheet(path):
    sheet = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    sheet.columns = [c.strip() for c in sheet.columns]
    return sheet.apply(lambda column: column.str.strip())


def design_terms(formula):
    """Terms of an additive formula; an interaction `a:b` is a tuple of its factors."""
    terms = [t.strip() for t in str(formula).strip().lstrip("~").split("+")]
    return [tuple(f.strip() for f in t.split(":")) for t in terms if t and t != "1"]


def design_factors(terms):
    factors = []
    for term in terms:
        factors += [f for f in term if f not in factors]
    return factors


def check_columns(sheet, factors):
    return [error("missing_column", None, f"column {c!r} is missing from the sample sheet")
            for c in (*BASE_COLUMNS, *factors) if c not in sheet.columns]


def check_duplicates(sheet):
    counts = sheet["sample_id"].value_counts()
    return [error("duplicate_sample", s, f"sample_id {s!r} occurs {n} times") for s, n in counts.items() if n > 1]


def make_name(text):
    """R's make.names for one string (without unique=TRUE)."""
    if not re.match(r"[A-Za-z]|\.(?![0-9])", text):
        text = "X" + text
    name = re.sub(r"[^A-Za-z0-9._]", ".", text)
    return name + "." if name in R_RESERVED else name


def check_names(sheet):
    groups = {}
    for sample_id in sheet["sample_id"].unique():
        groups.setdefault(make_name(sample_id), []).append(sample_id)
    return [error("name_collision", None, f"sample ids {ids} all become {name!r} in R")
            for name, ids in groups.items() if len(ids) > 1]


def paired_rows(sheet):
    """Rows that must have fastq_2: all rows, if any row has one."""
    if "fastq_2" not in sheet.columns or not (sheet["fastq_2"] != "").any():
        return sheet.iloc[0:0]
    return sheet


def check_pairs(sheet):
    rows = paired_rows(sheet)
    return [error("missing_fastq_2", r.sample_id, "paired-end sample has no fastq_2")
            for r in rows.itertuples() if r.fastq_2 == ""]


def fastq_entries(sheet):
    for row in sheet.itertuples():
        for column in ("fastq_1", "fastq_2"):
            yield row.sample_id, column, getattr(row, column, "")


def check_files(sheet, raw_dir):
    problems = []
    for sample_id, column, name in fastq_entries(sheet):
        if column == "fastq_1" and name == "":
            problems.append(error("missing_fastq", sample_id, "fastq_1 is empty"))
        elif name and not (Path(raw_dir) / name).is_file():
            problems.append(error("missing_fastq", sample_id, f"{column} {name!r} not found in {raw_dir}"))
    return problems


def check_shared_files(sheet):
    owners = {}
    for sample_id, column, name in fastq_entries(sheet):
        if name:
            owners.setdefault(posixpath.normpath(name.replace("\\", "/")), []).append(f"{sample_id} {column}")
    return [error("shared_fastq", None, f"{path} is named by {', '.join(uses)}")
            for path, uses in owners.items() if len(uses) > 1]


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


def indicators(sheet, factor):
    levels = sorted(sheet[factor].unique())
    return [(sheet[factor] == level).to_numpy(dtype=float) for level in levels[1:]]


def term_columns(sheet, term):
    columns = [np.ones(len(sheet))]
    for factor in term:
        columns = [a * b for a in columns for b in indicators(sheet, factor)]
    return columns


def check_rank(sheet, terms):
    columns = [np.ones(len(sheet))]
    for term in terms:
        columns += term_columns(sheet, term)
    matrix = np.column_stack(columns)
    if np.linalg.matrix_rank(matrix) < matrix.shape[1]:
        formula = " + ".join(":".join(t) for t in terms)
        return [error("confounded", None, f"design ~ {formula} is not full rank")]
    return []


def contrasts(design):
    return (design.get("contrasts") or {}).items()


def check_contrast_factors(design, factors):
    return [error("contrast_not_in_design", None, f"contrast {name}: {factor!r} is not in the design formula")
            for name, (factor, _, _) in contrasts(design) if factor not in factors]


def check_named_levels(sheet, design):
    problems = []
    named = [(f, lvl, "reference level") for f, lvl in (design.get("reference_level") or {}).items()]
    for name, (factor, numerator, denominator) in contrasts(design):
        named += [(factor, numerator, f"contrast {name}"), (factor, denominator, f"contrast {name}")]
    for factor, level, where in named:
        if factor in sheet.columns and str(level).strip() not in set(sheet[factor]):
            problems.append(error("missing_level", None, f"{where}: {factor} level {level!r} not in the sheet"))
    return problems


def check_replicates(sheet, design):
    factors = {c[0] for _, c in contrasts(design)} | set(design.get("reference_level") or {})
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
    terms = design_terms(design.get("design", ""))
    factors = design_factors(terms)
    problems = check_columns(sheet, factors)
    if any(c not in sheet.columns for c in BASE_COLUMNS):
        return problems
    present = [f for f in factors if f in sheet.columns]
    problems += check_duplicates(sheet)
    problems += check_names(sheet)
    problems += check_pairs(sheet)
    problems += check_files(sheet, raw_dir)
    problems += check_shared_files(sheet)
    problems += check_levels(sheet, present)
    if present == factors:
        problems += check_rank(sheet, terms)
    problems += check_contrast_factors(design, factors)
    problems += check_named_levels(sheet, design)
    problems += check_replicates(sheet, design)
    return problems
