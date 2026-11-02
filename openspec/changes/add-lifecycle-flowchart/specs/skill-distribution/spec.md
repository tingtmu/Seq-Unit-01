# Spec Delta

## ADDED Requirements

### Requirement: Lifecycle overview in the README
The repo README SHALL show, directly under the NERV briefing, a picture of a sequencing project's lifecycle. The picture SHALL mark which phases each skill serves and which phases are left to the user and their agent. Every skill in the skill set SHALL appear in it. The image SHALL have alt text that states the same message in words.

#### Scenario: Every skill is placed
- **WHEN** the skill set contains a skill
- **THEN** that skill's full name appears as drawn text in the lifecycle picture, not only in its title or description

#### Scenario: Placed under the briefing
- **WHEN** a reader opens the README
- **THEN** the lifecycle picture follows the NERV briefing, comes before Quick start, and has non-empty alt text

### Requirement: Honest scope in the lifecycle overview
The lifecycle picture SHALL say that a few hard rules and the folder READMEs apply in every phase. It SHALL NOT claim that NERV imposes nothing on how the user builds. Examples in the user's phases SHALL NOT name a tool or layout that the skill set has deferred, so readers don't take it as supported.

#### Scenario: Rules stated, not hidden
- **WHEN** a reader looks at the user's phases in the picture
- **THEN** the picture also shows that the hard rules and folder READMEs apply there, and the caption describes NERV as setting up the base and checking the gates

#### Scenario: A skill is shown only where it acts
- **WHEN** a phase recurs in a generated project without the skill (such as a later delivery, which follows the project's `data/README.md`)
- **THEN** the picture does not route that recurrence back through the skill

#### Scenario: No deferred layout as an example
- **WHEN** the skill set has deferred support for a layout (such as nf-core)
- **THEN** the picture does not list it as an example of what the user brings

### Requirement: Reproducible README art
The lifecycle picture SHALL be produced by a script checked into the repo that needs only the Python standard library. The committed picture SHALL match the script's output.

#### Scenario: Committed picture is current
- **WHEN** the script is run on a fresh clone
- **THEN** its output matches the committed picture, ignoring line-ending differences
