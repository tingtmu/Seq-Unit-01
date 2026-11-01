# Design

## Context

`scaffold.py` returns a fixed `NEXT_STEPS` tuple in the `created` result, and `SKILL.md` step 6 relays it word for word. The tuple's third entry is the identity check and commit. `git_init()` already runs git as a subprocess and reports `git: initialized | unavailable`. The prose (step 5) is written after the scaffold returns, so the scaffold cannot make the commit itself. The README tells users to commit the installed skill copies, so a target usually already holds `.claude/skills/`, `.agents/skills/`, and `skills-lock.json` before `nerv-init` runs.

## Goals / Non-Goals

**Goals:**
- Decide the identity in code (testable), and the commit in the skill (after the prose).
- Keep `next_steps` relayed word for word. The agent never edits the list.

**Non-Goals:**
- Setting the identity for the user, or guessing one.
- Changing hooks (frozen) or the interview.
- Detecting other facts, such as conda or Codex being installed. Add those only if a test run observes friction.

## Decisions

1. **The identity check lives in `scaffold.py`, not in prose.** After `git_init`, run `git config user.name` and `git config user.email` in the target. Both must exit 0 with non-empty output for `git_identity: "set"`. Anything else, including git being unavailable, gives `"missing"`. *Alternative:* have the agent run the check and drop the step from the list. That breaks "word for word" and can't be pytested.
2. **Two result values, not three.** When git is unavailable, report `missing` and keep the commit step: that is today's behavior, and the step still helps once git works. A third `unknown` value would add a branch to the skill with no scenario that needs it (YAGNI).
3. **The commit step is built conditionally.** `NEXT_STEPS` loses the commit entry. The scaffold inserts it at its current position (after the Claude Code entry, before `samples.tsv`) only when the identity is missing. The step's text stays as it is today.
4. **The agent commits in a new SKILL.md step**, between writing the prose and the summary, and only when `git_identity` is `set`. It runs `git status --porcelain --untracked-files=all` and compares the paths with the result's `files` list. Paths under `.claude/skills/`, `.agents/skills/`, or `skills-lock.json` are expected. Any other path is listed for the user, who is asked whether to include it. The agent then stages and commits by explicit path: `git add -- <paths>`, then `git commit -m "nerv-init scaffold" -- <paths>`, where `<paths>` is the generated files, the skill copies, and any approved paths. The pathspec on `git commit` keeps out changes the user had already staged in an existing repository (`git: existing` is common, because the README has users commit the installed skills before running `nerv-init`). The summary reports the commit. *Alternatives:* `git add -A` sweeps in declined paths, so it is rejected. Committing inside `scaffold.py` is rejected too: the prose would land in a second commit, and the scaffold can't ask the user about extra files.
5. **SKILL.md names the skill copies without the literal `skills/`.** `test_skill_folder_is_self_contained` flags `\bskills/` in a skill folder (hard rule 1), and `.claude/skills/` matches it. SKILL.md says "the `skills` folders under `.claude` and `.agents`, and `skills-lock.json`". The guard test stays as it is.
6. **Test isolation.** The identity tests point `GIT_CONFIG_GLOBAL` at a temp file and set `GIT_CONFIG_NOSYSTEM=1` through `monkeypatch`. This gives one test with an identity and one without, independent of the developer's machine. The existing order test runs with the identity missing, so it still checks where the commit step sits.

## Risks / Trade-offs

- [The identity is checked before the prose is written, and the user could change it in between] → This is unlikely during one skill run. If the commit fails anyway, the agent shows git's error. It does not retry with an invented identity.
- [The agent's commit step is agent behavior, not code] → It is checked in the next test run and recorded in its notes, per AGENTS.md. Pytests cover only the result field and `next_steps`.
- [Pre-existing user files in a non-empty target] → The agent asks before committing them (spec scenario "Other files in the target"). It never adds them silently.
