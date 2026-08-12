# Smoke Plan — test_routing.py Action List
- Objective: unblock `test_ask_routing.py` in the same pass audit returned.
- Constraint: keep protected flows (`Setup Wizard`, `Telegram Bot`, `Payment Flow`) intact; skip tests hitting absent provider secrets.
- Action list: stop entrypoint drift in `scripts/notes/forbidden-entrypoint-mxi.md`, validate router entries against live Typer registrations, re-run failing tests after patch.
- Deliverable: updated test file with corrected routing targets plus confirmation summary.
