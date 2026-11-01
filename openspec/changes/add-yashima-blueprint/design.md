# Design

## Context

The three existing skills are 27 to 73 lines of prose. A new skill has to follow "HUD, not Dummy Plug" (`SCOPE.md`). It is a cue at the moment of action, carries only the bioinformatics doctrine the agent would otherwise skip, uses prose only, and doesn't repeat `principles.md`. The generated `docs/principles.md` already states the principle: "Statistical honesty. Decide tests, thresholds, and corrections before looking at results; record them". This skill shows what that looks like in practice. Hard rule 1 requires each skill folder to be self-contained, and `test_skill_folder_is_self_contained` flags `../` and `\bskills/` in a skill's files. MELCHIOR-1 already checks "thresholds set in config, not tuned after the fact" (`magi-review/references/seat-briefs.md`), but it has no plan to compare against. Motivation is in proposal.md, and the requirements are in `specs/analysis-planning/spec.md`.

## Goals / Non-Goals

**Goals:**
- One short SKILL.md. It aims for about 50 lines and must not exceed the largest existing skill (73).
- The agent learns a concept (fatal risk) it can apply to any study, not a checklist for one assay.
- Every promise is checkable in a test run. The only code-level checks are the existing frontmatter and self-contained tests.

**Non-Goals:**
- Phases, gates, or a decision-complete plan (design B, rejected). Plan mode, `/opsx:propose`, and grilling skills already cover these.
- A plan template file, a validator, or any script.
- Second-tier risks such as normalization, seeds, or coordinate systems. `magi-review` covers those.
- Writing the analysis code or its tests.

## Decisions

1. **The defining test for a fatal risk is "no later code change can fix it."** This one sentence replaces an assay-specific list and works outside RNA-seq. It deliberately moves *wrong genome build* (listed as fatal in the ROADMAP row) into the fixable tier, because a rerun fixes it. *Alternative considered:* a fixed list of four risks. It was rejected because it ties the skill to RNA-seq.
2. **Three examples from different fields, labelled as illustrations:** bulk RNA-seq batch fully confounded with condition; n=1 per group, or cells treated as replicates; the test or cutoff chosen after seeing results. Each one is a line. The examples cover design, replication, and decision order, and the agent works out the rest. *Alternative considered:* the ancestry example for variant studies. It was dropped in favor of replication, which is the most common fatal risk. The spec's non-RNA-seq scenario still tests a variant study.
3. **Up to 8 risks, no minimum, one mandatory.** A minimum invites padding. Naming the false result each risk would produce makes the user's agreement meaningful without adding a gate. The mandatory risk ("analysis decisions fixed before results") gives the commit something to anchor to.
4. **The plan is a commit, scoped to its paths.** The plan goes in `docs/analysis-plan-<topic>.md`, or the project's existing docs folder. The thresholds go under a `<topic>:` key in the config file the code reads. The skill runs `git add -- <paths>`, then `git commit -m ... -- <paths>`. The add step is needed because a new plan file is untracked, and git rejects a pathspec commit of an untracked file. The pathspec keeps unrelated work, including work the user had already staged, out of the commit. *Alternative considered:* agreement in conversation only. It was rejected because chat leaves no evidence of order. A separate thresholds file was also rejected, since the config is already where code reads parameters (`config/README.md`).
5. **Evidence, not proof.** Commit dates can be rewritten, and results may already exist. Before writing, the skill checks for existing outputs and the git log of results and notebooks, and records "Results seen when written: none / <which>". The best time to run the skill is before the data arrives.
6. **Wording that works on any platform.** "Write only after the user agrees" covers Claude Code's read-only plan mode, Codex, and a plain chat, so the skill needs no platform-specific instructions.
7. **Rules that outlive the session go in the plan.** The skill runs once, but deviations and exploratory findings happen in later sessions. So the plan itself carries two lines: its confirmatory scope, and the first line of a Deviations section stating the append-only rule. A later agent reads the plan and follows it, and nothing has to re-trigger the skill. *Alternative considered:* re-invoking the skill whenever a plan exists. It was rejected because it needs a trigger mechanism and makes the skill own later work.
8. **Hand off to review without changing `magi-review`.** The skill says to pass the plan as `{REQUIREMENTS}` when reviewing the analysis code. That field already exists (`magi-review/SKILL.md` step 3), so no seat-brief or `code-review` spec change is needed. It also keeps the rule that MELCHIOR-1 grows only from incidents. The text names `magi-review` as a skill, not as a path, so the self-contained test still passes.
9. **The description limits the trigger.** The first sentence states the function in plain words: plan an analysis by finding the risks that would invalidate its conclusion before any results exist. The second gives the trigger and the exclusion (not for refactors, pipeline plumbing, or environment setup). That is the only trigger mechanism, so over-triggering is held back by prose rather than code.
10. **Glossary first.** Add **Analysis plan**, **Fatal risk**, and **Deviation** before writing SKILL.md. The section heading names the skill and says it exists because of the SCOPE.md Yashima clause, which is a different thing. Code and specs use only the plain terms.

## Risks / Trade-offs

- [The model rubber-stamps: it lists the mandatory risk and stops on a study that does have a design flaw] → Naming the false result for each risk makes the screening concrete. The behavior is checked in test run 4 on a seeded confounded design.
- [It over-triggers on engineering tasks] → The description excludes them. Test run 4 notes whether the skill is offered during setup or refactoring work.
- [A user changes thresholds silently after the plan, without a Deviation entry] → The rule in the plan makes this unlikely for an agent that reads it, but the skill can't prevent it. MELCHIOR-1 can see it once the plan is passed as the requirements. That is accepted, because hooks are frozen.
- [Generated projects give no cue to use the skill] → `principles.md` names the practice but not the skill. Template changes are out of scope, so the description is the only cue. Test run 4 notes whether the skill is under-triggered.
- [Behavior can't be pytested] → Per AGENTS.md, behavior scenarios are checked in the next test run and recorded in its notes. Pytests cover only the frontmatter and self-containment.
