# QUOTA - how to read remaining usage per tool

Check: `python3 .continuity/scripts/quota_check.py --tool <tool>` (exit 0 ok | 10 handoff | 4 stale | 3 none).
Record a reading: `python3 .continuity/scripts/quota_check.py --tool <tool> --window <name> --source "<where>" --set-remaining <pct>` (or `--set-used <pct>`, or `--used N --limit M`).
Threshold and windows: `.continuity/config.json`.

## Claude Code (automatic)
Install `.continuity/scripts/claude_statusline.sh` as the statusline (needs `jq`, Pro/Max login, Claude Code 2.1+): copy to `~/.claude/statusline.sh`, then in `~/.claude/settings.json`:
`{ "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" } }`
It writes `.continuity/quota/claude-code.json` after every reply (windows `five_hour`, `seven_day`). No manual step afterwards. API-key accounts have no rate-limit data: use manual readings.

## Codex CLI (manual, per checkpoint)
In the Codex prompt run `/status` (shows percent used/left for the 5-hour and weekly limits and reset times; send one message first). Optional: `/statusline` pins it to the footer so the user can read it. Record e.g. `--tool codex --window five_hour --set-remaining 42` and the same for `weekly`. If the model cannot run slash commands itself, ask the user to paste the output.

## Gemini CLI (manual, per checkpoint)
Run `/stats model`: shows session token use and the quota limits for your auth type (daily request limits such as 1000/1500/2000 for Google accounts). Record `--tool gemini --window daily --used <requests used> --limit <daily limit>`. Ask the user to paste the output if you cannot run it.

## Antigravity CLI (`agy`) (manual, per checkpoint)
In an interactive `agy` session `/usage` (alias `/quota`) shows model quota usage and `/credits` shows credits. Record `--tool antigravity --window <name> --set-remaining <pct>` (or `--used N --limit M`). In relay (non-interactive) sessions, if you cannot run slash commands, write `quota: unavailable` in LOG and checkpoint more often; the supervisor will not start a model whose last fresh reading is at or below the threshold.

## Cursor (manual)
Only the dashboard (cursor.com/dashboard, Spending tab) shows remaining allowance. Ask the user to read it and tell you; record `--tool cursor --window monthly --set-used <pct>`. Ask again at each takeover and each checkpoint series; mark `stale` readings honestly.

## Other tools
Use any status command, footer or dashboard the tool offers. Record with `--tool other`. If nothing exists, write `quota: unavailable` and checkpoint often.
