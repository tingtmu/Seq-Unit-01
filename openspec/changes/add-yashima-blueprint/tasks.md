# Tasks

## 1. Glossary first

- [ ] 1.1 In `GLOSSARY.md`, add a section "Planning an analysis (`yashima-blueprint`)" with **Analysis plan**, **Fatal risk** ("a risk no later code change can fix"), and **Deviation**, each with an _Avoid_ line (for example, avoid "preregistration" and "blueprint" for Analysis plan, and "blocker" for Fatal risk, since Blocker is a review Finding tag). The section intro states that the skill is named after the Yashima clause in `SCOPE.md` but is not the clause itself (design decision 9). Verify: the terms used in tasks 2.x appear here, and none of them clashes with an existing glossary term.

## 2. The skill

- [ ] 2.1 In `tests/test_skill_docs.py`, add `"yashima-blueprint"` to the parametrized skill lists of `test_skill_frontmatter_states_function_first` and `test_skill_folder_is_self_contained`. Run `.venv/Scripts/python -m pytest tests/test_skill_docs.py` and confirm the new cases fail because the file is missing (red).
- [ ] 2.2 Write `skills/yashima-blueprint/SKILL.md`, about 50 lines and no more than 73, prose only, following `specs/analysis-planning/spec.md` and design decisions 1-8. The frontmatter description's first sentence states the function with no EVA terms, and the second gives the trigger and the engineering-task exclusion. The body covers: discover before asking (including existing results and notebooks); the fatal-risk definition with the three labelled examples; ranking up to 8 with no minimum, the false result named for each risk, the mandatory risk, and the stop rule; unfixable risks; confirmatory scope; write and commit only after agreement, using existing locations, a `<topic>:` key, `git commit -- <paths>`, and the "Results seen" line; Deviation entries; the handoff (boundary tests first, plan passed as `{REQUIREMENTS}` to `magi-review`, no test or analysis code). Do not write the literal `skills/` or `../`. Verify: the full suite `.venv/Scripts/python -m pytest` passes (green), and each requirement in the spec maps to a sentence in SKILL.md.

## 3. README and distribution

- [ ] 3.1 Before touching the install command, re-check the `npx skills add --skill` syntax for several skills against the current `vercel-labs/skills` docs (Context7 or source), per AGENTS.md. Then, in `README.md`: add a `yashima-blueprint` row to the skills table (what it does, and the name: Operation Yashima, one shot, so remove what would make it miss before firing); add `yashima-blueprint` to the `--skill` list on line 22; change "Name the three skills explicitly" to "four"; and update the verification date. Verify: the README matches the `skill-distribution` delta ("the four skills"), and `grep -n "three skills" README.md` finds nothing.

## 4. Roadmap

- [ ] 4.1 In `ROADMAP.md` (local), set the planning skill row to `done` with the change name, mark the decisions taken (design A only, the name `yashima-blueprint`), and add a watch row for test run 4. That row covers: the agent derives study-specific risks with no padding on a clean design; it finds a seeded confounded design and states what the data can't show; it is not offered on engineering tasks; the plan commit contains only its paths; and a later threshold change gets a Deviation entry. Verify by reading the rows.

## Workflow follow-up

- Run the AGENTS.md review gate after propose, after apply, and after archive: tests, a commit, a fresh-context reviewer, and fixes.
- `/opsx:verify`, then `/opsx:archive`. Don't push unless asked.
- After archiving, run test run 4 in a new sibling project, covering this skill and the two existing watch items.
