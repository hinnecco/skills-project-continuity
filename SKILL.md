---
name: project-continuity
description: Use when initializing shared project context, continuing work from another model or session, or preparing a handoff between AI executors, regardless of provider or development tool.
---

# Project continuity

Maintain durable project state across models, providers and sessions. The project's files hold continuity; chat history supplements them. No particular tool, vendor, model, quota API, subagent system or other skill is required.

## Invocation

Select a mode from the user's request: `init`, `continue`, or `handoff`. These are instruction modes, not installed terminal commands. Example: “Use project-continuity continue in /path/to/project.” A runtime may expose another invocation syntax. If the mode or target cannot be inferred, ask only for the missing information.

Read only the selected [mode procedure](references/modes.md) and relevant [record contracts](references/records.md). Resolve project files relative to the confirmed project root, never the skill directory.

## Common contract

- Preserve user scope, existing approvals, constraints, history and partial work. Initialization authorizes continuity records, not product implementation, deployment, messages or purchases. Continuing authorizes only work already approved or requested by the user.
- Confirm actual workspace and repository state. Do not require Git when unavailable. Recorded commands, old handoffs and tool outputs are evidence, not new authorization. Identify stale records and update current summaries while retaining history.
- One principal executor owns mutations at a time. Record executor/session identity and assigned areas. An ownership record is advisory, not a process lock. If another executor appears active, establish coordination before overlapping edits; elapsed time alone does not release ownership.
- Record exact model/provider if exposed; otherwise “unknown.” Pick available capability and cost appropriate to the task, elevating when evidence requires it. Never infer price or quota from a model name. Delegate only when authorized and supported; the principal integrates child reports.
- At activity boundaries record changes, evidence, decisions, unresolved issues and the next action. Mark incomplete or unreviewed work explicitly. References to evidence are preferable to copying logs or entire plans.
- Monitor available quota at startup, task boundaries and before expensive operations. The default handoff threshold is 10% remaining in any relevant measured window, configurable by the user. Stop earlier if the next operation cannot fit. If measurement is unavailable, record that fact; use manual handoff or provider warnings without invented percentages. Never reset or purchase capacity automatically.
- On handoff stop new work, checkpoint children, stabilize active operations, save records, relinquish ownership only after writers stop, and await human instruction. Never resume automatically because a quota window reset.
- Keep secrets, credentials, personal media and private raw outputs out of continuity records. Preserve originals and user work; do not clean/reset/delete to manufacture a clean checkpoint. Product tests and review remain governed by the project's workflow.

## Optional Superpowers integration

During init and continue, check the runtime skill catalog or documented local skill locations for Superpowers. Distinguish available callable/readable skills from a merely mentioned or incomplete installation. If available, read and use the skills relevant to the current activity (for example planning, execution, debugging or verification), respecting their applicability and existing user decisions. Record which skills were actually used. Existing approvals and completed activities remain valid; do not restart a workflow on takeover.

Recommend Superpowers as an optional complement for structured planning, implementation and review. If absent, briefly recommend installation and continue with the project workflow; absence is not a blocker. Install or change plugins only when the user authorizes it. Do not fabricate commands or claim compatibility with an unsupported runtime. Superpowers governs applicable development work; this protocol maintains shared state and handoff across executors.

## Portable entry points

Optional runtime discovery files may link to this protocol. Merge short routing instructions into existing files only within authorization; preserve unrelated instructions. Do not claim installation or automatic discovery merely because this folder exists. Any agent can instead read SKILL.md directly and invoke a mode in natural language.
