# Proposal

## Why

The first test run (2026-10-30) showed that the next steps after scaffolding stop short of a usable first session. Nothing tells the user to commit the skeleton, so the sync-ratio report and reviews have no commit to diff against (finding 6), and that commit fails on a machine with no git identity (finding 14). On Windows, `git add` printed about 120 CRLF warnings, and shell scripts and hooks would be checked out with CRLF, which breaks bash on Linux and HPC (finding 7). The next steps say nothing about Claude Code's hooks, and the Windows `attrib` example fails in Git Bash with "Parameter format not correct" (finding 13).

## What Changes

- The scaffold writes a `.gitattributes` that stores and checks out text files with LF line endings, so the first `git add` is quiet on Windows and scripts stay runnable on Linux and HPC.
- Two new next steps, after the Codex trust step (which stays first):
  - **Claude Code:** run `/hooks` to confirm the nerv hook is listed, and restart Claude Code in the project root if it is not. Current Claude Code reloads `.claude/settings.json` without a restart (since v2.1.257, checked against the Claude Code docs 2026-11-01), so a restart is only the fallback.
  - **First commit:** check `git config user.email`; if it prints nothing, set a name and email (commands given); then `git add -A` and `git commit`. The commands are separate, not chained with `&&`, so they also work in Windows PowerShell 5.1.
- The read-only step names the right shell for each command: `chmod` for macOS, Linux, or Git Bash on Windows; `attrib` for Windows cmd or PowerShell. Checked on Windows 11 on 2026-11-01: `chmod -R a-w` in Git Bash sets the read-only attribute, `chmod -R u+w` clears it, and `attrib +R /S data\raw\*` works in PowerShell but fails in Git Bash.
- Not in scope: setting up the tool environment (shipped in `add-runnable-fresh-project`), committing automatically from the scaffold, and checking git identity in code.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `project-bootstrap`: the generated project gets a `.gitattributes` with LF line endings; the next steps add a Claude Code hook check and a first-commit step with a git identity check; the read-only step names the shell for each command.

## Impact

- `skills/nerv-init/scripts/scaffold.py`: a `.gitattributes` constant written by `plan()`, and the `NEXT_STEPS` text; the module docstring
- `tests/test_scaffold.py`: next-steps and `.gitattributes` tests; `test_other_assay_uses_base_only` pins the top-level names and gains `.gitattributes`
- `skills/nerv-init/SKILL.md` step 4 and `skills/nerv-init/references/interview.md`: list `.gitattributes` among the generated files
- `README.md` (user-facing): `nerv-init` row lists `.gitattributes`
- `ROADMAP.md`: mark the item done when it ships
