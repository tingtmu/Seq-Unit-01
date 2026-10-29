import json
import subprocess
import sys

import pytest

from conftest import NERV_INIT, git, load

SCRIPT = NERV_INIT / "scripts" / "scaffold.py"
scaffold = load("scaffold", SCRIPT)
SKELETON = ["config", "data/raw", "data/reference", "data/processed", "workflow", "scripts",
            "notebooks", "envs", "results", "tests", "docs"]
README_FOLDERS = ["config", "data", "workflow", "scripts", "notebooks", "envs", "results", "tests", "docs"]


def answers(**over):
    return {"project_name": "demo", "assay": "bulk-rnaseq", "engine": "snakemake",
            "languages": ["python", "r"], "compute": "local", "sensitive": False, "date": "2026-10-29", **over}


def build(tmp_path, **over):
    code, result = scaffold.scaffold(answers(**over), tmp_path)
    assert code == 0, result
    return tmp_path


def assert_common(project):
    for folder in SKELETON:
        assert (project / folder).is_dir(), folder
    for folder in README_FOLDERS:
        text = (project / folder / "README.md").read_text(encoding="utf-8")
        assert "## Current state" in text and "{{" not in text
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", ".gitignore", ".nerv/hooks/sync_ratio.py",
                 ".nerv/hooks/raw_guard.py", ".claude/settings.json", ".codex/hooks.json"):
        assert (project / name).is_file(), name
    assert not list(project.rglob("*.tmpl")) and not list(project.rglob("*.append"))
    assert (project / "CLAUDE.md").read_text().strip() == "@AGENTS.md"


def test_bulk_snakemake(tmp_path):
    project = build(tmp_path)
    assert_common(project)
    assert (project / "workflow/Snakefile").is_file()
    assert (project / "workflow/rules/common.smk").is_file()
    assert (project / "config/design.yaml").is_file()
    assert "design formula" in (project / "config/README.md").read_text()
    assert not (project / "config/qc_thresholds.tsv").exists()
    agents = (project / "AGENTS.md").read_text()
    assert "snakemake --use-conda" in agents and "pytest tests/" in agents and "testthat" in agents
    assert "Bulk RNA-seq" in agents


def test_sc_scripts(tmp_path):
    project = build(tmp_path, assay="scrnaseq", engine="scripts", languages=["r"])
    assert_common(project)
    assert (project / "workflow/run_all.sh").is_file()
    assert not (project / "workflow/Snakefile").exists()
    assert (project / "config/qc_thresholds.tsv").is_file()
    assert (project / "docs/integration-log.md").is_file()
    results = (project / "results/README.md").read_text()
    assert ".h5ad" in results and ".rds" in results
    assert "qc_thresholds.tsv" in (project / "config/README.md").read_text()
    readme = (project / "results/README.md").read_text()
    assert readme.index(".h5ad") < readme.index("## Current state")  # inserted into Conventions


def test_other_assay_uses_base_only(tmp_path):
    project = build(tmp_path, assay="other", assay_description="ATAC-seq", engine="snakemake")
    assert_common(project)
    assert not (project / "config/design.yaml").exists()
    assert not (project / "config/qc_thresholds.tsv").exists()
    assert "ATAC-seq" in (project / "AGENTS.md").read_text()
    top = {p.name for p in project.iterdir()}
    assert top == {".git", ".gitignore", ".nerv", ".claude", ".codex", "AGENTS.md", "CLAUDE.md", "README.md",
                   "config", "data", "workflow", "scripts", "notebooks", "envs", "results", "tests", "docs"}


def test_non_empty_target_reports_conflicts_and_writes_nothing(tmp_path):
    (tmp_path / "README.md").write_text("mine\n")
    (tmp_path / "scripts").mkdir()
    code, result = scaffold.scaffold(answers(), tmp_path)
    assert code == 1
    assert result["conflicts"] == ["README.md", "scripts/"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["README.md", "scripts"]
    assert (tmp_path / "README.md").read_text() == "mine\n"


def test_dry_run_writes_nothing(tmp_path):
    code, result = scaffold.scaffold(answers(), tmp_path, dry_run=True)
    assert code == 0 and "AGENTS.md" in result["files"]
    assert list(tmp_path.iterdir()) == []


def test_git_works_and_data_ignored(tmp_path):
    project = build(tmp_path)
    git(project, "status")
    (project / "data/raw/S1.fastq.gz").write_bytes(b"x")
    (project / "data/processed/x.tsv").write_text("x")
    (project / "results/de.h5ad").write_bytes(b"x")
    tracked = set(git(project, "ls-files", "--others", "--exclude-standard").split())
    assert "data/raw/S1.fastq.gz" not in tracked and "data/processed/x.tsv" not in tracked
    assert "results/de.h5ad" not in tracked
    assert {"data/README.md", "data/raw/.gitkeep", "AGENTS.md", ".nerv/hooks/raw_guard.py"} <= tracked


def test_sensitive_adds_rules_and_ignores(tmp_path):
    project = build(tmp_path, sensitive=True)
    agents = (project / "AGENTS.md").read_text()
    assert "sensitive (human or controlled-access)" in agents
    (project / "results/table.tsv").write_text("x")
    (project / "data/extra.csv").write_text("x")
    untracked = set(git(project, "ls-files", "--others", "--exclude-standard").split())
    assert "results/table.tsv" not in untracked and "data/extra.csv" not in untracked
    assert {"results/README.md", "data/README.md", "config/samples.tsv"} <= untracked


def test_not_sensitive_has_no_extra_rules(tmp_path):
    assert "sensitive" not in (build(tmp_path) / "AGENTS.md").read_text()


def test_adapters_point_to_project_hooks(tmp_path):
    project = build(tmp_path)
    claude = json.loads((project / ".claude/settings.json").read_text())
    commands = [h["command"] for groups in claude["hooks"].values() for g in groups for h in g["hooks"]]
    assert all(".nerv/hooks/" in c and "{{" not in c for c in commands)
    codex = json.loads((project / ".codex/hooks.json").read_text())
    commands = [h["command"] for groups in codex["hooks"].values() for g in groups for h in g["hooks"]]
    assert all(c.split()[1].startswith(".nerv/hooks/") for c in commands)


def test_installed_guard_finds_project_root(tmp_path):
    project = build(tmp_path)
    (project / "data/raw/S1.fq").write_text("x")
    event = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "cwd": str(project),
             "tool_input": {"file_path": "data/raw/S1.fq"}}
    out = subprocess.run([sys.executable, str(project / ".nerv/hooks/raw_guard.py"), "--agent", "claude"],
                         input=json.dumps(event), capture_output=True, text=True).stdout
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "ask"


@pytest.mark.parametrize("bad", [
    {"assay": "wgs"},
    {"assay": "other"},
    {"engine": "nextflow"},
    {"languages": []},
    {"project_name": ""},
])
def test_invalid_answers_rejected(tmp_path, bad):
    with pytest.raises(scaffold.AnswersError):
        scaffold.scaffold(answers(**bad), tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_cli(tmp_path):
    target = tmp_path / "proj"
    result = subprocess.run([sys.executable, str(SCRIPT), "--answers", "-", "--target", str(target)],
                            input=json.dumps(answers()), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["git"] == "initialized"
    again = subprocess.run([sys.executable, str(SCRIPT), "--answers", "-", "--target", str(target)],
                           input=json.dumps(answers()), capture_output=True, text=True)
    assert again.returncode == 1 and json.loads(again.stdout)["status"] == "conflict"
