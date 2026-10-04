# Record contracts

Templates are in `assets/templates/` (CONTEXT.md, HANDOFF.md, LOG.md, config.json) with filled examples in `assets/templates/examples/`. Adopt existing equivalent paths and ledgers if the project already has them; reference them instead of creating competing ones.

## One fact, one file

| Fact | Lives in |
|---|---|
| Purpose, constraints, approved scope, task board, decisions | CONTEXT.md |
| Status, owner, next action, working tree, verification, watch-outs | HANDOFF.md |
| Events, takeovers, checkpoints, evidence, quota readings | LOG.md |
| Quota threshold | config.json |

Other files point to the owner of a fact instead of copying it.

## Size and rotation

- CONTEXT.md: stable orientation, about 150 lines max, no session history.
- HANDOFF.md: overwritten each handoff, about 80 lines max, sections in priority order (next action first) so a cut-off leaves the most important part saved.
- LOG.md: append-only. When over 300 lines, at handoff move all but the last 50 lines to `archive/LOG-YYYY-MM.md`.

## Required fields

HANDOFF front matter: `status` (ACTIVE|PAUSED), `owner`, `updated` (with timezone, from `date`), `reason` (manual | limit-near | limit-hit | model-switch | recovered | complete | needs-human), `quota`, `next_model_hint`. Body: sections 1-7 as in the template. A paused checkpoint is not a completion report; a model name is not proof of capability; quota history is not proof of present capacity.

LOG entry header: `## <timestamp tz> | <tool (model or unknown)> | <task id> | <TYPE>` then done / files / evidence (command, result, revision) / quota / next. Types: INIT, TAKEOVER, CHECKPOINT, DECISION, HANDOFF, RECOVERED.

## Safety

No secrets, credentials, personal media or private raw output in any record; refer to them by name. Preserve originals and user work; never clean, reset or delete to produce a tidy checkpoint. Ownership is advisory, not a process lock.
