---
name: sync-ratio
description: Check which project folders changed significantly without a matching README update, and draft the README updates. Use when the user asks to sync, refresh, or check folder READMEs/docs, or after a large change in a project set up with nerv-init.
---

# sync-ratio: keep folder READMEs in sync

In Evangelion the sync ratio measures how well pilot and Eva move together; here it measures how well each folder's README matches its contents. The same check runs automatically as a Stop hook; this skill runs it on demand and drafts the fixes.

## Flow

1. From the project root, run the project's copy of the check in report mode:
   ```
   python .nerv/hooks/sync_ratio.py --report
   ```
   (`python3` if `python` is unavailable.) It prints a JSON list of out-of-sync folders, each with `folder`, `readme`, and the changed `files`. An empty list (`[]`) means everything is in sync: say so and stop.
   If `.nerv/hooks/sync_ratio.py` is missing, the project was not set up with nerv-init; tell the user and stop.
2. For each folder, inspect what changed (`git diff HEAD -- <folder>`, and read new untracked files) so the update describes the real change.
3. Draft edits to that folder's README, limited to two sections:
   - **Current state**: what the folder contains or does now.
   - **Last major change**: `YYYY-MM-DD: <one line on what changed and why>`.
   Do not touch Purpose or Conventions. If a change seems to break a Convention, point it out instead of rewriting the Convention.
4. Show all drafts together and ask for approval. Apply only the approved ones.

## Notes

- A change is "major" if a file was added or deleted, or more than 30 lines changed in the folder (`NERV_SYNC_THRESHOLD` overrides). Only top-level folders that have a README.md are checked.
- Report mode never changes the hook's remind-once state.
