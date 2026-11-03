# Spec Delta

## ADDED Requirements

### Requirement: Testing guidance focuses on distinguishing wrong results
The shared skeleton SHALL include one result-logic testing cue in `tests/README.md`: "For logic that decides results, use tiny synthetic inputs with explicit expected outputs. Include negative or boundary cases that distinguish the intended rule from a plausible wrong implementation." It SHALL omit the original red-green-refactor cue in `docs/principles.md`, failing-test-first cue in `scripts/README.md`, and result-logic cue in `tests/README.md`.

#### Scenario: Generated testing guidance
- **WHEN** a project is generated with any supported assay, engine, and language selection
- **THEN** its tests folder README contains the replacement cue once, and its principles and scripts folder README omit the original test-first cues
- **AND** its tests folder README omits the original "Test the logic that decides results: filters, thresholds, statistics." cue

#### Scenario: Testing advice stays flexible
- **WHEN** an agent reads the replacement cue
- **THEN** it finds advice about explicit expected outputs and a negative or boundary case that distinguishes a plausible wrong implementation, with no prescribed test order, coverage target, or mutation-tool requirement
