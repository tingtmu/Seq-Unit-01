# NERV skills for sequencing projects

Agent skills that set up and look after bioinformatics sequencing projects (bulk RNA-seq, scRNA-seq, and others) with AI coding agents. They give the agent layered documentation: a short `AGENTS.md` pointing to per-folder READMEs. A hook protects raw data, an on-demand check keeps those READMEs current, and a review process is tuned to bioinformatics risks such as reproducibility, provenance, and statistical validity.

Works with **Claude Code** and **Codex**. Hook logic is Python 3 standard library only.

## The skills

| Skill | What it does | The name |
|-------|--------------|----------|
| `nerv-init` | Interviews you (assay, workflow engine, language, compute, data sensitivity), then generates the project: folder skeleton, `AGENTS.md` + `CLAUDE.md`, a 4-section README per folder, `.gitignore`, `git init`, and the hooks below. | NERV is the organization that builds and runs the base everything launches from. |
| `sync-ratio` | Lists folders that changed significantly without a README update and drafts the updates (only "Current state" and "Last major change"). | The sync ratio measures how well pilot and Eva move as one; here, how well a README matches its folder. |
| `magi-review` | Risk-scaled review. TRIVIAL changes are skipped. STANDARD changes get one reviewer applying three lenses. CRITICAL changes get three independent seats that vote: MELCHIOR-1 (science), BALTHASAR-2 (safety), CASPER-3 (craft). A 2/3 majority wins; BALTHASAR can veto on hard-rule violations. | The MAGI are three supercomputers that decide by majority vote. |

`nerv-init` also installs the **raw-data guard**. New files in `data/raw/` are allowed, with a reminder to record their provenance in `data/README.md` and a ready-to-run SHA-256 command. Changing, moving, or deleting an existing raw file needs your approval, and the request warns that approving cannot be undone, because raw data is not in git. If a raw file changes, by an approved edit or some other way such as a script, the agent is told after the fact that its provenance record no longer matches and that getting it back means fetching it again from its source.

## Install (per project)

Run in the project directory. Nothing is installed globally (no `-g`).

```bash
npx skills add tingtmu/Seq-Unit-01 -a claude-code -a codex --skill nerv-init sync-ratio magi-review --copy -y
```

This puts the skills in `.agents/skills/` (Codex) and `.claude/skills/` (Claude Code). Then ask the agent to set up the project, or invoke `/nerv-init` in Claude Code.
- Name the three skills explicitly. `--skill '*'` would also pick up the repository's own development skills.
- `--copy` writes real files. Without it, `.claude/skills/` holds symlinks with absolute paths, and those break when the project is committed and cloned elsewhere.

The flags (`-a`, `--skill`, `--copy`, `-y`) and the install paths per agent were verified on 2026-10-29 against the `vercel-labs/skills` CLI docs (`docs/commands.md`, `docs/agents.md`).

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
                 templates/{base,addons,engines}/, hooks/{raw_guard.py,adapters/}
  sync-ratio/    SKILL.md
  magi-review/   SKILL.md, references/{levels,seat-briefs,receiving-feedback}.md
tests/           pytest for the scaffold, hooks, templates, and skill docs
```

Run the tests with `python -m pytest`; the only requirement is pytest.

## License

MIT
