# Tasks

## 1. Replace the cues and align their consumers

- [ ] 1.1 Before editing the current cue definition, adjust the benchmark tests/fixtures for the single replacement cue, current exposure, and non-exposure when only either former cue file was read. Map the three arm-building scenarios to `test_arms_differ_only_by_cue_lines`, `test_cue_drift_stops_build`, and `test_arm_b_test_command_passes`; verify the affected assertions fail for the intended old-definition mismatch rather than unrelated setup errors. Retain existing checks for unchanged process measures.
- [ ] 1.2 Delete the principles and scripts test-first cues, replace the third cue with the exact two-sentence bullet in the proposal, and make `bench/arms.py` define only that replacement. Verify the focused benchmark tests pass, arm B still rejects cue drift, and no new scorer configuration or scaffold API is introduced.
- [ ] 1.3 Generate a disposable project and inspect its documents against both `project-bootstrap` delta scenarios: replacement once in the tests folder README, original three cues absent, explicit expected outputs and negative-or-boundary advice without a test-order mandate. Record the inspection outcome in implementation notes; use existing scaffold coverage for supported selections rather than adding prose-grep pytests or claiming agent compliance.
- [ ] 1.4 In the same implementation commit, update `README.md` to explain the current generated testing guidance and describe the benchmark as historical evidence about the original bundle. Update `bench/README.md` with the original three cues, source revision `b16b90df1254cc3ec877de97a2b6011a1a202075`, links to saved results, and the unbenchmarked status of the replacement. Verify the historical-documentation scenario manually and confirm no diff under `bench/results/2026-11-03/` or archived changes.

## 2. Integration and review

- [ ] 2.1 Run `.venv/Scripts/python -m pytest` and `openspec validate replace-test-first-cues --strict`; confirm both pass. Do not run a benchmark pilot, grid, rescoring, or task redesign, and do not require a future benchmark as an acceptance gate.
- [ ] 2.2 Follow the repository's apply review gate: commit only this change's paths with the repo-local identity and a Co-Authored-By line, request a fresh-context reviewer for that commit range and applicable rules/specs, verify important findings, and commit any confirmed fixes. Verify the resulting review has no unresolved important findings; preserve unrelated user files and do not push.

## Workflow follow-up

- Run the verify workflow before archiving.
- Update the local ROADMAP item when the change ships; do not mark it shipped during planning.
- Archive only after verification, then perform the repository's post-archive test/commit/fresh-context review gate.
