#!/usr/bin/env python3
"""Deterministic part of nerv-init: build a project tree from interview answers.

Usage:
  scaffold.py --answers answers.json --target DIR [--dry-run]
  (--answers - reads the JSON from stdin)

Layers templates/base, templates/addons/<assay> and templates/engines/<engine>; a file
named X.append is inserted at the end of the Conventions section of base file X. Writes
.gitignore, copies hooks to .nerv/hooks/, installs agent adapters, and runs git init.
Refuses to write anything if a planned path already exists (lists the conflicts, exit 1).
Answers schema: see references/interview.md. Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "templates"
HOOKS = SKILL / "hooks"

ASSAYS = {"bulk-rnaseq": "Bulk RNA-seq", "scrnaseq": "Single-cell RNA-seq", "other": None}
ENGINES = {
    "snakemake": ("Snakemake", "snakemake --use-conda --cores 4", "snakemake -n"),
    "scripts": ("Plain scripts (workflow/run_all.sh)", "bash workflow/run_all.sh", None),
}
LANGUAGES = {"python": ("Python", "pytest tests/"), "r": ("R", "Rscript -e \"testthat::test_dir('tests')\"")}
VAR = re.compile(r"\{\{([A-Z_]+)\}\}")

GITIGNORE = """\
# nerv-init: raw/large data never goes into git
data/raw/*
!data/raw/.gitkeep
data/reference/*
!data/reference/.gitkeep
data/processed/*
!data/processed/.gitkeep
.nerv/*raw-snapshot*
*.fastq
*.fastq.gz
*.fq
*.fq.gz
*.bam
*.bai
*.cram
*.h5ad
*.h5
*.loom
*.mtx.gz
*.rds
.snakemake/
.ipynb_checkpoints/
__pycache__/
.Rhistory
.RData
.Rproj.user/
.env
"""
GITIGNORE_SENSITIVE = """\
# sensitive data: keep all derived outputs out of git as well
results/*
!results/README.md
data/*
!data/README.md
!data/raw/
!data/reference/
!data/processed/
*.vcf
*.vcf.gz
"""
SENSITIVE_RULES = """\
5. This project holds sensitive (human or controlled-access) data. Never paste sample-level data, \
identifiers, or file contents into prompts, issues, commits, or external services; share only \
aggregate results. Keep data only under `data/` and `results/` (both git-ignored).
6. Follow the data use agreement; record it (not the data) in `docs/`.
"""
NEXT_STEPS = (
    "Codex: project hooks are skipped until you trust them, so the raw-data guard and the sync "
    "reminder are off in Codex until you do. Start `codex` in the project root, run `/hooks`, and "
    "trust the nerv hooks (`.nerv/hooks/raw_guard.py` and `.nerv/hooks/sync_ratio.py`). Trust them "
    "again after any change to `.codex/hooks.json`.",
    "Fill `config/samples.tsv` and the reference pins in `config/config.yaml`.",
    "Optional: make `data/raw/` read-only at the OS level (`chmod -R a-w data/raw` on macOS or Linux, "
    "`attrib +R /S data\\raw\\*` on Windows), because the raw-data guard is best-effort.",
)


class AnswersError(ValueError):
    pass


def validate(answers):
    """Check the interview answers and fill defaults. Raises AnswersError."""
    if not isinstance(answers, dict):
        raise AnswersError("answers must be a JSON object")
    a = {"engine": "snakemake", "languages": ["python"], "compute": "local", "sensitive": False, **answers}
    if a.get("assay") not in ASSAYS:
        raise AnswersError(f"assay must be one of {sorted(ASSAYS)}")
    if a["assay"] == "other" and not str(a.get("assay_description", "")).strip():
        raise AnswersError("assay 'other' needs an assay_description")
    if a["engine"] not in ENGINES:
        raise AnswersError(f"engine must be one of {sorted(ENGINES)}")
    langs = a["languages"]
    if not isinstance(langs, list) or not langs or any(l not in LANGUAGES for l in langs):
        raise AnswersError(f"languages must be a non-empty list from {sorted(LANGUAGES)}")
    if not isinstance(a["sensitive"], bool):
        raise AnswersError("sensitive must be true or false")
    if not str(a.get("project_name", "")).strip():
        raise AnswersError("project_name is required")
    return a


def variables(a):
    engine_label, run, engine_test = ENGINES[a["engine"]]
    tests = ([engine_test] if engine_test else []) + [LANGUAGES[l][1] for l in a["languages"]]
    return {
        "PROJECT_NAME": a["project_name"],
        "ASSAY_LABEL": ASSAYS[a["assay"]] or a["assay_description"].strip(),
        "ENGINE_LABEL": engine_label,
        "LANGUAGES": " and ".join(LANGUAGES[l][0] for l in a["languages"]),
        "COMPUTE": str(a["compute"]),
        "DATE": a.get("date") or datetime.date.today().isoformat(),
        "RUN_COMMAND": run,
        "TEST_COMMAND": " && ".join(tests),
        "SENSITIVE_RULES": SENSITIVE_RULES if a["sensitive"] else "",
        "PYTHON": "python" if os.name == "nt" else "python3",
    }


def render(text, values, source):
    def sub(match):
        if match.group(1) not in values:
            raise KeyError(f"unknown template variable {match.group(0)} in {source}")
        return values[match.group(1)]
    return VAR.sub(sub, text)


def insert_conventions(text, extra):
    marker = "\n## Current state"
    if marker not in text:
        return text.rstrip("\n") + "\n" + extra
    head, tail = text.split(marker, 1)
    return head.rstrip("\n") + "\n" + extra.rstrip("\n") + "\n\n" + marker.lstrip("\n") + tail


def plan(a):
    """Return {relative posix path: file content (str)} for the whole project."""
    layers = [TEMPLATES / "base", TEMPLATES / "engines" / a["engine"]]
    if a["assay"] != "other":
        layers.insert(1, TEMPLATES / "addons" / a["assay"])
    files, appends = {}, []
    for layer in layers:
        for path in sorted(p for p in layer.rglob("*") if p.is_file()):
            rel = path.relative_to(layer).as_posix()
            text = path.read_text(encoding="utf-8")
            if rel.endswith(".append"):
                appends.append((rel.removesuffix(".append"), text))
                continue
            rel = rel.removesuffix(".tmpl")
            if rel in files:
                raise RuntimeError(f"template layers both define {rel}")
            files[rel] = text
    for rel, text in appends:
        files[rel] = insert_conventions(files[rel], text)
    files[".gitignore"] = GITIGNORE + (GITIGNORE_SENSITIVE if a["sensitive"] else "")
    for name in ("sync_ratio.py", "raw_guard.py"):
        files[f".nerv/hooks/{name}"] = (HOOKS / name).read_text(encoding="utf-8")
    files[".claude/settings.json"] = (HOOKS / "adapters" / "claude-settings.json").read_text(encoding="utf-8")
    files[".codex/hooks.json"] = (HOOKS / "adapters" / "codex-hooks.json").read_text(encoding="utf-8")
    values = variables(a)
    return {rel: text if rel.startswith(".nerv/") else render(text, values, rel) for rel, text in files.items()}


def conflicts(target, files):
    found = set()
    for rel in files:
        if (target / rel).exists():
            found.add(rel)
        top = rel.split("/", 1)[0]
        if "/" in rel and (target / top).exists() and not top.startswith("."):
            found.add(top + "/")
    return sorted(found)


def git_init(target):
    if (target / ".git").exists():
        return "existing"
    try:
        subprocess.run(["git", "init", "-q"], cwd=target, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"warning: git init failed: {exc}", file=sys.stderr)
        return "unavailable"
    return "initialized"


def scaffold(answers, target, dry_run=False):
    """Return (exit_code, result dict)."""
    a = validate(answers)
    files = plan(a)
    clash = conflicts(target, files)
    if clash:
        return 1, {"status": "conflict", "conflicts": clash,
                   "message": "Target already has these paths; nothing was written."}
    if dry_run:
        return 0, {"status": "planned", "files": sorted(files)}
    for rel, text in files.items():
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        if rel.endswith(".sh") or rel.startswith(".nerv/hooks/"):
            path.chmod(path.stat().st_mode | 0o111)
    return 0, {"status": "created", "files": sorted(files), "git": git_init(target),
               "next_steps": list(NEXT_STEPS)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--answers", required=True, help="answers JSON file, or - for stdin")
    parser.add_argument("--target", required=True, help="project directory to create or fill")
    parser.add_argument("--dry-run", action="store_true", help="list planned files and conflicts only")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.answers == "-" else Path(args.answers).read_text(encoding="utf-8")
        code, result = scaffold(json.loads(raw), Path(args.target).resolve(), args.dry_run)
    except (OSError, json.JSONDecodeError, AnswersError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
