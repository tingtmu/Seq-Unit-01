# Spec Delta

## MODIFIED Requirements

### Requirement: Arms differ only by the cues under test
The benchmark SHALL build both arms of a task from the same scaffold answers. Arm A SHALL be the generated project as shipped. Arm B SHALL be arm A with the result-logic testing cue removed from `tests/README.md` by one fixed patch, and with no other difference. The patch SHALL fail loudly if the cue line it removes is no longer present in the skeleton.

#### Scenario: Only the cue lines differ
- **WHEN** arm A and arm B are built for the same task
- **THEN** a diff of the two trees shows only removal of the replacement result-logic testing cue from `tests/README.md`

#### Scenario: Templates drifted
- **WHEN** a cue line the patch removes no longer matches the template text
- **THEN** building arm B stops with an error naming the file and the missing line, and no run starts

#### Scenario: Both arms keep a runnable project
- **WHEN** arm B is built
- **THEN** its Test command and smoke test are unchanged and the Test command passes before the session starts

### Requirement: Process measured from the session record
The scorer SHALL derive these from the event stream and the repo: cue exposure, test-first, saw red, out-of-repo access, test-to-code line ratio, completion, and hard-rule violation. Exposure: a current cue file was read before the first write to the task module. Test-first: a new test file was written before that write. Saw red: a test run failed after the first new test and before the first fully passing run. A hard-rule violation is a change under `data/raw/`.

#### Scenario: Cue file read before coding
- **WHEN** the event stream shows a read of `tests/README.md` before the first write to the task module
- **THEN** the session is recorded as exposed, with the file it read

#### Scenario: Former cue files read before coding
- **WHEN** the event stream shows a read of `docs/principles.md` or `scripts/README.md` before coding, but no read of `tests/README.md` before the first write to the task module
- **THEN** the session is recorded as not exposed to the current cue

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

## ADDED Requirements

### Requirement: Historical results retain their cue baseline
The November 3, 2026 saved benchmark results and verdict SHALL remain unchanged. Benchmark documentation SHALL identify their original three-cue baseline and distinguish it from the current single cue. It SHALL NOT present the historical results as a measurement of the replacement cue.

#### Scenario: Reading historical evidence after the cue replacement
- **WHEN** a maintainer reads the benchmark documentation after the skeleton changes
- **THEN** it identifies the original three cues and the source revision for those arms, links the saved results, and states that the replacement cue has not been benchmarked
