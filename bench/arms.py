"""The two arms of the cue benchmark.

Arm A is the generated project as shipped. Arm B removes exactly these lines, copied
from skills/nerv-init/templates/base. If a template changes, the build stops instead of
silently comparing two identical arms.
"""

ARMS = ("A", "B")

# (path in the generated project, exact line removed in arm B)
CUE_LINES = [
    ("docs/principles.md",
     "- **Test-driven (red-green-refactor).** Write a failing test on tiny synthetic data, "
     "make it pass, then clean up."),
    ("scripts/README.md",
     "- Before writing code that decides results (filters, thresholds, joins, sample-sheet checks), "
     "write a failing test first; see `tests/README.md`. Exploratory notebooks are exempt until "
     "their code moves here."),
    ("tests/README.md",
     "- Test the logic that decides results: filters, thresholds, statistics."),
]
