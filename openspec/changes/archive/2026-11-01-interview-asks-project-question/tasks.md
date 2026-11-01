# Tasks

## 1. Scaffold accepts the question answer

- [x] 1.1 Add `test_question_answer_accepted` to `tests/test_scaffold.py`: scaffold with `answers(question="Which genes respond to drug X in liver?")` and with `question="TBD"`, and assert each returns code 0 with the shared skeleton (`assert_common`). It pins existing behavior, so it passes without code changes; confirm it fails if `validate()` is made to reject unknown keys, then revert that probe. Verify with `.venv/Scripts/python -m pytest tests/test_scaffold.py`.

## 2. Interview and skill prose

- [x] 2.1 In `skills/nerv-init/references/interview.md`: add row 7 (`question`, "In one line, what biological question does this project answer?", one-line text or `TBD`, default `TBD`), add `"question"` to the answers JSON example, and add a `question` row to the answer-to-output table saying the agent writes it into `AGENTS.md` and `README.md`, as `TBD` if unknown. Verify by reading the file: every answers key in the table appears in the JSON example.
- [x] 2.2 In `skills/nerv-init/SKILL.md`: step 1 adds the question default (`TBD`) to the defaults list; step 5 says the `AGENTS.md` and `README.md` question comes from the `question` answer, written as `TBD` when unknown, never invented. Verify `test_skill_docs.py` still passes and the description's first sentence is unchanged.
- [x] 2.3 In the same commit as 2.1–2.2: in `README.md`, add "the project question (or `TBD`)" to the interview list in the `nerv-init` row; in `GLOSSARY.md`, extend the "Interview" definition with the one-line project question, which may be `TBD`. Verify with `grep -n "question" README.md GLOSSARY.md`, which shows both lines.

## 3. Integration

- [x] 3.1 Run the full suite with `.venv/Scripts/python -m pytest`; all tests pass. Run `openspec validate interview-asks-project-question --strict`; it passes.

## Workflow follow-up

- Review gate after apply: commit, then a fresh-context reviewer checks the commit range against AGENTS.md and this change's spec.
- Record in the next test run's notes whether the agent asked the question in the first round and wrote it (or `TBD`) in step 5.
- Archive, then mark the ROADMAP item `done`.
