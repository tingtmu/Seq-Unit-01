# Proposal

## Why

The v1 mission includes planning with an agent, but NERV has no planning skill. The planning failures that matter most can't be fixed by changing code afterwards: a design where batch is confounded with condition, too few biological replicates, or a test or cutoff chosen after seeing the results. `principles.md` says "decide tests, thresholds, and corrections before looking at results; record them", but it doesn't say how to check the design for fatal flaws, or how to show the plan came before the results. This change has not been observed in a test run. It is admitted under the **Yashima clause** in `SCOPE.md`: the first failure would be severe and irreversible (a wrong statistical plan reaching a paper). The clause waives only the "observed" item, so the skill stays prose only and adds no hook.

## What Changes

- New skill `skills/yashima-blueprint/SKILL.md`. It is prose only and about the size of the existing skills. It runs when the user invokes it, or when the model offers or starts it before an analysis whose result answers the scientific question. It does not run for engineering tasks. The skill:
  - Learns what the project's files can tell it (config, sample sheet, project question, data README, existing results) before asking the user anything.
  - Defines a **fatal risk** as a risk that no later code change can fix. It gives three short examples from different fields as illustrations, not as a checklist, and the agent finds the risks for this particular study.
  - Ranks up to 8 fatal risks, with no minimum, and names for each the false result it would produce. "Analysis decisions fixed before results" is always on the list. The agent stops when the remaining risks can be fixed later; those are left to `magi-review`.
  - When a risk can't be fixed, says plainly what the data cannot show, and plans only claims that avoid the risk (descriptive or within a batch), labelled as such.
  - Covers confirmatory conclusions only. Anything found during exploration is labelled exploratory, or tested under a new plan.
  - After the user agrees, writes the analysis plan to the project's docs folder, and the threshold values under a topic key in the config the code reads. It commits only those paths. The plan records which results, if any, had been seen when it was written. The commit order is evidence that the plan came first, not proof.
  - When the plan changes, adds a dated Deviation entry and leaves the original text unchanged.
  - Hands off to implementation: write the boundary tests first, and pass the plan as the requirements when the analysis goes to `magi-review`. It does not write tests or analysis code.
- `GLOSSARY.md`: add **Analysis plan**, **Fatal risk**, and **Deviation** under a new "Planning an analysis (`yashima-blueprint`)" section. The section separates the skill from the SCOPE.md clause it is named after.
- `README.md`: add a row to the skills table, add the skill to the `--skill` list in the install command, and change "Name the three skills" to "Name the four skills".
- Out of scope: changes to `magi-review` or its seat briefs (MELCHIOR-1 grows only from incidents), template changes in `nerv-init`, hooks, and any auto-trigger mechanism.

## Capabilities

### New Capabilities

- `analysis-planning`: what the planning skill promises. It finds and ranks fatal risks before any results exist, records the agreed plan and its thresholds as a commit, appends deviations instead of rewriting the plan, and hands off to tests and review.

### Modified Capabilities

- `skill-distribution`: the "Install via skills CLI" scenario says "the three skills". It becomes "the four skills".

## Impact

- New: `skills/yashima-blueprint/SKILL.md`.
- `tests/test_skill_docs.py`: add `yashima-blueprint` to the two parametrized skill lists (frontmatter states function first; folder is self-contained).
- `GLOSSARY.md`, `README.md` (skills table, install command, "four skills"), and the verification date for the install command.
- `ROADMAP.md` (local): mark the planning skill as shipped, and add a watch row so test run 4 checks the skill's behavior.
- No changes to hooks, `scaffold.py`, templates, or `magi-review`.
