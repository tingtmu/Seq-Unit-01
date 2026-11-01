# Design

## Context

See proposal.md (Why). Current code:
- `scaffold.py` keeps four entries in `NEXT_STEPS` and inserts `COMMIT_STEP` at index 2 when `git_identity()` returns `missing`.
- `SKILL.md` step 6 commits only when the identity is `set`, and says "Never set or invent an identity yourself".
- `tests/test_scaffold.py` pins the four or five entries, their order, and the commit commands.

This change assumes `add-data-intake` is applied first. That change rewrites the read-only entry to one sentence and makes data intake fill the sample sheet.

## Goals / Non-Goals

**Goals:**
- `next_steps` lists only what the user alone can do, in two short entries.
- A missing identity costs the user one line in their reply to the plan, never a set of commands.

**Non-Goals:**
- Showing only the entry for the agent in use. The scaffold can't tell which agent runs it, and a user may run both (spec: "whichever agent the user runs").
- Detecting whether the hook is live in the current session. Hooks may load only after a restart, so a missing raw snapshot proves nothing.
- Changing `git_identity()`. It stays in the result as the source of truth after `git init`, which covers a repository that already has its own local identity.

## Decisions

### 1. Delete `COMMIT_STEP` instead of moving identity into the scaffold
- **Choice:** the agent sets the identity with two commands after scaffolding (`git config user.name "<typed>"`, then `git config user.email "<typed>"`, run in the project), and then commits.
- **Alternative:** add `git_name` and `git_email` answers that `scaffold.py` validates and writes after `git init`. Rejected. It adds answer keys, validation, and tests to do what two commands already do, and it would leave two ways to set an identity. Deleting `COMMIT_STEP`, `COMMIT_STEP_AFTER`, and the conditional removes code (bar item 5, "deleting counts").
- **Project-only:** the identity is never set with `--global`. It leaves machine config alone and is safe on lab servers where several people share one account.

### 2. When to ask
- **Exploration** (from `add-data-intake`) already runs `git config user.name` and `git config user.email` in the target. In a folder that isn't a repository yet, this reads the global config.
- **Identity set:** the plan names it ("Commit as Nick <nick@…>"), so the user can catch a wrong work or personal identity.
- **Identity missing:** the plan asks for a name and email in the same message, so the user answers once.
- **After `git init`:** the scaffold's `git_identity` is checked again. If it is still `missing` and the user gave a name and email, the agent sets them. If the user gave none, the agent skips the commit and says why in one sentence.

### 3. Final text of the two entries
1. "Turn on the raw-data guard: run `/hooks` in your agent. In Codex, trust the nerv hook (`.nerv/hooks/raw_guard.py`); the guard stays off in Codex until you do, and again after any change to `.codex/hooks.json`. In Claude Code, check that it is listed; if not, restart Claude Code in the project root."
2. The read-only sentence from `add-data-intake`.

### 4. Reference pins and the forward pointer are SKILL.md prose
- **Pins:** filling the reference fields the data states sits in the data-intake step. The empty-field note and the closing "What do you want to compare?" sit in Summarize.
- **Testing:** both are agent behavior, checked in the next test run, not pytested (SCOPE).
- **Self-containment:** the closing line names no other skill (hard rule 1); it only invites the user to say what to compare.

## Risks / Trade-offs

- **The user gives a malformed email.** → The agent repeats back exactly what it set. Git accepts any string, and a wrong one is fixable with one command, so no validation code.
- **An agent that ignores the prose and leaves the repository uncommitted.** → Previously, the next steps still told the user how to commit. Now the summary's one-sentence reason is the only cue. This is accepted: the commit step is already a test-run watch item in ROADMAP.
- **Breaking `next_steps` change for anything that parses entry positions.** → The only consumer is `SKILL.md`, which relays the entries word for word.
