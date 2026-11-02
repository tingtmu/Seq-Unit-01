"""Build a run repo for one task and one arm.

Order (design.md, "Building a run repo"):
  1. scaffold.py with the task's answers and fixed date;
  2. fill what nerv-init's agent steps would fill: the project question, the reference pins,
     the task's config files, and the raw delivery with its provenance lines, made read-only;
  3. arm B only: remove each CUE_LINES entry, failing if one is missing;
  4. run the Test command (must pass), then commit and tag `baseline` as `bench`.

Usage: build.py TASK_DIR ARM TARGET [--python PATH]
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import arms

BENCH = Path(__file__).resolve().parent
REPO = BENCH.parent
SCAFFOLD = REPO / "skills" / "nerv-init" / "scripts" / "scaffold.py"
RUNS_ROOT = REPO.parent / "nerv_all_runs"
BENCH_VENV = RUNS_ROOT / "bench-venv"
BENCH_PYTHON = BENCH_VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
SCAFFOLD_KEYS = ("project_name", "assay", "engine", "languages", "compute", "sensitive", "date")
IDENTITY = ("-c", "user.name=bench", "-c", "user.email=bench@example.invalid")


class BenchError(RuntimeError):
    pass


def load_module(path, name=None):
    path = Path(path)
    spec = importlib.util.spec_from_file_location(name or f"bench_{path.parent.name}_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_writable(path):
    return os.access(path, os.W_OK)


def git(cwd, *args, check=True):
    result = subprocess.run(["git", *IDENTITY, *args], cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8")
    if check and result.returncode != 0:
        raise BenchError(f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip()}")
    return result.stdout


def quiet_env(extra=None):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(extra or {})}
    env.pop("PYTEST_ADDOPTS", None)
    return env


def run_test_command(repo, python):
    """The project's Test command (`pytest tests/`), leaving no cache or bytecode behind."""
    return subprocess.run([str(python), "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"],
                          cwd=repo, capture_output=True, text=True, env=quiet_env())


def default_python():
    return BENCH_PYTHON if BENCH_PYTHON.is_file() else Path(sys.executable)


def read_answers(task_dir):
    return json.loads((Path(task_dir) / "answers.json").read_text(encoding="utf-8"))


def replace_line(path, pattern, text):
    content = path.read_text(encoding="utf-8")
    new, count = re.subn(pattern, text, content, count=1, flags=re.M)
    if count != 1:
        raise BenchError(f"{path}: no line matches {pattern!r}")
    path.write_text(new, encoding="utf-8", newline="\n")


def fill_project(repo, answers):
    question = answers["project_question"]
    replace_line(repo / "AGENTS.md", r"^<!-- nerv: [^\n]*biological question[^\n]*-->$", question)
    replace_line(repo / "README.md", r"^<!-- nerv: what question this project answers[^\n]*-->$", question)
    config = repo / "config" / "config.yaml"
    for key, value in answers.get("reference", {}).items():
        replace_line(config, rf'^(\s*{key}: )""', rf'\g<1>"{value}"')


def generate_into(task_dir, stage):
    """Run the task generator in a scratch folder; return {project-relative path: bytes}."""
    gen = load_module(Path(task_dir) / "generate.py")
    with tempfile.TemporaryDirectory() as scratch:
        gen.generate(Path(scratch), stage=stage)
        root = Path(scratch)
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def add_provenance(repo, raw_files, source, received):
    """Append one provenance row per raw file to the table in data/README.md."""
    readme = repo / "data" / "README.md"
    lines = readme.read_text(encoding="utf-8").split("\n")
    try:
        start = lines.index("### Provenance")
    except ValueError as exc:
        raise BenchError(f"{readme}: no '### Provenance' section") from exc
    end = start + 1
    while end < len(lines) and not lines[end].startswith("|"):
        end += 1
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    rows = [f"| `{Path(rel).relative_to('data').as_posix()}` | {source} | {received} | {sha256(repo / rel)} |"
            for rel in raw_files]
    readme.write_text("\n".join(lines[:end] + rows + lines[end:]), encoding="utf-8", newline="\n")


def make_read_only(paths):
    for path in paths:
        os.chmod(path, stat.S_IREAD)


def place_inputs(repo, files, source, received):
    """Write generated files into the repo; raw files get provenance and become read-only."""
    raw = []
    for rel, data in files.items():
        dest = repo / rel
        if rel.startswith("data/raw/") and dest.exists():
            raise BenchError(f"{dest}: raw file already exists; new data goes in a new delivery")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and not is_writable(dest):
            raise BenchError(f"{dest}: read-only")
        dest.write_bytes(data)
        if rel.startswith("data/raw/"):
            raw.append(rel)
    if raw:
        add_provenance(repo, raw, source, received)
        make_read_only(repo / rel for rel in raw)
    return raw


def remove_cue_lines(repo, cue_lines=None):
    for rel, line in cue_lines if cue_lines is not None else arms.CUE_LINES:
        path = repo / rel
        lines = path.read_text(encoding="utf-8").split("\n")
        if line not in lines:
            raise BenchError(f"{rel}: cue line not found, the template drifted: {line!r}")
        path.write_text("\n".join(x for x in lines if x != line), encoding="utf-8", newline="\n")


def build_run_repo(task_dir, arm, target, python=None):
    if arm not in arms.ARMS:
        raise BenchError(f"arm must be one of {arms.ARMS}, got {arm!r}")
    task_dir, target = Path(task_dir), Path(target)
    if target.exists():
        raise BenchError(f"{target} already exists")
    answers = read_answers(task_dir)
    scaffold = load_module(SCAFFOLD, "scaffold")
    code, result = scaffold.scaffold({k: answers[k] for k in SCAFFOLD_KEYS if k in answers}, target)
    if code != 0:
        raise BenchError(f"scaffold failed: {result}")
    fill_project(target, answers)
    place_inputs(target, generate_into(task_dir, "first"), "sequencing core (synthetic, bench)", answers["date"])
    if arm == "B":
        remove_cue_lines(target)
    check = run_test_command(target, python or default_python())
    if check.returncode != 0:
        raise BenchError(f"Test command fails in {target}:\n{check.stdout}{check.stderr}")
    git(target, "config", "user.name", "bench")
    git(target, "config", "user.email", "bench@example.invalid")
    git(target, "add", "-A")
    git(target, "commit", "-qm", "baseline")
    git(target, "tag", "baseline")
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("task_dir")
    parser.add_argument("arm", choices=arms.ARMS)
    parser.add_argument("target")
    parser.add_argument("--python", help="Python that runs the Test command (default: bench-venv)")
    args = parser.parse_args(argv)
    try:
        print(build_run_repo(args.task_dir, args.arm, args.target, args.python))
    except BenchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
