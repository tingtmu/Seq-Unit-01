# Proposal

## Why

NERV exists to lower setup friction, but in the first test run `nerv-init`'s next steps told the user to check and set a git identity that was already set. The agent had confirmed the identity itself when it committed. Our own spec causes this: `project-bootstrap` "First commit reported after scaffolding" requires the identity check as a user step. The generated `docs/principles.md` teaches the same habit with "Ask, don't guess." Skills should answer what files, git, and the environment can tell them, and ask the user only about intent.

## What Changes

- `scaffold.py` checks, after `git init`, whether a git identity (`user.name` and `user.email`) is set for the new project, and reports this as a new `git_identity` field (`set` or `missing`) in the `created` result.
- When the identity is set, `next_steps` has no commit step. `nerv-init` makes the first commit itself, after it writes the prose (step 5). First it checks what `git add -A` would include. The installed skill copies (`.claude/skills/`, `.agents/skills/`, `skills-lock.json`) are expected. Any other path not in the scaffold's `files` list is shown to the user, and the agent asks before committing it.
- When the identity is missing, or git is unavailable, `next_steps` keeps a commit step. The step gives the commands that set the identity, then `git add -A` and `git commit`, each as a separate command.
- `next_steps` otherwise lists only actions that only the user can take: Codex trust, `/hooks` in Claude Code, filling `config/samples.tsv` and reference pins, and making `data/raw/` read-only.
- Generated `docs/principles.md`: replace "Ask, don't guess" with "Explore before asking. Answer what the files, git, and environment can tell you; ask only about intent or ambiguity they can't resolve." This is template prose with no spec requirement behind it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-bootstrap`: "First commit reported after scaffolding" becomes "First commit after scaffolding". The agent commits when an identity is set, and the identity commands appear in the next steps only when no identity is set.

## Impact

- `skills/nerv-init/scripts/scaffold.py`: identity check, `git_identity` result field, conditional commit step.
- `skills/nerv-init/SKILL.md`: a new commit step between writing the prose and the summary.
- `skills/nerv-init/templates/base/docs/principles.md`: one bullet.
- `tests/test_scaffold.py`: next-steps tests split by identity state, with git config isolated per test.
- `README.md`: the `nerv-init` row says it makes the first commit when a git identity is set.
- No hook changes (hooks stay frozen).
