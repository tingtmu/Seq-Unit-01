# Proposal

## Why

`nerv-init` step 2 tells the agent to show "the planned top-level tree, which add-ons apply, and any conflicts", but the dry-run result is only `{"status": "planned", "files": [...]}`. In the first test run (finding 5) the agent guessed the add-ons from file names, and inferred "no conflicts" from the missing key. The promise and the output disagree. The test run suggested growing the JSON; the ROADMAP item chose the deleting fix instead: the agent already knows the add-ons from the answers it just built, and the scaffold already reports conflicts, so the prose should say where each piece comes from.

## What Changes

- `nerv-init` SKILL.md step 2 says where each part of the plan summary comes from: the top-level tree from the dry run's `files`; the add-on and engine layers from the answers, using the answer-to-output table in `references/interview.md`; conflicts from a `status: "conflict"` result (whose `conflicts` list is shown, then the agent stops and asks). A `status: "planned"` result means there are no conflicts.
- `scaffold.py` is not changed. The dry run already checks conflicts before planning and returns the same conflict result as a real run. A pytest pins this, because no test covers conflicts on a dry run today.
- Not added (non-goals): `addons`, `engine`, `conflicts: []`, `git`, or a `next_steps` preview in the dry-run JSON. Step 4 already tells the agent what the real run does (`git init`, hooks).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `project-bootstrap`: "Interview before generation" says what the plan summary contains and where each part comes from; "Refuse to overwrite an existing project" says conflicts are found by the dry run, before the user confirms.

## Impact

- `skills/nerv-init/SKILL.md`: step 2 wording only. The description's first sentence is unchanged.
- `tests/test_scaffold.py`: one test for a dry run on a target with conflicts.
- No hook, scaffold, template, or adapter changes. `README.md` and `GLOSSARY.md` do not describe the dry run, so neither changes.
