# NERV skills for sequencing projects

Agent skills that set up and look after bioinformatics sequencing projects (bulk RNA-seq, scRNA-seq, and others) with AI coding agents. They give the agent layered documentation: a short `AGENTS.md` pointing to per-folder READMEs. Hooks keep those READMEs current and protect raw data, and a review process is tuned to bioinformatics risks such as reproducibility, provenance, and statistical validity.

Works with **Claude Code** and **Codex**. Hook logic is Python 3 standard library only.

## The skills

| Skill | What it does | The name |
|-------|--------------|----------|
| `nerv-init` | Interviews you (assay, workflow engine, language, compute, data sensitivity), then generates the project: folder skeleton, `AGENTS.md` + `CLAUDE.md`, a 4-section README per folder, `.gitignore`, `git init`, and the hooks below. | NERV is the organization that builds and runs the base everything launches from. |
| `sync-ratio` | Lists folders that changed significantly without a README update and drafts the updates (only "Current state" and "Last major change"). A Stop hook gives the agent the same reminder once, and never blocks. | The sync ratio measures how well pilot and Eva move as one; here, how well a README matches its folder. |
| `magi-review` | Risk-scaled review. TRIVIAL changes are skipped. STANDARD changes get one reviewer applying three lenses. CRITICAL changes get three independent seats that vote: MELCHIOR-1 (science), BALTHASAR-2 (safety), CASPER-3 (craft). A 2/3 majority wins; BALTHASAR can veto on hard-rule violations. | The MAGI are three supercomputers that decide by majority vote. |

`nerv-init` also installs the **raw-data guard**. New files in `data/raw/` are allowed, with a reminder to record their provenance in `data/README.md`. Changing, moving, or deleting an existing raw file needs your approval.

## Install (per project)

Run in the project directory. Nothing is installed globally (no `-g`).

```bash
npx skills add tingtmu/Seq-Unit-01 -a claude-code -a codex --skill nerv-init sync-ratio magi-review --copy -y
```

This puts the skills in `.agents/skills/` (Codex) and `.claude/skills/` (Claude Code). Then ask the agent to set up the project, or invoke `/nerv-init` in Claude Code.
- Name the three skills explicitly. `--skill '*'` would also pick up the repository's own development skills.
- `--copy` writes real files. Without it, `.claude/skills/` holds symlinks with absolute paths, and those break when the project is committed and cloned elsewhere.

### Fallback without Node

```bash
git clone --depth 1 https://github.com/tingtmu/Seq-Unit-01 /tmp/nerv-skills
mkdir -p .claude/skills .agents/skills
cp -r /tmp/nerv-skills/skills/* .claude/skills/
cp -r /tmp/nerv-skills/skills/* .agents/skills/
rm -rf /tmp/nerv-skills
```

PowerShell:

```powershell
git clone --depth 1 https://github.com/tingtmu/Seq-Unit-01 $env:TEMP\nerv-skills
New-Item -ItemType Directory -Force .claude\skills, .agents\skills | Out-Null
Copy-Item -Recurse $env:TEMP\nerv-skills\skills\* .claude\skills\
Copy-Item -Recurse $env:TEMP\nerv-skills\skills\* .agents\skills\
Remove-Item -Recurse -Force $env:TEMP\nerv-skills
```

Each skill folder is self-contained, so you can copy just one, for example only `nerv-init`.

## Requirements

- Python 3 (standard library) for hooks and the scaffold script
- git
- Node, only for `npx skills`

## Hooks and their limits

`nerv-init` copies the hook scripts into the project (`.nerv/hooks/`) and wires them up for each agent. The project owns its hook version, and the hooks keep working if the skills are removed.

| Hook | Claude Code (`.claude/settings.json`) | Codex (`.codex/hooks.json`) |
|------|---------------------------------------|-----------------------------|
| Raw-data guard, before a write | `PreToolUse` on Write/Edit/MultiEdit/NotebookEdit/Bash/PowerShell; existing raw file → **ask** you | `PreToolUse` on `apply_patch`/`Bash`; existing raw file → **deny** with instructions (Codex hooks have no "ask") |
| Provenance reminder | `PostToolUse` on Write (new files in `data/raw/`) | `PostToolUse` on `apply_patch` (added files) |
| README sync reminder | `Stop`: one `decision: block` per out-of-sync state; honors `stop_hook_active` | `Stop`: same output and `stop_hook_active` handling |

Limitations:
- **The raw-data guard is best-effort, not a security boundary.** Shell detection is a heuristic for `rm`, `mv`, `cp` onto existing files, `sed -i`/`perl -i`, `truncate`, `tee`, `>`/`>>`, and PowerShell `Remove-Item`/`Move-Item`/`Set-Content`/`Out-File`. Indirect writes, such as a script that writes into `data/raw/`, are not caught. For real protection, make `data/raw/` read-only at the OS level and keep checksums.
- If the guard itself fails (for example, on malformed input), it allows the action and writes the error to stderr, so a broken hook never breaks a session.
- **Codex silently skips project hooks until you trust them.** After `nerv-init`, open `codex` in the project, run `/hooks`, and trust the nerv hooks. Until you do, the raw-data guard and sync reminder are **off** in Codex, and nothing warns you. Re-trust after any change to `.codex/hooks.json`.
- Codex runs hook commands with relative paths, so start Codex from the project root.
- Claude Code hook commands use `python` on Windows and `python3` elsewhere, chosen when the project is scaffolded.
- In Codex, files written through the shell (not `apply_patch`) get no provenance reminder.

Hook schemas were verified on 2026-10-29 against the Claude Code hooks reference (code.claude.com/docs/en/hooks) and the Codex source (`openai/codex`: `codex-rs/hooks/src/schema.rs`, `output_parser.rs`, `config/src/hook_config.rs`). Codex rejects `permissionDecision: "ask"` in `PreToolUse`, so the guard denies there instead.

## Repository layout

```
skills/
  nerv-init/     SKILL.md, references/interview.md, scripts/scaffold.py,
                 templates/{base,addons,engines}/, hooks/{sync_ratio.py,raw_guard.py,adapters/}
  sync-ratio/    SKILL.md
  magi-review/   SKILL.md, references/{levels,seat-briefs,receiving-feedback}.md
tests/           pytest for the scaffold, hooks, templates, and skill docs
```

Run the tests with `python -m pytest`; the only requirement is pytest.

## License

MIT
