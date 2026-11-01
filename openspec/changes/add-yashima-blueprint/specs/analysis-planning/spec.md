# Spec Delta

## Purpose

Defines what the planning skill promises: before any result answers the scientific question, it removes the fatal risks first and records the agreed analysis plan as a commit, so the plan can be shown to predate the results.

## ADDED Requirements

### Requirement: Invoked for analyses that answer the question
The planning skill SHALL run when the user invokes it, or when the agent offers or starts it before an analysis whose result answers the project's scientific question. It SHALL NOT be offered for engineering work such as refactoring, pipeline plumbing, or environment setup. It SHALL have no automatic trigger beyond its description.

#### Scenario: User invokes the skill
- **WHEN** the user invokes the planning skill for a planned analysis
- **THEN** the skill runs its screening for that analysis

#### Scenario: Agent about to write a differential expression script
- **WHEN** the agent is about to write the first code for an analysis whose result answers the scientific question and no analysis plan for it exists
- **THEN** the agent may offer the planning skill before writing that code

#### Scenario: Engineering task
- **WHEN** the task is a refactor, pipeline plumbing, or environment setup
- **THEN** the planning skill is not offered

### Requirement: Discover before asking
Before asking the user anything, the skill SHALL read what the project can tell it: the project question, the sample sheet, the configuration, the data README, and whether results or notebook outputs for this analysis already exist. It SHALL ask the user only about what these cannot answer.

#### Scenario: Sample sheet already records batch
- **WHEN** the sample sheet has a batch column and a condition column
- **THEN** the skill checks them against each other itself and does not ask the user how samples were batched

### Requirement: Ranked fatal risks
The skill SHALL list the fatal risks for this study: risks that no later code change can fix. It SHALL derive them from the study, using its examples as illustrations, not as a checklist. It SHALL rank them by how surely they would sink the conclusion, list at most 8 with no minimum, name for each the false result it would produce, and stop when the remaining risks can be fixed later.

#### Scenario: Well-designed study
- **WHEN** the design has no fatal risk beyond the order of analysis decisions
- **THEN** the list contains only "analysis decisions fixed before results", and the skill adds no weaker risks to fill it

#### Scenario: Study outside RNA-seq
- **WHEN** the study is not an RNA-seq study, for example a variant association study
- **THEN** the listed risks come from that study's design, not from the RNA-seq example

#### Scenario: Risk that a rerun fixes
- **WHEN** a problem can be fixed by changing code or rerunning, such as a wrong genome build or a missing seed
- **THEN** it is not listed as a fatal risk; it is left to review

### Requirement: Analysis decisions fixed before results
Every list of fatal risks SHALL include "analysis decisions fixed before results": the test or model, the contrast, the thresholds, and the multiple-testing correction are agreed before any result that answers the question is seen.

#### Scenario: Mandatory risk present
- **WHEN** the skill lists fatal risks for any study
- **THEN** "analysis decisions fixed before results" is on the list

### Requirement: Unfixable risks stated plainly
When a fatal risk cannot be removed, such as batch fully confounded with condition, the skill SHALL say plainly what the data cannot show. It SHALL plan only claims that avoid the risk, labelled as such (for example descriptive, or within one batch), and SHALL NOT plan around the risk silently.

#### Scenario: Batch equals condition
- **WHEN** every treated sample is in one batch and every control in another
- **THEN** the skill tells the user that the condition effect cannot be separated from batch, and any plan it records labels its claims as descriptive or within-batch

### Requirement: Confirmatory conclusions only
The analysis plan SHALL cover confirmatory conclusions only. Findings from exploration SHALL be labelled exploratory, or tested under a new analysis plan.

#### Scenario: Pattern found while exploring
- **WHEN** a pattern found in exploratory work is to be reported as a conclusion
- **THEN** it is labelled exploratory or tested under a new analysis plan, not added to the existing plan's conclusions

### Requirement: Plan committed after agreement
Only after the user agrees, the skill SHALL write the analysis plan to the project's docs location and its threshold values under a topic key in the configuration the code reads, using existing locations and creating `docs/` or `config/` only when none exist. It SHALL commit only those paths. The plan SHALL record which results, if any, had been seen when it was written.

#### Scenario: User agrees
- **WHEN** the user agrees to the plan
- **THEN** the skill writes the plan and the thresholds and commits only those paths, leaving any other uncommitted changes out of the commit

#### Scenario: User has not agreed
- **WHEN** the user has not yet agreed to the plan, or the agent cannot write files (for example, in a read-only plan mode)
- **THEN** the skill writes and commits nothing

#### Scenario: Results already seen
- **WHEN** results for this analysis already exist when the plan is written
- **THEN** the plan names which results had been seen, and the skill describes the commit as evidence, not proof, that the plan came first

#### Scenario: Project not set up by nerv-init
- **WHEN** the project already keeps its configuration elsewhere, for example `conf/` in an nf-core project
- **THEN** the thresholds go into that existing configuration, and no new `config/` folder is created

### Requirement: Deviations appended
When an agreed plan changes, the skill SHALL add a dated Deviation entry stating what changed, why, and whether the change was made before or after seeing results. It SHALL NOT rewrite the plan's original text.

#### Scenario: Failed sample excluded after QC
- **WHEN** QC shows a sample must be excluded after the plan was committed
- **THEN** the plan gains a dated Deviation entry giving the exclusion, the reason, and that it was made before or after seeing results, and the original text is unchanged

### Requirement: Handoff to tests and review
After committing the plan, the skill SHALL hand off rather than implement: the thresholds become boundary tests written first (values exactly at each threshold), and the plan is given as the requirements when the analysis code is reviewed with `magi-review`. The skill SHALL NOT write tests or analysis code.

#### Scenario: Plan committed
- **WHEN** the plan commit is made
- **THEN** the skill tells the agent to write boundary tests at the threshold values first and to pass the plan as the requirements to `magi-review`, and it writes no test or analysis code itself
