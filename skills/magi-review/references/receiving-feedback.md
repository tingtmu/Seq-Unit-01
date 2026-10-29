# Receiving review feedback (rules for the author)

The author is the agent (or person) who wrote the change. Review findings are claims to check, not orders.

1. **Verify every finding against the code before acting.** Open the cited file:line, run the cited check or a cheaper one, and decide: correct, partly correct, or wrong.
2. **Push back with evidence when a finding is wrong.** Cite what disproves it (e.g. "`grep -n load_counts scripts/` shows a caller at `scripts/de.R:14`"). Do not change code to satisfy a wrong finding.
3. **No performative agreement.** Do not write "great catch" or "you're right" before verifying. State the verdict and the evidence: "Confirmed: … Fixed in …" or "Rejected: … because …".
4. **Fix what is confirmed, nothing more.** Keep fixes scoped to the finding; no drive-by refactors.
5. **One re-review, scoped.** After fixes, at most one re-review runs, on the fix diff only (`git diff <pre-fix>..<post-fix>`). The re-review brief lists the settled findings; they are not raised again.
6. **Pre-existing findings** are reported to the user, not fixed in this change unless the user asks.
7. **Disagreement after the re-review.** If the author and a reviewer still disagree, do not loop. Present both positions with evidence to the user, who gives an explicit ruling. Record the ruling in the review report.
8. **Hard-rule findings** (BALTHASAR veto) are never dismissed by the author alone; disputing one requires the user's explicit ruling.
