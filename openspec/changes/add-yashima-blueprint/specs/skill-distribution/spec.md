# Spec Delta

## MODIFIED Requirements

### Requirement: Project-level installation
The skill set SHALL be installable into one project with a single `npx skills add tingtmu/Seq-Unit-01` command. The repo README SHALL document a fallback that copies the files without Node. Installation SHALL NOT require a global install.

#### Scenario: Install via skills CLI
- **WHEN** a user runs the documented install command in an empty project directory
- **THEN** the four skills are available to the agent in that project only

#### Scenario: Fallback install
- **WHEN** a user without Node follows the documented fallback
- **THEN** the same skill files end up in the project's agent skill directories
