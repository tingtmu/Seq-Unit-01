# Spec Delta

## Purpose

Measures whether a set of template cues in a generated project changes what an agent does and how correct, reliable, and costly its work is. It compares two arms that differ only by those cues, so the skill set can keep, drop, or strengthen them on evidence.

## ADDED Requirements

### Requirement: Arms differ only by the cues under test
The benchmark SHALL build both arms of a task from the same scaffold answers. Arm A SHALL be the generated project as shipped. Arm B SHALL be arm A with the test-first cues removed by one fixed patch, and with no other difference. The patch SHALL fail loudly if a cue line it removes is no longer present in the templates.

#### Scenario: Only the cue lines differ
- **WHEN** arm A and arm B are built for the same task
- **THEN** a diff of the two trees shows only the removed cue lines: the red-green-refactor line in `docs/principles.md`, the failing-test-first line in `scripts/README.md`, and the "test the logic that decides results" line in `tests/README.md`

#### Scenario: Templates drifted
- **WHEN** a cue line the patch removes no longer matches the template text
- **THEN** building arm B stops with an error naming the file and the missing line, and no run starts

#### Scenario: Both arms keep a runnable project
- **WHEN** arm B is built
- **THEN** its Test command and smoke test are unchanged and the Test command passes before the session starts

### Requirement: Same inputs in both arms
Every run of a task SHALL receive the same synthetic raw data, generated from the task's fixed seed, and the same task prompt. Runs of the two arms SHALL be started in interleaved order, so drift over time does not line up with an arm.

#### Scenario: Data is identical across runs
- **WHEN** the raw data for a task is generated twice from its seed
- **THEN** every file is byte-identical

#### Scenario: Interleaved order
- **WHEN** the runner plans the sessions for a task
- **THEN** no two consecutive sessions of that task come from the same arm, unless only one arm remains

### Requirement: Isolated headless sessions
Each session SHALL run headless on Haiku in its own run repo, outside this repository. The run repo's own `AGENTS.md` (through its `CLAUDE.md`) SHALL be its only project context: no context files in its parent folders, no user-level rules, and no skills installed. Hidden tests, reference implementations, and mutants SHALL NOT be stored in the run repo or in any of its parent folders.

#### Scenario: Session command
- **WHEN** the runner builds the command for a session
- **THEN** the command names the pinned Haiku model, loads project settings only, records the event stream, and runs with the run repo as its working directory

#### Scenario: No context leaks into a run
- **WHEN** a run repo is created
- **THEN** none of its parent folders holds a `CLAUDE.md` or `AGENTS.md`, and no hidden test, reference implementation, or mutant is inside it or its parent folders

### Requirement: Task prompts do not mention tests
The task and follow-up prompts SHALL state the task, the module path, and the function signature the hidden tests call, precisely enough that each trap tests carelessness rather than ambiguity. They SHALL NOT mention tests, TDD, or test-first.

#### Scenario: Prompt wording
- **WHEN** a task or follow-up prompt is loaded
- **THEN** it contains no mention of tests, testing, TDD, or test-first (case-insensitive)

### Requirement: Valid hidden tests and mutants
Each task SHALL have a reference implementation, hidden tests, and mutants. Every trap SHALL be covered by at least one hidden test and one mutant. The reference SHALL pass every hidden test, and each mutant SHALL fail at least one.

#### Scenario: Reference passes
- **WHEN** a task's hidden tests run against its reference implementation
- **THEN** every hidden test passes

#### Scenario: Each mutant is caught by the hidden tests
- **WHEN** a task's hidden tests run against each of its mutants
- **THEN** each mutant fails at least one hidden test

#### Scenario: Every trap is covered
- **WHEN** the task's trap list is compared with its hidden tests and mutants
- **THEN** each trap names at least one hidden test and one mutant

### Requirement: Follow-up session on the same repo
After scoring the first session, the benchmark SHALL start a follow-up session in a new conversation on the same run repo with the task's follow-up prompt. It SHALL then score the follow-up behavior and, separately, the original behavior, as the regression-free result.

#### Scenario: Regression scored separately
- **WHEN** a follow-up session ends
- **THEN** the record holds the pass rate of the follow-up hidden tests and, separately, whether every hidden test for the original behavior still passes

### Requirement: Outcome measured per session
The scorer SHALL record per session: the hidden-test pass rate overall and per trap, whether the result is silent-wrong, and the mutant kill rate of the agent's own tests. Silent-wrong means the function returns without error and with the documented output shape, but at least one hidden value test fails.

#### Scenario: Silent-wrong result
- **WHEN** the agent's function returns output of the documented shape and a hidden value test fails
- **THEN** the session is recorded as silent-wrong

#### Scenario: Crash is not silent-wrong
- **WHEN** the agent's function raises on valid input
- **THEN** the session is recorded as failing that hidden test, not as silent-wrong

#### Scenario: Mutant kill rate
- **WHEN** the agent's own tests run on a copy of its repo with the task module replaced by a mutant
- **THEN** that mutant counts as killed only if a test that passed on the agent's own code fails, and the kill rate is killed mutants over all mutants (zero when the agent wrote no tests)

### Requirement: One cost metric
The scorer SHALL record the session's total cost in US dollars as reported by the session itself. Each session SHALL have a cost cap and a time limit. A session that hits either limit SHALL be recorded as not completed, and it SHALL NOT be rerun without a note in the results.

#### Scenario: Cost recorded
- **WHEN** a session ends normally
- **THEN** its record holds the reported total cost in US dollars

#### Scenario: Limit hit
- **WHEN** a session hits its cost cap or time limit
- **THEN** its record marks it not completed with the limit that stopped it, and the session is still scored on the files it left

### Requirement: Process measured from the session record
The scorer SHALL derive the session's process measures from its event stream and repo: test-first, saw red, the ratio of test lines to code lines added, completion, and hard-rule violation. Test-first means a new test file was written before the first write to the task module. Saw red means a test run failed after the first new test was written and before the first fully passing test run. A hard-rule violation means a file under `data/raw/` changed.

#### Scenario: Test written first
- **WHEN** the event stream shows a write to a new file under `tests/` before the first write to the task module
- **THEN** the session is recorded as test-first

#### Scenario: Implementation written first
- **WHEN** the first write to the task module comes before any new test file
- **THEN** the session is recorded as not test-first

#### Scenario: Raw data changed
- **WHEN** a checksum of `data/raw/` taken after the session differs from the one taken before it
- **THEN** the session is recorded with a hard-rule violation

### Requirement: Pilot before the grid
Before the full set of sessions, the benchmark SHALL run one arm B session per task as a pilot. If a pilot session passes every hidden test, that task's traps SHALL be made harder and its validity checks rerun before the full set starts. Pilot sessions SHALL NOT count in the results.

#### Scenario: Traps too easy
- **WHEN** a pilot session passes every hidden test of its task
- **THEN** that task gets at least one harder trap, with its hidden test and mutant, before the full set starts

### Requirement: Results summary with a decision
The benchmark SHALL write a summary with one table per task and arm (outcome, cost, process, and pass^3, which is whether all reps pass every hidden test), the per-session raw table, and a verdict of keep, drop, or strengthen from a stated decision rule. A difference SHALL count only when it points the same way in every task and meets the threshold the summary states for that measure; otherwise it is no difference.

#### Scenario: Verdict follows the rule
- **WHEN** the summary is written
- **THEN** it states the decision rule, the row of the rule that applied, and the verdict, next to the tables it was read from

#### Scenario: Small difference
- **WHEN** arm A and arm B differ on a yes/no measure by less than one run in some task
- **THEN** the summary reports that measure as no difference

#### Scenario: Mixed direction
- **WHEN** arm A is better on a measure in one task and worse in another
- **THEN** the summary reports that measure as no difference, whatever the pooled size
