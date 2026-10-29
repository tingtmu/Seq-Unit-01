import re

import pytest

from conftest import NERV_INIT

TEMPLATES = NERV_INIT / "templates"
BASE = TEMPLATES / "base"
SECTIONS = ["## Purpose", "## Conventions", "## Current state", "## Last major change"]
FOLDERS = ["config", "data", "workflow", "scripts", "notebooks", "envs", "results", "tests", "docs"]


@pytest.mark.parametrize("folder", FOLDERS)
def test_folder_readme_has_four_sections_in_order(folder):
    text = (BASE / folder / "README.md").read_text(encoding="utf-8")
    positions = [text.find(s) for s in SECTIONS]
    assert -1 not in positions, f"{folder}/README.md missing a section"
    assert positions == sorted(positions)
    assert len(re.findall(r"^## ", text, re.MULTILINE)) == 4  # nothing else at section level


def test_data_subfolders_exist():
    for sub in ("raw", "reference", "processed"):
        assert (BASE / "data" / sub).is_dir()


def test_agents_md_size():
    lines = (BASE / "AGENTS.md.tmpl").read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 200  # hard ceiling; ~60 is only a recommendation


def test_agents_md_points_to_folder_readmes():
    text = (BASE / "AGENTS.md.tmpl").read_text(encoding="utf-8")
    for folder in FOLDERS:
        assert f"`{folder}/README.md`" in text
    assert "docs/principles.md" in text


LAYERS = sorted(p for kind in ("addons", "engines") for p in (TEMPLATES / kind).iterdir() if p.is_dir())


@pytest.mark.parametrize("layer", LAYERS, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_layer_only_contains_differences(layer):
    base_texts = {p.read_bytes() for p in BASE.rglob("*") if p.is_file()}
    files = [p for p in layer.rglob("*") if p.is_file()]
    assert files
    for path in files:
        rel = path.relative_to(layer)
        assert path.read_bytes() not in base_texts, f"{rel} duplicates a base file verbatim"
        if path.name.endswith(".append"):
            target = BASE / rel.with_name(path.name.removesuffix(".append"))
            assert target.is_file(), f"{rel} appends to a file that is not in base"
        else:
            assert not (BASE / rel).exists(), f"{rel} would overwrite a base file"


def test_claude_md_only_imports_agents_md():
    assert (BASE / "CLAUDE.md").read_text(encoding="utf-8").strip() == "@AGENTS.md"
