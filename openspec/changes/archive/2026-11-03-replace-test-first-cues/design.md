# Design

## Context

See `proposal.md` for motivation. Three base skeleton documents hold the original cues. `bench/arms.py` copies their exact lines; the arm-B builder rejects drift, and `bench/score.py` derives exposure paths from that list. Existing scorer fixtures exercise reads of the former cue files. This coupling warrants a design even though the user-facing edit is small.

## Goals / Non-Goals

**Goals:** Keep one source of current cue text per consumer, preserve runnable benchmark arms, and separate historical evidence from current guidance.

**Non-Goals:** No changes to `scaffold.py`, MAGI briefs, or `yashima-blueprint`'s existing boundary-tests-first handoff. The latter is a separate, analysis-specific promise; removing the three skeleton cues does not repeal it. No existing-project migration or new benchmark sessions.

## Decisions

### One bullet in the tests folder README

Use the exact two-sentence replacement in the proposal. Delete the other two cues and replace the third. Retain the adjacent synthetic-input/privacy convention, which also explains fixture placement, plus the existing Goal-driven and Zero-trust review principles. Do not repeat fail-fast advice here; the principles already cover it. This changes the testing expectation without introducing a prescribed implementation sequence.

Keeping all three old cues retains duplication; deletion alone discards an opportunity to address the observed weak distinction. Neither is preferred to one concrete cue.

### Update the existing harness definition

Make `CUE_LINES` contain only the replacement bullet. Its current coupling to `score.CUE_FILES` then makes only `tests/README.md` count toward current exposure, without new configuration or version-selection machinery. Adjust affected scorer assertions/fixtures and retain explicit coverage that reading only either former cue file is not exposure. Keep drift rejection and both arms' smoke tests.

Freezing a second skeleton or adding a historical mode would add maintenance for an experiment the user does not want to repeat. Leaving the old list would break arm-B construction and the current cue-matching test.

### Preserve the historical experiment

Leave `bench/results/2026-11-03/` and archived changes untouched. Document in `bench/README.md` that those results used the three original cues, available at revision `b16b90df1254cc3ec877de97a2b6011a1a202075`, and that current cue definitions/exposure semantics cannot be used to rescore that experiment. Historical reproduction uses that revision. The replacement has not been benchmarked; no grid, pilot, rescoring, or task redesign is part of this change.

### Verify content and harness behavior separately

During apply, inspect generated documents for both scaffold scenario outcomes; do not add pytests that merely grep testing advice or purport to prove agents follow it. For code behavior, adjust benchmark tests before editing the cue definition. Map arm differences, drift rejection, runnable smoke tests, current exposure, and former-file non-exposure to the existing benchmark tests plus focused cases where needed. Verify historical-documentation wording manually and ensure the historical results have no diff. Run the repository pytest suite; it runs deterministic checks, not paid agent sessions. Update README in the implementation commit and local ROADMAP when shipped.

## Risks / Trade-offs

- The replacement may not improve correctness -> describe it as an evidence-informed expectation, with no measured-benefit claim or benchmark prerequisite.
- Removing test-first cues may lose useful behavior on some tasks -> retain meaningful testing guidance and the existing review mechanism, acknowledging this does not establish equal protection.
- Scorer fixtures can silently preserve obsolete exposure semantics -> check both a current cue read and reads of each former cue file.
- Historical arm labels could be confused with current arms -> identify the old revision and cue bundle in benchmark documentation while preserving saved data.

## Migration Plan

Ship the three document edits, harness alignment, and documentation together after tests and review. Only newly generated projects receive the changed guidance. Revert that implementation commit to restore the previous skeleton/harness pair if needed; historical results require no migration.
