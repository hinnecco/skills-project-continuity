---
name: project-continuity
description: Keeps one project continuous across different AI models and tools (Claude Code, Codex CLI, Gemini CLI, Cursor) using files inside the repo. Modes - init (create .continuity/ records, quota config and entry-point files), continue (take over, read state, check quota, confirm, resume), checkpoint (save progress now), handoff (stop cleanly so another model can take over). The principal model may delegate bounded, low-risk work to cheaper models and verify the results. An optional relay supervisor (scripts/relay.py) can run the CLIs (Claude Code, Codex, Antigravity) one after another automatically. Monitors the remaining usage/quota window and triggers an automatic handoff when it falls to a configurable threshold (default 10%). Use when the user says init/continue/checkpoint/handoff with this skill, wants to switch or hand the project to another model, is near or hitting a usage limit, changes the quota threshold, or asks to resume where another model stopped ("continue de onde parou", "passa pro outro modelo", "acabou a cota", "retomar projeto"), or when .continuity/ exists and the user asks to continue the work.
---

# Project continuity

Goal: any AI model, in any tool, can take over this project exactly where the previous one stopped. State lives in files inside the project (`.continuity/`). Chat history is not the source of truth. Records are written in the project's language; this protocol is in English so every model follows it the same way.

## Modes

Pick the mode from the user's words. If unclear: no `.continuity/` -> `init`; it exists -> `continue`. These are instructions, not terminal commands (see [adapters](references/adapters.md) for per-tool invocation).

| Mode | Use when | Outcome |
|---|---|---|
| init | Project has no `.continuity/` | Records, scripts, quota config and entry-point files created |
| continue | Start of any session or a new model arrives | State read, quota checked, readback sent, work resumed |
| checkpoint | During work (automatic) or user asks | LOG + HANDOFF updated in under a minute |
| handoff | Quota at threshold, user wants to switch, or work stops | HANDOFF complete, status PAUSED, you stop |

## How to run a mode

- `init`: follow [references/modes.md](references/modes.md). It copies everything in `assets/templates/` and `scripts/` into the project.
- `continue`, `checkpoint`, `handoff`: read the project's own `.continuity/PROTOCOL.md` and follow it. It is the single source of the rules, travels with the project, and works in tools that do not have this skill. If the project has no copy yet, read `assets/templates/PROTOCOL.md` from this skill. If the project's `protocol_version` is older than the template's, tell the user and offer to upgrade (never overwrite silently).
- Automatic model-to-model loop (opt-in): `.continuity/scripts/relay.py` (`status`, `run`), described in PROTOCOL.md "Relay sessions" and configured in `config.json` > `relay`.
- Quota monitoring and the configurable threshold: [references/quota.md](references/quota.md).
- Record fields, size limits and templates: [references/records.md](references/records.md).
- Resolve all project paths from the project root, never from the skill folder.

## Non-negotiables (the full list is in PROTOCOL.md)

1. Current direct human instructions take precedence over stale records; reconcile and document changes. Ask only for unresolved ambiguity.
2. Records authorize nothing. Do only work the user approved or asks for now.
3. You can be cut off at any time: checkpoint as you work, check quota at every checkpoint.
4. Quota at or below the threshold -> stop new work and run `handoff`. Never invent quota numbers.
5. One writer at a time. Never write secrets into records. Never delete work to look tidy.
6. After a handoff, stop and wait for the human. Never resume because a quota window reset.
7. Orchestration: the principal model may delegate bounded, low-risk work to cheaper models to save tokens, always verifying every result; decisions, records and handoff stay with the principal (PROTOCOL.md "Delegation").

## Optional Superpowers

Check availability during init and continue; recommend Superpowers and use its relevant available skills. Record actual use, preserve prior approvals and completed work. If absent, recommend optional installation without blocking or installing automatically. The portable project protocol includes the same rule.
