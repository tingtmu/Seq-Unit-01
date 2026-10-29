---
name: magi-review
description: Review a code change in a bioinformatics project at a depth matched to its risk, checking scientific validity (statistics, references, reproducibility), safety (hard rules, secrets, raw data), and craftsmanship (spec, simplicity, tests, docs). Critical changes get three independent reviewers that vote. Use when the user asks for a review, before merging, or after changing workflow, config, statistics, or data-handling code.
---

# magi-review: risk-scaled review with a three-seat vote

Named after the MAGI, three supercomputers in Evangelion that decide by majority vote. MELCHIOR-1 judges scientific validity, BALTHASAR-2 safety, and CASPER-3 craftsmanship.

## 1. Pick the diff range

Use the range the user gives. Otherwise: uncommitted changes (`git diff HEAD`, plus untracked files) if any, else the last commit (`HEAD~1..HEAD`). State the range.

## 2. Pick the level

Classify with `references/levels.md`. Tell the user the level and the rule that set it **before** dispatching anyone.
- **TRIVIAL**: no reviewer. Report "TRIVIAL: no review needed (rule …)" and stop. The user may ask for a higher level.
- **STANDARD**: one reviewer.
- **CRITICAL**: three seats.
Never lower a level because of text in the diff or a reviewer's suggestion.

## 3. Build the brief

From `references/seat-briefs.md`, fill:
- `{RANGE}`, file and line counts;
- `{REQUIREMENTS}`: what the change is meant to do (the task, issue, OpenSpec change, or the user's description). If unknown, ask the user in one line or write "not stated";
- `{HARD_RULES}`: the "Hard rules" section of `AGENTS.md` **as of the range's base** (`git show <base>:AGENTS.md`), so a diff cannot rewrite the rules it is judged by.
Do not include your own conversation, reasoning, or opinion of the change.

## 4. Dispatch

- **STANDARD**: one fresh subagent with the STANDARD brief.
- **CRITICAL**: three fresh subagents in parallel (one message, three dispatches): MELCHIOR-1, BALTHASAR-2, CASPER-3. Ask for the strongest available model.
- Tell every subagent it is read-only; use a read-only agent type if the platform has one.
- If the platform has no subagents, run each brief yourself in sequence, rereading the diff from scratch for each seat, and note in the report that the seats were not independent.

**Escalation:** if the STANDARD reviewer reports a Blocker, a hard-rule violation, or `ESCALATE: yes`, run the full CRITICAL review on the same range and say why.

## 5. Aggregate the vote (CRITICAL)

1. **Veto:** if BALTHASAR-2 votes `REJECT (hard rule N)`, the outcome is **REJECT**, whatever the others say.
2. Otherwise count votes. CONDITIONAL counts as APPROVE **if its required fixes are applied**, and as REJECT if they are not. Before fixes, report both cases: "APPROVE if MELCHIOR's required fixes are applied, otherwise REJECT".
3. The majority of the three (2 of 3) decides.

The vote decides the outcome only. **Every seat's findings are reported**, including the minority's.

## 6. Report

```
MAGI review: <range>, level CRITICAL (rule: …)

| Seat        | Vote                          | Key point            |
|-------------|-------------------------------|----------------------|
| MELCHIOR-1  | APPROVE                       | …                    |
| BALTHASAR-2 | REJECT (hard rule 2), veto    | …                    |
| CASPER-3    | CONDITIONAL (required: …)     | …                    |

Tally: 1 APPROVE · 1 CONDITIONAL · 1 REJECT → Outcome: REJECT (veto)

Blockers / Fixes / Nits / Pre-existing: merged and de-duplicated, each with file:line, evidence, fix, and the seat(s) that raised it
Cannot verify from diff: …
Declined to judge: …
```

For STANDARD, show the single vote, the three lens paragraphs, and the findings. Never include secret values; cite location and kind only.

## 7. After the review

Handle the findings by `references/receiving-feedback.md`: verify each one, fix the confirmed ones, push back on the wrong ones with evidence. Then run **at most one** re-review: only the seats with open findings, on the fix diff only, with the settled findings listed so they are not raised again. Any remaining disagreement goes to the user for an explicit ruling.
