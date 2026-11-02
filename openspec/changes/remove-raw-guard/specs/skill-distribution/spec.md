# Spec Delta

## MODIFIED Requirements

### Requirement: Self-contained skills
Each skill SHALL contain everything it needs at runtime: its instructions, references, templates, and scripts. It SHALL NOT depend on files elsewhere in this repo.

#### Scenario: Only nerv-init installed
- **WHEN** only the bootstrap skill is copied into a project
- **THEN** it can generate the full skeleton, including the doc-sync report script

## REMOVED Requirements

### Requirement: Single-source hooks with per-agent adapters
**Reason**: The skills no longer ship any agent hook, so there is no hook logic to share and no per-agent adapter to keep thin.
**Migration**: None. If a hook is ever reintroduced, it needs a new change that restates this requirement.
