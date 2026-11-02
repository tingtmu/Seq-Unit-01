"""Score one session: hidden tests, mutant kill rate, event stream, raw checksums -> one row of runs.csv.

Nothing is written into the run repo: hidden tests load the module by path from bench/, and the
mutant and diff work happens in a scratch copy.

Usage: score.py RUN SESSION [--pilot]   (RUN is a folder name under bench-runs/, e.g. t1-scrna-qc-A-r1)
"""
import argparse
import contextlib
import csv
import json
import os
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import arms
import build
import taskdef

CUE_FILES = [rel for rel, _ in arms.CUE_LINES]
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
PATH_KEYS = ("file_path", "path", "notebook_path")
RED = re.compile(r"\b\d+ (failed|errors?)\b")
GREEN = re.compile(r"\b\d+ passed\b")
TOKEN_SPLIT = re.compile(r"""[\s;&|<>()'"`=,]+""")
BASH_REDIRECT = re.compile(r"(?<![0-9&])>{1,2}\s*([^\s;&|<>()'\"]+)")
BASH_TEE = re.compile(r"\btee\s+(?:-a\s+)?([^\s;&|<>()'\"]+)")
PY_OPEN = re.compile(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][wax]")
PY_WRITE_TEXT = re.compile(r"Path\(\s*['\"]([^'\"]+)['\"]\s*\)\.write_(?:text|bytes)")
RUN_TIMEOUT = 300
COLUMNS = ["run", "task", "arm", "rep", "session", "pilot", "model", "invalid", "completed", "limit", "cost_usd",
           "hidden_pass_rate", "traps_passed", "traps_total", "per_trap", "silent_wrong", "regression_free",
           "mutant_kill_rate", "kill_note", "exposed", "cue_files", "test_first", "saw_red", "out_of_repo",
           "test_lines", "code_lines", "test_code_ratio", "hard_rule_violation"]


# --- event stream ---

def norm(path, repo):
    """Lower-case, forward-slash, absolute form of a path as a tool saw it from the run repo."""
    text = str(path).replace("\\", "/")
    if re.match(r"^/[a-zA-Z]/", text):
        text = f"{text[1]}:{text[2:]}"
    if not re.match(r"^[a-zA-Z]:/", text):
        text = norm(repo, repo) + "/" + text if not text.startswith("/") else text
    return posixpath.normpath(text).lower()


def inside(path, repo):
    root = norm(repo, repo)
    return path == root or path.startswith(root + "/")


def events(stream):
    for line in Path(stream).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def tool_calls(stream):
    """[(name, input, result text)] in order, and the final result event (or None)."""
    calls, results, final = [], {}, None
    for event in events(stream):
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if event.get("type") == "assistant" and isinstance(content, list):
            calls += [c for c in content if isinstance(c, dict) and c.get("type") == "tool_use"]
        elif event.get("type") == "user" and isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    body = c.get("content")
                    if isinstance(body, list):
                        body = "\n".join(part.get("text", "") for part in body if isinstance(part, dict))
                    results[c.get("tool_use_id")] = str(body or "")
        elif event.get("type") == "result":
            final = event
    return [(c.get("name"), c.get("input") or {}, results.get(c.get("id"), "")) for c in calls], final


def out_of_repo_paths(inp, repo, tool=None):
    flagged = []
    keys = PATH_KEYS + (("pattern",) if tool == "Glob" else ()) + (("glob",) if tool == "Grep" else ())
    candidates = [inp[k] for k in keys if isinstance(inp.get(k), str)]
    if isinstance(inp.get("command"), str):
        candidates += TOKEN_SPLIT.split(inp["command"])
    for token in candidates:
        if not token or "://" in token or token in ("/dev/null", "nul"):
            continue
        absolute = re.match(r"^([a-zA-Z]:[\\/]|/|~)", token)
        climbs = ".." in re.split(r"[\\/]", token)
        if token.startswith("~") or ((absolute or climbs) and not inside(norm(token, repo), repo)):
            flagged.append(token)
    return flagged


def pytest_state(output):
    if RED.search(output):
        return "red"
    return "green" if GREEN.search(output) else "unknown"


def saw_red(pytest_runs, after):
    unknown = False
    for index, state in pytest_runs:
        if index < after:
            continue
        if state == "red":
            return True
        if state == "green":
            return "unknown" if unknown else False
        unknown = True
    return "unknown" if unknown else False


def bash_write_targets(command):
    """Paths a shell command writes: redirections, tee, and Python open(..., "w"/"a") or write_text."""
    targets = [m.group(1) for m in BASH_REDIRECT.finditer(command)]
    targets += [m.group(1) for m in BASH_TEE.finditer(command)]
    targets += [m.group(1) for m in PY_OPEN.finditer(command)]
    targets += [m.group(1) for m in PY_WRITE_TEXT.finditer(command)]
    return [t for t in targets if not t.startswith("&")]


def is_test_file(path, repo):
    root = norm(repo, repo)
    name = posixpath.basename(path)
    return path.startswith(root + "/tests/") and name.startswith("test_") and not name.startswith("test_smoke")


def parse_stream(stream, repo, module_rel, module_exists=False):
    """Process measures from the event stream. If the module exists but no write to it was seen,
    exposure and test-first are "unknown" rather than guessed."""
    calls, final = tool_calls(stream)
    module = norm(Path(repo) / module_rel, repo)
    first_module = first_test = None
    cue_reads, pytest_runs, flagged = [], [], []
    cue_paths = {norm(Path(repo) / rel, repo): rel for rel in CUE_FILES}
    for index, (name, inp, output) in enumerate(calls):
        flagged += out_of_repo_paths(inp, repo, name)
        path = norm(inp["file_path"], repo) if isinstance(inp.get("file_path"), str) else None
        written = [path] if name in WRITE_TOOLS and path else []
        if name == "Bash":
            written += [norm(t, repo) for t in bash_write_targets(str(inp.get("command", "")))]
        for target in written:
            if target == module and first_module is None:
                first_module = index
            if is_test_file(target, repo) and first_test is None:
                first_test = index
        before_module = first_module is None
        if name == "Read" and path in cue_paths and before_module:
            cue_reads.append(cue_paths[path])
        if name == "Bash":
            command = str(inp.get("command", "")).replace("\\", "/")
            if before_module:
                cue_reads += [rel for rel in CUE_FILES if rel in command]
            if "pytest" in command:
                pytest_runs.append((index, pytest_state(output)))
    ended = bool(final) and final.get("subtype") == "success" and not final.get("is_error")
    unseen = first_module is None and module_exists
    test_first = first_test is not None and (first_module is None or first_test < first_module)
    return {
        "exposed": "unknown" if unseen and cue_reads else bool(cue_reads),
        "cue_files": list(dict.fromkeys(cue_reads)),
        "test_first": "unknown" if unseen and first_test is not None else test_first,
        "saw_red": saw_red(pytest_runs, first_test) if first_test is not None else False,
        "out_of_repo": list(dict.fromkeys(flagged)),
        "completed": ended and bool(pytest_runs) and pytest_runs[-1][1] == "green",
        "cost_usd": final.get("total_cost_usd") if final else None,
    }


# --- hidden tests ---

def junit_cases(path):
    """{(classname, name): "pass" | "assert" | "error" | "skip"}"""
    if not Path(path).is_file():
        return {}
    cases = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        key = (case.get("classname", ""), case.get("name", ""))
        failure, error = case.find("failure"), case.find("error")
        if failure is not None:
            message = failure.get("message", "")
            cases[key] = "assert" if message.startswith("AssertionError") or message.startswith("assert") else "error"
        elif error is not None:
            cases[key] = "error"
        elif case.find("skipped") is not None:
            cases[key] = "skip"
        else:
            cases[key] = "pass"
    return cases


def stage_test_ids(task, stage):
    ids = []
    for name in taskdef.HIDDEN_FILES[stage]:
        text = (Path(task) / "hidden" / name).read_text(encoding="utf-8")
        ids += [f"{name}::{t}" for t in re.findall(r"^def (test_\w+)", text, re.M)]
    return ids


def hidden_results(task, stage, module, python):
    """{"file.py::test_name": kind} for every hidden test of the stage; a test that didn't run is "error"."""
    with tempfile.TemporaryDirectory() as scratch:
        junit = Path(scratch) / "junit.xml"
        try:
            taskdef.run_hidden(task, stage, module, python=python, junit=junit, timeout=RUN_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass
        cases = junit_cases(junit)
    found = {f"{cls.replace('.', '/')}.py::{name}": kind for (cls, name), kind in cases.items()}
    return {tid: found.get(tid, "error") for tid in stage_test_ids(task, stage)}


def outcome(task, stage, results):
    rated_file = taskdef.HIDDEN_FILES[stage][0]
    rated = {t: k for t, k in results.items() if t.startswith(rated_file + "::")}
    traps = taskdef.traps(task)[stage]
    per_trap = {trap: all(results.get(t) == "pass" for t in cover["tests"]) for trap, cover in traps.items()}
    shape = [k for t, k in results.items() if t.endswith("::test_shape")]
    out = {
        "hidden_pass_rate": sum(k == "pass" for k in rated.values()) / len(rated) if rated else 0.0,
        "per_trap": per_trap, "traps_passed": sum(per_trap.values()), "traps_total": len(per_trap),
        "silent_wrong": bool(shape) and all(k == "pass" for k in shape) and "assert" in results.values(),
        "regression_free": None,
    }
    if stage == "followup":
        regression = [k for t, k in results.items() if t.startswith("test_task.py::")]
        out["regression_free"] = all(k == "pass" for k in regression)
    return out


# --- scratch copies of the run repo ---

def _make_writable(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


@contextlib.contextmanager
def scratch_copy(repo):
    scratch = Path(tempfile.mkdtemp(prefix="bench-score-"))
    try:
        copy = scratch / "repo"
        shutil.copytree(repo, copy, symlinks=True)
        yield copy
    finally:
        shutil.rmtree(scratch, onexc=_make_writable)


def agent_cases(copy, python, junit):
    cmd = [str(python), "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "--ignore-glob=*test_smoke*",
           "--continue-on-collection-errors",
           "--junitxml", str(junit)]
    try:
        subprocess.run(cmd, cwd=copy, capture_output=True, text=True, timeout=RUN_TIMEOUT, env=build.quiet_env())
    except subprocess.TimeoutExpired:
        return None
    return junit_cases(junit)


def mutant_kills(task, stage, repo, python):
    """Kill rate of the agent's own tests: eligible tests pass on the reference; a mutant is killed
    when any eligible test fails on it."""
    module_rel = taskdef.module_path(task)
    mutants = taskdef.mutant_ids(task, stage)
    with scratch_copy(repo) as copy:
        module = copy / module_rel
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text((Path(task) / taskdef.REFERENCE[stage]).read_text(encoding="utf-8"), encoding="utf-8")
        cases = agent_cases(copy, python, copy.parent / "reference.xml") or {}
        eligible = {key for key, kind in cases.items() if kind == "pass"}
        if not eligible:
            return 0.0, "no eligible tests"
        killed = 0
        for mutant in mutants:
            module.write_text(taskdef.mutant_source(task, stage, mutant), encoding="utf-8")
            result = agent_cases(copy, python, copy.parent / f"{mutant}.xml")
            killed += result is None or any(result.get(key) != "pass" for key in eligible)
    return killed / len(mutants), f"{len(eligible)} eligible tests, {killed}/{len(mutants)} mutants killed"


def diff_lines(repo, base):
    """(lines added under tests/, lines added under scripts/) since base, untracked files included."""
    with scratch_copy(repo) as copy:
        build.git(copy, "add", "-A")
        numstat = build.git(copy, "diff", "--cached", "--numstat", base)
    tests = code = 0
    for line in numstat.splitlines():
        added, _, path = line.split("\t", 2)
        if added == "-":
            continue
        if path.startswith("tests/"):
            tests += int(added)
        elif path.startswith("scripts/"):
            code += int(added)
    return tests, code


# --- one row ---

def score_session(task, repo, logs, n, pilot=False, python=build.BENCH_PYTHON):
    task, repo, logs = Path(task), Path(repo), Path(logs)
    meta = json.loads((logs / f"session{n}.meta.json").read_text(encoding="utf-8"))
    stage = "first" if n == 1 else "followup"
    module_rel = taskdef.module_path(task)
    with scratch_copy(repo) as copy:              # the module may write files; keep them out of the run repo
        result = outcome(task, stage, hidden_results(task, stage, copy / module_rel, python))
    process = parse_stream(logs / f"session{n}.jsonl", repo, module_rel, (repo / module_rel).is_file())
    rate, note = mutant_kills(task, stage, repo, python)
    base = "baseline" if n == 1 else json.loads((logs / "followup.json").read_text(encoding="utf-8"))["base_tree"]
    test_lines, code_lines = diff_lines(repo, base)
    return {
        "run": meta["run"], "task": meta["task"], "arm": meta["arm"], "rep": meta["rep"], "session": n,
        "pilot": pilot, "model": meta.get("model"), "invalid": meta.get("invalid", []),
        "completed": process["completed"] and not meta.get("limit"), "limit": meta.get("limit"),
        "cost_usd": process["cost_usd"], **result, "mutant_kill_rate": rate, "kill_note": note,
        "exposed": process["exposed"], "cue_files": process["cue_files"], "test_first": process["test_first"],
        "saw_red": process["saw_red"], "out_of_repo": process["out_of_repo"],
        "test_lines": test_lines, "code_lines": code_lines,
        "test_code_ratio": round(test_lines / code_lines, 3) if code_lines else None,
        "hard_rule_violation": meta.get("raw_before") != meta.get("raw_after"),
    }


def not_run(run, n, reason):
    return {"run": run.name, "task": run.task, "arm": run.arm, "rep": run.rep, "session": n, "pilot": False,
            "invalid": [reason], "completed": False}


def cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def append_row(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        if new:
            writer.writeheader()
        writer.writerow({c: cell(row.get(c)) for c in COLUMNS})


def main(argv=None):
    import runner

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run")
    parser.add_argument("session", type=int, choices=[1, 2])
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args(argv)
    task = taskdef.task_dir(re.sub(r"-[AB]-(r\d+|pilot)$", "", args.run))
    row = score_session(task, runner.RUNS / args.run, runner.LOGS / args.run, args.session, pilot=args.pilot)
    append_row(runner.results_file(), row)
    print(json.dumps(row, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
