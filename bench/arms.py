"""The two arms of the cue benchmark.

Arm A is the generated project as shipped. Arm B removes exactly these lines, copied
from skills/nerv-init/templates/base. If a template changes, the build stops instead of
silently comparing two identical arms.
"""

ARMS = ("A", "B")

# (path in the generated project, exact line removed in arm B)
CUE_LINES = [
    ("tests/README.md",
     "- For logic that decides results, use tiny synthetic inputs with explicit expected outputs. "
     "Include negative or boundary cases that distinguish the intended rule from a plausible "
     "wrong implementation."),
]
