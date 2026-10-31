# Proposal

## Why

The first test run showed two problems with `magi-review` levels (M1, M2 in `nerv-testrun/TESTRUN-NOTES.md`). The 29 statistics keywords are matched against changed lines only, so a change to a QC-threshold file came out STANDARD, while the keyword `scale` would make a colors-only `colorscale` plot CRITICAL. And when a stray file (such as an uncommitted notes file) sets the level, the report doesn't show which file did it. A keyword list is the wrong tool: agents can judge the category directly, and the existing "when unsure, CRITICAL" rule already covers the doubtful cases.

## What Changes

- Replace the statistics keyword list in `levels.md` with the category it stands for: statistics or QC code (statistical tests, normalization, clustering, integration, thresholds), judged by what the touched files do, not by matching words. When unsure, CRITICAL. This removes the cause of M2.
- Simplify CONDITIONAL in the vote: it is tallied as APPROVE. The report no longer shows two outcomes ("APPROVE if …, otherwise REJECT"); it shows one outcome and lists the required fixes. A required fix the author declines goes to the user for a ruling.
- The level statement and the report name the files that set the level (M1). For a line-count rule, each Markdown file is listed with its changed-line count.
- Update the worked examples in `levels.md` to match (including a QC-threshold file → CRITICAL).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `code-review`: "Review level selection" now classifies statistics or QC code by category rather than keywords, and states the files that set the level. "Three-seat vote at CRITICAL" defines CONDITIONAL as APPROVE once its required fixes are applied, with one reported outcome.

## Impact

- `skills/magi-review/references/levels.md`: keyword paragraph removed, CRITICAL row reworded, worked examples updated.
- `skills/magi-review/SKILL.md`: step 2 (state the files), step 5 (CONDITIONAL rule), step 6 (report template).
- `openspec/specs/code-review/spec.md` via the delta.
- No hook, scaffold, or template code changes. No README change expected (it doesn't describe levels in this detail); checked during apply.
- Agent behavior (classification, report wording) is checked in the next test run, not by pytests that grep prose.
