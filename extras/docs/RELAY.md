# Relay: automatic model-to-model loop (optional extra)

`scripts/relay.py` is a supervisor that you run in a terminal. It launches one AI CLI at a time in non-interactive mode with the `continue` prompt, waits for it to exit, reads HANDOFF, then launches the next available CLI. It is **off by default** and needs permissions that the core does not: each CLI runs unattended, so its command pre-authorizes tools (edit files, scoped git, tests) and the CLI's sandbox settings apply.

Status of this extra: validated with real Claude Code (2.1.289) and Codex (0.160.0) in a two-task handoff test, and with fake CLIs in the unit tests. Not exercised with Antigravity. In non-interactive sessions none of the CLIs could read its own quota, so the quota threshold does not trigger there; handoff happens by cut-off recovery, `model-switch`, `complete` or `needs-human`.

Enable: copy `scripts/relay.py` and `scripts/quota_check.py` into the project's `.continuity/scripts/`, merge `templates/config.extras.json` into `.continuity/config.json`, review each model's command, then set `relay.enabled` to `true`.

```bash
python3 .continuity/scripts/relay.py status        # CLIs found, quota state, HANDOFF state
python3 .continuity/scripts/relay.py run --dry-run # next model, nothing executed
python3 .continuity/scripts/relay.py run           # start the loop
```

Try it on a throwaway project: `TWO_TASKS=1 bash extras/scripts/smoke_test.sh ~/relay-troca` (asks for confirmation before running; it uses the quota of the real CLIs).

## How the relay behaves (automatic model-to-model loop, opt-in)

`scripts/relay.py` is a supervisor the user runs in a terminal (`python3 .continuity/scripts/relay.py run`). It launches one AI CLI at a time in non-interactive mode with the `continue` prompt, waits for it to exit, reads HANDOFF, then launches the next available CLI. It only runs if the user set `relay.enabled: true`. It skips CLIs that are missing or whose last quota reading is at or below the threshold, never waits for or exploits a quota reset, never raises permissions, and stops on `complete`, `needs-human`, no available model, a stall (no recorded progress), or the session limit.

If you were started by it (your prompt says so): you are non-interactive, so never ask questions; put them in HANDOFF section 6 and hand off with `needs-human`. Do the normal `continue`, checkpoint and quota rules. When quota reaches the threshold, hand off with `limit-near` and exit, so the supervisor can start the next model. If all approved work is done, hand off with `complete`. A model that hands off with `model-switch` is not launched again right after, so a different model takes over. If a session ends with a usage-limit message in its log, the supervisor treats that model as at its limit for a while (it records an observation, not an estimate). The supervisor appends RELAY entries to LOG; it does not edit other records.

## Headless commands per CLI

Each CLI's non-interactive mode, as documented by the vendors in October 2026. Verify against the installed version; flags change.

| Tool | Command in `config.json` | Notes |
|---|---|---|
| Claude Code | `claude -p "<prompt>" --allowedTools "Read,Edit,Write,Glob,Grep,Bash(git:*),Bash(python3 .continuity/scripts/quota_check.py:*),Bash(date:*)"` | `-p` prints and exits; headless cannot ask for approval, so tools are pre-authorized with `--allowedTools`. Add the project's test command as another `Bash(...)` entry. `--max-turns` is not listed in `claude --help` of version 2.1.289, so it is not in the default command (the supervisor's timeout bounds the run); add it only if your version accepts it. `--permission-mode` (acceptEdits, dontAsk, plan, ...) and `--max-budget-usd` exist in that version. Needs the statusline script for automatic quota readings. |
| Codex CLI | `codex exec --sandbox workspace-write "<prompt>"` | `--sandbox workspace-write` allows edits inside the workspace (network off by default). `--full-auto` is the equivalent shortcut. `codex exec` may refuse to run outside a Git repository; in a project without Git add `--skip-git-repo-check` to the command (check `codex exec --help` on your version). |
| Antigravity | `agy -p "<prompt>" --print-timeout 60m` | `-p` runs non-interactively. Headless permissions are inconsistent in current versions: `command()` grants in `~/.gemini/antigravity-cli/settings.json` may be ignored, and a denied tool can hang or soft-deny. Grant permissions in `~/.gemini/config/config.json` (global grants) or accept the risk of `--dangerously-skip-permissions`; that choice is the user's. The supervisor's timeout kills hung runs. |
| Gemini CLI | `gemini -p "<prompt>"` | Exit code 53 = turn limit. Add only if the user has it. |
| Cursor | not configured | No verified headless mode; add `cursor-agent` only after checking its docs. |

Any `--model` flag can be added to a command to pin a model (for example a cheaper one for routine work); the supervisor treats each list entry as one runnable model, so the same CLI can appear twice with different models and priorities.
