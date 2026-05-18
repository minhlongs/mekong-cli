# VN Pilot Hub — Multi-Tenant org_id Design

**Phase:** 7 P04 (minimal impl) | **Status:** Complete
**Author:** OpenClaw P04 | **Date:** 2026-05-17

---

## Why Multi-Tenant

Partner agencies, business schools, and distributor networks need to run their
own pilot batches without pilots from different sponsors seeing each other.

Use cases driving Phase 7 P04:
- Agency A runs 50 pilots for retail clients
- Business school B runs 50 pilots for student cohort
- Founder's direct signups remain in `default` org

Without org isolation, caps would be global (50 total), partners would
compete for the same slots, and reporting would mix across sponsors.

---

## Scope

### P04 (this phase — minimal impl)

- `org_id` on **signup**: validation, user_id format, per-org cap, record storage
- `org_id` on **stats** and **recent**: `?org_id=<slug>` query param
- `org_id` on **health**: `per_org: dict[str, int]` breakdown

### Deferred to Phase 8

- **convert** endpoint: org_id wiring (conversion records remain global for now)
- **revenue** endpoint: per-org MRR breakdown
- **export**: pilot export filtered by org_id
- **VietQR memo**: update to `MEKONG-{org_id}-{user_id}` for non-default orgs

### Deferred to P05 (parallel this phase)

- **Admin token scoping**: `?org_id=` filter on admin-only endpoints
  See `docs/vn-admin-scopes-design.md` when P05 completes.

---

## Schema Design

### org_id field

- Location: `pilots.jsonl` record
- Type: string, validated by regex `^[a-z0-9][a-z0-9-]{0,31}$`
- Default: `"default"` (implicit when omitted from SignupRequest)
- Sentinel: `"default"` is the canonical default org — not a real org name

### Validation rules

| Rule | Reason |
|------|--------|
| lowercase alphanumeric + dashes only | URL-safe slug, no ambiguity |
| must start with alnum | No leading dashes (URL path safety) |
| max 32 chars | Fits in user_id without excessive length |

### Backward compatibility

Existing records in `~/.mekong/pilots.jsonl` have no `org_id` field.
All filter helpers use `r.get("org_id", "default")` — never `r["org_id"]`.
Zero migration needed: additive-only contract.

---

## User ID Format Change

### Default org (unchanged)

```
opc_NNN_xxxxxx
```
Example: `opc_001_abc123`

Sequence `NNN` = count within the org (1-indexed).

### Custom org (new)

```
opc_<orgslug>_NNN_xxxxxx
```
Example: `opc_acme_001_abc123`

### Backward-compat guarantee

- All existing user_ids (`opc_NNN_xxxxxx`) remain valid
- `PollResponseRequest` and `ConversionRequest` validate `startswith("opc_")` — both formats pass
- No client-side changes required for existing integrations

---

## Per-Org Cap Rationale

Previous: 50 total pilots across all orgs.
New: 50 pilots PER org.

At 5 partner orgs × 50 = 250 pilots within Phase 7 infra. The Phase 7 stage 1
cap of 50 applies per-org to protect compute resources per partner batch.

Founder can increase `MAX_PILOTS` per-process via env var `MEKONG_MAX_PILOTS`
when a specific org needs a larger batch. Global cap enforcement deferred to Phase 8
SQLite migration (where per-org quotas can be stored in DB).

---

## VietQR Memo Format (Phase 8 Update Planned)

Current memo: `MEKONG-{user_id}` (e.g. `MEKONG-opc_001_abc12`)

Phase 8 planned update for non-default orgs:
```
MEKONG-{org_id}-{user_id}
```
Example: `MEKONG-acme-opc_acme_001_abc12`

Default org: unchanged format (backward-compat for existing QR codes).

---

## Admin Token Scoping

Currently `POST /v1/pilot/convert` is gated by `MEKONG_ADMIN_TOKEN` but
operates globally (no org filtering). P05 will design scoped admin tokens.

Until P05 ships: founder's admin token can see all orgs. Per-org admin
access requires P05 delivery.

---

## Migration Path

Contract: **zero rewrite, additive only**.

1. New `org_id` field added to `SignupRequest` with `default="default"`
2. Existing clients sending no `org_id` → receive `"default"` transparently
3. Existing `pilots.jsonl` records without `org_id` → read as `"default"` via `.get()`
4. No migration script needed
5. No downtime required

---

## Phase 8 Followup Checklist

- [ ] Wire `org_id` into `convert` endpoint (record + lookup scoping)
- [ ] Wire `org_id` into `revenue` endpoint (per-org MRR)
- [ ] Wire `org_id` into pilot export
- [ ] Update VietQR memo format for non-default orgs
- [ ] SQLite migration: store `org_id` as column with index
- [ ] Per-org `MAX_PILOTS` quota stored in DB (not env var)
- [ ] Admin endpoint: return 403 if token scope doesn't cover org_id
