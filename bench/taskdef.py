"""Task definitions: where each task's hidden material lives and how mutants are made.

A task folder holds:
  answers.json           scaffold answers, project_question, reference pins
  allowed_phrases.txt    statistical phrases the wording check removes first (one per line)
  prompt.md followup.md  what the agent is asked, in session 1 and in the follow-up session
  generate.py            seeded inputs: generate(out, stage) writes project-relative files
  reference.py reference_followup.py
  hidden/                conftest.py, test_task.py, test_followup.py
  mutants.json           {stage: {mutant id: [[old, new], ...]}}, applied to that stage's reference
  traps.json             {"module": path, stage: {trap: {"tests": [...], "mutants": [...]}}}

Each mutant is the reference with exact text replacements, so it can't drift from it.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
TASKS = BENCH / "tasks"
STAGES = ("first", "followup")
REFERENCE = {"first": "reference.py", "followup": "reference_followup.py"}
HIDDEN_FILES = {"first": ["test_task.py"], "followup": ["test_followup.py", "test_task.py"]}
FORBIDDEN_WORDS = re.compile(r"\b(test-first|tests|testing|test|pytest|TDD)\b", re.I)


class TaskError(ValueError):
    pass


def task_dirs():
    return sorted(p for p in TASKS.iterdir() if (p / "traps.json").is_file()) if TASKS.is_dir() else []


def task_dir(name):
    path = TASKS / name
    if not (path / "traps.json").is_file():
        raise TaskError(f"no task {name!r} under {TASKS}")
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def traps(task):
    return read_json(Path(task) / "traps.json")


def module_path(task):
    return traps(task)["module"]


def mutant_ids(task, stage):
    return list(read_json(Path(task) / "mutants.json").get(stage, {}))


def mutant_source(task, stage, mutant):
    """The stage's reference with the mutant's replacements; each old text must occur exactly once."""
    task = Path(task)
    source = (task / REFERENCE[stage]).read_text(encoding="utf-8")
    for old, new in read_json(task / "mutants.json")[stage][mutant]:
        if source.count(old) != 1:
            raise TaskError(f"{task.name}/{stage}/{mutant}: {old!r} occurs {source.count(old)} times")
        source = source.replace(old, new)
    return source


def allowed_phrases(task):
    path = Path(task) / "allowed_phrases.txt"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    return [line.strip() for line in lines if line.strip()]


def forbidden_words(text, allowed=()):
    """Software-testing words left after removing the allowed phrases (case-insensitive)."""
    for phrase in sorted(allowed, key=len, reverse=True):
        text = re.sub(re.escape(phrase), " ", text, flags=re.I)
    return FORBIDDEN_WORDS.findall(text)


def hidden_env(module, stage, extra=None):
    env = {**os.environ, "BENCH_MODULE": str(module), "BENCH_STAGE": stage,
           "PYTHONDONTWRITEBYTECODE": "1", **(extra or {})}
    env.pop("PYTEST_ADDOPTS", None)
    return env


def run_hidden(task, stage, module, python=None, junit=None, tests=None, timeout=None):
    """Run the stage's hidden tests against a module file, from the task's hidden/ folder."""
    hidden = Path(task) / "hidden"
    cmd = [str(python or sys.executable), "-m", "pytest", "-q", "-p", "no:cacheprovider",
           "--rootdir", str(hidden), "-c", os.devnull, *(tests or HIDDEN_FILES[stage])]
    if junit:
        cmd += ["--junitxml", str(junit)]
    return subprocess.run(cmd, cwd=hidden, capture_output=True, text=True, encoding="utf-8",
                          env=hidden_env(module, stage), timeout=timeout)
