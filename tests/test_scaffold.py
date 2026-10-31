import json
import re
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
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", ".gitignore", ".nerv/scripts/sync_ratio.py",
                 ".nerv/hooks/raw_guard.py", ".claude/settings.json", ".codex/hooks.json"):
        assert (project / name).is_file(), name
    assert not (project / ".nerv/hooks/sync_ratio.py").exists()
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


def env_dependencies(project):
    """Map package name to pinned version from the generated envs/workflow.yaml."""
    text = (project / "envs/workflow.yaml").read_text(encoding="utf-8")
    deps = text.split("dependencies:", 1)[1]
    return dict(re.findall(r"^\s+- ([A-Za-z0-9_.-]+)=([0-9][^\s]*)$", deps, re.MULTILINE))


def test_env_snakemake_python(tmp_path):
    deps = env_dependencies(build(tmp_path, languages=["python"]))
    assert {"snakemake-minimal", "pandas", "python", "pytest"} <= set(deps)
    assert "r-base" not in deps


def test_env_scripts_r(tmp_path):
    project = build(tmp_path, engine="scripts", languages=["r"])
    assert "conda (or mamba) and `bash`" in (project / "README.md").read_text()
    deps = env_dependencies(project)
    assert {"r-base", "r-testthat"} <= set(deps)
    assert not any("snakemake" in name for name in deps) and "pytest" not in deps


def test_env_both_languages(tmp_path):
    deps = env_dependencies(build(tmp_path, engine="scripts", languages=["python", "r"]))
    assert {"pytest", "r-testthat"} <= set(deps)


def test_env_name_matches_readme_activate(tmp_path):
    project = build(tmp_path, project_name="Mouse liver RNA")
    name = re.search(r"^name: (.+)$", (project / "envs/workflow.yaml").read_text(), re.MULTILINE).group(1)
    assert re.fullmatch(r"[A-Za-z0-9_.-]+", name)
    readme = (project / "README.md").read_text()
    assert "`conda env create -f envs/workflow.yaml`" in readme
    assert f"`conda activate {name}`" in readme
    assert "conda (or mamba)" in readme and "`bash`" not in readme


@pytest.mark.parametrize("project_name, env_name", [
    ("小鼠 肝臟", "project"), ("!!!", "project"), ("base", "project"), ("-x", "x"), ("Mouse liver RNA", "Mouse-liver-RNA"),
])
def test_env_name_is_usable_by_conda(tmp_path, project_name, env_name):
    project = build(tmp_path, project_name=project_name)
    assert f"\nname: {env_name}\n" in (project / "envs/workflow.yaml").read_text(encoding="utf-8")
    assert f"`conda activate {env_name}`" in (project / "README.md").read_text(encoding="utf-8")


def test_smoke_test_only_for_chosen_languages(tmp_path):
    python_only = build(tmp_path / "py", languages=["python"])
    assert (python_only / "tests/test_smoke.py").is_file() and not (python_only / "tests/test_smoke.R").exists()
    r_only = build(tmp_path / "r", languages=["r"])
    assert (r_only / "tests/test_smoke.R").is_file() and not (r_only / "tests/test_smoke.py").exists()


def run_pytest(project):
    return subprocess.run([sys.executable, "-m", "pytest", "tests/", "-p", "no:cacheprovider"],
                          cwd=project, capture_output=True, text=True)


def test_python_smoke_test_passes_on_fresh_project(tmp_path):
    result = run_pytest(build(tmp_path, languages=["python"]))
    assert result.returncode == 0, result.stdout + result.stderr
    assert " passed" in result.stdout


def test_python_smoke_test_accepts_excel_tsv(tmp_path):
    project = build(tmp_path, languages=["python"])
    sheet = project / "config/samples.tsv"
    sheet.write_bytes(b"\xef\xbb\xbf" + sheet.read_bytes().replace(b"\n", b"\r\n"))  # Excel "UTF-8 TSV"
    result = run_pytest(project)
    assert result.returncode == 0, result.stdout


def test_python_smoke_test_names_missing_column(tmp_path):
    project = build(tmp_path, languages=["python"])
    sheet = project / "config/samples.tsv"
    sheet.write_text(sheet.read_text().replace("fastq_1	", ""))
    result = run_pytest(project)
    assert result.returncode == 1 and "fastq_1" in result.stdout


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


def test_created_result_lists_next_steps(tmp_path):
    code, result = scaffold.scaffold(answers(), tmp_path)
    assert code == 0 and result["status"] == "created"
    steps = result["next_steps"]
    assert isinstance(steps, list) and steps and all(isinstance(s, str) and s for s in steps)
    trust = steps[0]
    assert "/hooks" in trust and "Codex" in trust
    assert "raw-data guard" in trust and "off in Codex until" in trust
    assert "sync reminder" not in trust and "sync_ratio.py" not in trust
    assert "again after any change to `.codex/hooks.json`" in trust
    rest = " ".join(steps[1:])
    assert "config/samples.tsv" in rest and "data/raw/" in rest and "read-only" in rest
    read_only = steps[2]
    assert "Recommended" in read_only and "optional" not in read_only.lower()
    assert "chmod -R a-w data/raw" in read_only and "attrib +R" in read_only
    assert "chmod -R u+w data/raw" in read_only and "attrib -R" in read_only
    assert "recorded in `data/README.md`" in read_only and "best-effort" in read_only


def test_no_next_steps_when_nothing_created(tmp_path):
    _, planned = scaffold.scaffold(answers(), tmp_path, dry_run=True)
    assert "next_steps" not in planned
    (tmp_path / "README.md").write_text("mine\n")
    _, clash = scaffold.scaffold(answers(), tmp_path)
    assert clash["status"] == "conflict" and "next_steps" not in clash


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
    git(project, "check-ignore", ".nerv/raw-snapshot.json")  # exits non-zero if not ignored


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


def test_adapters_have_no_stop_hook(tmp_path):
    project = build(tmp_path)
    for path in (NERV_INIT / "hooks/adapters/claude-settings.json", NERV_INIT / "hooks/adapters/codex-hooks.json",
                 project / ".claude/settings.json", project / ".codex/hooks.json"):
        assert "Stop" not in json.loads(path.read_text())["hooks"], path


@pytest.mark.parametrize("adapter", ["claude-settings.json", "codex-hooks.json"])
def test_guard_pre_and_post_matchers_cover_same_tools(adapter):
    hooks = json.loads((NERV_INIT / "hooks/adapters" / adapter).read_text())["hooks"]
    matchers = {event: [g["matcher"] for g in hooks[event] if "raw_guard.py" in g["hooks"][0]["command"]]
                for event in ("PreToolUse", "PostToolUse")}
    assert matchers["PreToolUse"] == matchers["PostToolUse"] and len(matchers["PreToolUse"]) == 1


def test_installed_guard_finds_project_root(tmp_path):
    project = build(tmp_path)
    (project / "data/raw/S1.fq").write_text("x")
    event = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "cwd": str(project),
             "tool_input": {"file_path": "data/raw/S1.fq"}}
    out = subprocess.run([sys.executable, str(project / ".nerv/hooks/raw_guard.py"), "--agent", "claude"],
                         input=json.dumps(event), capture_output=True, text=True).stdout
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_installed_sync_report_runs(tmp_path):
    project = build(tmp_path)
    out = subprocess.run([sys.executable, str(project / ".nerv/scripts/sync_ratio.py")], cwd=project,
                         capture_output=True, text=True)
    assert out.returncode == 0 and isinstance(json.loads(out.stdout), list)


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
