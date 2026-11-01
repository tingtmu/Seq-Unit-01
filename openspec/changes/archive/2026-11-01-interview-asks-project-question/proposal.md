# Proposal

## Why

`nerv-init` step 5 tells the agent to write "the one-line project question" into `AGENTS.md` and `README.md`, but no interview question collects it. In the first test run (finding 4) the agent had to guess or stop to ask after scaffolding. The interview should collect every answer the flow later needs.

## What Changes

- The interview gains a seventh question: the biological question the project answers, in one line. The answers key is `question`; `TBD` is allowed and is the default.
- `nerv-init` step 5 uses the `question` answer for the `AGENTS.md` and `README.md` prose. When it is `TBD`, the agent writes a visible `TBD` line rather than inventing a question.
- `scaffold.py` is not changed: it already ignores answers keys it does not use. A pytest pins that a `question` key is accepted, so a future stricter validator cannot silently break the interview.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `project-bootstrap`: "Interview before generation" adds the project question (which may be `TBD`) to the interview and says how the agent uses it.

## Impact

- `skills/nerv-init/references/interview.md`: new row 7, `question` in the answers JSON example, and a row in the answer-to-output table.
- `skills/nerv-init/SKILL.md`: step 1 names the `TBD` default; step 5 says where the answer goes.
- `tests/test_scaffold.py`: one test showing that answers with `question` scaffold successfully.
- `README.md`: the `nerv-init` row lists the project question among the interview topics ("README follows behavior").
- `GLOSSARY.md`: the "Interview" definition adds the project question.
- No hook, template, or adapter changes.
