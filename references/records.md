# Record contracts

Adopt existing equivalent paths/fields. Two main records and links to the project's existing ledger are sufficient; do not add redundant history files.

## CONTEXT.md

Start with instructions addressed to any incoming executor:

> This project is shared across AI models and human contributors. Read this context before acting, preserve prior work and authorization boundaries, and document your contribution at activity boundaries and before interruption. Use the shared continuity protocol; never assume chat history is complete. Consult the authoritative handoff and current task ledger. Coordinate mutation ownership before editing.

Maintain a compact current summary:

- Project purpose, confirmed root, scope and constraints.
- Approved work versus proposals, with source/date of human approval.
- Current phase/task and authoritative plan, ledger and handoff paths.
- Executor/session/model/provider (unknown where unavailable), ownership and child assignments.
- Completed, partial, blocked and pending work; verified evidence references.
- Configuration decisions relevant to continuation, quota threshold and last observation (historical, not current).
- Exact next action.

Append chronological contribution entries with timestamp/timezone, executor identity/role, activity/status, files or commits, verification command/result/revision, decisions and rationale, unresolved concerns and next action. Distinguish implementation, review and documentation. Update summaries without erasing earlier entries. Separate child contributions by identity, integrated by the principal.

## HANDOFF.md (or existing authoritative equivalent)

Minimum checkpoint fields:

- Time/timezone; author; pause reason; measured quota/window/observation time or “unavailable.”
- Root; repository branch/revision if applicable; current changed/untracked work or non-Git equivalents.
- Human approval boundaries and binding restrictions.
- Current activity, completed tasks, partial files, failures and evidence paths.
- Tests/reviews actually completed and important checks not run.
- Provisioned dependencies/assets and reproducibility metadata when relevant; no credentials or private payloads.
- Active operations/children/processes and ownership; verified status versus last known state. PID alone is not process identity.
- Recovery needs and the first concrete action for the next executor, followed by pending tasks.

A paused checkpoint is not a completion report. Quota history is not proof of present capacity. Model names are not proof of capability, price or availability.

## Task ledger

Reuse the project's existing ledger. Record task status, implementation/review identity, commits or file snapshots, test evidence, findings/fix state, decisions and next action. It is the detailed execution record; CONTEXT is orientation and HANDOFF is takeover state. Link between them rather than copying the full ledger.

## Optional runtime adapter

A short entry point may say:

> Before continuing this shared project, read CONTEXT.md, then its authoritative handoff and current ledger. Follow project-continuity in the requested mode, or read its SKILL.md by the recorded path. Keep progress documented and preserve approval boundaries.

Adapt discovery syntax to actual runtime support. No provider-specific file is required. Do not overwrite existing instructions or install into global skill directories without authorization.
