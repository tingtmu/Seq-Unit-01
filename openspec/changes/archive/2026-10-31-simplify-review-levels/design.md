# Design

## Context

See proposal.md for the motivation. The level rules live in `skills/magi-review/references/levels.md`. The vote and report rules live in `skills/magi-review/SKILL.md` steps 2, 5, and 6. The seat brief (`seat-briefs.md`) already defines CONDITIONAL as "acceptable once the listed required fixes are applied", and `GLOSSARY.md` defines Vote the same way. Only SKILL.md step 5 adds the two-case report.

## Goals / Non-Goals

**Goals:**
- One judgment rule for statistics or QC code, applied the same way every time.
- A level statement that shows which files caused the level.

**Non-Goals:**
- Changing the other CRITICAL rows (paths under `workflow/`, `config/`, `envs/`, `data/`, hook wiring, AGENTS.md/CLAUDE.md), or the TRIVIAL/STANDARD line threshold.
- The other magi-review wording nits (skipping the re-review, naming agent types, marking findings raised by several seats). Those stay in the roadmap "Small skill wording" item.

## Decisions

- **Judge the touched file, not the changed lines.** The rule asks what the touched code under `scripts/` or `notebooks/` does. A 3-line change to a QC-summary script is QC code even if those lines only check a column (M2). Alternative: judge only the changed lines. Rejected, because it is what made M2 borderline.
- **A category, not word-boundary matching.** M2 suggested word-boundary matching or dropping `scale`. Both keep a list that needs tuning per language (R `scale_color_*`, Python `scale`). The category plus "when unsure, CRITICAL" is shorter and fails safe. Trade-off: two agents may still disagree on rare borderline files. The fallback resolves that toward more review, which costs tokens, not correctness.
- **Name the files in the first line.** Format: `level CRITICAL (rule 1: workflow/rules/align.smk)`. For the Markdown line-count rule, list each Markdown file with its changed-line count, for example `level STANDARD (rule 3: Markdown, 62 lines: notes.md 60, docs/README.md 2)`. If many files match, name up to three and give the count of the rest. Alternative: a separate "Files" section. Rejected as extra report shape for one fact.
- **CONDITIONAL is tallied as APPROVE.** The outcome line is followed by "Required fixes: …" naming the seat. If the author declines a required fix, it goes to the user for a ruling, using the path step 7 already has for disagreements. Alternative: keep "APPROVE once applied" and define a separate outcome for before the fixes. Rejected, because that is the two-case report being removed.

## Risks / Trade-offs

- [More changes become CRITICAL, since any edit to a QC or statistics script now qualifies] → Accepted. That is the intent of "when unsure, CRITICAL", and these files decide results.
- [A CONDITIONAL whose fixes are never applied reads as APPROVE] → The report always lists the required fixes, and a declined required fix must go to the user (spec scenario "Required fix declined"). The next test run checks this.
