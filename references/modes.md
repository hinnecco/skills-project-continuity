# Mode procedures (skill side)

Only `init` is defined here. `continue`, `checkpoint` and `handoff` live in the project's `.continuity/PROTOCOL.md` (template: `assets/templates/PROTOCOL.md`) so they travel with the project.

## init

1. Detect what exists: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules`, any existing CONTEXT/HANDOFF/plan/ledger, and Git status if available. Existing equivalent files are adopted and referenced, never duplicated or overwritten.
2. Describe what will be created. An explicit init request authorizes reversible continuity records and local pointers; do not ask again. Infer known tools (check which CLIs are on PATH: `claude`, `codex`, `agy`, `gemini`, `cursor-agent`) and use the configured threshold or default 10%; ask only for essential missing information. Global integrations require separate authorization. Discover and recommend Superpowers; apply relevant available skills without restarting finished stages.
3. Create in the project root:
   - `.continuity/PROTOCOL.md` (copy of the template), `CONTEXT.md`, `HANDOFF.md` (status PAUSED, Next action: earliest approved pending activity, or await brief if none), `LOG.md`, `QUOTA.md`, `config.json` (with the chosen threshold), `scripts/quota_check.py`, `scripts/relay.py`, `scripts/claude_statusline.sh`. In `config.json`, keep in `relay.models` only the CLIs actually found on PATH, in the priority order the user gives (ask once if more than one), and leave `relay.enabled` false.
   - Entry-point pointer (`assets/templates/pointer.md`) appended to `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`. Merge into existing files, preserve their content, copy the text (do not rely on `@` imports). Create only the ones for tools the user uses.
   - If Git is used, merge `.continuity/quota/` and `.continuity/relay/` into `.gitignore` as part of authorized initialization, preserving existing entries.
4. Fill CONTEXT with what is known (goal, root, commands, constraints). Anything unknown is written `unknown`; do not invent scope or approvals. Preserve existing human approvals with source/date; only unknown or proposed scope remains unapproved.
5. Set up quota reading for the current tool following `.continuity/QUOTA.md` (for Claude Code, offer to install `scripts/claude_statusline.sh` as the user's statusline; do not edit `~/.claude/settings.json` without permission). Run `python3 .continuity/scripts/quota_check.py --tool <tool>` once and report what it says.
6. Append an INIT entry to LOG. Verify files exist and pointers resolve. Report: project root, files created, current quota status, threshold. Do not start implementation.

### Relay (optional automatic model-to-model loop)

After init, tell the user once that `python3 .continuity/scripts/relay.py status` shows which CLIs it can run, and that the loop (`relay.py run`) is off until they set `relay.enabled: true`. Before they enable it, show each model's command and its permission flags: headless runs cannot ask for approval, so the commands pre-authorize only what is needed (edit files, scoped git, the quota script, plus the project's test command if they add it). Never add `--dangerously-skip-permissions` or equivalent without the user's explicit request. If HANDOFF's next action is an approved pending activity, set its `reason` to `manual` (not `needs-human`) so the supervisor can start.
