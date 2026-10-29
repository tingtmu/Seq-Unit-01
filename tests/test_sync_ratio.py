import json
import subprocess
import sys

from conftest import NERV_INIT, git, load

SCRIPT = NERV_INIT / "hooks" / "sync_ratio.py"
sync = load("sync_ratio", SCRIPT)


def folders(repo):
    return [r["folder"] for r in sync.find_out_of_sync(str(repo))[1]]


def stop(repo, active=False):
    return sync.run_hook(json.dumps({"hook_event_name": "Stop", "cwd": str(repo), "stop_hook_active": active}))


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


def test_stop_reminds_once_per_state(repo):
    (repo / "workflow" / "Snakefile").write_text("rule all:\n")
    first = json.loads(stop(repo))
    assert first["decision"] == "block"
    assert "workflow/README.md" in first["reason"]
    assert stop(repo) is None  # repeated stop, same state
    (repo / "scripts" / "new.py").write_text("x\n")
    assert json.loads(stop(repo))["decision"] == "block"  # state changed


def test_stop_hook_active_never_blocks(repo):
    (repo / "workflow" / "Snakefile").write_text("rule all:\n")
    assert stop(repo, active=True) is None


def test_state_cleared_when_in_sync(repo):
    new = repo / "scripts" / "new.py"
    new.write_text("x\n")
    assert stop(repo) is not None
    new.unlink()
    assert stop(repo) is None
    new.write_text("x\n")
    assert stop(repo) is not None  # a fresh out-of-sync state reminds again


def run_cli(cwd, stdin, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, input=stdin,
                          capture_output=True, text=True)


def test_no_git_is_silent(tmp_path):
    result = run_cli(tmp_path, json.dumps({"cwd": str(tmp_path)}))
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def test_cli_one_continuation_at_most(repo):
    (repo / "scripts" / "new.py").write_text("x\n")
    event = {"hook_event_name": "Stop", "cwd": str(repo), "stop_hook_active": False}
    first = run_cli(repo, json.dumps(event))
    assert json.loads(first.stdout)["decision"] == "block"
    event["stop_hook_active"] = True
    assert run_cli(repo, json.dumps(event)).stdout == ""
    event["stop_hook_active"] = False
    assert run_cli(repo, json.dumps(event)).stdout == ""


def test_report_mode_lists_folders_without_touching_state(repo):
    (repo / "scripts" / "new.py").write_text("x\n")
    result = run_cli(repo, "", "--report")
    report = json.loads(result.stdout)
    assert report == [{"folder": "scripts/", "readme": "scripts/README.md", "files": ["scripts/new.py"]}]
    assert not (repo / ".git" / "nerv-sync-state").exists()
    assert stop(repo) is not None  # the hook still reminds after a report
    assert json.loads(run_cli(repo, "", "--report").stdout) == report


def test_report_mode_in_sync_and_no_git(repo, tmp_path_factory):
    assert json.loads(run_cli(repo, "", "--report").stdout) == []
    assert json.loads(run_cli(tmp_path_factory.mktemp("nogit"), "", "--report").stdout) == []


def test_malformed_stdin_uses_cwd(repo):
    (repo / "scripts" / "new.py").write_text("x\n")
    result = run_cli(repo, "not json")
    assert result.returncode == 0
    assert "scripts/README.md" in json.loads(result.stdout)["reason"]
