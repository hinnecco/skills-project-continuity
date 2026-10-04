## Project continuity (multi-model project)
Different AI models and tools work on this project in turns. Before anything else:
1. Read `.continuity/PROTOCOL.md`, then `.continuity/CONTEXT.md` and `.continuity/HANDOFF.md`.
2. Follow PROTOCOL.md "continue": check quota, send a short readback, then proceed with the Next action.
3. Checkpoint as you work (each checkpoint includes a quota check). When quota reaches the threshold in `.continuity/config.json`, or the user says "handoff", follow PROTOCOL.md "handoff" and stop.
If the `project-continuity` skill is installed you may use it instead (`continue`, `checkpoint`, `handoff`).
