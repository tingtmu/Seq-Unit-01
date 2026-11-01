# Proposal

## Why

In the yeast test run (2026-11-01), the user found `nerv-init`'s five next steps overwhelming. They pointed to four problems:

- The Codex and Claude Code hook entries say almost the same thing.
- The commit entry handed the user four git commands, because no identity was set. Our own spec forbids the agent from setting one, even with the user's answer.
- "Fill `config/samples.tsv` and the reference pins" was confusing: the user didn't know why they were told it.
- The read-only warning was a paragraph of shell commands. `add-data-intake` already shrinks this one.

Each next step should be something only the user can do, said in a sentence or two.

## What Changes

- **One hook entry.** The Codex trust entry and the Claude Code `/hooks` entry merge into a single "Turn on the raw-data guard" entry. It names `/hooks`, says the guard is off in Codex until the hooks are trusted and must be trusted again after `.codex/hooks.json` changes, and says to restart Claude Code in the project root if the hook isn't listed.
- **No commit entry, ever.** **BREAKING** for the `next_steps` contract: `COMMIT_STEP` and its conditional insertion are deleted from `scaffold.py`. When no git identity is set, `nerv-init` asks for the user's name and email in its plan message. After `git init`, it sets them for this project only, with `git config` and no `--global`, and then commits as it already does. It never invents an identity. If the user gives none, or git is unavailable, the summary says in one sentence that nothing was committed and why.
- **No sample-sheet entry.** The "fill `config/samples.tsv` and the reference pins" entry is deleted. Data intake (`add-data-intake`) fills the sample sheet. The agent fills the reference fields the data's own files state, such as the organism, and leaves the rest empty. If an empty field matters for the next run, its summary says so in one line.
- **The summary points forward.** It ends by inviting the user to say what they want to compare, which leads into planning the analysis.
- **Result:** after this change, `next_steps` holds exactly two entries: the hook entry, then the read-only entry. The agent still relays them word for word.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-bootstrap`:
  - "Codex trust step reported after scaffolding": becomes the single hook entry.
  - "Claude Code hook check reported after scaffolding": removed, merged into the hook entry.
  - "First commit after scaffolding": the agent asks for and sets a project-only identity, and next steps never hold git commands.
  - New: "Git identity set for the project only" (split out of "First commit after scaffolding"), "Sample sheet and reference pins are not a user step", and "Summary points to the analysis".

## Impact

- `skills/nerv-init/scripts/scaffold.py`: `NEXT_STEPS` (merged entry, the samples entry removed), and `COMMIT_STEP`, `COMMIT_STEP_AFTER`, and the conditional in `next_steps()` deleted. `git_identity` stays in the result, so the agent knows whether to set one.
- `skills/nerv-init/SKILL.md`: the plan asks for the name and email when identity is missing. The Commit step sets them project-only, and no longer says "never set an identity yourself". The Summarize step adds the one-line no-commit note, the empty-pin note, and the forward pointer.
- `tests/test_scaffold.py`: the next-steps tests are rewritten for two entries, and the identity-missing and git-unavailable tests now assert that no git command appears.
- `README.md`: the `nerv-init` row (identity) and any next-steps wording.
- `GLOSSARY.md`: the **Next steps** example, if it changes.
- Depends on `add-data-intake`, which changes the read-only entry and fills the sample sheet, and edits the same `NEXT_STEPS`. Apply and archive it first.
- No hook changes.
