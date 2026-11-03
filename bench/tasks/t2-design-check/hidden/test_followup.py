"""Hidden checks for the T2 follow-up: a layout column (SE/PE) and an optional batch column."""
from conftest import CLEAN, DESIGN, found, paired

LAYOUT = ["sample_id", "fastq_1", "fastq_2", "layout", "condition", "batch"]


def single(sample_id, condition, batch, **over):
    return {**paired(sample_id, condition, batch, fastq_2=""), "layout": "SE", **over}


def mixed():
    return [{**r, "layout": "PE"} for r in CLEAN[:4]] + [single("T2", "treated", "b2"), single("T3", "treated", "b2")]


def test_shape(check):
    problems = check(mixed()[:-1] + [single("T3", "treated", "b2", layout="paired")], columns=LAYOUT)
    assert isinstance(problems, list) and problems
    assert all(p.severity in ("error", "warning") and p.message for p in problems)


def test_mixed_layout_is_clean(check):
    assert check(mixed(), columns=LAYOUT) == []


def test_pe_row_without_fastq_2(check):
    rows = mixed()[:3] + [{**paired("T1", "treated", "b1", fastq_2=""), "layout": "PE"}] + mixed()[4:]
    assert found(check(rows, columns=LAYOUT)) == {("error", "missing_fastq_2", "T1")}


def test_se_row_with_fastq_2(check):
    rows = mixed()[:-1] + [single("T3", "treated", "b2", fastq_2="T3_R2.fastq.gz")]
    assert found(check(rows, columns=LAYOUT)) == {("error", "unexpected_fastq_2", "T3")}


def test_unknown_layout(check):
    rows = mixed()[:-1] + [single("T3", "treated", "b2", layout="paired")]
    assert ("error", "bad_layout", "T3") in found(check(rows, columns=LAYOUT))


def test_layout_value_stripped(check):
    rows = mixed()[:-1] + [single("T3", "treated", "b2", layout="SE ")]
    assert check(rows, columns=LAYOUT) == []


def test_batch_absent_means_condition_only(check):
    rows = [{k: v for k, v in r.items() if k != "batch"} for r in mixed()]
    assert check(rows, columns=[c for c in LAYOUT if c != "batch"]) == []


def test_confounding_checked_with_layout(check):
    rows = [{**r, "batch": "b1" if r["condition"] == "control" else "b2"} for r in mixed()]
    assert found(check(rows, columns=LAYOUT)) == {("error", "confounded", None)}


def test_duplicates_checked_with_layout(check):
    rows = mixed() + [single("T2 ", "treated", "b1")]
    assert ("error", "duplicate_sample", "T2") in found(check(rows, columns=LAYOUT))


def test_batch_absent_drops_its_interaction(check):
    design = {**DESIGN, "design": "~ batch + condition + batch:condition"}
    rows = [{k: v for k, v in r.items() if k != "batch"} for r in mixed()]
    assert check(rows, design=design, columns=[c for c in LAYOUT if c != "batch"]) == []
