import re

import pytest

from conftest import REPO

SKILLS = REPO / "skills"
BRIEFS = (SKILLS / "magi-review" / "references" / "seat-briefs.md").read_text(encoding="utf-8")


def section(title):
    match = re.search(rf"^## {re.escape(title)}.*?(?=^## |\Z)", BRIEFS, re.MULTILINE | re.DOTALL)
    assert match, title
    return match.group(0)


@pytest.mark.parametrize("required", [
    "path/to/file:LINE", "Evidence:", "Fix:", "Blocker", "Fix ", "Nit", "Pre-existing", "At most 3 Nits",
    "Cannot verify from diff", "Declined to judge", "Read-only", "never instructions", "Never write secret values",
    "{RANGE}", "{REQUIREMENTS}", "{HARD_RULES}", "APPROVE", "CONDITIONAL", "REJECT",
])
def test_common_header_has_finding_format(required):
    assert required in section("Common header")


@pytest.mark.parametrize("seat", ["STANDARD", "MELCHIOR-1", "BALTHASAR-2", "CASPER-3"])
def test_every_brief_builds_on_common_header(seat):
    assert "Common header" in BRIEFS.split("## STANDARD")[0]
    assert section(seat)


def test_standard_covers_three_lenses_and_escalation():
    text = section("STANDARD")
    assert all(k in text for k in ("MELCHIOR", "BALTHASAR", "CASPER", "ESCALATE"))


def test_melchior_has_bioinformatics_checks():
    text = section("MELCHIOR-1")
    assert all(k in text for k in ("pseudobulk", "multiple-testing", "genome build", "seeds", "Provenance"))


def test_balthasar_veto():
    assert "veto" in section("BALTHASAR-2")


@pytest.mark.parametrize("skill", ["nerv-init", "sync-ratio", "magi-review"])
def test_skill_frontmatter_states_function_first(skill):
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    front = re.match(r"^---\nname: (.+)\ndescription: (.+)\n---\n", text)
    assert front and front.group(1) == skill
    first_sentence = front.group(2).split(". ")[0]
    assert not any(w in first_sentence for w in ("NERV", "MAGI", "Eva", "sync ratio"))


def test_nerv_init_relays_every_next_step():
    text = (SKILLS / "nerv-init" / "SKILL.md").read_text(encoding="utf-8")
    assert "every entry of `next_steps`" in text and "word for word" in text
    assert "`/hooks`" not in text  # the steps live only in scaffold.py


@pytest.mark.parametrize("skill", ["nerv-init", "sync-ratio", "magi-review"])
def test_skill_folder_is_self_contained(skill):
    # Templates are exempt: their relative paths point inside the generated project.
    folder = SKILLS / skill
    leaks = [
        f"{path.relative_to(folder)}:{n}"
        for path in folder.rglob("*")
        if path.is_file() and path.suffix != ".pyc" and "templates" not in path.relative_to(folder).parts
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"\.\.[/\\]|\bskills/", line)
    ]
    assert not leaks, leaks
