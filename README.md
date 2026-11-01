<div align="center">

<img src="assets/banner.svg" alt="NERV · Seq-Unit-01: agent skills for sequencing projects" width="100%">

[![nerv-init](https://img.shields.io/badge/nerv--init-setup-734F9A?style=for-the-badge&labelColor=0B0A14)](skills/nerv-init/)
[![sync-ratio](https://img.shields.io/badge/sync--ratio-doc_sync-8BD450?style=for-the-badge&labelColor=0B0A14)](skills/sync-ratio/)
[![magi-review](https://img.shields.io/badge/magi--review-review-FF9900?style=for-the-badge&labelColor=0B0A14)](skills/magi-review/)
[![yashima-blueprint](https://img.shields.io/badge/yashima--blueprint-analysis_plan-E52F20?style=for-the-badge&labelColor=0B0A14)](skills/yashima-blueprint/)

**[Quick start](#quick-start) · [The skills](#the-skills) · [Install](#install-per-project) · [Requirements](#requirements) · [Hooks and their limits](#hooks-and-their-limits) · [Repository layout](#repository-layout) · [License](#license)**

</div>

> **NERV briefing.** NERV builds the base, and every project it sets up is a Unit. The MAGI vote on risky changes. The AT Field (the raw-data guard) stands around `data/raw/`. The sync ratio shows which READMEs have fallen behind their folders. And, as in Operation Yashima, where there was only one shot, everything that could make an analysis miss is removed before any result exists.
>
> <sub>Unofficial fan homage. Not affiliated with or endorsed by khara, Inc. The MIT license covers this code, not Evangelion names or marks.</sub>

# NERV skills for sequencing projects

Agent skills that set up and look after bioinformatics sequencing projects (bulk RNA-seq, scRNA-seq, and others) with AI coding agents. They give the agent layered documentation: a short `AGENTS.md` pointing to per-folder READMEs. A hook protects raw data, an on-demand check keeps those READMEs current, and a review process is tuned to bioinformatics risks such as reproducibility, provenance, and statistical validity.

Works with **Claude Code** and **Codex**. Hook logic is Python 3 standard library only.

## Quick start

1. In a new, empty project folder, install the skills:
   ```bash
   npx skills add tingtmu/Seq-Unit-01 -a claude-code -a codex --skill nerv-init sync-ratio magi-review yashima-blueprint --copy -y
   ```
2. Start your agent in that folder. In Claude Code, run `/nerv-init`; in Codex, ask it to set up the project. Answer the short interview (assay, workflow engine, language, compute, data sensitivity, project question). The agent then generates the project.
   - **Codex only:** run `/hooks` and trust the nerv hooks, or the raw-data guard stays off.
3. Day to day, ask for what you need:
   - "Plan the analysis" → `yashima-blueprint`
   - "Review my change" → `magi-review`
   - "Are the folder READMEs up to date?" → `sync-ratio`

[Install](#install-per-project) explains the flags and gives a fallback without Node.

## The skills

| Skill | What it does | The name |
|-------|--------------|----------|
| `nerv-init` | Interviews you (assay, workflow engine, language, compute, data sensitivity, the project question or `TBD`), then generates the project: folder skeleton, `AGENTS.md` + `CLAUDE.md`, a 4-section README per folder, a pinned conda environment (`envs/workflow.yaml`) and one smoke test per language so the Run and Test commands pass on day one, `.gitignore`, `.gitattributes` (LF line endings), `git init`, and the hooks below. If a git identity is already set, it makes the first commit itself (and asks before including files it didn't generate); otherwise its next steps give the commands to set one and commit. | NERV is the organization that builds and runs the base everything launches from. |
| `sync-ratio` | Lists folders that changed significantly without a README update and drafts the updates (only "Current state" and "Last major change"). | The sync ratio measures how well pilot and Eva move as one; here, how well a README matches its folder. |
| `magi-review` | Risk-scaled review. TRIVIAL changes are skipped. STANDARD changes get one reviewer applying three lenses. CRITICAL changes get three independent seats that vote: MELCHIOR-1 (science), BALTHASAR-2 (safety), CASPER-3 (craft). A 2/3 majority wins; BALTHASAR can veto on hard-rule violations. | The MAGI are three supercomputers that decide by majority vote. |
| `yashima-blueprint` | Plans an analysis that answers the scientific question before any results exist. It reads the project first, ranks the fatal risks (those no later code change can fix, such as batch confounded with condition) and names the false result each would produce, then, once you agree, commits the analysis plan and its thresholds. The plan carries its own confirmatory scope and an append-only Deviations section. It hands off to boundary tests and `magi-review`; it writes no code. | Operation Yashima had one shot, so everything that could make it miss was removed before firing. |

`nerv-init` also installs the **raw-data guard**. New files in `data/raw/` are allowed, with a reminder to record their provenance in `data/README.md` and a ready-to-run SHA-256 command. Changing, moving, or deleting an existing raw file needs your approval, and the request warns that approving cannot be undone, because raw data is not in git. If a raw file changes, by an approved edit or some other way such as a script, the agent is told after the fact that its provenance record no longer matches and that getting it back means fetching it again from its source.

## Install (per project)

Run in the project directory. Nothing is installed globally (no `-g`).

```bash
npx skills add tingtmu/Seq-Unit-01 -a claude-code -a codex --skill nerv-init sync-ratio magi-review yashima-blueprint --copy -y
```

This puts the skills in `.agents/skills/` (Codex) and `.claude/skills/` (Claude Code). Then ask the agent to set up the project, or invoke `/nerv-init` in Claude Code.
- Name the four skills explicitly. `--skill '*'` would also pick up the repository's own development skills.
- `--copy` writes real files. Without it, `.claude/skills/` holds symlinks with absolute paths, and those break when the project is committed and cloned elsewhere.
- Use only the agents you need. Each `-a` adds a full copy of the skills, because each agent reads its own folder.
- If the agent doesn't list the new skills yet, wait a turn or start a new session before running `/nerv-init`.

**Commit the installed skills.** Commit `.claude/skills/`, `.agents/skills/`, and `skills-lock.json` with the project, so every clone has the same skill versions without Node. The lock file records where each skill came from and a hash of its files. Installing from GitHub records `tingtmu/Seq-Unit-01`; installing from a local folder records a relative path, which breaks if the project moves. Don't git-ignore the copies with a plan to restore them from the lock file: the restore command (`npx skills experimental_install`) is experimental and fills only `.agents/skills/`, so Claude Code would get nothing.

The flags (`-a`, `--skill`, `--copy`, `-y`) and the install paths per agent were verified on 2026-10-29 against the `vercel-labs/skills` CLI docs (`docs/commands.md`, `docs/agents.md`); the space-separated `--skill` list was re-checked on 2026-11-01 (`--skill <skills...>`, `docs/commands.md`). The `skills-lock.json` behavior and the restore command were checked on 2026-11-01 against the same docs (`docs/commands.md`) and the lock reference (`src/local-lock.ts`).

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

`nerv-init` copies the hook script into the project (`.nerv/hooks/`) and wires it up for each agent; it also copies the doc-sync report that `sync-ratio` runs into `.nerv/scripts/`. The project owns its copies, and they keep working if the skills are removed.

| Hook | Claude Code (`.claude/settings.json`) | Codex (`.codex/hooks.json`) |
|------|---------------------------------------|-----------------------------|
| Raw-data guard, before a write | `PreToolUse` on Write/Edit/MultiEdit/NotebookEdit/Bash/PowerShell; existing raw file → **ask** you, warning that approving cannot be undone | `PreToolUse` on `apply_patch`/`Bash`; existing raw file → **deny** with instructions (Codex hooks have no "ask") |
| Raw-data guard, after a write | `PostToolUse` on the same tools: compares `data/raw/` with the raw snapshot (`.nerv/raw-snapshot.json`, git-ignored); new raw files → provenance reminder with a SHA-256 command for your OS, modified or removed raw files → reported after the fact, with a note that their provenance records in `data/README.md` no longer match | `PostToolUse` on `apply_patch`/`Bash`: same |

Limitations:
- **The raw-data guard is best-effort, not a security boundary.** Shell detection is a heuristic for `rm`, `mv`, `cp` onto existing files, `sed -i`/`perl -i`, `truncate`, `tee`, `>`/`>>`, and PowerShell `Remove-Item`/`Move-Item`/`Set-Content`/`Out-File`. Indirect writes, such as a script that writes into `data/raw/`, are not prevented: after each covered tool call, the guard compares each raw file's size and modification time with the raw snapshot and reports new, modified, or removed files. Rewrites that keep both size and modification time are missed, and a raw change from a failed command is reported at the next covered tool call. For real protection, make `data/raw/` read-only at the OS level (a recommended next step after scaffolding) and record checksums.
- If the guard itself fails (for example, on malformed input), it allows the action and writes the error to stderr, so a broken hook never breaks a session.
- **Codex silently skips project hooks until you trust them.** Open `codex` in the project root, run `/hooks`, and trust the nerv hooks. Until you do, the raw-data guard is **off** in Codex, and Codex itself does not warn you. `nerv-init` prints this step in its next steps after scaffolding. Re-trust after any change to `.codex/hooks.json`.
- Codex runs hook commands with relative paths, so start Codex from the project root.
- Claude Code hook commands use `python` on Windows and `python3` elsewhere, chosen when the project is scaffolded.

Hook schemas were verified on 2026-10-29 against the Claude Code hooks reference (code.claude.com/docs/en/hooks) and the Codex source (`openai/codex`: `codex-rs/hooks/src/schema.rs`, `output_parser.rs`, `config/src/hook_config.rs`). The `PostToolUse` matchers for shell tools and `additionalContext` output were re-checked on 2026-10-29; Codex reports shell tools as `Bash` (`core/src/tools/hook_names.rs`), and both agents run `PostToolUse` only after a tool succeeds. The Codex trust behavior (untrusted or modified project hooks are skipped; `/hooks` trusts them) was checked on 2026-10-29 against `codex-rs/hooks/src/engine/discovery.rs`. Codex rejects `permissionDecision: "ask"` in `PreToolUse`, so the guard denies there instead.

## Repository layout

```
skills/
  nerv-init/     SKILL.md, references/interview.md, scripts/{scaffold.py,sync_ratio.py},
                 templates/{base,addons,engines,languages}/, hooks/{raw_guard.py,adapters/}
  sync-ratio/    SKILL.md
  magi-review/   SKILL.md, references/{levels,seat-briefs,receiving-feedback}.md
  yashima-blueprint/ SKILL.md
tests/           pytest for the scaffold, hooks, templates, and skill docs
assets/          banner.svg (README art) and make_banner.py, which generates it
```

Run the tests with `python -m pytest`; the only requirement is pytest.

## License

MIT
