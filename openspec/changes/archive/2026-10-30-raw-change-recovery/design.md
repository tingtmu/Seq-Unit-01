# Design

## Context

`raw_guard.py` already has everything this change needs to detect. PreToolUse returns "ask" (Claude Code) or "deny" (Codex). PostToolUse diffs `data/raw/` against the raw snapshot and builds its message from two templates, `PROVENANCE` (new files) and `CHANGED` (modified or removed files). The read-only step lives in `NEXT_STEPS` in `scaffold.py`. This change only alters text, plus one small choice of checksum command per operating system. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- Every message about a raw change tells the user that it can't be undone and what that means for the provenance record.
- Recording a checksum for a new raw file takes one copy-paste, not a lookup.

**Non-Goals:**
- Reading or parsing `data/README.md`. The guard doesn't check whether a provenance record exists or what checksum it holds.
- Computing checksums inside the hook.
- Any change to detection, to decisions ("ask" or "deny"), or to the hook adapters.

## Decisions

**1. The checksum command is chosen by `sys.platform`, not computed.** On Linux it is `sha256sum <files>`, on macOS `shasum -a 256 <files>` (macOS has no `sha256sum` by default), and on Windows `Get-FileHash -Algorithm SHA256 -LiteralPath <files> | Format-List Hash, Path`. Paths are relative to the project root, which is where agents run. On Linux and macOS they are quoted with `shlex.quote`. On Windows each path is single-quoted, with any `'` doubled, and the paths are comma-separated.
- *Alternative: hash in the hook.* Rejected. Raw FASTQs can be tens of GB, PostToolUse runs after every covered tool call and has a timeout, and a timeout would fail open with no reminder at all.
- *Alternative: a `python -c` one-liner, which works on every OS.* Rejected because it is hard to read, and the user may run it themselves.
- `-LiteralPath`, not `-Path`: `-Path` reads `[ ]` as wildcards, so a name like `S1[rep2].fq.gz` matches nothing and the command succeeds silently. `Format-List` keeps each hash next to its full path, because the default table cuts off the Path column.
- On Windows, `Get-FileHash` is chosen over `sha256sum` because Codex on Windows runs PowerShell, and Claude Code on Windows has a PowerShell tool. Git Bash users can still use `sha256sum`, but the reminder names only one command.
- The command names the same files the message lists, so it follows the existing `MAX_LISTED` cap. Beyond the cap, the message says "and N more" but doesn't name those files, so the command doesn't cover them. The agent has to list `data/raw/` to finish. This is a known gap, left for a follow-up.

**2. The mismatch notice is one fixed sentence added to `CHANGED`.** It applies the same way to modified and removed files, so neither case needs its own wording. The guard can't tell whether the user approved the change, so the sentence describes what follows from it, not who caused it.

**3. Only the Claude Code "ask" reason gains the warning.** Codex already denies the action, and its message tells the user to run the command themselves. Nothing is approved there, so there is nothing to warn about.

**4. The next-steps entry keeps its position (third) and its commands.** Only its framing changes: "Recommended", when to apply it, and how to undo it (`chmod -R u+w data/raw`, `attrib -R /S data\raw\*`). The Git Bash quoting of `attrib` is left to the "First-run next steps" item, to keep this change to one concern.

## Risks / Trade-offs

- Every raw-change message gets longer, and agents may skim it. To limit this, each addition is one sentence. The command goes at the end of the provenance reminder, where it is easy to copy.
- On Windows, the guard can't tell whether the agent will run Git Bash or PowerShell, so the suggested command may not match the agent's current shell. This is acceptable: both shells are available on Windows, and the agent can translate the command.
- Making `data/raw/` read-only can make an agent's download into a new batch fail with "permission denied". This is the intended effect. The next step says to undo it before adding a batch.
