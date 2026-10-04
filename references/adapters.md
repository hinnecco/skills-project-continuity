# Adapters: using the protocol in each tool

The project carries the protocol (`.continuity/PROTOCOL.md` plus pointer files), so every tool works even without this skill installed. Installing the skill only adds the `init` procedure and nicer triggering.

## Entry-point files (written by `init`, text copied from `assets/templates/pointer.md`)

| Tool | Reads automatically | Note |
|---|---|---|
| Claude Code | `CLAUDE.md` | Does not read `AGENTS.md` by itself; copy the pointer into `CLAUDE.md` |
| Codex CLI | `AGENTS.md` | |
| Antigravity CLI (`agy`) | `AGENTS.md` or `GEMINI.md`, plus `.agents/rules/*.md` | The pointer in `AGENTS.md` is enough |
| Gemini CLI | `GEMINI.md` | `AGENTS.md` can be configured as a context file; copying is safer |
| Cursor | `AGENTS.md` and `.cursor/rules` | Confirm in your Cursor version |

Copy the pointer text instead of using `@` imports: it works with small models and does not depend on version support. Merge into existing files; never overwrite them.

## Natural-language invocation (works everywhere)

- `Use project-continuity init in <path>`
- `continue` (with the pointer in place) or `Use project-continuity continue`
- `checkpoint` / `handoff`
- `set the quota threshold to 15%`

Slash-command or skill syntax differs by tool and version; use the natural-language form.

## Installing the skill

Only with the user's authorization, and never into global skill directories on your own. Place the `project-continuity` folder where the tool looks for skills or custom commands (check its current docs), or keep it in a known path and say "read <path>/SKILL.md and run continue".
