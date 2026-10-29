import json
import os
import subprocess
import sys

import pytest

from conftest import NERV_INIT

SCRIPT = NERV_INIT / "hooks" / "raw_guard.py"


@pytest.fixture
def project(tmp_path):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    (raw / "S1_R1.fastq.gz").write_bytes(b"\x1f\x8b")
    (tmp_path / "data" / "processed").mkdir()
    return tmp_path


def run(project, event, agent="claude", raw_stdin=None):
    event = {"cwd": str(project), **event} if raw_stdin is None else None
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--agent", agent],
        input=raw_stdin if raw_stdin is not None else json.dumps(event),
        capture_output=True, text=True, env={**os.environ, "NERV_PROJECT_ROOT": str(project)},
    )
    assert result.returncode == 0
    return (json.loads(result.stdout) if result.stdout.strip() else None), result.stderr


def pre(tool, **tool_input):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}


def decision(output):
    return output and output["hookSpecificOutput"]["permissionDecision"]


def test_new_raw_file_allowed(project):
    out, _ = run(project, pre("Write", file_path="data/raw/batch2/S1_R1.fastq.gz", content="x"))
    assert out is None


def test_edit_existing_raw_file_asks_in_claude(project):
    out, _ = run(project, pre("Edit", file_path=str(project / "data/raw/S1_R1.fastq.gz"),
                              old_string="a", new_string="b"))
    assert decision(out) == "ask"
    assert "data/raw/S1_R1.fastq.gz" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_overwrite_existing_raw_file_asks(project):
    out, _ = run(project, pre("Write", file_path="data/raw/S1_R1.fastq.gz", content="x"))
    assert decision(out) == "ask"


def test_windows_style_and_dotdot_paths(project):
    out, _ = run(project, pre("Edit", file_path="data\\processed\\..\\raw\\S1_R1.fastq.gz"))
    assert decision(out) == "ask"


def test_processed_file_untouched(project):
    (project / "data/processed/x.tsv").write_text("x")
    assert run(project, pre("Write", file_path="data/processed/x.tsv", content="y"))[0] is None


def test_rm_denied_in_codex_with_instructions(project):
    out, _ = run(project, pre("Bash", command="rm data/raw/S1_R1.fastq.gz"), agent="codex")
    assert decision(out) == "deny"
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "Hard rule" in reason and "run it themselves" in reason


@pytest.mark.parametrize("command", [
    "rm -rf data/raw",
    "cd . && mv data/raw/S1_R1.fastq.gz /tmp/",
    "sed -i 's/a/b/' data/raw/S1_R1.fastq.gz",
    "truncate -s 0 data/raw/S1_R1.fastq.gz",
    "echo x > data/raw/S1_R1.fastq.gz",
    "echo x >> data/raw/S1_R1.fastq.gz",
    "cp other.fq data/raw/S1_R1.fastq.gz",
    "Remove-Item data\\raw\\S1_R1.fastq.gz",
])
def test_destructive_shell_asks(project, command):
    assert decision(run(project, pre("Bash", command=command))[0]) == "ask"


@pytest.mark.parametrize("command", [
    "zcat data/raw/S1_R1.fastq.gz | head",
    "fastqc data/raw/S1_R1.fastq.gz -o results/qc",
    "cp data/raw/S1_R1.fastq.gz data/processed/",
    "wc -l < data/raw/S1_R1.fastq.gz > data/processed/count.txt",
    "echo x > data/raw/new_file.txt",
    "mv download.fq data/raw/",
])
def test_non_destructive_shell_allowed(project, command):
    assert run(project, pre("Bash", command=command))[0] is None


def test_codex_apply_patch(project):
    update = "*** Begin Patch\n*** Update File: data/raw/S1_R1.fastq.gz\n@@\n-a\n+b\n*** End Patch\n"
    assert decision(run(project, pre("apply_patch", command=update), agent="codex")[0]) == "deny"
    add = "*** Begin Patch\n*** Add File: data/raw/new.txt\n+x\n*** End Patch\n"
    assert run(project, pre("apply_patch", command=add), agent="codex")[0] is None


@pytest.mark.parametrize("stdin", ["", "not json", "[1, 2]", '{"hook_event_name": "PreToolUse", "tool_input": 5}'])
def test_malformed_input_fails_open(project, stdin):
    out, err = run(project, None, raw_stdin=stdin)
    assert out is None
    if stdin != '{"hook_event_name": "PreToolUse", "tool_input": 5}':
        assert "nerv raw_guard" in err


def post(tool, **tool_input):
    return {"hook_event_name": "PostToolUse", "tool_name": tool, "tool_input": tool_input, "tool_response": {}}


def context(output):
    return output["hookSpecificOutput"]["additionalContext"]


@pytest.fixture
def settled(project):
    """A project whose raw snapshot already matches data/raw/."""
    run(project, post("Bash", command="ls"))
    return project


def test_post_tool_use_provenance_reminder(settled):
    new = settled / "data/raw/batch2/S1_R1.fastq.gz"
    new.parent.mkdir()
    new.write_bytes(b"x")
    out, _ = run(settled, {**post("Write", file_path="data/raw/batch2/S1_R1.fastq.gz"),
                           "tool_response": {"type": "create", "filePath": "data/raw/batch2/S1_R1.fastq.gz"}})
    assert "data/README.md" in context(out) and "data/raw/batch2/S1_R1.fastq.gz" in context(out)
    assert "data/raw/S1_R1.fastq.gz" not in context(out)


def test_post_tool_use_codex_patch_and_non_raw(settled):
    (settled / "data/raw/new.txt").write_text("x")
    add = "*** Begin Patch\n*** Add File: data/raw/new.txt\n+x\n*** End Patch\n"
    out, _ = run(settled, post("apply_patch", command=add), agent="codex")
    assert "data/README.md" in context(out)
    (settled / "scripts").mkdir()
    (settled / "scripts/a.py").write_text("x")
    assert run(settled, post("Write", file_path="scripts/a.py"))[0] is None


@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_new_raw_file_from_shell_reminds_once(settled, agent):
    new = settled / "data/raw/batch3/S5_R1.fastq.gz"
    new.parent.mkdir()
    new.write_bytes(b"x")
    out, _ = run(settled, post("Bash", command="python scripts/download.py"), agent=agent)
    assert "data/README.md" in context(out) and "data/raw/batch3/S5_R1.fastq.gz" in context(out)
    assert run(settled, post("Bash", command="ls"), agent=agent)[0] is None


def test_script_modifying_raw_file_reported(settled):
    (settled / "data/raw/S1_R1.fastq.gz").write_bytes(b"rewritten by a script")
    out, _ = run(settled, post("Bash", command="python scripts/fix_headers.py"))
    assert "data/raw/S1_R1.fastq.gz" in context(out) and "modified" in context(out)
    assert "stop" in context(out).lower() and "data/README.md" not in context(out)


def test_raw_file_removed_indirectly_reported(settled):
    (settled / "data/raw/S1_R1.fastq.gz").unlink()
    out, _ = run(settled, post("Bash", command="make clean"))
    assert "data/raw/S1_R1.fastq.gz" in context(out) and "removed" in context(out)


def test_read_only_command_gives_no_message(settled):
    (settled / "data/processed/count.txt").write_text("1")
    assert run(settled, post("Bash", command="wc -l data/raw/S1_R1.fastq.gz > data/processed/count.txt"))[0] is None


def test_corrupt_snapshot_fails_open(settled):
    (settled / ".nerv/raw-snapshot.json").write_text("{not json")
    (settled / "data/raw/S1_R1.fastq.gz").write_bytes(b"changed")
    out, err = run(settled, post("Bash", command="ls"))
    assert out is None and "nerv raw_guard" in err
    assert run(settled, post("Bash", command="ls"))[0] is None  # snapshot replaced with current state


def test_gitkeep_ignored(project):
    (project / "data/raw/S1_R1.fastq.gz").unlink()
    (project / "data/raw/.gitkeep").write_text("")
    assert run(project, post("Bash", command="ls"))[0] is None


def test_missing_raw_folder_gives_no_message(tmp_path):
    out, err = run(tmp_path, post("Bash", command="ls"))
    assert out is None and err == ""


def test_long_file_lists_are_capped(settled):
    for i in range(30):
        (settled / f"data/raw/S{i:02d}_R2.fastq.gz").write_bytes(b"x")
    out, _ = run(settled, post("Bash", command="python scripts/download.py"))
    assert "and 10 more" in context(out) and "S29_R2" not in context(out)


def test_symlink_loop_does_not_hang(settled):
    try:
        os.symlink(settled / "data/raw", settled / "data/raw/loop", target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not permitted here")
    assert run(settled, post("Bash", command="ls"))[0] is None
