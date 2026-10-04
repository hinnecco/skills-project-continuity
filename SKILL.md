---
name: project-continuity
description: Keeps one project continuous across different AI models and tools (Claude Code, Codex, Antigravity, Gemini CLI, Cursor) using files inside the repo. Modes - init (create .continuity/ records and entry-point files), continue (take over - read state, check quota, confirm, resume), checkpoint (save progress now), handoff (stop cleanly so another model can take over). Hands off when the remaining usage quota reaches a configurable threshold (default 10%). Uses Superpowers skills when they are already available. Use when the user says init/continue/checkpoint/handoff with this skill, wants to switch or hand the project to another model, is near or hitting a usage limit, changes the quota threshold, or asks to resume where another model stopped ("continue de onde parou", "passa pro outro modelo", "acabou a cota", "retomar projeto"), or when .continuity/ exists and the user asks to continue the work.
---

# Project continuity

Goal: any AI model, in any tool, can take over this project exactly where the previous one stopped. State lives in files inside the project (`.continuity/`); chat history is not the source of truth. Records are written in the project's language; the protocol is in English so every model follows it the same way. The default setup needs no permissions beyond editing the project's own files.

## Modes

Pick the mode from the user's words. If unclear: no `.continuity/` -> `init`; it exists -> `continue`. These are instructions in natural language, not terminal commands.

| Mode | Use when | Outcome |
|---|---|---|
| init | Project has no `.continuity/` | Records and entry-point files created |
| continue | Start of any session or a new model arrives | State read, quota checked, readback sent, work resumed |
| checkpoint | During work (automatic) or user asks | LOG + HANDOFF updated in under a minute |
| handoff | Quota at threshold, user wants to switch, or work stops | HANDOFF complete, status PAUSED, you stop |

## How to run a mode

- `init`: follow [references/modes.md](references/modes.md). It copies the files in `assets/templates/` into the project.
- `continue`, `checkpoint`, `handoff`: read the project's own `.continuity/PROTOCOL.md` and follow it. It is the single source of the rules, travels with the project and works in tools that do not have this skill. If the project has no copy yet, read `assets/templates/PROTOCOL.md` here. If the project's `protocol_version` is older than the template's, tell the user and offer to upgrade (never overwrite silently).
- Record fields, size limits and templates: [references/records.md](references/records.md). Entry-point files and invocation per tool: [references/adapters.md](references/adapters.md).
- Resolve project paths from the project root, never from the skill folder.

## Non-negotiables (full list in PROTOCOL.md)

1. Current direct human instructions take precedence over stale records.
2. Records authorize nothing. Do only work the user approved or asks for now.
3. You can be cut off at any time: checkpoint as you work and check quota at every checkpoint.
4. Quota at or below the threshold -> stop new work and run `handoff`. Never invent quota numbers.
5. One writer at a time. Never write secrets into records. Never delete work to look tidy.
6. After a handoff, stop. Never resume because a quota window reset.

## Superpowers

If Superpowers skills are already available in the environment, use the ones relevant to the current activity (planning, execution, debugging, verification) without restarting finished stages, and record which ones you used. If they are not available, continue normally; do not install anything.

## Optional extras

[extras/README.md](extras/README.md) describes add-ons that are off by default: automatic quota reading, delegation to cheaper models, and a relay runner that launches the next CLI automatically. They need extra permissions, so enable them only when the user asks.
