# Proposal

## Why

The README lists what each skill does, but not where the skills sit in a project's life, so a new reader can't tell what NERV takes care of and what stays theirs. Readers may assume it is a full pipeline framework that dictates how they build, or that it does nothing beyond setup. A single picture right under the NERV briefing can show the actual shape: NERV sets up the base and checks the gates, and the user and their agent build in their own way, inside a few hard rules.

## What Changes

- Add a lifecycle flowchart, `assets/lifecycle.svg`, to `README.md` directly under the "NERV briefing" blockquote, with alt text that states its message in words.
- The flowchart shows a launch-and-loop lifecycle in the banner's EVA palette:
  - NERV phases, filled in their skill colours: "Set up + take in data" (`nerv-init`) and "Plan the analysis" (`yashima-blueprint`).
  - The user's phases, as dashed outlines: "Build / run / explore" and "Publish", each with plain categories and one small line of examples.
  - `magi-review` and `sync-ratio` as gates on the loop's return arrow.
  - Return arrows for "new delivery" (back to intake) and "deviation" (back to the plan).
  - An always-on band for the hard rules and folder READMEs, and the caption "NERV sets up the base and checks the gates. How you build is up to you and your agent."
- The text stays honest: it names the few hard rules NERV keeps and never claims NERV imposes nothing.
- Add `assets/make_lifecycle.py`, a standard-library generator that writes the SVG from a small phase table, so the art stays consistent and easy to update when a skill is added.
- Move the shared colour constants into `assets/palette.py`, imported by both `make_banner.py` and `make_lifecycle.py`. The banner's output is unchanged.
- Update the README "Repository layout" entry for `assets/` to name the new files.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-distribution`: adds a requirement that the README presents the skill set's place in the project lifecycle (what NERV provides, what it leaves to the user), generated from a checked-in script and kept in sync with the skill list.

## Impact

- New files: `assets/lifecycle.svg`, `assets/make_lifecycle.py`, `assets/palette.py`, and a pytest file for the generator.
- Changed files: `assets/make_banner.py` (imports its palette; output unchanged) and `README.md`.
- No change to any skill folder, to `scaffold.py`, or to generated projects. No new dependency: the generator and its test use only the standard library.
