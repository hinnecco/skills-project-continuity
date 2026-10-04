---
status: PAUSED              # ACTIVE = someone is working | PAUSED = clean handoff
owner: unknown              # tool / model, or unknown
updated: <YYYY-MM-DD HH:MM TZ>
reason: needs-human         # manual | limit-near | limit-hit | model-switch | recovered | complete | needs-human
quota: unavailable          # e.g. "five_hour 8% remaining @ 14:32, threshold 10%"
next_model_hint: standard   # strong-reasoning | standard | cheap  (why: <short>)
---
# HANDOFF
<!-- Overwritten at every handoff. Max ~80 lines. Sections are in priority order: if you are cut off while writing, the top is already saved. -->

## 1. Next action (do this first)
Await the user's brief.

## 2. Where things stand
<3-8 lines: done, partial, blocked>

## 3. Working tree and delegations
<branch/revision; changed and untracked files; which are partial>
Delegations: <child/model, task, files changed, verified yes/no; or "none">

## 4. Verification
Done: <command -> result @ revision>
NOT done: <checks skipped>

## 5. Do not / Watch out
<binding restrictions, traps, things that look done but are not>

## 6. Open questions for the human

## 7. Then (pending, in order)
