# Proposal

## Why

Codex skips project hooks until the user trusts them in `/hooks`, and it does not say so. A Codex user of a generated project therefore has the raw-data guard and the sync reminder switched off and does not know it. Today the only mention of the trust step is one bullet in step 6 of `nerv-init`'s SKILL.md, which the agent may or may not pass on. Nothing in a spec or a test requires the user to be told.

## What Changes

- `scaffold.py` returns a `next_steps` list in its `created` result. The first entry is the Codex trust step: start `codex` in the project root, run `/hooks`, and trust the nerv hooks, because until then the raw-data guard and sync reminder are off in Codex. The entry also says to trust them again after any change to `.codex/hooks.json`.
- The other next steps already listed in SKILL.md step 6 (fill `config/samples.tsv` and the reference pins, and optionally make `data/raw/` read-only) move into the same list, so all of them come from one place.
- `nerv-init` SKILL.md step 6 tells the agent to show every entry of `next_steps` to the user, without shortening them, and drops its hand-written copy of the list.
- `--dry-run` and conflict results do not change. The step is shown for every scaffold, because every generated project gets `.codex/hooks.json`, whatever agent the user runs now.

Out of scope: detecting whether the hooks are actually trusted (Codex exposes no way to check this from a hook or a script), and putting the step into the generated project's AGENTS.md.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `project-bootstrap`: adds the requirement "Codex trust step reported after scaffolding". When scaffolding finishes, the user is told how to trust the Codex hooks and that the hooks stay off in Codex until they do. The existing "Git initialization and hook installation" requirement does not change.

## Impact

- `skills/nerv-init/scripts/scaffold.py`: `scaffold()` result for `status: created`.
- `skills/nerv-init/SKILL.md`: step 6 (Summarize).
- `tests/test_scaffold.py`: new tests for `next_steps`.
- `README.md`: the "Hooks and their limits" Codex trust bullet says that `nerv-init` now prints this step. The Codex trust behavior is checked again against the Codex source, and the verification date is updated.
- `GLOSSARY.md`: add the term **Next steps** if it is used in specs and code.
- No change to the hook scripts or the adapters.
