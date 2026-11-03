# Proposal

## Why

The November 3 cue benchmark changed test-first behavior (8/9 first sessions with cues versus 0/9 without), but correctness was near the ceiling and mutant kill rates were mixed. One T2 run missed a distinction despite having a relevant test; replace the three process cues with one concrete expectation about test quality, without claiming a measured improvement.

## What Changes

- Remove the red-green-refactor cue from generated `docs/principles.md` and the failing-test-first cue from generated `scripts/README.md`.
- Replace the result-logic cue in generated `tests/README.md` with one bullet: "For logic that decides results, use tiny synthetic inputs with explicit expected outputs. Include negative or boundary cases that distinguish the intended rule from a plausible wrong implementation."
- Align the benchmark's current cue definition and exposure checks with that one cue, retaining its fail-loudly check for drift. Preserve the historical results and verdict, and document their original three-cue baseline.
- Update user-facing documentation in the implementation commit. Keep the existing review mechanism and analysis-planning handoff unchanged.
- Do not rerun the benchmark grid, redesign its tasks, or introduce tooling, hooks, test-order requirements, or coverage targets.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-bootstrap`: generated testing guidance uses one outcome-focused cue in the tests folder README instead of the three original cues.
- `cue-benchmark`: current arms and exposure measurement use the replacement cue; existing results remain evidence about the original bundle only.

## Impact

Implementation touches three base skeleton documents, `bench/arms.py`, affected benchmark checks/fixtures, `bench/README.md`, and `README.md`. The scorer derives cue files from `arms.CUE_LINES`; this dependency must remain coherent. Existing projects are not migrated. No new dependencies, scaffold API changes, review-brief changes, or changes to archived OpenSpec artifacts are needed. Update the local roadmap when the change ships.
