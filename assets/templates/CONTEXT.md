# CONTEXT - <project name>
<!-- Stable orientation. Max ~150 lines. NO session history here (that is LOG.md). -->
This project is shared across AI models and human contributors. Read `.continuity/PROTOCOL.md` first, then this file, `.continuity/HANDOFF.md` and the end of `.continuity/LOG.md`. Preserve prior work and approval boundaries. Never assume chat history is complete.

## Purpose and constraints
- Goal: <one sentence>
- Root: <absolute path>   Repo: <git branch / "no git">
- Run / test commands: <commands, or unknown>
- Binding constraints: <e.g. "do not touch /legacy", "no new dependencies">

## Approved scope (only what a human approved)
| Item | Approved by / date | Source |
|---|---|---|
| <item> | <name, YYYY-MM-DD> | <chat / file> |

## Proposed, NOT approved
- <idea from a model, waiting for the human>

## Task board
| ID | Task | Status (todo/doing/partial/blocked/done) | Evidence |
|---|---|---|---|
| T1 | <task> | todo | - |

## Decisions
- D1 (<date>, <model/tool>): <decision> - <reason>

## Settings
Quota threshold and windows live in `.continuity/config.json` (single source). Other settings:
- git_wip_commits: no
- preferred_workflow_skills: none   (optional skills or workflows the user wants applied)
