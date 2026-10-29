# Proposal

## Why

The raw-data guard only sees what a tool call names: a file path or a shell command it can parse. A script that writes into `data/raw/` (`python scripts/fix.py`, `Rscript -e ...`, a workflow rule) changes raw data with no prompt and no notice. For the same reason, Codex never reminds the agent to record provenance for raw files added through the shell, because only `apply_patch` adds are seen. Both are open ROADMAP items, and one mechanism fixes both.

## What Changes

- After each agent tool call that can write files (file-edit tools and shell commands), the raw-data guard compares `data/raw/` with a saved snapshot of file sizes and modification times.
- New raw files get the existing provenance reminder no matter how they were written, including Codex shell commands.
- A raw file that was changed or removed gets one message telling the agent that raw data changed and to stop and tell the user if they did not approve it. Detection happens after the fact. It does not block or undo anything.
- This snapshot diff replaces the current per-tool PostToolUse parsing (Write `type`, `apply_patch` add lines). There is one code path.
- The PostToolUse matchers in both adapters widen to cover shell tools.
- The README hook table and limitations are updated: indirect writes are now reported, but still not prevented.
- The scaffolded `.gitignore` ignores the snapshot file.
- Out of scope: read-only locking, checksum manifests, hashing inside hooks, Stop-hook checks.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `raw-data-guard`: the provenance reminder now covers new raw files written by any tool, including shell commands, and a new requirement reports changes or deletions to existing raw files that the guard did not see beforehand.

## Impact

- `skills/nerv-init/hooks/raw_guard.py`: PostToolUse logic.
- `skills/nerv-init/hooks/adapters/claude-settings.json`, `codex-hooks.json`: PostToolUse matchers.
- `skills/nerv-init/scripts/scaffold.py`: one `.gitignore` line.
- `tests/test_raw_guard.py`, `tests/test_scaffold.py`.
- `README.md` (hook table, limitations, verification date), `skills/nerv-init/SKILL.md` hook summary, `ROADMAP.md` statuses.
- Projects already generated keep their own copy of the hooks and are not affected until they copy the new ones.
