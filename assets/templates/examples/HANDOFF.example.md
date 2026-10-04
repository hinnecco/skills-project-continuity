---
status: PAUSED
owner: claude-code / unknown model
updated: 2026-10-04 14:32 -03
reason: limit-near
quota: five_hour 8% remaining @ 14:32, threshold 10%
next_model_hint: standard   # why: remaining work is routine endpoint code
---
# HANDOFF

## 1. Next action (do this first)
In `src/api/orders.py`, finish `update_order()` (stops at the TODO on line 58), then run `pytest tests/api -q`.

## 2. Where things stand
T1 schema done. T2: GET and POST /orders work; PUT is half-written. T3 (auth) not started.

## 3. Working tree
branch feature/orders @ a1b2c3d. Modified: src/api/orders.py (partial). Untracked: tests/api/test_orders_put.py (draft, not run).

## 4. Verification
Done: `pytest tests/api -q -k "get or post"` -> 12 passed @ a1b2c3d
NOT done: full test suite; PUT tests.

## 5. Do not / Watch out
Do not start T3 (auth): not approved yet. `orders.py` compiles but `update_order()` returns None.

## 6. Open questions for the human
Should PUT replace the whole order or patch fields?

## 7. Then
Run full suite; ask the user to approve T3.
