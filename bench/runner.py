"""Plan and run the benchmark sessions: headless Claude Code on Haiku, one run repo per run.

Usage:
  runner.py plan                       print the planned runs and sessions; starts nothing
  runner.py pilot [--cap USD]          one arm B session per task (not counted)
  runner.py grid --cap USD [--tasks T ...]
                                       every planned run: build, session 1, score, stage the
                                       follow-up, session 2, score
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import arms
import build
import taskdef

MODEL = "claude-haiku-5-5"
REPS = 3
TIME_LIMIT = 30 * 60
PILOT_CAP = 5.0
RUNS = build.RUNS_ROOT / "bench-runs"
LOGS = build.RUNS_ROOT / "bench-logs"
PROJECTS = Path.home() / ".claude" / "projects"
PINNED = build.BENCH / "bench-venv.txt"
ALLOWED = ["Bash(python:*)", "Bash(pytest:*)", "Bash(git:*)", "Bash(ls:*)", "Bash(cat:*)"]
DENIED = ["WebSearch", "WebFetch", "Bash(pip:*)", "Bash(python -m pip:*)"]
CONTEXT_FILES = ("CLAUDE.md", "AGENTS.md")
INIT_LISTS = ("skills", "slash_commands", "mcp_servers", "rules")


@dataclass(frozen=True)
class Run:
    task: str
    arm: str
    rep: object

    @property
    def name(self):
        return f"{self.task}-{self.arm}-{'r' if isinstance(self.rep, int) else ''}{self.rep}"


@dataclass(frozen=True)
class Command:
    argv: list
    env: dict
    cwd: Path
    stream: Path
    timeout: int


def plan(tasks, reps=REPS):
    """Each rep holds one run of each arm; the arm that goes first alternates (A B | B A | A B)."""
    runs = []
    for task in tasks:
        for rep in range(1, reps + 1):
            order = arms.ARMS if rep % 2 else arms.ARMS[::-1]
            runs += [Run(task, arm, rep) for arm in order]
    return runs


def sessions(runs):
    return [(run, n) for run in runs for n in (1, 2)]


def session_command(repo, prompt, stream, cap):
    argv = ["claude", "-p", prompt, "--model", MODEL, "--setting-sources", "project",
            "--strict-mcp-config", "--disable-slash-commands", "--output-format", "stream-json", "--verbose",
            "--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED, "--disallowedTools", *DENIED,
            "--max-budget-usd", f"{cap:g}", "--no-session-persistence"]
    env = {**os.environ, "PATH": os.pathsep.join([str(build.BENCH_PYTHON.parent), os.environ.get("PATH", "")]),
           "PYTHONDONTWRITEBYTECODE": "1", "PIP_NO_INDEX": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
    for name in ("VIRTUAL_ENV", "PYTHONPATH", "PYTEST_ADDOPTS"):
        env.pop(name, None)
    return Command(argv, env, Path(repo), Path(stream), TIME_LIMIT)


def hidden_hashes():
    return {build.sha256(p) for p in taskdef.TASKS.rglob("*") if p.is_file() and p.stat().st_size}


def context_leaks(run_root):
    """Problems that would let a session see context it shouldn't: parent context files, hidden
    material or session streams anywhere under the run root."""
    run_root = Path(run_root).resolve()
    leaks = [str(parent / name) for parent in [run_root, *run_root.parents] for name in CONTEXT_FILES
             if (parent / name).is_file()]
    hidden = hidden_hashes()
    for path in run_root.rglob("*"):
        if not path.is_file():
            continue
        if re.fullmatch(r"session.*\.jsonl", path.name) or (path.stat().st_size and build.sha256(path) in hidden):
            leaks.append(str(path))
    return leaks


def init_leaks(init):
    """Names of init-event fields that show context beyond the run repo's own AGENTS.md."""
    leaks = [field for field in INIT_LISTS if init.get(field)]
    if any(p.get("path") != "builtin" for p in init.get("plugins") or []):
        leaks.append("plugins")
    if init.get("memory_paths"):
        leaks.append("memory_paths")
    return leaks


def first_init(stream):
    for line in Path(stream).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            return event
    return None


def freeze(python):
    out = subprocess.run([str(python), "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
    return {line.strip() for line in out.stdout.splitlines() if line.strip()}


def restore_packages(python, extra):
    """Put the session environment back to the pinned list."""
    names = sorted({re.split(r"[=<>@ ]", line)[0] for line in extra})
    if names:
        subprocess.run([str(python), "-m", "pip", "uninstall", "-y", *names], check=True, capture_output=True)
    subprocess.run([str(python), "-m", "pip", "install", "-q", "-r", str(PINNED)], check=True, capture_output=True)


def package_check(before, after, python):
    changed = sorted(f"+{p}" for p in after - before) + sorted(f"-{p}" for p in before - after)
    if changed:
        restore_packages(python, after - before)
    return changed


def memory_dir(repo, projects=PROJECTS):
    return Path(projects) / re.sub(r"[^A-Za-z0-9]", "-", str(Path(repo))) / "memory"


def memory_files(repo, projects=PROJECTS):
    folder = memory_dir(repo, projects)
    return sorted(p for p in folder.rglob("*") if p.is_file()) if folder.is_dir() else []


def followup_allowed(meta):
    return not any(reason.startswith("memory") for reason in meta["invalid"])


def raw_checksums(repo):
    raw = Path(repo) / "data" / "raw"
    return {p.relative_to(repo).as_posix(): build.sha256(p) for p in sorted(raw.rglob("*")) if p.is_file()}


def tree_of_worktree(repo, scratch):
    """Tree hash of the working tree with every file staged, via a temporary index outside the repo.
    The repo's own index, branch, and status are untouched."""
    index = Path(scratch) / "index"
    shutil.copyfile(Path(repo) / ".git" / "index", index)
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    subprocess.run(["git", "add", "-A"], cwd=repo, env=env, check=True, capture_output=True)
    return subprocess.run(["git", "write-tree"], cwd=repo, env=env, check=True, capture_output=True,
                          text=True).stdout.strip()


def stage_followup(repo, task_dir, log_dir, python=None):
    """Add the follow-up inputs, record the session-2 diff base, then take checksums and packages."""
    answers = build.read_answers(task_dir)
    build.place_inputs(Path(repo), build.generate_into(task_dir, "followup"),
                       "sequencing core (synthetic, bench), second delivery", answers["date"])
    with tempfile.TemporaryDirectory() as scratch:
        base_tree = tree_of_worktree(repo, scratch)
    staged = {"base_tree": base_tree, "raw_checksums": raw_checksums(repo)}
    if python:
        staged["packages"] = sorted(freeze(python))
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    (Path(log_dir) / "followup.json").write_text(json.dumps(staged, indent=1), encoding="utf-8")
    return staged


def kill_tree(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def result_event(stream):
    result = None
    for line in Path(stream).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event
    return result


def run_session(run, n, prompt, cap, repo, log_dir, python=build.BENCH_PYTHON):
    """One headless session; writes sessionN.jsonl and sessionN.meta.json under log_dir."""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    cmd = session_command(repo, prompt, log_dir / f"session{n}.jsonl", cap)
    meta = {"run": run.name, "task": run.task, "arm": run.arm, "rep": run.rep, "session": n, "cap": cap,
            "started": datetime.datetime.now().isoformat(timespec="seconds"), "invalid": [], "limit": None,
            "raw_before": raw_checksums(repo)}
    packages = freeze(python)
    with open(cmd.stream, "wb") as out, open(log_dir / f"session{n}.stderr.txt", "wb") as err:
        proc = subprocess.Popen(cmd.argv, cwd=cmd.cwd, env=cmd.env, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        try:
            meta["returncode"] = proc.wait(timeout=cmd.timeout)
        except subprocess.TimeoutExpired:
            kill_tree(proc)
            meta["returncode"], meta["limit"] = proc.wait(), "time"
    meta["ended"] = datetime.datetime.now().isoformat(timespec="seconds")
    meta["raw_after"] = raw_checksums(repo)
    result = result_event(cmd.stream)
    if result and "budget" in str(result.get("subtype", "")):
        meta["limit"] = "cost"
    init = first_init(cmd.stream)
    meta["model"] = init.get("model") if init else None
    leaks = init_leaks(init) if init else ["no init event"]
    meta["invalid"] += [f"init: {leak}" for leak in leaks]
    meta["packages_changed"] = package_check(packages, freeze(python), python)
    meta["invalid"] += [f"package: {p}" for p in meta["packages_changed"]]
    meta["invalid"] += [f"memory: {p.name}" for p in memory_files(repo)]
    (log_dir / f"session{n}.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


def check_isolation():
    RUNS.mkdir(parents=True, exist_ok=True)
    leaks = context_leaks(RUNS)
    if leaks:
        raise build.BenchError("context leak under the run root:\n  " + "\n  ".join(leaks))


def prompt_text(task_dir, n):
    return (Path(task_dir) / ("prompt.md" if n == 1 else "followup.md")).read_text(encoding="utf-8")


def do_run(run, cap, results, pilot=False):
    import score  # the scorer depends on the runner's file layout, so import it late

    task = taskdef.task_dir(run.task)
    repo, logs = RUNS / run.name, LOGS / run.name
    check_isolation()
    build.build_run_repo(task, run.arm, repo)
    meta = run_session(run, 1, prompt_text(task, 1), cap, repo, logs)
    score.append_row(results, score.score_session(task, repo, logs, 1, pilot=pilot))
    if pilot:
        return
    if not followup_allowed(meta):
        score.append_row(results, score.not_run(run, 2, "follow-up blocked: memory written in session 1"))
        return
    stage_followup(repo, task, logs, python=build.BENCH_PYTHON)
    run_session(run, 2, prompt_text(task, 2), cap, repo, logs)
    score.append_row(results, score.score_session(task, repo, logs, 2))


def results_file(logs=None):
    """The runs.csv of this benchmark, fixed at its first pilot or grid step, so a grid restarted
    on a later date keeps writing to the same file."""
    marker = Path(logs or LOGS) / "results-path.txt"
    if marker.is_file():
        return Path(marker.read_text(encoding="utf-8").strip())
    path = build.BENCH / "results" / datetime.date.today().isoformat() / "runs.csv"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(path), encoding="utf-8")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["plan", "pilot", "grid"])
    parser.add_argument("--cap", type=float, help="cost cap per session in USD (required for grid)")
    parser.add_argument("--tasks", nargs="*", help="task names (default: all)")
    args = parser.parse_args(argv)
    tasks = args.tasks or [t.name for t in taskdef.task_dirs()]
    if args.step == "plan":
        runs = plan(tasks)
        for run, n in sessions(runs):
            print(f"{run.name}\tsession {n}")
        print(f"{len(runs)} runs, {len(sessions(runs))} sessions")
        return 0
    if args.step == "grid" and args.cap is None:
        parser.error("grid needs --cap (three times the highest pilot cost)")
    results = results_file()
    try:
        if args.step == "pilot":
            for task in tasks:
                do_run(Run(task, "B", "pilot"), args.cap or PILOT_CAP, results, pilot=True)
        else:
            for run in plan(tasks):
                if (LOGS / run.name / "session1.meta.json").exists():
                    print(f"skip {run.name}: already ran (rerun only with a note in the results)")
                    continue
                do_run(run, args.cap, results)
    except build.BenchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
