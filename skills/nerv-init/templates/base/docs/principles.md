# Working principles

These shape how humans and AI agents work in this project. The hard rules are in `AGENTS.md`; these are judgment calls.

## Working with AI agents

- **Plan first, small slices.** State assumptions and a short plan before changing code; deliver in small, verifiable steps.
- **Ask, don't guess.** If a request has several readings, name them and ask.
- **Goal-driven.** Turn each task into a check that proves it worked (a test, a dry run, a known output).
- **Zero-trust review.** Treat generated code as unverified until reviewed (`magi-review`) and tested.
- **Surgical changes.** Touch only what the task needs; don't reformat or refactor unrelated code.

## Classic software engineering

- **Test-driven (red-green-refactor).** Write a failing test on tiny synthetic data, make it pass, then clean up.
- **KISS / YAGNI.** The simplest thing that answers the question; no speculative options or folders.
- **Fail fast.** Validate inputs (sample sheet, config) at the start of a run and stop with a clear message.
- **Never swallow errors.** Friendly message to the user; full context in logs.
- **Boy Scout Rule.** Leave each folder's README as accurate as you found it, or better.
- **DRY, small files.** One fact in one place (reference pins live only in `config/config.yaml`).

## Bioinformatics

- **Reproducibility.** Pinned environments, pinned references, recorded seeds; results only from the workflow.
- **Provenance.** Every raw file has a recorded source and checksum.
- **Statistical honesty.** Decide tests, thresholds, and corrections before looking at results; record them.
