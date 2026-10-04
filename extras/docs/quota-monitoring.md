# Quota monitoring and automatic handoff

Purpose: the model watches the remaining usage window and, when it reaches a configurable threshold (default 10% remaining), stops and hands off, so the next model continues with full records.

## Honest limits of what a model can measure

A model cannot see its own quota by itself. It only knows what a tool exposes: a status line, a command, or a file. This design makes the reading available as a small JSON file per tool, and the model checks it with one command. Where a tool offers no readable source, the user (or the model, if it can run the tool's command) records the number manually. Checkpoints are the safety net: a cut-off between readings still leaves the next action saved.

## Configuration (`.continuity/config.json`)

```json
{
  "handoff_threshold_percent": 10,
  "thresholds": { "five_hour": 10, "seven_day": 5 },
  "windows": ["five_hour", "seven_day"],
  "stale_after_minutes": 30
}
```

- `handoff_threshold_percent`: remaining percent that triggers handoff. Default for all windows.
- `thresholds`: optional per-window override.
- `windows`: which windows to monitor (empty = all that were reported).
- `stale_after_minutes`: a reading older than this is "stale" (exit 4) and must be refreshed.

The user changes it by asking ("set the threshold to 15%", "only watch the 5-hour window") or by editing the file. The model that applies the change logs a DECISION entry.

## Where readings come from (details in `extras/docs/quota-per-tool.md`)

| Tool | Readable source | How it reaches the file |
|---|---|---|
| Claude Code | statusline JSON `rate_limits.five_hour` / `seven_day` (`used_percentage`, `resets_at`), Pro/Max login, v2.1+ | `scripts/claude_statusline.sh` writes `.continuity/quota/claude-code.json` automatically after each reply |
| Codex CLI | `/status` (5h and weekly percent), `/statusline` pins it in the footer | model or user records it with `--set-remaining` |
| Gemini CLI | `/stats model` (session usage and quota limits for your auth type) | record with `--used N --limit M` or `--set-remaining` |
| Antigravity CLI | `/usage` (alias `/quota`), `/credits` in an interactive session | record with `--set-remaining` or `--used N --limit M` |
| Cursor | Dashboard > Spending only (no documented CLI/API) | user reads it and tells the model; record with `--set-used` |

Sources were checked against vendor docs and community guides in October 2026; tools change quickly, so if a command no longer exists, tell the user and fall back to manual readings.

## Rules

- Check at: start of `continue`, every checkpoint, before long operations.
- Exit 10 -> handoff now (reason `limit-near`). Put the exact numbers in HANDOFF `quota:` and in the LOG entry.
- Exit 3/4 -> refresh; if impossible, ask the user once per session; if still unknown write `quota: unavailable` and checkpoint more often. Never estimate a percentage from token counts or from the model name.
- Never reset, purchase or switch accounts to get more capacity. After handoff, wait for the human; a window reset is not permission to resume.
- Account windows are shared across projects: a handoff in project A because of the 5h window also affects project B.

Readings carry observed_at and source per window. Updating one window does not refresh the others. Legacy shared timestamps are retained per window on first write. Reject invalid/nonfinite percentages and thresholds; stale low values require refresh, not a claim of current exhaustion. Prefer an available official quota tool (including desktop APIs) to manual entry; record its observations without copying account identifiers.
