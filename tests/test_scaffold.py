import json
import re
import shutil
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
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", ".gitignore", ".nerv/scripts/sync_ratio.py"):
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
    assert top == {".git", ".gitattributes", ".gitignore", ".nerv", "AGENTS.md", "CLAUDE.md", "README.md",
                   "config", "data", "workflow", "scripts", "notebooks", "envs", "results", "tests", "docs"}



def test_gitattributes_sets_lf(tmp_path):
    project = build(tmp_path)
    text = (project / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in text.splitlines()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_git_add_quiet_with_autocrlf(tmp_path):
    project = build(tmp_path, engine="scripts")  # includes workflow/run_all.sh
    added = subprocess.run(["git", "-c", "core.autocrlf=true", "add", "-A"], cwd=project,
                           check=True, capture_output=True, text=True)
    assert "CRLF" not in added.stderr and "LF will be replaced" not in added.stderr, added.stderr
    eol = git(project, "ls-files", "--eol").splitlines()
    text_files = [line for line in eol if line.startswith("i/lf")]
    assert text_files and all("attr/text=auto eol=lf" in line for line in text_files)
    for name in (".nerv/scripts/sync_ratio.py", "workflow/run_all.sh"):
        assert any(line.endswith(name) for line in text_files), name

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
    sheet.write_text(sheet.read_text().replace("sample_id	", ""))
    result = run_pytest(project)
    assert result.returncode == 1 and "sample_id" in result.stdout


COUNTS_SHEET = "sample_id\tcondition\treplicate\nS1\tcontrol\t1\n"


def test_python_smoke_test_accepts_counts_sheet(tmp_path):
    project = build(tmp_path, languages=["python"])
    (project / "config/samples.tsv").write_text(COUNTS_SHEET)
    result = run_pytest(project)
    assert result.returncode == 0, result.stdout + result.stderr


def run_common_smk(project, sheet_text):
    """Execute the generated common.smk with a stub Snakemake config; return its namespace."""
    pytest.importorskip("pandas")  # common.smk imports it; the repo venv has it
    sheet = project / "config/samples.tsv"
    sheet.write_text(sheet_text)
    source = (project / "workflow/rules/common.smk").read_text(encoding="utf-8")
    namespace = {"config": {"samples": str(sheet)}}
    exec(compile(source, "common.smk", "exec"), namespace)
    return namespace


def test_common_smk_accepts_counts_sheet(tmp_path):
    namespace = run_common_smk(build(tmp_path), COUNTS_SHEET)
    assert namespace["SAMPLES"] == ["S1"]


def test_common_smk_names_missing_fastq(tmp_path):
    missing = str(tmp_path / "absent_R1.fastq.gz")
    with pytest.raises(ValueError, match=r"absent_R1\.fastq\.gz"):  # list repr doubles Windows backslashes
        run_common_smk(build(tmp_path / "proj"), f"sample_id\tfastq_1\nS1\t{missing}\n")


def test_common_smk_names_missing_sample_id(tmp_path):
    with pytest.raises(ValueError, match="sample_id"):
        run_common_smk(build(tmp_path), "condition\treplicate\ncontrol\t1\n")


def test_bulk_design_left_open_without_batch(tmp_path):
    project = build(tmp_path)
    design = (project / "config/design.yaml").read_text(encoding="utf-8")
    assert re.search(r'^design: ""\s+# fix in the analysis plan before looking at results', design, re.MULTILINE)
    header = (project / "config/samples.tsv").read_text(encoding="utf-8").splitlines()[0].split("\t")
    assert "batch" not in design and "batch" not in header


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
    assert code == 0 and result["status"] == "planned" and "AGENTS.md" in result["files"]
    assert list(tmp_path.iterdir()) == []


def test_dry_run_plans_around_data_outside_skeleton(tmp_path):
    delivery = tmp_path / "input_data" / "GSE141713"
    delivery.mkdir(parents=True)
    (delivery / "counts.tsv.gz").write_bytes(b"x")
    code, result = scaffold.scaffold(answers(), tmp_path, dry_run=True)
    assert code == 0 and result["status"] == "planned"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["input_data"]


def test_dry_run_reports_conflicts(tmp_path):
    (tmp_path / "README.md").write_text("mine\n")
    (tmp_path / "scripts").mkdir()
    code, result = scaffold.scaffold(answers(), tmp_path, dry_run=True)
    assert code == 1 and result["status"] == "conflict"
    assert result["conflicts"] == ["README.md", "scripts/"]
    assert "files" not in result
    assert sorted(p.name for p in tmp_path.iterdir()) == ["README.md", "scripts"]
    assert (tmp_path / "README.md").read_text() == "mine\n"


def isolated_git_config(tmp_path, monkeypatch, identity):
    """Point git at a temp global config (no system config), with or without user.name/user.email."""
    config = tmp_path / "gitconfig"
    config.write_text("[user]\n\tname = Test User\n\temail = test@example.org\n" if identity else "",
                      encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def identity_set(tmp_path, monkeypatch):
    isolated_git_config(tmp_path, monkeypatch, identity=True)


@pytest.fixture
def identity_missing(tmp_path, monkeypatch):
    isolated_git_config(tmp_path, monkeypatch, identity=False)


def create(tmp_path):
    """Scaffold into a fresh subfolder (the temp git config lives in tmp_path itself)."""
    code, result = scaffold.scaffold(answers(), tmp_path / "proj")
    assert code == 0 and result["status"] == "created", result
    return result


GIT_COMMANDS = ("git config", "git commit", "git add")


def assert_one_user_step(steps):
    """Exactly the read-only entry; no git command or sample sheet."""
    assert len(steps) == 1, steps
    assert "read-only" in steps[0]
    assert not any(c in steps[0] for c in GIT_COMMANDS), steps[0]
    assert "config/samples.tsv" not in steps[0], steps[0]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_identity_set_leaves_commit_to_agent(tmp_path, identity_set):
    result = create(tmp_path)
    assert result["git"] == "initialized" and result["git_identity"] == "set"
    assert_one_user_step(result["next_steps"])


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_identity_missing_has_no_git_step(tmp_path, identity_missing):
    result = create(tmp_path)
    assert result["git"] == "initialized" and result["git_identity"] == "missing"
    assert_one_user_step(result["next_steps"])


def test_git_unavailable_reports_identity_missing(tmp_path, identity_set, monkeypatch):
    def no_git(*args, **kwargs):
        raise OSError("git not found")
    monkeypatch.setattr(scaffold.subprocess, "run", no_git)
    result = create(tmp_path)
    assert result["git"] == "unavailable" and result["git_identity"] == "missing"
    assert_one_user_step(result["next_steps"])


def test_created_result_lists_next_steps(tmp_path, identity_missing):
    result = create(tmp_path)
    steps = result["next_steps"]
    assert isinstance(steps, list) and all(isinstance(s, str) and s for s in steps)
    assert len(steps) == 1, steps
    read_only = steps[0]

    assert len(re.findall(r"[.!?](?:\s|$)", read_only)) <= 2, read_only
    assert "delivery" in read_only and "data/raw/" in read_only
    assert "new delivery folder" in read_only
    assert "chmod" not in read_only and "attrib" not in read_only
    assert not any(w in read_only.lower() for w in ("guard", "hook", "/hooks")), read_only
    assert not re.search(r"no tool|any tool|every tool|cannot be deleted", read_only, re.IGNORECASE), read_only
    assert not re.search(r"\block\b", read_only, re.IGNORECASE)


def test_addon_conventions_land_before_subsections(tmp_path):
    readme = (build(tmp_path) / "data/README.md").read_text(encoding="utf-8")
    addon = readme.index("A precomputed count matrix stays in its delivery folder")
    assert addon < readme.index("### Adding a delivery") < readme.index("### Provenance")
    table_end = readme.index("|------|")
    assert readme[table_end:].split("\n", 2)[1] == "", "provenance table must stay last before Current state"


def test_data_readme_explains_adding_a_delivery(tmp_path):
    readme = (build(tmp_path) / "data/README.md").read_text(encoding="utf-8")
    assert "### Adding a delivery" in readme
    section = readme.split("### Adding a delivery", 1)[1].split("\n## ", 1)[0]
    for phrase in ("checksum", "raw/<delivery>/", "provenance", "read-only", "config/samples.tsv"):
        assert phrase in section, phrase
    sequence = ["chmod -R a-w data/raw/<delivery>", "Git Bash",
                "attrib +R /S data\\raw\\<delivery>\\*", "cmd or PowerShell",
                "chmod -R u+w data/raw/<delivery>", "Git Bash",
                "attrib -R /S data\\raw\\<delivery>\\*", "cmd or PowerShell"]
    position = 0
    for text in sequence:
        found = section.find(text, position)
        assert found >= 0, (text, section)
        position = found + len(text)
    assert "sha256sum" not in readme
    assert not re.search(r"\block\b", readme, re.IGNORECASE)


def test_data_readme_states_windows_limit(tmp_path):
    readme = (build(tmp_path) / "data/README.md").read_text(encoding="utf-8")
    section = readme.split("### Adding a delivery", 1)[1].split("### Provenance", 1)[0]
    assert "Git Bash `rm`" in section and "`Remove-Item -Force`" in section and "hard rule" in section, section
    assert not re.search(r"hook|guard", readme, re.IGNORECASE)


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
    assert {"data/README.md", "data/raw/.gitkeep", "AGENTS.md", ".nerv/scripts/sync_ratio.py"} <= tracked


def test_sensitive_adds_rules_and_ignores(tmp_path):
    project = build(tmp_path, sensitive=True)
    agents = (project / "AGENTS.md").read_text()
    assert "sensitive (human or controlled-access)" in agents
    (project / "results/table.tsv").write_text("x")
    (project / "data/extra.csv").write_text("x")
    untracked = set(git(project, "ls-files", "--others", "--exclude-standard").split())
    assert "results/table.tsv" not in untracked and "data/extra.csv" not in untracked
    assert {"results/README.md", "data/README.md", "config/samples.tsv"} <= untracked


def test_raw_data_rule_names_deletion(tmp_path):
    agents = (build(tmp_path) / "AGENTS.md").read_text(encoding="utf-8")
    first_rule = re.search(r"^1\. (.+)$", agents, re.MULTILINE).group(1)
    assert "Never delete, move, overwrite, or edit files in `data/raw/`" in first_rule
    assert "read-only" in first_rule
    assert "record its source and checksum in `data/README.md`" in first_rule


def test_not_sensitive_has_no_extra_rules(tmp_path):
    assert "sensitive" not in (build(tmp_path) / "AGENTS.md").read_text()


def test_no_agent_hooks(tmp_path):
    """No hook files or hook config, so nothing can intercept an intake move or run at end of turn."""
    project = build(tmp_path)
    for path in (".nerv/hooks", ".claude/settings.json", ".codex/hooks.json"):
        assert not (project / path).exists(), path
    assert "raw-snapshot" not in (project / ".gitignore").read_text(encoding="utf-8")
    assert (project / ".nerv/scripts/sync_ratio.py").is_file()


def test_installed_sync_report_runs(tmp_path):
    project = build(tmp_path)
    out = subprocess.run([sys.executable, str(project / ".nerv/scripts/sync_ratio.py")], cwd=project,
                         capture_output=True, text=True)
    assert out.returncode == 0 and isinstance(json.loads(out.stdout), list)


@pytest.mark.parametrize("question", ["Which genes respond to drug X in liver?", "TBD"])
def test_question_answer_accepted(tmp_path, question):
    assert_common(build(tmp_path, question=question))


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
