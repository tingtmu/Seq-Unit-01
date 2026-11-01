---
name: yashima-blueprint
description: Plan an analysis by finding the risks that would invalidate its conclusion before any results exist, then record the agreed plan and thresholds as a commit. Use when the user asks to plan an analysis, or offer it before writing the first code for an analysis whose result answers the project's scientific question and has no analysis plan yet; do not offer it for refactors, pipeline plumbing, or environment setup.
---

# yashima-blueprint: remove fatal risks before the analysis runs

Operation Yashima had one shot, so everything that could make it miss was removed before firing. An analysis that answers the scientific question is the same: some flaws can't be fixed by changing code afterwards. Find those first, agree on the plan, and commit it before any result is seen.

## Flow

1. **Discover before asking.** Read the project question, the sample sheet, the config, and the data README. Check whether results or notebook outputs for this analysis already exist (look in the results and notebook folders and their `git log`). Check what the files can answer yourself, for example cross the batch and condition columns of the sample sheet. Ask the user only what the files can't tell you.
2. **List the fatal risks.** A fatal risk is one that no later code change can fix. Illustrations, not a checklist:
   - Design: in bulk RNA-seq, every treated sample in one batch and every control in another.
   - Replication: n=1 per group, or cells counted as replicates instead of donors.
   - Decision order: the test or cutoff chosen after seeing the results.
   Derive the risks from this study's design, whatever the assay. A problem a rerun or code change fixes (wrong genome build, missing seed, normalization choice) is not fatal; leave it to `magi-review`.
3. **Rank them.** Order by how surely each would sink the conclusion. List at most 8, with no minimum, and name for each the false result it would produce. Always include "analysis decisions fixed before results": the test or model, the contrast, the thresholds, and the multiple-testing correction are agreed before any result that answers the question is seen. Stop when the remaining risks can be fixed later. On a well-designed study the list may hold only that one risk; don't pad it.
4. **State unfixable risks plainly.** If a fatal risk can't be removed, tell the user what the data cannot show (for example, a condition effect can't be separated from a batch that equals condition). Plan only claims that avoid the risk, and label them as such: descriptive, or within one batch. Never plan around a risk silently.
5. **Agree, then write.** Write nothing until the user agrees to the plan; if you can't write files (for example, a read-only plan mode), stop at the agreed text. After agreement:
   - Write the plan to the project's existing docs folder, as `analysis-plan-<topic>.md`.
   - Write the threshold values under a `<topic>:` key in the config file the code already reads (for example `conf/` in an nf-core project). Create `docs/` or `config/` only if no such location exists.
   - Commit only those paths: `git add -- <paths>`, then `git commit -m "Analysis plan: <topic>" -- <paths>`. Other changes, staged or not, stay out of the commit.
6. **Hand off.** Don't write tests or analysis code. Tell the agent that implements the analysis to write boundary tests first, with values exactly at each threshold, and to pass the plan as `{REQUIREMENTS}` when the analysis code is reviewed with `magi-review`.

## What the plan must contain

- The question, the design, the ranked fatal risks with their false results, and the agreed test or model, contrast, thresholds, and correction.
- `Results seen when written: none` or the results that had been seen. If any had, tell the user the commit is evidence, not proof, that the plan came first.
- A scope line: "This plan covers confirmatory conclusions only. Findings outside it are labelled exploratory, or tested under a new analysis plan."
- A closing `## Deviations` section whose first line states the rule: "Add each change as a dated entry giving what changed, why, and whether it was made before or after seeing results. Never edit the text above."

These lines live in the plan so a later agent, in a later session, follows them without this skill running again.
