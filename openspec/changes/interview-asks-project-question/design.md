# Design

## Context

`scaffold.py` `validate()` fills defaults, checks only the keys it uses, and passes any other key through unchanged. `AGENTS.md.tmpl` and `README.md.tmpl` already hold `<!-- nerv: ... -->` comments for the question, and SKILL.md step 5 tells the agent to replace them. The only missing piece is where the answer comes from.

## Goals / Non-Goals

**Goals:** collect the question with the other answers, in the same single interview round, and say how step 5 uses it.

**Non-Goals:** checking the question's quality, asking follow-up questions about it, or changing the dry-run output.

## Decisions

**The agent writes the question in prose; the scaffold does not template it.** The alternative was a `{{QUESTION}}` template variable that `scaffold.py` fills. That needs a code change, a validation rule, and `TBD` handling in two templates, while the agent already rewrites these same lines in step 5. Prose first, per the admission bar. The answer still goes in the answers JSON, so all interview answers live in one record that the agent can refer back to.

**`TBD` is the default, not a required answer.** Many projects start before the question is sharp. Forcing an answer would make the agent push for one or make one up, which is the failure this change fixes. A visible `TBD` in `AGENTS.md` and `README.md` is honest and easy to find later.

**One pytest pins that the key is accepted.** No scaffold code changes, but the interview now depends on `validate()` passing unknown keys through. A test that scaffolds with `question` set guards that dependency. It does not check the prose, because agent behavior is checked in the next test run.

## Risks / Trade-offs

- [The agent ignores the answer in step 5] → step 5 names the `question` key explicitly; check it in the next test run.
- [A stricter validator later rejects `question`] → the new pytest fails first.
