import json
import subprocess
import sys

from conftest import NERV_INIT, git, load

SCRIPT = NERV_INIT / "scripts" / "sync_ratio.py"
sync = load("sync_ratio", SCRIPT)


def folders(repo):
    return [r["folder"] for r in sync.find_out_of_sync(str(repo))[1]]


def test_new_script_reported(repo):
    (repo / "scripts" / "new.py").write_text("print(1)\n")
    assert folders(repo) == ["scripts/"]


def test_minor_edit_not_reported(repo):
    path = repo / "scripts" / "existing.py"
    path.write_text(path.read_text().replace("line 1\n", "line one\n"))
    assert folders(repo) == []


def test_large_edit_reported_and_threshold_configurable(repo, monkeypatch):
    path = repo / "scripts" / "existing.py"
    path.write_text("".join(f"changed {i}\n" for i in range(20)) + path.read_text()[200:])
    assert folders(repo) == ["scripts/"]
    monkeypatch.setenv("NERV_SYNC_THRESHOLD", "1000")
    assert folders(repo) == []


def test_staged_deletion_reported(repo):
    git(repo, "rm", "-q", "workflow/existing.py")
    assert folders(repo) == ["workflow/"]


def test_readme_updated_not_reported(repo):
    (repo / "scripts" / "new.py").write_text("print(1)\n")
    (repo / "scripts" / "README.md").write_text("# readme\nnew.py added\n")
    assert folders(repo) == []


def test_undocumented_folder_ignored(repo):
    (repo / "misc").mkdir()
    (repo / "misc" / "x.txt").write_text("x\n")
    assert folders(repo) == []


def test_no_commits_yet(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "README.md").write_text("# r\n")
    (tmp_path / "scripts" / "a.py").write_text("x\n")
    assert folders(tmp_path) == []  # README is new too, so the folder is in sync


def run_cli(cwd):
    return subprocess.run([sys.executable, str(SCRIPT)], cwd=cwd, capture_output=True, text=True)


def test_report_lists_folders_without_state(repo):
    (repo / "scripts" / "new.py").write_text("x\n")
    result = run_cli(repo)
    assert result.returncode == 0
    assert json.loads(result.stdout) == [
        {"folder": "scripts/", "readme": "scripts/README.md", "files": ["scripts/new.py"]}
    ]
    assert not (repo / ".git" / "nerv-sync-state").exists()


def test_report_in_sync_and_no_git(repo, tmp_path_factory):
    for cwd in (repo, tmp_path_factory.mktemp("nogit")):
        result = run_cli(cwd)
        assert (result.returncode, json.loads(result.stdout)) == (0, [])
