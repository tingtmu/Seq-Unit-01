# Design

## Context

`scaffold()` validates the answers, plans the files, then checks conflicts before it looks at `--dry-run`. So a dry run on a target with conflicts already returns `{"status": "conflict", "conflicts": [...], "message": ...}` with exit code 1, the same as a real run. Only the clean case returns `{"status": "planned", "files": [...]}`. The gap in finding 5 is in the prose: SKILL.md step 2 asks for add-ons and conflicts without saying where they come from, so the agent looked for them in the clean result and found neither.

The answer-to-output table in `references/interview.md` already maps each `assay`, `engine`, and `languages` value to its add-on content. The agent built the answers JSON one step earlier, so it has everything needed to name the layers.

## Goals / Non-Goals

**Goals:**
- Step 2 tells the agent, for each part of the plan summary, which source to read.
- A pytest pins the conflict result on a dry run, which today is covered only for a real run.

**Non-Goals:**
- Growing the dry-run JSON (`addons`, `engine`, `conflicts: []`, `git`, `next_steps`). That duplicates what the answers already say, and is a second mechanism for the same fact.
- Changing what step 4 or step 6 report.

## Decisions

**Fix the prose, not the output.** The ROADMAP item and the admission bar ("tried as prose before code", "deleting counts as progress") favor this. The alternative, adding an `addons` key, would need a scaffold change, a spec scenario, and a test for data the agent wrote itself a moment earlier.

**Point to the existing table rather than repeat it.** Step 2 names `references/interview.md` (inside the skill folder, so rule 1 holds) for the answer-to-add-on mapping, and does not copy the mapping into SKILL.md.

**Spell out both result shapes.** Step 2 says `status: "planned"` means no conflicts, and `status: "conflict"` means show `conflicts` and stop. This removes the inference the test-run agent had to make.

## Risks / Trade-offs

- [The agent still guesses add-ons from file names] → the wording names the source explicitly; the next test run records whether the agent followed it.
- [The "other" assay has no add-on layer] → the table already says it gets the shared skeleton only; step 2's wording covers it by pointing to the table.
