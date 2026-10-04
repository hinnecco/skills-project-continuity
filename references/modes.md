# Mode procedures (skill side)

Only `init` is defined here. `continue`, `checkpoint` and `handoff` live in the project's `.continuity/PROTOCOL.md` (template: `assets/templates/PROTOCOL.md`) so they travel with the project.

## init

1. Detect what exists: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules`, any existing CONTEXT/HANDOFF/plan/ledger, and Git status if available. Existing equivalent files are adopted and referenced, never duplicated or overwritten.
2. Describe what will be created. An explicit init request authorizes reversible continuity records and local pointers; do not ask again. Use the threshold the user states or the default 10%. Ask only for essential missing information. Global integrations (settings outside the project, installing anything) need separate authorization. Check whether Superpowers skills are actually available and note it in LOG.
3. Create in the project root:
   - `.continuity/PROTOCOL.md` (copy of the template), `CONTEXT.md`, `LOG.md`, `config.json` (with the chosen threshold) and `HANDOFF.md` (status PAUSED; Next action: the earliest approved pending activity, with `reason: manual`; or "await the user's brief" with `reason: needs-human` if there is none).
   - The entry-point pointer (`assets/templates/pointer.md`) appended to `AGENTS.md` (Codex, Antigravity, Cursor), `CLAUDE.md` (Claude Code) and `GEMINI.md` (Gemini CLI, Antigravity) for the tools the user uses. Merge into existing files, preserve their content, copy the text (do not rely on `@` imports).
4. Fill CONTEXT with what is known (goal, root, commands, constraints). Anything unknown is written `unknown`; do not invent scope or approvals. Preserve existing human approvals with source and date; only unknown or proposed scope remains unapproved.
5. Append an INIT entry to LOG (timestamp from `date`). Verify the files exist and the pointers resolve. Report: project root, files created, threshold, next action. Do not start implementation. Mention once that optional extras exist and are off (see `extras/README.md`).

## Enabling an extra (only when the user asks)

Follow `extras/README.md`. Extras need extra permissions, so show the user what will be copied and which permissions the commands pre-authorize before enabling anything. If Git is used, add `.continuity/quota/` and `.continuity/relay/` to `.gitignore`, preserving existing entries.
