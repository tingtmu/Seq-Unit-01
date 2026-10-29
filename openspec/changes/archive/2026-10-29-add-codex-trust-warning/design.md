# Design

## Context

`scaffold()` returns `(exit_code, result)`, and `main()` prints `result` as JSON. A created project currently gives `{"status": "created", "files": [...], "git": "..."}`. `nerv-init` SKILL.md step 6 asks the agent to report next steps from a bullet list written in the SKILL.md itself. The scaffold result says nothing about them, so the agent has to remember the list. See proposal.md (Why).

## Goals / Non-Goals

**Goals:**
- The trust step comes from a deterministic place that a test can check.
- The SKILL.md and the script keep one list between them, not two.

**Non-Goals:**
- Finding out whether Codex has actually trusted the hooks.
- Changing the hook scripts, the adapters, or the generated project's files.

## Decisions

**`next_steps` in the scaffold result, not just SKILL.md prose.** The script is the one part of `nerv-init` that tests can run. A `NEXT_STEPS` constant (a tuple of strings, Codex trust step first) is added to the `created` result as a list. *Alternative:* keep the prose and add a test that greps SKILL.md for "/hooks". That would show the text exists, not that the user sees it, and the list would still live only in prose.

**Static text, the same for every project.** None of the steps depend on the interview answers today. The Codex adapter is installed for everyone, so the trust step applies to every project too. *Alternative:* show the step only when the user says they use Codex. That would add a question to the interview, and it fails when someone opens the project in Codex later.

**Codex trust step first.** It is the only step without which a safety feature stays switched off with no warning. The other steps are routine setup.

**SKILL.md says to show the list in full, without shortening it.** Agents tend to shorten summaries, and the clause that says what is off until the hooks are trusted is the part most likely to be cut.

## Risks / Trade-offs

- [Codex changes how hooks are trusted or renames `/hooks`] → Before shipping, check the trust behavior against the Codex source again and record the date in README, as the repo's habits require. The text is in one constant, so it is easy to update.
- [The agent still leaves the step out] → This cannot be enforced against an LLM. Making the step part of the script's output, and telling the agent to show it in full, makes leaving it out less likely.
- [Callers that read the JSON break] → The only caller is the agent following SKILL.md. Adding a key does not affect the existing keys.

## Verification (2026-10-29)

Checked against `openai/codex` main via Context7:
- `codex-rs/hooks/src/engine/discovery.rs`: a discovered hook is registered to run only when its trust status is `Managed` or `Trusted` (or `--dangerously-bypass-hook-trust` is set). Untrusted project hooks are skipped.
- The same file: `hook_trust_status()` compares the hook's hash with the saved trusted state and yields `Trusted`, `Modified`, or `Untrusted`. A change to `.codex/hooks.json` makes the hooks `Modified`, so they must be trusted again.
- `codex-rs/tui/assets/tooltips.txt`: "Use **/hooks** to view and manage lifecycle hooks." `/hooks` is still the command.

The behavior matches the proposal and the spec, so neither changes.
