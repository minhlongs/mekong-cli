# VN Pilot Outreach — Implementation Plan

**Scope:** Add outreach log + history endpoints and tests.

**Dependencies:** `vn_pilot_state` JSONL persistence; FastAPI test client.

**Tasks:**
1. Add `outreach_commands.py` with `/v1/pilot/outreach/log` and `/v1/pilot/outreach/{user_id}` routes.
2. Add Pydantic schemas `OutreachLogIn` / `OutreachLogOut` / `OutreachHistory`.
3. Extend `tests/vn/test_vn_pilot_outreach.py` for error paths.
4. Run `python3 -m pytest tests/vn/test_vn_pilot_outreach.py`.