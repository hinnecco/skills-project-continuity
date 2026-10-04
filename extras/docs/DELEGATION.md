# Delegation to cheaper models (optional extra)

Lets the principal model hand routine work to smaller models to save tokens, without lowering quality. It needs no scripts, but the harness must support subagents or model switching, and children may run commands, so it is off by default. To enable it, merge the `delegation` block of `templates/config.extras.json` into `.continuity/config.json` and add the section below to the project's `PROTOCOL.md`.

## Delegation (orchestrating cheaper models)

The principal executor (the model the user started in this harness) may hand bounded work to smaller or cheaper models to save tokens, but only when quality is not compromised. If the harness has no subagents or model switching, do the work inline; that is not a blocker. Use only what the harness actually offers; do not invent commands. Which model fills each tier (`light`, `standard`, `strong`) is declared by the user in `config.json` > `delegation.model_tiers`; if empty, use the harness's own cheaper option and record the model, or `unknown`. A model name alone is not proof of capability, price or availability. `delegation.enabled: false` turns this off; `max_parallel` caps simultaneous children.

1. Good to delegate (light tier): codebase search and reading, summarizing logs or test output, mechanical or repetitive edits, boilerplate, tests for already-specified behavior, formatting, docs from known facts, running commands and reporting results.
2. Keep on the principal (standard/strong tier): ambiguous requirements, architecture and design decisions, security, auth or data-loss-sensitive changes, cross-cutting refactors, debugging with unknown cause, final review and integration, every write to `.continuity/` records, and the handoff.
3. Do not delegate when writing the brief costs about as much as doing the task, or when the task depends on most of the conversation context.
4. Brief every child with: goal; exact files and scope; constraints and "do not touch"; acceptance criteria; how to verify; expected return format (short report plus changed files). Never include secrets.
5. Children stay inside the approved scope, never expand it, never write to `.continuity/` and never run handoff. Parallel writers get disjoint files; otherwise children are read-only.
6. A child's "done" is a claim, not evidence. Before accepting any result, read the diff, run the relevant check and compare against the acceptance criteria. Record each delegation in LOG as a child contribution (child identity/model or unknown, task, result, your verification).
7. Escalate instead of shipping doubt: if a child fails verification or reports uncertainty, retry once with a sharper brief or a higher tier, then do it yourself. Never integrate unverified child work.
8. Quota: children normally draw from the same account window. Run the quota check before dispatching a batch; at the threshold stop dispatching and start `handoff`. Cheaper tiers burn less, but a window is still shared.
9. At handoff, list active and finished delegations in HANDOFF section 3 (what each child changed, verified or not). `next_model_hint` is a different thing: it tells the human which model tier should take over next.

## Delegation by harness

The protocol's Delegation section is harness-agnostic; what each tool offers differs and changes by version, so verify on the installed version before relying on it.

- Claude Code: the principal can dispatch subagents (Agent/Task tool, or custom subagents in `.claude/agents/`) and choose a smaller model per subagent (aliases such as haiku, sonnet, opus). Fill `delegation.model_tiers` accordingly, for example light=haiku, standard=sonnet, strong=opus.
- Codex CLI, Gemini CLI, Cursor: use sub-agents or a model picker only if the installed version offers one; otherwise work inline. Record `unknown` for models you cannot identify.
- Any tool: if you cannot dispatch or identify a child model, do not pretend to; execute inline and keep the quota checks.
