# VN Pilot Outreach — spec-kit spec

**Outcome:** Clients have a contact log and a sorted outreach history for each VN pilot user.

**Constraints:**
- Use FastAPI endpoints under `/v1/pilot/outreach`.
- Keep changes localized to `src/api/` and tests.
- Bilingual docs for client-facing summaries.

**Non-goals:**
- No new auth system.
- No bulk import or CSV export.
- No front-end dashboard changes.

## Acceptance Criteria

1. `POST /v1/pilot/outreach/log` stores outreach attempt and returns 200 with contact fields + `ts`.
2. `GET /v1/pilot/outreach/{user_id}` returns contacts sorted latest first.
3. Unknown user returns 404; bad prefix returns 400.