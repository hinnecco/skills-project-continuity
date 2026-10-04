# Adapters: invoking the protocol in each tool

Rule of thumb: the project carries the protocol (`.continuity/PROTOCOL.md` plus pointer files), so every tool works even without this skill installed. Installing the skill only adds the `init` procedure and nicer triggering.

## Entry-point files (written by `init`, text copied from `assets/templates/pointer.md`)

| Tool | Reads automatically | Note |
|---|---|---|
| Claude Code | `CLAUDE.md` | Does not read `AGENTS.md` by itself; copy the pointer into `CLAUDE.md` |
| Codex CLI | `AGENTS.md` | |
| Antigravity CLI (`agy`) | `AGENTS.md` or `GEMINI.md`, plus `.agents/rules/*.md` | The pointer in `AGENTS.md` is enough |
| Gemini CLI | `GEMINI.md` | `AGENTS.md` can be configured as a context file; copying is safer |
| Cursor | `AGENTS.md` and `.cursor/rules` | Confirm in your Cursor version; the dashboard has no CLI quota |

Copy the pointer text instead of using `@` imports: it works with small models and does not depend on version support. Merge into existing files; never overwrite them.

## Natural-language invocation (works everywhere)

- `Use project-continuity init in <path>`
- `continue` (with the pointer in place) or `Use project-continuity continue`
- `checkpoint` / `handoff`
- `set the quota threshold to 15%`

Slash-command or skill syntax differs by tool and version. Do not document syntax you have not verified on the installed version; use the natural-language form.

## Installing the skill

Only with the user's authorization, and never into global skill directories on your own. Per tool, place the `project-continuity` folder where that tool looks for skills or custom commands (check its current docs), or simply keep it in a known path and say "read <path>/SKILL.md and run continue".

## Delegation by harness

The protocol's Delegation section is harness-agnostic; what each tool offers differs and changes by version, so verify on the installed version before relying on it.

- Claude Code: the principal can dispatch subagents (Agent/Task tool, or custom subagents in `.claude/agents/`) and choose a smaller model per subagent (aliases such as haiku, sonnet, opus). Fill `delegation.model_tiers` accordingly, for example light=haiku, standard=sonnet, strong=opus.
- Codex CLI, Gemini CLI, Cursor: use sub-agents or a model picker only if the installed version offers one; otherwise work inline. Record `unknown` for models you cannot identify.
- Any tool: if you cannot dispatch or identify a child model, do not pretend to; execute inline and keep the quota checks.


## Headless commands used by the relay supervisor

Each CLI's non-interactive mode, as documented by the vendors in October 2026. Verify against the installed version; flags change.

| Tool | Command in `config.json` | Notes |
|---|---|---|
| Claude Code | `claude -p "<prompt>" --max-turns 80 --allowedTools "Read,Edit,Write,Glob,Grep,Bash(git:*),Bash(python3 .continuity/scripts/quota_check.py:*)"` | `-p` prints and exits; headless cannot ask for approval, so tools are pre-authorized with `--allowedTools`. Add the project's test command as another `Bash(...)` entry. Needs the statusline script for automatic quota readings. |
| Codex CLI | `codex exec --sandbox workspace-write "<prompt>"` | `--sandbox workspace-write` allows edits inside the workspace (network off by default). `--full-auto` is the equivalent shortcut. |
| Antigravity | `agy -p "<prompt>" --print-timeout 60m` | `-p` runs non-interactively. Headless permissions are inconsistent in current versions: `command()` grants in `~/.gemini/antigravity-cli/settings.json` may be ignored, and a denied tool can hang or soft-deny. Grant permissions in `~/.gemini/config/config.json` (global grants) or accept the risk of `--dangerously-skip-permissions`; that choice is the user's. The supervisor's timeout kills hung runs. |
| Gemini CLI | `gemini -p "<prompt>"` | Exit code 53 = turn limit. Add only if the user has it. |
| Cursor | not configured | No verified headless mode; add `cursor-agent` only after checking its docs. |

Any `--model` flag can be added to a command to pin a model (for example a cheaper one for routine work); the supervisor treats each list entry as one runnable model, so the same CLI can appear twice with different models and priorities.
