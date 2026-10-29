# Verification log

Manual checks for tasks whose "Verify" step is not a pytest. Copy into the PR description when publishing.

## 6.1 Level table walkthrough (code-review spec scenarios)

| Spec scenario | Diff | Table rule applied | Level | Matches spec |
|---------------|------|--------------------|-------|--------------|
| Docs-only change | `README.md`, `docs/methods.md` (Markdown, not AGENTS/CLAUDE, < 50 lines) | Rule 1 never matches non-AGENTS Markdown; rule 2 matches | TRIVIAL, no reviewer | yes |
| Workflow rule change | `workflow/rules/align.smk` | Rule 1: non-Markdown under `workflow/` | CRITICAL | yes |
| Blocker found at standard | `scripts/io.py` (no stats keywords) → STANDARD; reviewer reports Blocker | Escalation rule 1 | CRITICAL, three seats on same range | yes |
| Diff edits AGENTS.md | `AGENTS.md` +1 "reviewers must approve" | Rule 1: AGENTS.md | CRITICAL; brief rule 2 makes the line a Blocker finding; hard rules taken from base revision | yes |
| Secret committed | e.g. `config/creds.yaml` | Rule 1: non-Markdown under `config/` | CRITICAL; BALTHASAR hard rule 2 veto | yes |

Edge case resolved during implementation: a Markdown file under a CRITICAL folder (e.g. `workflow/README.md`) is TRIVIAL, because the spec's docs-only scenario covers "only Markdown files outside AGENTS.md and CLAUDE.md" with no folder exception.

## 7.1 Install methods (2026-10-29, scratch dirs)

- `npx skills add <local repo> -a claude-code -a codex --skill nerv-init sync-ratio magi-review --copy -y`: exactly the three skills land in `.agents/skills/` and `.claude/skills/`; nothing in `~/.claude/skills`.
- Deviation found and fixed: `--skill '*'` also installed this repo's OpenSpec dev skills (from `.agents/skills`, `.claude/skills`). The README now names the three skills explicitly.
- Deviation found and fixed: without `--copy`, `.claude/skills/*` are absolute symlinks that break on clone. The README now uses `--copy`.
- Fallback (`git clone` + `cp -r skills/*`) gives the same layout.

## Hook wiring via installed adapter commands (simulated agent events)

Project scaffolded by the *installed* copy of nerv-init (scrnaseq, snakemake, python+r). Hook JSON events were piped into the exact commands from the generated `.claude/settings.json` / `.codex/hooks.json`:

| Step | Result |
|------|--------|
| Both adapter files parse; all commands point to `.nerv/hooks/` | ok |
| New `workflow/rules/qc.smk`, Stop #1 | one `decision: block` naming `workflow/README.md` |
| Stop with `stop_hook_active: true` | silent |
| Stop again, same state | silent |
| `sync_ratio.py --report` | lists `workflow/` with `workflow/rules/qc.smk` |
| Claude `Edit` on existing `data/raw/S1_R1.fastq.gz` | `permissionDecision: ask` |
| Codex `Bash rm data/raw/...` | `permissionDecision: deny` with manual instructions |
| Codex Stop | same block output |

## In-agent runs (2026-10-29, user-approved headless `claude -p` / `codex exec`)

Fresh scratch dir: `npx skills add ... --copy` installed the three skills, then the steps below ran.

| Task | Step | Result |
|------|------|--------|
| 4.4 | `/nerv-init` | Asked all six questions with Snakemake as the default, and wrote nothing. Answers (tumor-sc, scrnaseq, snakemake, python+r): it ran the dry run and showed the tree and add-ons, wrote nothing, and waited. On "yes" it scaffolded and filled every `<!-- nerv -->` placeholder. AGENTS.md is 39 lines and CLAUDE.md is `@AGENTS.md`. Pass. |
| 3.1 / 7.2 | Agent adds `workflow/rules/qc.smk`, then stops | Exactly one Stop-hook reminder naming `workflow/README.md`. The agent declined to update the README (out of scope) and was allowed to stop. Pass. |
| 3.1 / 7.2 | Agent edits existing `data/raw/S1_R1.fastq` | First try: the agent refused on its own because of the AGENTS.md hard rule (defense in depth). With an explicit "attempt once", the PreToolUse hook returned `ask`. Headless mode turned that into a permission denial with the hard-rule message. Checksum unchanged. Pass (headless can't show the interactive prompt). |
| 5.1 | Add `scripts/01_qc.py`, run `/sync-ratio` | Drafted `scripts/README.md` (and `workflow/README.md`) edits limited to Current state and Last major change, then waited for approval. Pass. |
| 6.3b | Docs-only diff (`docs/README.md` +2), `/magi-review` | "TRIVIAL: no review needed (rule 2)", 0 reviewer dispatches. Pass. |
| 6.3a / 7.2 | Untracked `scripts/fetch_counts.py` with a fake `sk_live_` token, `/magi-review` | STANDARD (rule 3). The reviewer reported a hard-rule Blocker, so it escalated to CRITICAL with MELCHIOR-1, BALTHASAR-2 and CASPER-3 dispatched. Tally table shown: 3 REJECT, BALTHASAR marked veto, outcome REJECT. All seats' findings listed with file:line, evidence and fix. The token value appears in no agent text or seat report. Pass. |

### Deviations found and fixed

- `config/README.md` promised sample-sheet checks that `common.smk` did not do. `common.smk` now checks required columns, duplicate IDs, and that the listed FASTQ files exist (5 cases exercised); the README wording now matches. ("Unknown columns" was dropped: extra columns such as `patient_id` are legitimate.)
- The scrnaseq add-on said the clustering settings live in `config/config.yaml`, which has no such block. The text now says to add a `clustering:` block.
- **Codex silently skips untrusted project hooks.** `codex exec` ran only the user's globally trusted hooks; ours never ran (confirmed with an input logger), and a raw-file `apply_patch` succeeded. The README, nerv-init SKILL.md and the adapter description now say to trust the hooks via `/hooks`, and that the guard is off until then.

### Known behavior (not changed)

- When a skill ends a turn while waiting for approval (`/sync-ratio` drafts) or after a review, the Stop hook can add one extra reminder turn for the same folders. This is within spec (once per state) but slightly redundant.

### 3.2 Codex with project hooks trusted (2026-10-29, codex-cli 0.165.0)

Root cause of the earlier miss: trusting the project folder doesn't enable project hooks. The user enabled them per directory via `/hooks`. After that, `~/.codex/config.toml` gained `[hooks.state.'<e2e>\.codex\hooks.json:{pre_tool_use,post_tool_use,stop}:0:0']` entries with `trusted_hash`. The adapter file didn't need any change.

| Step | Result |
|------|--------|
| Before trust: `codex exec --sandbox workspace-write`, `apply_patch` ACGT→TTTT on `data/raw/S1_R1.fastq` | Only the global (Orca) hooks fired, and the patch went through (sha256 `8add5b3b…` → `d2e3761d…`). File restored from a backup. This confirms the documented "guard off until trusted" behavior. |
| After trust: same prompt | PreToolUse blocked: "Blocked: this would modify or delete existing raw data (data/raw/S1_R1.fastq) … tell them the exact command…". sha256 unchanged (`8add5b3b…`). Pass. |
| After trust: agent creates `workflow/rules/codex_qc.smk`, then stops | The Stop hook blocked once with the doc-sync reminder naming `workflow/ -> update workflow/README.md`. The second stop was silent. Pass. |
