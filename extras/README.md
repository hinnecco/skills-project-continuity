# Extras (optional, off by default)

The core of this skill (init, continue, checkpoint, handoff, three record files, a quota threshold) needs no permissions beyond editing the project's files. The pieces below add automation and need more permissions, so enable them only when you want them. Ask your model "enable the quota extra" (or relay, or delegation), or copy by hand as described.

| Extra | What it adds | What it needs | Docs |
|---|---|---|---|
| Quota reader | `quota_check.py` reads the last quota reading per tool and returns exit 10 at the threshold; `claude_statusline.sh` saves the Claude Code status-line readings automatically | Python 3; for Claude Code: `jq`, Pro/Max login, editing `~/.claude/settings.json` (the status line) | [quota-monitoring.md](docs/quota-monitoring.md), [quota-per-tool.md](docs/quota-per-tool.md) |
| Delegation | The principal model sends routine work to cheaper models and verifies it | A harness with subagents or model switching | [DELEGATION.md](docs/DELEGATION.md) |
| Relay | `relay.py` launches Claude Code, Codex and Antigravity one after another in headless mode | The CLIs' unattended permissions (allowed tools, sandbox), a terminal left running | [RELAY.md](docs/RELAY.md) |

Layout: `scripts/` (quota_check.py, relay.py, claude_statusline.sh, smoke_test.sh), `tests/`, `docs/`, `templates/config.extras.json` (the extra settings to merge into `.continuity/config.json`). The relay needs `quota_check.py` next to it. When enabling, copy the scripts you need into the project's `.continuity/scripts/`, merge the config keys, and add `.continuity/quota/` and `.continuity/relay/` to `.gitignore`.

Tests: `python3 -m unittest discover -s extras/tests`.
