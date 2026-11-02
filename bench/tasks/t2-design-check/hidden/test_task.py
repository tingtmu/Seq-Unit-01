"""Hidden checks for T2 session 1: check_design(samples_path, design_path, raw_dir) -> list[Problem]."""
from conftest import CLEAN, DESIGN, found, paired


def test_shape(check):
    problems = check(CLEAN[:-1] + [paired("C1", "treated", "b2")])
    assert isinstance(problems, list) and problems
    for p in problems:
        assert {p.severity, p.code} and p.severity in ("error", "warning")
        assert isinstance(p.message, str) and p.message


def test_clean_sheet_has_no_problems(check):
    assert check(CLEAN) == []


def test_all_problems_reported(check):
    rows = CLEAN + [paired("C1", "control", "b2"), paired("T9", "treated", "b1")]
    design = {**DESIGN, "reference_level": {"condition": "untreated"}}
    got = found(check(rows, design=design, missing=("T9_R1.fastq.gz",)))
    assert {("error", "duplicate_sample", "C1"), ("error", "missing_fastq", "T9"),
            ("error", "missing_level", None)} <= got


def test_duplicate_after_stripping_whitespace(check):
    rows = CLEAN + [paired("T3 ", "treated", "b1")]
    assert ("error", "duplicate_sample", "T3") in found(check(rows))


def test_paired_row_without_fastq_2(check):
    rows = CLEAN[:-1] + [paired("T3", "treated", "b2", fastq_2="")]
    assert found(check(rows)) == {("error", "missing_fastq_2", "T3")}


def test_missing_fastq_file(check):
    problems = check(CLEAN, missing=("C2_R2.fastq.gz",))
    assert found(problems) == {("error", "missing_fastq", "C2")}


def test_level_names_stripped(check):
    rows = [{**r, "condition": r["condition"] + " "} if r["sample_id"] == "C2" else r for r in CLEAN]
    assert check(rows) == []


def test_levels_differing_only_by_case(check):
    rows = [{**r, "condition": "Control"} if r["sample_id"] == "C3" else r for r in CLEAN]
    codes = {code for _, code, _ in found(check(rows))}
    assert "level_case_conflict" in codes


def test_batch_confounded_with_condition(check):
    rows = [{**r, "batch": "b1" if r["condition"] == "control" else "b2"} for r in CLEAN]
    assert found(check(rows)) == {("error", "confounded", None)}


def test_unbalanced_but_estimable_design(check):
    rows = [{**r, "batch": "b1"} if r["sample_id"] in ("C2", "T3") else r for r in CLEAN]
    rows = [{**r, "batch": "b2"} if r["sample_id"] == "T1" else r for r in rows]
    assert check(rows) == []


def test_reference_level_absent(check):
    design = {**DESIGN, "reference_level": {"condition": "untreated"}}
    assert found(check(CLEAN, design=design)) == {("error", "missing_level", None)}


def test_contrast_level_absent(check):
    design = {**DESIGN, "contrasts": {"ko_vs_control": ["condition", "knockout", "control"]}}
    assert found(check(CLEAN, design=design)) == {("error", "missing_level", None)}


def test_single_replicate_is_a_warning(check):
    rows = CLEAN + [paired("K1", "knockout", "b1")]
    design = {**DESIGN, "contrasts": {**DESIGN["contrasts"], "ko_vs_control": ["condition", "knockout", "control"]}}
    assert found(check(rows, design=design)) == {("warning", "single_replicate", "K1")}


def test_bom_header(check):
    assert check(CLEAN, bom=True) == []
    assert check(CLEAN, bom=False) == []


def test_missing_design_column(check):
    rows = [{k: v for k, v in r.items() if k != "condition"} for r in CLEAN]
    assert ("error", "missing_column", None) in found(check(rows))
