"""Cue benchmark harness (openspec/changes/add-cue-benchmark): arms, tasks, runner, scorer, summary."""
import filecmp
import re
import json
import sys
from pathlib import Path

import pytest

from conftest import REPO

BENCH = REPO / "bench"
sys.path.insert(0, str(BENCH))
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bench"

import arms  # noqa: E402
import build  # noqa: E402

FAKE_GENERATE = '''\
from pathlib import Path

SEED = 7


def generate(out, stage="first"):
    out = Path(out)
    if stage == "first":
        (out / "data/raw/delivery-01").mkdir(parents=True, exist_ok=True)
        (out / "data/raw/delivery-01/counts.tsv").write_bytes(b"gene\\tS1\\nG1\\t5\\n")
        (out / "config").mkdir(parents=True, exist_ok=True)
        (out / "config/samples.tsv").write_bytes(b"sample_id\\tcondition\\nS1\\tctrl\\n")
    else:
        (out / "data/raw/delivery-02").mkdir(parents=True, exist_ok=True)
        (out / "data/raw/delivery-02/counts.tsv").write_bytes(b"gene\\tS2\\nG1\\t7\\n")
'''


@pytest.fixture
def fake_task(tmp_path):
    task = tmp_path / "tasks" / "t0-fake"
    task.mkdir(parents=True)
    (task / "answers.json").write_text(json.dumps({
        "project_name": "t0-fake", "assay": "bulk-rnaseq", "engine": "scripts", "languages": ["python"],
        "compute": "local", "sensitive": False, "date": "2026-11-03",
        "project_question": "Which genes change with treatment?",
        "reference": {"organism": "Homo sapiens", "genome_build": "GRCh38", "annotation": "GENCODE v43"},
    }))
    (task / "generate.py").write_text(FAKE_GENERATE)
    return task


def tree(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if p.is_file() and ".git" not in p.relative_to(root).parts)


# --- 2.1 arms and run repo build ---

def test_arms_differ_only_by_cue_lines(fake_task, tmp_path):
    a = build.build_run_repo(fake_task, "A", tmp_path / "A", python=sys.executable)
    b = build.build_run_repo(fake_task, "B", tmp_path / "B", python=sys.executable)
    assert tree(a) == tree(b)
    differing = [rel for rel in tree(a) if not filecmp.cmp(a / rel, b / rel, shallow=False)]
    assert sorted(differing) == sorted(f for f, _ in arms.CUE_LINES)
    for rel, line in arms.CUE_LINES:
        lines_a = (a / rel).read_text(encoding="utf-8").splitlines()
        lines_b = (b / rel).read_text(encoding="utf-8").splitlines()
        assert line in lines_a and line not in lines_b
        assert [x for x in lines_a if x != line] == lines_b


def test_run_repo_has_inputs_and_baseline(fake_task, tmp_path):
    repo = build.build_run_repo(fake_task, "B", tmp_path / "B", python=sys.executable)
    agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "Which genes change with treatment?" in agents and "biological question" not in agents
    assert "Which genes change with treatment?" in (repo / "README.md").read_text(encoding="utf-8")
    config = (repo / "config/config.yaml").read_text(encoding="utf-8")
    assert 'genome_build: "GRCh38"' in config and 'annotation: "GENCODE v43"' in config
    raw = repo / "data/raw/delivery-01/counts.tsv"
    assert raw.is_file() and not build.is_writable(raw)
    data_readme = (repo / "data/README.md").read_text(encoding="utf-8")
    assert "`raw/delivery-01/counts.tsv`" in data_readme and build.sha256(raw) in data_readme
    log = build.git(repo, "log", "--format=%an %s", "baseline")
    assert log.strip() == "bench baseline"
    assert build.git(repo, "status", "--porcelain").strip() == ""
    assert not (repo / ".pytest_cache").exists()


def test_cue_drift_stops_build(fake_task, tmp_path, monkeypatch):
    monkeypatch.setattr(arms, "CUE_LINES", [*arms.CUE_LINES[:2], ("tests/README.md", "- Not in the template.")])
    with pytest.raises(build.BenchError, match=r"tests/README\.md.*Not in the template"):
        build.build_run_repo(fake_task, "B", tmp_path / "B", python=sys.executable)


def test_cue_lines_match_templates():
    base = REPO / "skills/nerv-init/templates/base"
    for rel, line in arms.CUE_LINES:
        assert line in (base / rel).read_text(encoding="utf-8").splitlines(), rel


def test_arm_b_test_command_passes(fake_task, tmp_path):
    repo = build.build_run_repo(fake_task, "B", tmp_path / "B", python=sys.executable)
    assert build.run_test_command(repo, sys.executable).returncode == 0
    assert (repo / "tests/test_smoke.py").is_file()


def task_dirs():
    return sorted(p for p in (BENCH / "tasks").glob("*/") if (p / "generate.py").is_file())


@pytest.mark.parametrize("task", ["fake", *task_dirs()], ids=lambda t: getattr(t, "name", t))
@pytest.mark.parametrize("stage", ["first", "followup"])
def test_generate_is_deterministic(task, stage, fake_task, tmp_path):
    task = fake_task if task == "fake" else task
    gen = build.load_module(task / "generate.py")
    gen.generate(tmp_path / "one", stage=stage)
    gen.generate(tmp_path / "two", stage=stage)
    files = tree(tmp_path / "one")
    assert files and files == tree(tmp_path / "two")
    for rel in files:
        assert (tmp_path / "one" / rel).read_bytes() == (tmp_path / "two" / rel).read_bytes(), rel


# --- 3.1 task validity: hidden tests, mutants, traps, prompt wording ---

import taskdef  # noqa: E402

TASKS = taskdef.task_dirs()
STAGED = [(t, s) for t in TASKS for s in taskdef.STAGES]
MUTANTS = [(t, s, m) for t, s in STAGED for m in taskdef.mutant_ids(t, s)]


def staged_id(value):
    return value.name if isinstance(value, Path) else str(value)


def test_three_tasks_exist():
    assert [t.name for t in TASKS] == ["t1-scrna-qc", "t2-design-check", "t3-de-annotation"]


@pytest.mark.parametrize("task,stage", STAGED, ids=staged_id)
def test_reference_passes_hidden_tests(task, stage):
    result = taskdef.run_hidden(task, stage, task / taskdef.REFERENCE[stage])
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]


@pytest.mark.parametrize("task,stage,mutant", MUTANTS, ids=staged_id)
def test_each_mutant_fails_a_hidden_test(task, stage, mutant, tmp_path):
    module = tmp_path / Path(taskdef.module_path(task)).name
    module.write_text(taskdef.mutant_source(task, stage, mutant), encoding="utf-8")
    result = taskdef.run_hidden(task, stage, module)
    assert result.returncode == 1, f"mutant {mutant} survives:\n{result.stdout[-2000:]}"


def hidden_test_names(task, stage):
    names = set()
    for name in taskdef.HIDDEN_FILES[stage]:
        text = (task / "hidden" / name).read_text(encoding="utf-8")
        names |= {f"{name}::{t}" for t in re.findall(r"^def (test_\w+)", text, re.M)}
    return names


@pytest.mark.parametrize("task,stage", STAGED, ids=staged_id)
def test_every_trap_names_a_hidden_test_and_mutant(task, stage):
    traps = taskdef.traps(task)[stage]
    tests, mutants = hidden_test_names(task, stage), set(taskdef.mutant_ids(task, stage))
    assert traps
    for trap, cover in traps.items():
        assert cover["tests"] and set(cover["tests"]) <= tests, trap
        assert cover["mutants"] and set(cover["mutants"]) <= mutants, trap
    assert mutants == {m for cover in traps.values() for m in cover["mutants"]}


@pytest.mark.parametrize("task", TASKS, ids=staged_id)
@pytest.mark.parametrize("name", ["prompt.md", "followup.md"])
def test_prompts_do_not_mention_tests(task, name):
    text = (task / name).read_text(encoding="utf-8")
    assert taskdef.forbidden_words(text, taskdef.allowed_phrases(task)) == []
    assert taskdef.module_path(task) in text or name == "followup.md"


def test_wording_check_whole_words_only():
    assert taskdef.forbidden_words("The latest data were tested and attested.") == []
    assert taskdef.forbidden_words("Write a Test, run pytest, go test-first, TDD.") == [
        "Test", "pytest", "test-first", "TDD"]
    assert taskdef.forbidden_words("Use a Wald test here.", ["Wald test"]) == []


# --- 4.1 runner ---

import runner  # noqa: E402


def test_plan_counterbalanced():
    runs = runner.plan(["t1", "t2"])
    assert len(runs) == 12 and len(runner.sessions(runs)) == 24
    t1 = [r for r in runs if r.task == "t1"]
    assert [(r.rep, r.arm) for r in t1] == [(1, "A"), (1, "B"), (2, "B"), (2, "A"), (3, "A"), (3, "B")]
    assert t1[2].name == "t1-B-r2"


def test_session_command(tmp_path):
    repo, log = tmp_path / "bench-runs" / "t1-A-r1", tmp_path / "bench-logs" / "t1-A-r1" / "session1.jsonl"
    cmd = runner.session_command(repo, "Do the task.", log, cap=1.5)
    argv = cmd.argv
    assert argv[:3] == ["claude", "-p", "Do the task."]
    pairs = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("--")}
    assert pairs["--model"] == runner.MODEL == "claude-haiku-5-5"
    assert pairs["--setting-sources"] == "project"
    assert pairs["--output-format"] == "stream-json" and pairs["--permission-mode"] == "acceptEdits"
    assert pairs["--max-budget-usd"] == "1.5"
    for flag in ("--strict-mcp-config", "--disable-slash-commands", "--verbose", "--no-session-persistence"):
        assert flag in argv
    allowed = argv[argv.index("--allowedTools") + 1:argv.index("--disallowedTools")]
    assert set(allowed) == {"Bash(python:*)", "Bash(pytest:*)", "Bash(git:*)", "Bash(ls:*)", "Bash(cat:*)"}
    denied = argv[argv.index("--disallowedTools") + 1:argv.index("--max-budget-usd")]
    assert {"WebSearch", "WebFetch", "Bash(pip:*)", "Bash(python -m pip:*)"} <= set(denied)
    assert cmd.cwd == repo and cmd.stream == log and log.parent.parent.name == "bench-logs"
    assert cmd.env["PATH"].split(runner.os.pathsep)[0] == str(runner.build.BENCH_PYTHON.parent)
    assert cmd.env["PIP_NO_INDEX"] == "1" and cmd.env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert cmd.env["PYTHONDONTWRITEBYTECODE"] == "1" and cmd.timeout == 30 * 60


def test_context_leak_check(tmp_path):
    root = tmp_path / "proj" / "bench-runs"
    root.mkdir(parents=True)
    assert runner.context_leaks(root) == []
    (tmp_path / "proj" / "CLAUDE.md").write_text("x")
    assert any("CLAUDE.md" in p for p in runner.context_leaks(root))
    (tmp_path / "proj" / "CLAUDE.md").unlink()
    (tmp_path / "AGENTS.md").write_text("x")
    assert any("AGENTS.md" in p for p in runner.context_leaks(root))
    (tmp_path / "AGENTS.md").unlink()
    (root / "t1-A-r1").mkdir()
    (root / "t1-A-r1" / "AGENTS.md").write_text("own project context is fine")
    assert runner.context_leaks(root) == []
    (root / "t1-A-r1" / "session1.jsonl").write_text("{}")
    assert any("session1.jsonl" in p for p in runner.context_leaks(root))
    (root / "t1-A-r1" / "session1.jsonl").unlink()
    hidden = root / "t1-A-r1" / "notes" / "test_task.py"
    hidden.parent.mkdir()
    hidden.write_bytes((BENCH / "tasks/t1-scrna-qc/hidden/test_task.py").read_bytes())
    assert any("test_task.py" in p for p in runner.context_leaks(root))


@pytest.mark.parametrize("field,value", [("skills", ["tdd"]), ("slash_commands", ["review"]),
                                         ("mcp_servers", [{"name": "context7", "status": "connected"}]),
                                         ("plugins", [{"name": "x", "path": "C:/plugins/x"}]),
                                         ("memory_paths", {"auto": "C:/memory"}), ("rules", ["coding-style.md"])])
def test_init_leak_marks_invalid(field, value):
    init = json.loads((FIXTURES / "stream_spike.jsonl").read_text(encoding="utf-8").splitlines()[0])
    init.pop("memory_paths", None)
    assert runner.init_leaks(init) == []
    assert runner.init_leaks({**init, field: value}) != []


def test_spike_init_is_clean_apart_from_memory():
    init = json.loads((FIXTURES / "stream_spike.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert runner.init_leaks(init) == ["memory_paths"]


def test_package_change_invalid_and_restored(monkeypatch):
    before = {"numpy==2.5.4", "pandas==3.1.0"}
    restored = []
    monkeypatch.setattr(runner, "restore_packages", lambda python, extra: restored.append(extra))
    assert runner.package_check(before, before, python="py") == []
    changed = runner.package_check(before, before | {"requests==3.0.0"}, python="py")
    assert changed == ["+requests==3.0.0"] and restored == [{"requests==3.0.0"}]


def test_memory_folder_marks_invalid(tmp_path):
    repo = Path("C:/Tingwei/x_y/bench-runs/t1-A-r1")
    projects = tmp_path / "projects"
    folder = projects / "C--Tingwei-x-y-bench-runs-t1-A-r1" / "memory"
    assert runner.memory_dir(repo, projects) == folder
    assert runner.memory_files(repo, projects) == []
    folder.mkdir(parents=True)
    (folder / "MEMORY.md").write_text("- note")
    assert runner.memory_files(repo, projects) == [folder / "MEMORY.md"]
    meta = {"invalid": []}
    assert not runner.followup_allowed({**meta, "invalid": ["memory: MEMORY.md"]})
    assert runner.followup_allowed(meta)


def test_stage_followup_order(fake_task, tmp_path):
    repo = build.build_run_repo(fake_task, "B", tmp_path / "B", python=sys.executable)
    before = build.git(repo, "rev-parse", "baseline^{tree}").strip()
    (repo / "scripts" / "mod.py").write_text("x = 1\n")          # the agent's untracked work
    staged = runner.stage_followup(repo, fake_task, tmp_path / "log")
    raw = repo / "data/raw/delivery-02/counts.tsv"
    assert raw.is_file() and not build.is_writable(raw)
    assert "`raw/delivery-02/counts.tsv`" in (repo / "data/README.md").read_text(encoding="utf-8")
    assert "data/raw/delivery-02/counts.tsv" in staged["raw_checksums"]
    assert staged["base_tree"] != before
    listing = build.git(repo, "ls-tree", "-r", "--name-only", staged["base_tree"])
    assert "scripts/mod.py" in listing and "data/README.md" in listing
    assert build.git(repo, "status", "--porcelain", "--", "data/README.md").strip().startswith("M")
    assert json.loads((tmp_path / "log" / "followup.json").read_text())["base_tree"] == staged["base_tree"]


# --- 5.1 scorer ---

import score  # noqa: E402

FIXTURE_REPO = Path(r"C:\bench-runs\t1-A-r1")
TOY_CONFTEST = '''\
import importlib.util, os, sys
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def mod():
    path = Path(os.environ["BENCH_MODULE"])
    spec = importlib.util.spec_from_file_location("module_under_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
'''
TOY_REFERENCE = "def clip(values, lo):\n    return [max(v, lo) for v in values]\n"
TOY_FOLLOWUP = TOY_REFERENCE + "\n\ndef cap(values, hi):\n    return [min(v, hi) for v in values]\n"


@pytest.fixture
def toy_task(tmp_path):
    task = tmp_path / "toy"
    (task / "hidden").mkdir(parents=True)
    (task / "hidden/conftest.py").write_text(TOY_CONFTEST)
    (task / "hidden/test_task.py").write_text(
        "def test_shape(mod):\n    assert isinstance(mod.clip([1, 2], 0), list)\n\n\n"
        "def test_floor(mod):\n    assert mod.clip([-2, 3], 0) == [0, 3]\n")
    (task / "hidden/test_followup.py").write_text("def test_cap(mod):\n    assert mod.cap([5, 1], 2) == [2, 1]\n")
    (task / "reference.py").write_text(TOY_REFERENCE)
    (task / "reference_followup.py").write_text(TOY_FOLLOWUP)
    (task / "mutants.json").write_text(json.dumps({
        "first": {"no_floor": [["max(v, lo)", "v"]], "floor_off_by_one": [["max(v, lo)", "max(v, lo + 1)"]]},
        "followup": {"no_cap": [["min(v, hi)", "v"]]}}))
    (task / "traps.json").write_text(json.dumps({
        "module": "scripts/clip.py",
        "first": {"floor": {"tests": ["test_task.py::test_floor"], "mutants": ["no_floor", "floor_off_by_one"]}},
        "followup": {"cap": {"tests": ["test_followup.py::test_cap"], "mutants": ["no_cap"]}}}))
    return task


def toy_repo(tmp_path, module, tests=None):
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "tests/test_smoke.py").write_text("def test_smoke():\n    assert True\n")
    build.git(repo, "init", "-q")
    build.git(repo, "add", "-A")
    build.git(repo, "commit", "-qm", "baseline")
    build.git(repo, "tag", "baseline")
    (repo / "scripts/clip.py").write_text(module)
    for name, text in (tests or {}).items():
        (repo / "tests" / name).write_text(text)
    return repo


IMPORT_CLIP = "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))\n"
AGENT_TESTS = {
    "test_clip.py": IMPORT_CLIP + "from clip import clip\n\n\ndef test_no_negatives():\n    assert clip([-1], 0)[0] >= 0\n",
    "test_private.py": IMPORT_CLIP + "from clip import _helper\n\n\ndef test_helper():\n    assert _helper(1) == 1\n",
}


def stream(name):
    return FIXTURES / name


def test_stream_test_first_exposed_saw_red():
    p = score.parse_stream(stream("stream_test_first.jsonl"), FIXTURE_REPO, "scripts/qc_filter.py")
    assert p["exposed"] and p["cue_files"] == ["docs/principles.md"]
    assert p["test_first"] and p["saw_red"] is True
    assert p["completed"] and p["cost_usd"] == 0.1234 and p["out_of_repo"] == []


def test_stream_implementation_first_out_of_repo():
    p = score.parse_stream(stream("stream_impl_first.jsonl"), FIXTURE_REPO, "scripts/qc_filter.py")
    assert not p["exposed"] and p["cue_files"] == []
    assert not p["test_first"] and p["saw_red"] is False
    flagged = " ".join(p["out_of_repo"])
    assert "../nerv-tdd-run/scripts/qc.py" in flagged and "elsewhere" in flagged
    assert "config/samples.tsv" not in flagged
    assert p["completed"] and p["cost_usd"] == 0.0811


def test_stream_unparseable_red_is_unknown():
    p = score.parse_stream(stream("stream_unparseable.jsonl"), FIXTURE_REPO, "scripts/qc_filter.py")
    assert p["exposed"] and p["cue_files"] == ["tests/README.md"]
    assert p["test_first"] and p["saw_red"] == "unknown"
    assert not p["completed"]


def test_stream_limit_has_unknown_cost():
    p = score.parse_stream(stream("stream_limit.jsonl"), FIXTURE_REPO, "scripts/qc_filter.py")
    assert p["cost_usd"] is None and not p["completed"]


def test_spike_stream_parses():
    repo = Path(r"C:\Tingwei\test_claude\personal_proj\nerv_all_runs\bench-spike")
    p = score.parse_stream(stream("stream_spike.jsonl"), repo, "scripts/x.py")
    assert p["cost_usd"] == pytest.approx(0.00330288)
    assert any(".claude" in path for path in p["out_of_repo"])


def test_silent_wrong_versus_crash(toy_task, tmp_path):
    wrong = tmp_path / "wrong.py"
    wrong.write_text("def clip(values, lo):\n    return list(values)\n")
    crash = tmp_path / "crash.py"
    crash.write_text("def clip(values, lo):\n    raise ValueError('no')\n")
    w = score.outcome(toy_task, "first", score.hidden_results(toy_task, "first", wrong, sys.executable))
    c = score.outcome(toy_task, "first", score.hidden_results(toy_task, "first", crash, sys.executable))
    assert w["silent_wrong"] and w["hidden_pass_rate"] == 0.5 and w["traps_passed"] == 0
    assert not c["silent_wrong"] and c["hidden_pass_rate"] == 0
    none = score.hidden_results(toy_task, "first", tmp_path / "none.py", sys.executable)
    missing = score.outcome(toy_task, "first", none)
    assert missing["hidden_pass_rate"] == 0 and not missing["silent_wrong"]


def test_regression_scored_separately(toy_task, tmp_path):
    module = tmp_path / "followup.py"
    module.write_text("def clip(values, lo):\n    return list(values)\n\n\ndef cap(values, hi):\n"
                      "    return [min(v, hi) for v in values]\n")
    o = score.outcome(toy_task, "followup", score.hidden_results(toy_task, "followup", module, sys.executable))
    assert o["hidden_pass_rate"] == 1.0 and o["regression_free"] is False


def test_mutant_kill_rate(toy_task, tmp_path):
    repo = toy_repo(tmp_path, TOY_REFERENCE, AGENT_TESTS)
    rate, note = score.mutant_kills(toy_task, "first", repo, sys.executable)
    assert rate == 0.5 and "1 eligible" in note
    assert build.git(repo, "status", "--porcelain").count("??") == 3


def test_mutant_kill_rate_without_tests(toy_task, tmp_path):
    repo = toy_repo(tmp_path, TOY_REFERENCE)
    assert score.mutant_kills(toy_task, "first", repo, sys.executable) == (0.0, "no eligible tests")


def test_untracked_files_counted_in_ratio(tmp_path):
    repo = toy_repo(tmp_path, "a = 1\nb = 2\n", {"test_a.py": "def test_a():\n    assert True\n\n# end\n"})
    assert score.diff_lines(repo, "baseline") == (4, 2)
    assert build.git(repo, "status", "--porcelain").count("??") == 2


def test_score_session_row(toy_task, tmp_path):
    repo = toy_repo(tmp_path, TOY_REFERENCE, AGENT_TESTS)
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "session1.jsonl").write_bytes(stream("stream_limit.jsonl").read_bytes())
    meta = {"run": "toy-A-r1", "task": "toy", "arm": "A", "rep": 1, "session": 1, "limit": "time", "invalid": [],
            "model": "claude-haiku-5-5", "raw_before": {"data/raw/d/x": "1"}, "raw_after": {"data/raw/d/x": "2"}}
    (logs / "session1.meta.json").write_text(json.dumps(meta))
    row = score.score_session(toy_task, repo, logs, 1, python=sys.executable)
    assert row["completed"] is False and row["limit"] == "time" and row["cost_usd"] is None
    assert row["hidden_pass_rate"] == 1.0 and row["hard_rule_violation"] is True
    assert row["mutant_kill_rate"] == 0.5 and row["test_lines"] > 0
    assert build.git(repo, "status", "--porcelain").count("??") == 3
    out = tmp_path / "runs.csv"
    score.append_row(out, row)
    score.append_row(out, score.not_run(runner.Run("toy", "A", 1), 2, "blocked"))
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3 and lines[0].startswith("run,")


# --- 6.1 summary and decision rule ---

import itertools  # noqa: E402

import summarize  # noqa: E402

TASK_NAMES = ["t1", "t2", "t3"]


def synthetic_rows(test_first, exposed=None, passed=None, regress=None, silent=None):
    """Rows for 3 tasks x 2 arms x 3 reps. Each argument maps arm -> {task: list of 3 values} or a value."""
    def pick(spec, arm, task, rep, default):
        if spec is None:
            return default
        value = spec[arm]
        value = value[task] if isinstance(value, dict) else value
        return value[rep] if isinstance(value, list) else value
    rows = []
    for task, arm, rep in itertools.product(TASK_NAMES, "AB", range(3)):
        base = {"run": f"{task}-{arm}-r{rep + 1}", "task": task, "arm": arm, "rep": rep + 1, "pilot": False,
                "invalid": [], "cost_usd": 0.1, "out_of_repo": []}
        hidden = pick(passed, arm, task, rep, 1.0)
        rows.append({**base, "session": 1, "test_first": pick(test_first, arm, task, rep, False),
                     "exposed": pick(exposed, arm, task, rep, True), "hidden_pass_rate": hidden,
                     "silent_wrong": pick(silent, arm, task, rep, False)})
        rows.append({**base, "session": 2, "test_first": False, "exposed": False, "hidden_pass_rate": 1.0,
                     "regression_free": pick(regress, arm, task, rep, True), "silent_wrong": False})
    return rows


def tf(a_per_task, b_per_task):
    """Test-first counts per task (0-3) -> per-rep booleans."""
    return {arm: {t: [i < n for i in range(3)] for t, n in zip(TASK_NAMES, counts)}
            for arm, counts in (("A", a_per_task), ("B", b_per_task))}


def verdict(rows):
    return summarize.verdict(rows)


def test_row1_cues_not_reached():
    rows = synthetic_rows(tf([3, 3, 3], [0, 0, 0]), exposed={"A": [True, False, False], "B": False})
    assert verdict(rows)["row"] == 1 and verdict(rows)["verdict"].startswith("CUES NOT REACHED")


def test_row2_both_high_drop():
    assert verdict(synthetic_rows(tf([3, 2, 2], [2, 2, 3])))["row"] == 2


def test_row3_keep():
    rows = synthetic_rows(tf([3, 3, 3], [1, 1, 1]), passed={"A": 1.0, "B": 0.7})
    v = verdict(rows)
    assert v["row"] == 3 and v["verdict"] == "KEEP"


def test_row4_drop_when_outcome_same():
    assert verdict(synthetic_rows(tf([3, 3, 3], [1, 1, 1])))["row"] == 4


def test_row5_strengthen():
    passed = {"A": {t: [1.0, 0.5, 0.5] for t in TASK_NAMES}, "B": {t: [1.0, 0.5, 0.5] for t in TASK_NAMES}}
    v = verdict(synthetic_rows(tf([1, 1, 1], [1, 0, 1]), passed=passed))
    assert v["row"] == 5 and v["verdict"].startswith("STRENGTHEN")


def test_row6_both_low_drop():
    assert verdict(synthetic_rows(tf([1, 0, 1], [1, 1, 0])))["row"] == 6


def test_row7_b_greater_inconclusive():
    assert verdict(synthetic_rows(tf([0, 1, 0], [3, 3, 2])))["row"] == 7


def test_small_difference_is_no_difference():
    rows = synthetic_rows(tf([3, 2, 3], [2, 2, 2]))
    assert summarize.yes_no_direction(summarize.first_sessions(rows), "test_first") == 0


def test_mixed_direction_is_no_difference():
    passed = {"A": {"t1": 1.0, "t2": 0.2, "t3": 1.0}, "B": {"t1": 0.5, "t2": 0.6, "t3": 0.5}}
    rows = summarize.first_sessions(synthetic_rows(tf([0, 0, 0], [0, 0, 0]), passed=passed))
    assert summarize.rate_direction(rows, "hidden_pass_rate") == 0


def test_disagreeing_outcomes_are_no_difference():
    rows = synthetic_rows(tf([3, 3, 3], [1, 1, 1]), passed={"A": 1.0, "B": 0.7},
                          silent={"A": True, "B": False})
    assert summarize.outcome_direction(rows) == 0
    assert verdict(rows)["row"] == 4


@pytest.mark.parametrize("exposed,a_high,b_high,a_vs_b,outcome,tf_better", list(itertools.product(
    [True, False], [True, False], [True, False], [1, 0, -1], [1, 0, -1], [True, False])))
def test_every_case_has_one_row(exposed, a_high, b_high, a_vs_b, outcome, tf_better):
    flags = summarize.Flags(exposed, a_high, b_high, a_vs_b, outcome, tf_better)
    matching = [number for number, rule, _ in summarize.RULES if rule(flags)]
    row, _ = summarize.decide(flags)
    assert matching and row == matching[0]
    assert summarize.RULES[-1][0] == 7 and summarize.RULES[-1][1](flags)
    if not exposed:
        assert row == 1


def test_summary_states_rule_and_row(tmp_path):
    rows = synthetic_rows(tf([3, 3, 3], [1, 1, 1]), passed={"A": 1.0, "B": 0.7})
    rows[0]["out_of_repo"] = ["../other"]
    rows.append({"run": "t1-B-pilot", "task": "t1", "arm": "B", "rep": "pilot", "session": 1, "pilot": True,
                 "invalid": [], "cost_usd": 0.4})
    csv_path = tmp_path / "runs.csv"
    for row in rows:
        score.append_row(csv_path, row)
    text = summarize.write_summary(csv_path, tmp_path / "summary.md")
    assert "## Decision rule" in text and "Row applied: 3" in text and "KEEP" in text
    assert "0.10" in text and "25%" in text and "6 of 9" in text
    assert "Without flagged sessions" in text and "t1-A-r1" in text
    assert "pass^3" in text and (tmp_path / "summary.md").read_text(encoding="utf-8") == text
