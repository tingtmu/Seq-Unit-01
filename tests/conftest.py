import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
NERV_INIT = REPO / "skills" / "nerv-init"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout


@pytest.fixture
def repo(tmp_path):
    """A committed git repo with documented scripts/ and workflow/ folders."""
    for folder in ("scripts", "workflow"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "README.md").write_text("# readme\n")
        (tmp_path / folder / "existing.py").write_text("".join(f"line {i}\n" for i in range(100)))
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "init")
    return tmp_path
