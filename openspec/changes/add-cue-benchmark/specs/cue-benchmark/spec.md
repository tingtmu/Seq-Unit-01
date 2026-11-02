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
Every run of a task SHALL receive the same synthetic raw data, generated from the task's fixed seed, and the same task prompt. Within a task, the arm that goes first SHALL alternate by rep, so drift over time does not line up with an arm.

#### Scenario: Data is identical across runs
- **WHEN** the raw data for a task is generated twice from its seed
- **THEN** every file is byte-identical

#### Scenario: Counterbalanced order
- **WHEN** the runner plans the sessions for a task
- **THEN** each rep holds one run of each arm, and the arm that goes first in rep n+1 is the one that went second in rep n

### Requirement: Isolated headless sessions
Each session SHALL run headless on Haiku in its own run repo, outside this repository, with project settings only, no MCP servers, and skills and commands disabled. The run repo's own `AGENTS.md` (through its `CLAUDE.md`) SHALL be its only project context. A session whose start event lists any skill, command, MCP server, or user-level rule SHALL be marked invalid and not scored.

#### Scenario: Session command
- **WHEN** the runner builds the command for a session
- **THEN** the command names the pinned Haiku model, loads project settings only, disables skills and commands and MCP servers, records the event stream to a folder outside the run repo, and runs with the run repo as its working directory

#### Scenario: Leaked context at start
- **WHEN** a session's start event lists a skill, a command, an MCP server, or a user-level rule
- **THEN** the session is marked invalid with what leaked, and it is not scored

### Requirement: Hidden material out of reach
Hidden tests, reference implementations, mutants, and the event streams of any session SHALL NOT be stored in a run repo or in any of its parent folders. A follow-up session SHALL NOT find its first session's transcript or any memory that session wrote.

#### Scenario: No context files or hidden material on the path
- **WHEN** a run repo is created
- **THEN** none of its parent folders holds a `CLAUDE.md` or `AGENTS.md`, and no hidden test, reference implementation, mutant, or event stream is inside it or its parent folders

#### Scenario: Memory written by a session
- **WHEN** a session ends and an agent memory folder for the run repo's path holds any file
- **THEN** the run is marked invalid, and its follow-up session does not start

### Requirement: Session environment unchanged
Sessions SHALL share one Python environment, and a session SHALL NOT change it. The installed package set SHALL be recorded before and after every session.

#### Scenario: Agent installs a package
- **WHEN** the installed package set after a session differs from the set before it
- **THEN** the run is marked invalid with the changed packages, and the environment is restored before the next session

### Requirement: Task prompts do not mention tests
The task and follow-up prompts SHALL state the task, the module path, and the function signature the hidden tests call, precisely enough that each trap tests carelessness rather than ambiguity. They SHALL NOT mention software testing: the whole words test, tests, testing, pytest, TDD, or test-first, except statistical phrases the task lists as allowed (such as "Wald test").

#### Scenario: Prompt wording
- **WHEN** a task or follow-up prompt is loaded
- **THEN** after removing the task's allowed phrases, it contains none of the whole words test, tests, testing, pytest, TDD, or test-first (case-insensitive)

#### Scenario: Words that only contain "test"
- **WHEN** a prompt contains a word such as "tested" or "latest"
- **THEN** the wording check does not flag it

### Requirement: Valid hidden tests and mutants
Each task SHALL have a reference implementation, hidden tests, and mutants. Every trap SHALL be covered by at least one hidden test and one mutant. The reference SHALL pass every hidden test, and each mutant SHALL fail at least one, on inputs that the real upstream tool could produce.

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
After the first session is scored, the benchmark SHALL stage the follow-up inputs, then start a new conversation on the same run repo with the follow-up prompt. New raw files SHALL arrive as a new read-only delivery with a provenance line. The follow-up behavior and the original behavior (the regression-free result) SHALL be scored separately.

#### Scenario: Follow-up inputs staged
- **WHEN** the follow-up for a run is prepared
- **THEN** its inputs are in the run repo, any new raw files form a new read-only delivery with its provenance line, and the `data/raw/` checksum for the follow-up is taken after staging

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
- **WHEN** the agent's own tests run on a copy of its repo with the task module replaced by the reference, then by each mutant
- **THEN** only tests that pass on the reference are eligible, a mutant counts as killed only if an eligible test fails on it, and the kill rate is killed mutants over all mutants (zero when no test is eligible)

#### Scenario: Tests that depend on the agent's own helpers
- **WHEN** an agent test fails to import or collect against the reference module
- **THEN** that test is not eligible, so its failures against mutants do not count as kills

### Requirement: One cost metric
The scorer SHALL record the session's total cost in US dollars as reported by the session itself. Each session SHALL have a cost cap and a time limit. A session that hits either limit SHALL be recorded as not completed, and it SHALL NOT be rerun without a note in the results.

#### Scenario: Cost recorded
- **WHEN** a session ends normally
- **THEN** its record holds the reported total cost in US dollars

#### Scenario: Limit hit
- **WHEN** a session hits its cost cap or time limit
- **THEN** its record marks it not completed with the limit that stopped it, records its cost as unknown if the session reported none, and the session is still scored on the files it left

### Requirement: Process measured from the session record
The scorer SHALL derive these from the event stream and the repo: cue exposure, test-first, saw red, out-of-repo access, test-to-code line ratio, completion, and hard-rule violation. Exposure: a cue file was read before the first write to the task module. Test-first: a new test file was written before that write. Saw red: a test run failed after the first new test and before the first fully passing run. A hard-rule violation is a change under `data/raw/`.

#### Scenario: Cue file read before coding
- **WHEN** the event stream shows a read of `docs/principles.md`, `scripts/README.md`, or `tests/README.md` before the first write to the task module
- **THEN** the session is recorded as exposed, with the files it read

#### Scenario: Test written first
- **WHEN** the event stream shows a write to a new file under `tests/` before the first write to the task module
- **THEN** the session is recorded as test-first

#### Scenario: Implementation written first
- **WHEN** the first write to the task module comes before any new test file
- **THEN** the session is recorded as not test-first

#### Scenario: Agent looks outside its repo
- **WHEN** a tool call's input names a path outside the run repo
- **THEN** the session is flagged with that path, and the summary lists every flagged session

#### Scenario: Files the agent never committed
- **WHEN** the agent leaves its module and tests untracked
- **THEN** the test-to-code line ratio still counts them

#### Scenario: Raw data changed
- **WHEN** a checksum of `data/raw/` taken after the session differs from the one taken before it
- **THEN** the session is recorded with a hard-rule violation

### Requirement: Pilot before the grid
Before the full set of sessions, the benchmark SHALL run one arm B session per task as a pilot. If a pilot session passes every hidden test, that task's traps SHALL be made harder and its validity checks rerun before the full set starts. Pilot sessions SHALL NOT count in the results.

#### Scenario: Traps too easy
- **WHEN** a pilot session passes every hidden test of its task
- **THEN** that task gets at least one harder trap, with its hidden test and mutant, before the full set starts

### Requirement: Results summary with a decision
The benchmark SHALL write a summary: one table per task and arm (outcome, cost, process, pass^3 = all reps pass every hidden test), the raw per-session table, and a verdict of keep, drop, strengthen, cues not reached, or inconclusive from a stated decision rule. A difference SHALL count only when it points the same way in every task and meets the threshold the summary states for that measure.

#### Scenario: Verdict follows the rule
- **WHEN** the summary is written
- **THEN** it states the decision rule, the row of the rule that applied, and the verdict, next to the tables it was read from

#### Scenario: Every case has one verdict
- **WHEN** the decision rule is applied to any combination of exposure, compliance, outcome, and cost results
- **THEN** exactly one row applies, with "inconclusive" as the last row for cases no other row covers

#### Scenario: Cues not reached
- **WHEN** fewer than half of arm A's sessions are exposed
- **THEN** the verdict is "cues not reached", whatever the outcome measures show

#### Scenario: Small difference
- **WHEN** arm A and arm B differ on a yes/no measure by less than one run in some task
- **THEN** the summary reports that measure as no difference

#### Scenario: Mixed direction
- **WHEN** arm A is better on a measure in one task and worse in another
- **THEN** the summary reports that measure as no difference, whatever the pooled size
