# project-continuity

[Português](README.md) | **English**

A skill for working on **one project with different AI models** (Claude Code, Codex, Antigravity, Gemini CLI, Cursor) without losing continuity. Project state lives in files inside the repository; chat history is only a complement. When a model is about to stop (quota near the threshold, tool switch, work finished), it writes a handoff and the next model picks up exactly where the previous one left off.

The protocol is written in English so models from any vendor follow it the same way; project records are written in the project's own language.

## Core (default): simple, no extra permissions

Four modes, spoken in natural language ("use project-continuity init in this project", "continue", "handoff"):

| Mode | When to use | Result |
|---|---|---|
| `init` | Project has no `.continuity/` | Creates the records and the entry-point files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) |
| `continue` | Start of any session, or when another model takes over | Reads the state, checks quota, sends a 5-line readback and resumes |
| `checkpoint` | During work or on request | Updates LOG and HANDOFF in under a minute |
| `handoff` | Quota at threshold, model switch or end of work | Status `PAUSED`, next action recorded, the model stops |

`init` creates this in the project:

```
AGENTS.md / CLAUDE.md / GEMINI.md   short pointer to the protocol (merged, never overwritten)
.continuity/
  PROTOCOL.md   the rules, single source of truth (the protocol travels with the project)
  CONTEXT.md    stable orientation: goal, approved scope, task board, decisions
  HANDOFF.md    current state (ACTIVE/PAUSED), next action, working tree; overwritten
  LOG.md        append-only history and evidence
  config.json   quota threshold (default 10% remaining)
```

Key points of the protocol:

- **Continuous checkpointing.** The model writes the next action before each step, so a cut-off by a usage limit does not lose context. A HANDOFF left `ACTIVE` means the previous model did not finish; the next one runs a recovery without discarding anything.
- **Configurable quota threshold.** The model only counts quota that is real: what the tool displays (`/status` in Codex, `/usage` in Antigravity and Claude Code, etc.), what you tell it, or a provider warning. If it cannot tell, it records `quota: unavailable` and checkpoints more often. It never invents percentages. At the threshold, it hands off.
- **Records authorize nothing.** The model only does work inside the approved scope or what you ask for now.
- **Superpowers.** If it already exists in the environment, the model uses the relevant skills without redoing finished stages; if absent, it carries on and installs nothing.
- **Timestamps come from `date`**, because models do not know the time.

## Extras (optional, off by default)

Automation that needs more permissions. Enable only what you want; details in [`extras/README.md`](extras/README.md).

| Extra | What it does | Needs |
|---|---|---|
| Quota reader | `quota_check.py` reads the latest reading per tool and flags the threshold; the Claude Code statusline writes the reading automatically | Python 3; for Claude Code, `jq`, a Pro/Max login and editing `~/.claude/settings.json` |
| Delegation | The principal model hands routine tasks to cheaper models and verifies every result | A harness with subagents or model switching |
| Relay | `relay.py` runs Claude Code, Codex and Antigravity one after another in headless mode | Non-interactive CLI permissions (allowed tools, sandbox) and an open terminal |

Status of each extra: the relay was validated with real Claude Code (2.1.289) and Codex (0.160.0) in a two-task run with a model switch, and with fake CLIs in the automated tests; Antigravity has not been exercised. In non-interactive sessions no CLI could read its own quota, so the threshold does not trigger there; the relay switches models on `model-switch`, `complete`, `needs-human`, or by recovering after a cut-off.

## Repository layout

```
SKILL.md                    modes and non-negotiable rules
references/                 modes.md (init), records.md (record contracts), adapters.md (per tool)
assets/templates/           PROTOCOL, CONTEXT, HANDOFF, LOG, config.json, pointer and examples
extras/                     scripts, tests, docs and config for the optional extras
```

## Installation

Put this folder where your tool looks for skills, or keep it at a known path and say "read `<path>/SKILL.md` and run `init`". Install only with your authorization and check each tool's current documentation, since locations and syntax change between versions.

## Tests

```bash
python3 -m unittest discover -s extras/tests
```

Python 3 standard library only, no dependencies. The tests cover the extras (quota reader and relay); the core is plain text files.

## Known limitations

- Quota belongs to the account, not the project: a handoff caused by one window applies to every project that uses it.
- The headless commands and flags in the extras come from vendor documentation as of October 2026 and must be checked against the installed version.
- Models sometimes get timestamps wrong even with the `date` rule.

## History

v1 was created with ChatGPT. v2 was reviewed with an expert subagent and added continuous checkpointing, templates, a configurable quota threshold, delegation and the relay. v3 split the core from the extras to cut complexity and the permissions required.
