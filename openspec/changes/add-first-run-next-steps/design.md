# Design

## Context

The scaffold writes `.gitignore` from a constant in `scaffold.py` (`GITIGNORE`) and writes every file with `newline="\n"`, so the working tree is already LF. The CRLF warnings in finding 7 came from `core.autocrlf=true`, which would convert those LF files to CRLF on checkout. Next steps live in one tuple, `NEXT_STEPS`, which the agent relays word for word. `test_created_result_lists_next_steps` currently reads the read-only step by index (`steps[2]`).

## Goals / Non-Goals

**Goals:**
- The three missing next steps and the line-ending fix, with the smallest change to `scaffold.py`.

**Non-Goals:**
- Running `git commit` or checking git identity from the scaffold.
- Detecting the user's shell or the Claude Code version.

## Decisions

**`.gitattributes` is a constant written by `plan()`, next to `.gitignore`.** It holds a comment and one line: `* text=auto eol=lf`. The `eol` attribute overrides `core.autocrlf`, so checkouts are LF on every platform. A separate `*.sh text eol=lf` line adds nothing, because git never auto-detects a shell script as binary. Alternative: a dotfile in `templates/base/`. Rejected because `.gitignore` is already a constant, and dotfiles in skill folders are easy for an installer to drop.

**Next-step order: Codex trust, Claude Code check, first commit, fill config, read-only.** Codex trust stays first because `SKILL.md` step 6 says so. The two hook checks sit together. The commit comes before filling `config/` so the first diff the user sees is their own edits.

**The Claude Code step is a check, with restart as the fallback.** The Claude Code docs (checked 2026-11-01) say settings files are watched and reloaded, including hooks and a `.claude/` folder created mid-session, since v2.1.257. Telling every user to restart would be wrong for current versions. Running `/hooks` costs one command and covers older versions.

**Git identity check is prose, not code.** The step says to run `git config user.email` and, if it prints nothing, gives `git config --global user.name "Your Name"` and `git config --global user.email "you@example.org"`, noting that dropping `--global` sets them for this project only. Alternative: the scaffold runs `git config user.email` and adds the hint only when it is missing. Rejected under the admission bar ("prose before code"): one static step covers both cases, and the result stays deterministic for tests.

**Commit commands are separate.** `git add -A`, then `git commit -m "nerv-init scaffold"`. A `&&` chain fails in Windows PowerShell 5.1, the default shell on Windows.

**Shell labels in the read-only step.** `chmod` for "macOS, Linux, or Git Bash on Windows"; `attrib` for "Windows cmd or PowerShell". Verified on Windows 11, 2026-11-01: Git Bash `chmod -R a-w data/raw` sets the R attribute on files in subfolders and `chmod -R u+w data/raw` clears it; `attrib +R /S data\raw\*` and `attrib -R /S data\raw\*` work in PowerShell; in Git Bash the same `attrib` command fails ("Parameter format not correct") because Git Bash rewrites the backslashes and `/S`.

**Tests find steps by content, not index.** With five steps, index-based reads break whenever the order changes. Only the Codex step keeps an index check (`steps[0]`), because its position is a promise.

## Risks / Trade-offs

- [The Claude Code version boundary changes or a user runs an old version] → the step tells them to restart if `/hooks` doesn't list the hook, which works on any version.
- [A project that already tracks files with CRLF] → not possible here: the scaffold creates new projects only and refuses to overwrite.
- [Longer next-steps list, relayed word for word] → five short entries; each was a real snag in the test run.
