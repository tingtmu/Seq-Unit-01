"""Summarize runs.csv: per-task tables, the decision rule, and a verdict -> summary.md.

Usage: summarize.py [RUNS_CSV]   (default: the newest bench/results/<date>/runs.csv)
"""
import argparse
import csv
import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"
RATE_THRESHOLD = 0.10
COST_THRESHOLD = 0.25
HIGH_SHARE = 2 / 3                       # 6 of 9 runs per arm
EXPOSED_SHARE = 0.5
MIN_GROUP = 3


@dataclass(frozen=True)
class Flags:
    exposed: bool
    a_high: bool
    b_high: bool
    a_vs_b: int        # +1 A > B, -1 B > A, 0 no difference (test-first, yes/no threshold)
    outcome: int       # +1 A better, -1 A worse, 0 no difference
    tf_better: bool    # test-first runs did better (pooled across arms, observational)


RULES = [
    (1, lambda f: not f.exposed, "CUES NOT REACHED (the links in AGENTS.md aren't followed; next step is to "
                                 "move one line into AGENTS.md or drop the cues)"),
    (2, lambda f: f.a_high and f.b_high, "DROP (default behavior)"),
    (3, lambda f: f.a_vs_b == 1 and f.outcome == 1, "KEEP"),
    (4, lambda f: f.a_vs_b == 1 and f.outcome <= 0, "DROP (cues don't pay)"),
    (5, lambda f: not f.a_high and not f.b_high and f.tf_better, "STRENGTHEN (weak: observational)"),
    (6, lambda f: not f.a_high and not f.b_high, "DROP"),
    (7, lambda f: True, "INCONCLUSIVE"),
]
RULE_TEXT = """\
Rows are checked top to bottom; the first that matches applies.

| # | Condition | Verdict |
|---|-----------|---------|
| 1 | A not exposed | CUES NOT REACHED |
| 2 | A high and B high | DROP (default behavior) |
| 3 | A > B and outcome: A better | KEEP |
| 4 | A > B and outcome: no difference or A worse | DROP (cues don't pay) |
| 5 | A low and B low and test-first runs did better | STRENGTHEN (weak: observational) |
| 6 | A low and B low | DROP |
| 7 | otherwise | INCONCLUSIVE |

Thresholds for "different": yes/no measures differ by at least one run per task, in the same direction in \
every task; rates by at least 0.10 pooled, same direction in every task; cost by at least 25% pooled, same \
direction in every task. High compliance is test-first in at least 6 of 9 runs (2/3) per arm. Exposed means at \
least half of arm A's first sessions read a cue file before coding. Test-first runs did better means their mean \
hidden pass rate beats the other runs by at least 0.10, with at least 3 runs in each group. Outcome is the \
hidden pass rate, the regression-free rate, and the silent-wrong rate; if they disagree, outcome is no difference.
"""


def decide(flags):
    for number, rule, verdict_text in RULES:
        if rule(flags):
            return number, verdict_text


# --- loading ---

def parse(value):
    if value in ("", None):
        return None
    if value in ("True", "False"):
        return value == "True"
    if value[:1] in "[{":
        return json.loads(value)
    try:
        return float(value) if any(c in value for c in ".e") else int(value)
    except ValueError:
        return value


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [{k: parse(v) for k, v in row.items()} for row in csv.DictReader(fh)]


def counted(rows):
    return [r for r in rows if not r.get("pilot") and not r.get("invalid")]


def first_sessions(rows):
    return [r for r in counted(rows) if r["session"] == 1]


def tasks_of(rows):
    return sorted({r["task"] for r in rows})


def by(rows, task, arm):
    return [r for r in rows if r["task"] == task and r["arm"] == arm]


def mean(values):
    values = [float(v) for v in values if v is not None]
    return statistics.fmean(values) if values else None


# --- directions ---

def yes_no_direction(rows, measure):
    diffs = [sum((r.get(measure) is True) for r in by(rows, t, "A")) - sum((r.get(measure) is True) for r in by(rows, t, "B"))
             for t in tasks_of(rows)]
    if diffs and all(d >= 1 for d in diffs):
        return 1
    if diffs and all(d <= -1 for d in diffs):
        return -1
    return 0


def rate_direction(rows, measure, threshold=RATE_THRESHOLD, higher_better=True):
    diffs = []
    for t in tasks_of(rows):
        a, b = mean(r.get(measure) for r in by(rows, t, "A")), mean(r.get(measure) for r in by(rows, t, "B"))
        if a is None or b is None:
            return 0
        diffs.append(a - b)
    pooled = (mean(r.get(measure) for r in rows if r["arm"] == "A") or 0) - \
        (mean(r.get(measure) for r in rows if r["arm"] == "B") or 0)
    sign = 1 if higher_better else -1
    if diffs and all(d > 0 for d in diffs) and pooled >= threshold:
        return sign
    if diffs and all(d < 0 for d in diffs) and pooled <= -threshold:
        return -sign
    return 0


def regression_rows(rows):
    """Follow-up sessions of runs whose first session passed every hidden test."""
    passed = {r["run"] for r in first_sessions(rows) if r.get("hidden_pass_rate") == 1}
    return [r for r in counted(rows) if r["session"] == 2 and r["run"] in passed]


def outcome_direction(rows):
    first = first_sessions(rows)
    directions = [rate_direction(first, "hidden_pass_rate"),
                  rate_direction(regression_rows(rows), "regression_free"),
                  rate_direction(first, "silent_wrong", higher_better=False)]
    moved = {d for d in directions if d}
    return moved.pop() if len(moved) == 1 else 0


def high(rows, arm):
    runs = [r for r in rows if r["arm"] == arm]
    return bool(runs) and sum((r.get("test_first") is True) for r in runs) >= HIGH_SHARE * len(runs)


def test_first_did_better(rows):
    yes = [r["hidden_pass_rate"] for r in rows if r.get("test_first") is True]
    no = [r["hidden_pass_rate"] for r in rows if r.get("test_first") is False]
    return len(yes) >= MIN_GROUP and len(no) >= MIN_GROUP and mean(yes) - mean(no) >= RATE_THRESHOLD


def flags_for(rows):
    first = first_sessions(rows)
    arm_a = [r for r in first if r["arm"] == "A"]
    exposed = bool(arm_a) and sum((r.get("exposed") is True) for r in arm_a) >= EXPOSED_SHARE * len(arm_a)
    return Flags(exposed, high(first, "A"), high(first, "B"), yes_no_direction(first, "test_first"),
                 outcome_direction(rows), test_first_did_better(first))


def verdict(rows):
    flags = flags_for(rows)
    row, text = decide(flags)
    return {"row": row, "verdict": text, "flags": flags}


def cost_direction(rows):
    return rate_direction(first_sessions(rows) + [r for r in counted(rows) if r["session"] == 2], "cost_usd",
                          threshold=COST_THRESHOLD * (mean(r.get("cost_usd") for r in counted(rows)) or 0),
                          higher_better=False)


# --- writing ---

def fmt(value):
    if value is None:
        return "-"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def task_table(rows):
    first, lines = first_sessions(rows), []
    lines += ["| Task | Arm | Runs | Pass rate | pass^3 | Silent-wrong | Regression-free (n) | Kill rate | "
              "Cost USD (unknown) | Exposed | Test-first | Saw red | Test/code | Out-of-repo | Hard rule |",
              "|" + "---|" * 15]
    for task in tasks_of(first):
        for arm in "AB":
            f, s2 = by(first, task, arm), by(regression_rows(rows), task, arm)
            all_sessions = by(counted(rows), task, arm)
            costs = [r.get("cost_usd") for r in all_sessions]
            lines.append("| " + " | ".join([
                task, arm, str(len(f)), fmt(mean(r.get("hidden_pass_rate") for r in f)),
                str(bool(f) and all(r.get("hidden_pass_rate") == 1 for r in f)),
                fmt(mean(r.get("silent_wrong") for r in f)),
                f"{fmt(mean(r.get('regression_free') for r in s2))} ({len(s2)})",
                fmt(mean(r.get("mutant_kill_rate") for r in f)),
                f"{fmt(mean(costs))} ({sum(c is None for c in costs)})",
                f"{sum((r.get('exposed') is True) for r in f)}/{len(f)}",
                f"{sum((r.get('test_first') is True) for r in f)}/{len(f)}",
                f"{sum(r.get('saw_red') is True for r in f)}/{len(f)}",
                fmt(mean(r.get("test_code_ratio") for r in f)),
                str(sum(bool(r.get("out_of_repo")) for r in all_sessions)),
                str(sum(bool(r.get("hard_rule_violation")) for r in all_sessions)),
            ]) + " |")
    return lines


RAW_COLUMNS = ["run", "session", "completed", "limit", "cost_usd", "hidden_pass_rate", "traps_passed",
               "silent_wrong", "regression_free", "mutant_kill_rate", "exposed", "test_first", "saw_red",
               "test_code_ratio", "hard_rule_violation", "invalid", "out_of_repo"]


def raw_table(rows):
    lines = ["| " + " | ".join(RAW_COLUMNS) + " |", "|" + "---|" * len(RAW_COLUMNS)]
    for r in rows:
        lines.append("| " + " | ".join(fmt(r.get(c)) if not isinstance(r.get(c), list) else ", ".join(r[c]) or "-"
                                       for c in RAW_COLUMNS) + " |")
    return lines


def flag_line(name, flags):
    return (f"- {name}: exposed {flags.exposed}, A high {flags.a_high}, B high {flags.b_high}, "
            f"A vs B test-first {flags.a_vs_b:+d}, outcome {flags.outcome:+d}, test-first runs did better "
            f"{flags.tf_better}")


def missing_runs(rows, reps=3):
    first = first_sessions(rows)
    return [f"{t} arm {a}: {len(by(first, t, a))} of {reps} counted first sessions"
            for t in tasks_of(rows) for a in "AB" if len(by(first, t, a)) < reps]


def write_summary(csv_path, out_path):
    rows = load(csv_path)
    main = verdict(rows)
    short = missing_runs(rows)
    unflagged = [r for r in rows if not r.get("out_of_repo")]
    clean = verdict(unflagged)
    invalid = [r for r in rows if r.get("invalid")]
    flagged = [r for r in rows if r.get("out_of_repo")]
    pilots = [r for r in rows if r.get("pilot")]
    lines = ["# Cue benchmark summary", "",
             "Haiku only, 3 reps per arm: a self-test, not statistical significance. The raw table is below.", "",
             "## Verdict", "", *([f"**INCOMPLETE:** {'; '.join(short)}.", ""] if short else []),
             f"**{main['verdict']}**", "", f"Row applied: {main['row']}",
             flag_line("Inputs", main["flags"]), f"- Cost (A vs B, lower is better): {cost_direction(rows):+d}", "",
             f"Without flagged sessions: **{clean['verdict']}** (row {clean['row']})",
             flag_line("Inputs", clean["flags"]), "",
             "## Decision rule", "", RULE_TEXT,
             "## Per task and arm", "", "First sessions; regression-free counts only runs whose first session "
             "passed every hidden test (n in brackets). pass^3: all reps passed every hidden test.", "",
             *task_table(rows), "",
             "## Invalid sessions", "", *([f"- {r['run']} session {r['session']}: {'; '.join(r['invalid'])}"
                                          for r in invalid] or ["None."]), "",
             "## Flagged sessions (out-of-repo access)", "",
             *([f"- {r['run']} session {r['session']}: {', '.join(r['out_of_repo'])}" for r in flagged] or ["None."]),
             "", "## Pilot", "", *([f"- {r['run']}: pass rate {fmt(r.get('hidden_pass_rate'))}, cost "
                                    f"{fmt(r.get('cost_usd'))}" for r in pilots] or ["None."]), "",
             "## Raw table", "", *raw_table([r for r in rows if not r.get("pilot")]), ""]
    text = "\n".join(lines)
    Path(out_path).write_text(text, encoding="utf-8", newline="\n")
    return text


def newest_runs():
    found = sorted(RESULTS.glob("*/runs.csv"))
    return found[-1] if found else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs_csv", nargs="?", help="default: the newest bench/results/<date>/runs.csv")
    args = parser.parse_args(argv)
    path = Path(args.runs_csv) if args.runs_csv else newest_runs()
    if not path or not path.is_file():
        print("error: no runs.csv found", file=sys.stderr)
        return 1
    out = path.with_name("summary.md")
    write_summary(path, out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
