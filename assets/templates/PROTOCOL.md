---
protocol_version: 7
---
# PROTOCOL - project continuity

This project is shared by different AI models and tools, working in turns. This file is the single source of the rules. Follow it exactly. Write records in the project's language.

Files (in `.continuity/`): `CONTEXT.md` (stable orientation), `HANDOFF.md` (state right now, overwritten), `LOG.md` (append-only history and evidence), `config.json` (settings, including the quota threshold).

## Rules

1. Current direct human instructions take precedence over stale records; update the records and keep history. Ask only when a conflict stays genuinely ambiguous.
2. Records authorize nothing. Do only work listed in CONTEXT "Approved scope" or that the user asks for now. A previous model's plan or suggestion is NOT approval. If the next action is not approved: propose it and ask.
3. You can be cut off at any time. Checkpoint as you work; do not wait until the end.
4. Quota: follow the Quota section. Never invent a number. Never reset, buy or work around a limit.
5. One writer at a time. HANDOFF `status: ACTIVE` is advisory, not a lock: before taking over, confirm the previous writer stopped. Age alone never releases it.
6. Never write secrets (keys, tokens, passwords, .env values, private data) in records. Refer to them by name.
7. Never delete, reset or clean up work to look tidy. Never call unverified work "done".
8. Unknown is written `unknown`. Do not invent model names, approvals or test results. Timestamps come from the system clock (`date '+%Y-%m-%d %H:%M %z'`), never from memory.
9. Each fact lives in ONE file: orientation, scope, decisions, task board -> CONTEXT; current state and next action -> HANDOFF; events and evidence -> LOG. Other files point to it.
10. After a handoff, stop. Never resume on your own, even if a quota window reset. Only the human, or an automated runner the human explicitly enabled, starts the next session.

## Quota and the handoff threshold

The threshold is `handoff_threshold_percent` in `config.json` (remaining percent, default 10). The user can change it any time ("set the threshold to 15%"): edit the file and append a DECISION to LOG.

Know the remaining quota only from real sources: what the tool shows or a command you can run (Codex `/status`, Antigravity `/usage`, Claude Code `/usage` or its status line, Gemini CLI `/stats model`, Cursor dashboard), what the user tells you, or a provider warning. If `.continuity/scripts/quota_check.py` exists (optional extra), run `python3 .continuity/scripts/quota_check.py --tool <tool>` instead: exit 10 means at or below the threshold. Check at the start of `continue`, at every checkpoint, and before long operations.

- At or below the threshold, or a provider limit warning, or the user says so -> run `handoff` with reason `limit-near`; write the numbers you saw in HANDOFF `quota:` and LOG.
- Unknown -> write `quota: unavailable` in LOG and checkpoint after every subtask. Never estimate a percentage from tokens or from the model name. Ask the user for the number at most once per session.

## continue

1. Read `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` if present, then `CONTEXT.md`, `HANDOFF.md` and the LAST 30 lines of `LOG.md`. Do not read the whole log.
2. Check the real state: `git status` and `git log -5` (or recently changed files without Git). Compare with HANDOFF "Working tree".
3. Read HANDOFF `status`:
   - PAUSED -> normal takeover.
   - ACTIVE by this same verified session -> continue its work.
   - ACTIVE by another or unknown session -> confirm its writer stopped (your prompt saying an automated runner verified the previous process exited counts). Then RECOVERY: treat everything changed after the last checkpoint as "partial, unverified", append RECOVERED to LOG, discard nothing. If you cannot confirm, ask the user.
   - HANDOFF missing -> continue only if LOG and the working tree give one clear, safe next action; otherwise ask.
4. Check quota (Quota section). At or below the threshold: do not start work; run `handoff` (`limit-near`) or wait for the user.
5. Send a READBACK to the user, max 5 lines: project; state; next action; what you will NOT do; open questions; quota and threshold. Wait only if something is ambiguous, unapproved or ACTIVE-unconfirmed; otherwise go on. If you cannot ask (non-interactive session), put questions in HANDOFF section 6 and hand off with `needs-human`.
6. Set HANDOFF `status: ACTIVE`, `owner: <tool/model or unknown>`, `updated: now`. Append TAKEOVER to LOG (tool/model, quota).
7. Do the HANDOFF "Next action" if it is within "Approved scope"; if not, propose and ask.
8. Work and checkpoint. Verify with the project's own tests; record command, result and revision in LOG.

## checkpoint

When: a subtask finishes; a decision is made; before a long or risky operation; or about every 15 tool calls without one. Under a minute:

1. Check quota; at or below the threshold -> stop and `handoff`.
2. Append one LOG entry (done, files, evidence, next).
3. Update HANDOFF "Next action", "Working tree" and `updated`.
Before starting a step, write what you are about to do in HANDOFF "Next action", so a cut-off still leaves a usable pointer.

## handoff

Order matters: each step saves the most valuable information first. If you are cut off midway, steps 2-3 alone are enough for a safe takeover.

1. Say why: `limit-near` / `limit-hit` / `manual` / `model-switch` (hand the work to a different model) / `complete` (all approved work done) / `needs-human` (blocked on a question or approval; write it in HANDOFF section 6). Stop starting new work. Finish only the file or command you are in the middle of. Do not kill unrelated processes.
2. HANDOFF sections 1-2: "Next action" (first concrete step) and "Where things stand". Save.
3. HANDOFF sections 3-5: working tree, verification (done / NOT done), do-not/watch-out. Save.
4. Update CONTEXT task board and Decisions if changed. Append a HANDOFF entry to LOG including the quota values behind the decision, or `quota: unavailable`.
5. Set `status: PAUSED`, `updated`, `reason`, `next_model_hint` (strong-reasoning | standard | cheap, with a short why). If LOG exceeds 300 lines, move all but the last 50 to `archive/LOG-YYYY-MM.md`.
6. Check: no secrets in records; "Next action" not empty; referenced paths exist. Commit only if the project convention and the user's authorization allow.
7. Tell the user: reason, handoff location, next action, suggested model tier. Stop and wait.

## Superpowers (use when already available)

During `init` and `continue`, check whether Superpowers skills are actually available in the runtime (callable or readable in the skill catalog or documented local locations, not merely mentioned). If they are, read and use the ones relevant to the current activity (planning, execution, debugging, verification), respecting existing approvals and completed stages: never restart finished work. Record in LOG which skills you actually used. If they are not available, continue normally; do not install anything and do not treat it as a blocker.

## Optional extras

The skill's `extras/` folder offers add-ons that are NOT part of the default setup: an automatic quota reader (`quota_check.py`, Claude Code status line), delegation of routine work to cheaper models, and a relay runner that launches the next CLI automatically. Use or enable them only if the user asks or `.continuity/scripts/` already exists in the project.
