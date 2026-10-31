# Spec Delta

## MODIFIED Requirements

### Requirement: Review level selection
The review skill SHALL put each change into one level: TRIVIAL, STANDARD, or CRITICAL. The level is based on which paths changed, what the touched files do, and how large the diff is. Changes that touch workflow logic, statistics or QC code, or data handling SHALL be at least CRITICAL. Statistics or QC code SHALL be recognized by what the touched files do, not only the changed lines, and not by matching a keyword list; when unsure, the level SHALL be CRITICAL. The level SHALL be stated to the user before the review starts, together with the rule and the files that set it.

#### Scenario: Docs-only change
- **WHEN** the diff touches only Markdown files outside AGENTS.md and CLAUDE.md, with fewer than 50 changed lines in total
- **THEN** the level is TRIVIAL and no reviewer is dispatched

#### Scenario: Workflow rule change
- **WHEN** the diff modifies a file under `workflow/`
- **THEN** the level is CRITICAL

#### Scenario: QC-threshold code
- **WHEN** the diff changes a script that computes or applies QC thresholds, even if the changed lines name no statistical method
- **THEN** the level is CRITICAL

#### Scenario: Plot styling only
- **WHEN** the diff changes only colors or color scales in a plotting script
- **THEN** the level is not raised to CRITICAL by the statistics rule

#### Scenario: Files that set the level
- **WHEN** an uncommitted 60-line notes file is in the range together with a 2-line docs edit
- **THEN** the level is STANDARD, and the level statement names the notes file and its changed-line count as what set the level

### Requirement: Three-seat vote at CRITICAL
At CRITICAL level, three independent reviewers SHALL run in parallel on the same change, each through one lens: MELCHIOR-1 (scientific validity), BALTHASAR-2 (safety), and CASPER-3 (craftsmanship). Each seat SHALL vote APPROVE, CONDITIONAL, or REJECT, with findings. A CONDITIONAL vote SHALL be tallied as APPROVE, and the report SHALL show one outcome with that seat's required fixes listed. A required fix the author declines SHALL go to the user for a ruling. The outcome SHALL be the majority of the three votes.

#### Scenario: Two approve, one rejects
- **WHEN** MELCHIOR and CASPER vote APPROVE and BALTHASAR votes REJECT without a hard-rule violation
- **THEN** the outcome is APPROVE, and BALTHASAR's findings are still reported

#### Scenario: Vote tally shown
- **WHEN** a CRITICAL review completes
- **THEN** the report shows each seat's vote and the final tally

#### Scenario: Conditional vote decides
- **WHEN** MELCHIOR votes CONDITIONAL, CASPER votes APPROVE, and BALTHASAR votes REJECT without a hard-rule violation
- **THEN** the report shows a single outcome, APPROVE, and lists MELCHIOR's required fixes, without a second "otherwise REJECT" outcome

#### Scenario: Required fix declined
- **WHEN** the author declines a required fix from a CONDITIONAL vote
- **THEN** the disagreement goes to the user for an explicit ruling instead of the vote silently standing as APPROVE
