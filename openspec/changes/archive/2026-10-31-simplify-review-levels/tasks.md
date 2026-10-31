# Tasks

## 1. Level rules (`levels.md`)

- [x] 1.1 Reword the statistics CRITICAL row as "statistics or QC code in `scripts/` or `notebooks/` (statistical tests, normalization, clustering, integration, thresholds), judged by what the touched file does; when unsure, CRITICAL". Delete the "Statistics keywords" paragraph. Verify: `grep -n -i "keyword\|padj\|colorscale" skills/magi-review/references/levels.md` finds no keyword list.
- [x] 1.2 Update the line "State the level and the rule that set it" so it also names the files that set the level, using the format in design.md (up to three files, line counts for the Markdown rule). Verify by reading the section against the spec scenario "Files that set the level".
- [x] 1.3 Update the worked examples: the `plot_umap.py` row cites "not statistics or QC code" instead of "no statistics keywords", the `de.R` row cites the category, and add rows for `scripts/qc_summary.py` (3-line column check) → CRITICAL and a notes file + docs edit → STANDARD naming the notes file. Verify each spec scenario in the delta has a matching example row.

## 2. Vote and report (`SKILL.md`)

- [x] 2.1 Step 2: state the level with its rule and the files that set it (point to `levels.md`). Verify that the TRIVIAL message template also names the files.
- [x] 2.2 Step 5: replace the CONDITIONAL rule with "CONDITIONAL is tallied as APPROVE; its required fixes are listed under the outcome" and delete the "report both cases" sentence. Step 7: state that a declined required fix goes to the user for a ruling. Verify: `grep -n "otherwise REJECT\|both cases" skills/magi-review/` returns nothing.
- [x] 2.3 Step 6: change the report template's first line to show the files that set the level, and add a "Required fixes: … (seat)" line under the tally. Verify that the template is consistent with the example in design.md.
- [x] 2.4 Check that `seat-briefs.md`, `GLOSSARY.md` (Vote), and `README.md` still match the new rules, and edit them only if they don't. Verify with `grep -rn "CONDITIONAL\|keyword" skills/ GLOSSARY.md README.md`.

## 3. Integration

- [x] 3.1 Run `.venv/Scripts/python -m pytest` and `openspec validate simplify-review-levels --strict`. Both pass.
- [x] 3.2 Add the M1/M2 scenarios to the next test run's checklist in `../nerv-testrun/` (QC script → CRITICAL, colors-only plot → STANDARD, files named in the level line, single outcome with CONDITIONAL). Verify that the checklist lists them.

## Workflow follow-up

- Run a fresh-context reviewer on the change (this changes what a skill promises).
- Set the roadmap row "magi-review: drop the keyword list" to `done` when archiving.
- `/opsx:verify`, then `/opsx:archive`.
