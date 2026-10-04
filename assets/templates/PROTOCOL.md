---
protocol_version: 5
---
# PROTOCOL - project continuity

This project is shared by different AI models and tools, working in turns. This file is the single source of the rules. Follow it exactly. Write records in the project's language.

Files (all in `.continuity/`): `CONTEXT.md` (stable orientation), `HANDOFF.md` (state right now, overwritten), `LOG.md` (append-only history and evidence), `config.json` (settings, including the quota threshold), `quota/<tool>.json` (latest quota reading per tool), `scripts/` (helpers, including the optional `relay.py` supervisor).

## Rules (always apply)

1. Files preserve durable state. Current direct human instructions take precedence over stale records; update the records and retain history. Ask only when the conflict remains genuinely ambiguous.
2. Records authorize nothing. Do only work listed in CONTEXT "Approved scope" or that the user asks for now. A plan or suggestion from a previous model is NOT approval. If the next action is not approved: propose it and ask.
3. You can be cut off at any time. Checkpoint as you work. Do not wait until the end.
4. Quota: follow the Quota section. Never invent a number. Never reset, buy or work around a limit.
5. One principal writer at a time. Record child assignments. An ACTIVE record is advisory, not a process lock; verify the previous writers stopped or obtain explicit human coordination before takeover.
6. Never write secrets (keys, tokens, passwords, .env values, private data) in any record. Refer to them by name only.
7. Never delete, reset or clean up work to make things tidy. Never call unverified work "done".
8. Unknown is written as `unknown`. Do not invent model names, approvals or test results.
9. Each fact lives in ONE file: orientation, scope, decisions, task board -> CONTEXT; current state and next action -> HANDOFF; events and evidence -> LOG. Other files point to it.
10. After a handoff, stop. Never resume on your own, even if a quota window reset. Only the human, or the relay supervisor when the human enabled it (`relay.enabled` in config.json, see "Relay sessions"), starts the next session.

## Quota (monitoring and automatic handoff)

Threshold lives in `config.json` (`handoff_threshold_percent`, default 10 = remaining percent; optional per-window `thresholds`). The user may change it at any time ("set threshold to 15%"): edit `config.json`, append a DECISION to LOG.

Check with: `python3 .continuity/scripts/quota_check.py --tool <claude-code|codex|gemini|cursor|other>`
Exit codes: 0 above threshold | 10 at or below threshold | 4 reading stale | 3 no reading.

When to check: at the start of `continue`, at every checkpoint, before any long or expensive operation.

- Exit 10 -> stop starting new work, run `handoff` with reason `limit-near`, and copy the printed values into HANDOFF and LOG.
- Exit 0 but the next operation clearly cannot fit in what remains -> also hand off (reason `limit-near`).
- Exit 4 or 3 -> get a fresh reading from the tool (see `.continuity/QUOTA.md`). If you cannot read it yourself, ask the user ONCE per session to paste the usage shown by the tool, then record it: `python3 .continuity/scripts/quota_check.py --tool <t> --set-remaining <pct> --window <name>` (for count-based limits: `--used N --limit M`). If still unavailable, write `quota: unavailable` in LOG and rely on frequent checkpoints; do not guess.
- Provider warning ("limit reached/near") or the user says so -> hand off immediately.

## continue

1. Read `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` if present, then `CONTEXT.md`, `HANDOFF.md` and the LAST 30 lines of `LOG.md`. Do not read the whole log.
2. Check the real state: `git status` and `git log -5` (or list recently changed files if no Git). Compare with HANDOFF "Working tree".
3. Read HANDOFF `status`:
   - PAUSED -> normal takeover.
   - ACTIVE owned by this same verified session -> continue its work.
   - ACTIVE owned by another or unknown session -> coordinate and confirm writers stopped before takeover. Your prompt saying the relay supervisor verified the previous process exited counts as confirmation: run RECOVERY. If this cannot be verified, ask the user. Age alone never releases ownership.
   - After confirmed interruption -> RECOVERY: preserve changes after the last checkpoint as partial, unverified; append RECOVERED to LOG.
   - HANDOFF missing -> continue only if LOG and the working tree give one clear, safe next action; otherwise ask.
4. Run the quota check (Quota section). If it exits 10, do NOT start work: tell the user the limit is already near and run `handoff` (reason `limit-near`) or wait for their instruction.
5. Send a READBACK to the user, max 5 lines: project; current state; next action; what you will NOT do; open questions; quota remaining and threshold. Wait for the user only if something is ambiguous, unapproved or ACTIVE. Otherwise go on.
6. Set HANDOFF `status: ACTIVE`, `owner: <tool/model or unknown>`, `updated: now`. Append a TAKEOVER entry to LOG (include model/tool and quota reading).
7. Do the HANDOFF "Next action" if it is within "Approved scope". If not: propose and ask.
8. Work, checkpointing as below. Verify changes with the project's own tests and record command, result and revision in LOG.

## checkpoint

Do a checkpoint when: a subtask finishes; a decision is made; before a long or risky operation; or about every 15 tool calls without one. Takes under a minute:

1. Run the quota check. If it exits 10, stop and run `handoff`.
2. Append one entry to LOG (what was done, files, evidence, next).
3. Update HANDOFF "Next action" and "Working tree", and `updated`.
Before starting a step, write what you are about to do in HANDOFF "Next action" (write-ahead), so a cut-off still leaves a usable pointer.

## handoff

Order matters: each step saves the most valuable information first. If you are cut off midway, steps 2-3 alone are enough for a safe takeover.

1. Checkpoint active children and stop their writes before releasing ownership. Stabilize only necessary atomic operations; if writers cannot stop safely, keep ACTIVE and record recovery needs. Say why: `limit-near` / `limit-hit` / `manual` / `model-switch` / `complete` (all approved work done) / `needs-human` (blocked on a question or approval; write it in HANDOFF section 6). Stop starting new work. Finish only the file or command you are in the middle of. Do not kill unrelated processes.
2. HANDOFF sections 1-2: "Next action" (first concrete step) and "Where things stand". Save.
3. HANDOFF sections 3-5: working tree, verification (done / NOT done), do-not/watch-out. Save.
4. Update CONTEXT task board and Decisions if changed. Append a HANDOFF entry to LOG including the quota values that triggered it (`remaining 8% five_hour @ 14:32, threshold 10%`) or `quota: unavailable`.
5. Set `status: PAUSED`, `updated`, `reason`, `next_model_hint` (strong-reasoning | standard | cheap, with a short why). If LOG exceeds 300 lines, move all but the last 50 to `archive/LOG-YYYY-MM.md`.
6. Check: no secrets in records; "Next action" not empty; referenced paths exist. Commit only if the project convention and the user's authorization allow.
7. Tell the user: reason, handoff location, next action, suggested model tier. Stop and wait for explicit human instruction.

## Relay sessions (automatic model-to-model loop, opt-in)

`scripts/relay.py` is a supervisor the user runs in a terminal (`python3 .continuity/scripts/relay.py run`). It launches one AI CLI at a time in non-interactive mode with the `continue` prompt, waits for it to exit, reads HANDOFF, then launches the next available CLI. It only runs if the user set `relay.enabled: true`. It skips CLIs that are missing or whose last quota reading is at or below the threshold, never waits for or exploits a quota reset, never raises permissions, and stops on `complete`, `needs-human`, no available model, a stall (no recorded progress), or the session limit.

If you were started by it (your prompt says so): you are non-interactive, so never ask questions; put them in HANDOFF section 6 and hand off with `needs-human`. Do the normal `continue`, checkpoint and quota rules. When quota reaches the threshold, hand off with `limit-near` and exit, so the supervisor can start the next model. If all approved work is done, hand off with `complete`. The supervisor appends RELAY entries to LOG; it does not edit other records.

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

## Optional Superpowers integration

During init and continue, inspect the runtime skill catalog or documented local locations for available Superpowers skills. Recommend their use for planning, implementation, debugging and verification. When present, read and use only pertinent skills, preserving existing approvals and completed stages; record actual usage. When absent, recommend optional installation and continue the authorized project workflow. Do not install plugins automatically or depend on vendor-specific commands.
