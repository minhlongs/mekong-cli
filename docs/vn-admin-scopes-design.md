# Role-Based Admin Scopes — Design Document

> **Phase 7 P05** — DESIGN ONLY per founder override (locked 2026-05-17).
> JWT implementation deferred to Phase 8. Legacy `MEKONG_ADMIN_TOKEN`
> remains the active auth path until then.

## Why Scopes

Phase 6 ships a single `MEKONG_ADMIN_TOKEN` env var that grants god-mode
to anyone holding it. As the team grows beyond founder-only ops, this
becomes a liability:

| Future role | Needs | Risks of god-mode token |
|-------------|-------|-------------------------|
| Founder | All endpoints | (acceptable) |
| CS contractor | Mark conversions + respond to NPS | Can leak MRR data, modify revenue numbers |
| Marketing freelancer | Read stats + revenue for campaigns | Same — over-broad access |
| Read-only auditor | Recent timeline for compliance | Same |

Rotating the shared token also means coordinating with everyone who holds
it. With scoped tokens, revoking one role doesn't disrupt others.

## Scope Definitions

Four scopes, ordered from most to least powerful:

| Scope | Permissions | Typical holder |
|-------|------------|----------------|
| `founder` | All endpoints (read + write + admin) | Founder, technical co-founder |
| `cs` | Read all + write convert + write response | Customer support contractor |
| `marketing` | Read stats + read revenue + read recent | Marketing/growth freelancer |
| `readonly` | Read recent only (no PII surface) | Auditor, investor demo |

Notable: `cs` can mark conversions because they often confirm payments
during user support calls. `marketing` can see revenue for campaign
attribution. `readonly` is intentionally limited to non-PII timeline.

## Endpoint-to-Scope Matrix

Required scope per endpoint. ANY listed scope grants access:

| Endpoint | Required Scope | Notes |
|----------|----------------|-------|
| `POST /v1/pilot/signup` | (none — public) | Anyone can submit signup |
| `POST /v1/pilot/response` | `founder` `cs` | NPS poll recording |
| `POST /v1/pilot/convert` | `founder` `cs` | Mark paid + record MRR |
| `GET /v1/pilot/stats` | `founder` `cs` `marketing` `readonly` | All scopes |
| `GET /v1/pilot/recent` | `founder` `cs` `marketing` `readonly` | All scopes (no PII) |
| `GET /v1/pilot/revenue` | `founder` `cs` `marketing` | Revenue data |
| `GET /v1/pilot/health` | (none — public) | Sanity check only |
| `GET /v1/pilot/export/misa` | `founder` | PII + financial (Phase 03) |
| `POST /v1/payments/vietqr/webhook` | (HMAC instead of JWT) | Bank-signed payload |

## Token Format — JWT (Recommended)

**Decision: JWT with short TTL + manual rotation.** Stateless, no DB
lookup, claims encoded, easy to verify with `PyJWT` (already battle-tested,
MIT license).

### JWT Claim Structure

```json
{
  "sub": "founder-name",            // human identifier (for logs)
  "scopes": ["founder"],            // array — may have multiple
  "allowed_orgs": ["*"],            // Phase 04 integration; "*" = all
  "iat": 1747498800,                // issued-at (unix ts)
  "exp": 1747585200                 // expires (iat + 24h default)
}
```

Signing: HMAC-SHA256 with `MEKONG_JWT_SECRET=REDACTED` env var (32+ bytes).

Header (sent on request):
```
Authorization: Bearer eyJhbGciOiJIUzI1NiI...
```

Same header shape as Phase 6 — drop-in replacement for legacy token.

### Why JWT vs Random + Lookup Table

| Criterion | JWT | Random + DB lookup |
|-----------|-----|---------------------|
| Stateless verification | ✅ pure crypto | ❌ DB hit per req |
| Instant revocation | ❌ TTL only | ✅ delete row |
| Claim portability | ✅ encoded | ❌ separate lookup |
| Infrastructure deps | ✅ none | ❌ DB / Redis |
| Founder ops simplicity | ✅ no schema | ❌ schema mgmt |

For 1-person ops at <100 pilots, JWT wins. When team grows to 5+ people
needing instant revocation, swap to random+lookup (designed below).

### Why NOT Random + Lookup (Yet)

- Adds DB / Redis dependency
- Requires schema migration story
- Adds verification latency (~5-10ms DB round-trip)
- Overkill for founder + 1-2 contractors

Phase 9+ reconsideration: when CS team ≥ 3, switch to lookup table for
instant revocation.

## Verification Flow (Phase 8 Impl)

```
Authorization: Bearer <token>
                │
                ▼
   try MEKONG_ADMIN_TOKEN exact match (legacy) ──hit──▶ allow (god scope, "*" org)
                │ miss
                ▼
   try jwt.decode(token, MEKONG_JWT_SECRET=REDACTED) ──invalid sig──▶ 401 invalid
                │ valid
                ▼
   check exp claim ──expired──▶ 401 expired
                │ ok
                ▼
   check required_scope in claims["scopes"] ──no──▶ 403 insufficient scope
                │ yes
                ▼
   check request org_id in claims["allowed_orgs"] or "*" ──no──▶ 403 wrong org
                │ yes
                ▼
   allow + log [scope, org_id, sub] for audit
```

Verification budget: < 5ms (pure HMAC crypto, no I/O).

## Token Issuance CLI (Phase 8 Impl)

Founder-only CLI tool, runs locally on M1 (uses `MEKONG_JWT_SECRET=REDACTED` from
host env, NOT shared):

```bash
python3 scripts/admin-token-issue.py \
  --sub "cs-contractor-nam" \
  --scope cs \
  --org acme \
  --ttl 24h

# Output:
# eyJhbGciOiJIUzI1NiI...
# 
# Subject:   cs-contractor-nam
# Scopes:    [cs]
# Orgs:      [acme]
# Expires:   2026-05-18T16:00:00+00:00 (24h)
# 
# Send via Signal / Zalo (never email).
```

Flag reference:
- `--sub <name>` — required, for audit logs
- `--scope <s>` — required, can repeat (multi-scope tokens)
- `--org <id>` — required, default `default`. Use `*` for cross-org
- `--ttl <duration>` — default `24h`, max `7d`

## Backward Compatibility

`MEKONG_ADMIN_TOKEN` remains active even after JWT is implemented:

1. Verification tries legacy token first (exact string match)
2. Falls through to JWT decode if no match
3. Founder can rotate via either path independently

This means Phase 8 ships JWT support but doesn't break any Phase 6/7
clients. Migration is opt-in per client.

## Phase 8 Implementation Checklist (NOT done in P05)

Files to touch when ready:
- [ ] `requirements.txt` — add `PyJWT>=2.8`
- [ ] `src/services/admin_token_service.py` — new, ~80 LOC
  - `decode_jwt(token, secret) -> claims`
  - `check_scope(claims, required) -> bool`
  - `check_org(claims, request_org_id) -> bool`
- [ ] `src/api/vn_pilot_routes.py` — replace `_require_admin_token` with
  `_require_scope(required: list[str])` dependency factory
- [ ] `scripts/admin-token-issue.py` — CLI tool (gitignored, founder-local)
- [ ] `tests/vn/test_admin_scopes.py` — ~150 LOC
  - Legacy token still works (smoke test)
  - JWT with `founder` scope passes everywhere
  - JWT with `readonly` scope blocked on `/convert`
  - Expired JWT → 401
  - Wrong org JWT → 403
  - JWT with no scope claim → 403
- [ ] `docs/vn-admin-scopes-runbook.md` — operator guide
  - How to issue first token
  - How to rotate JWT secret
  - How to revoke (rotate secret → all tokens dead)

## Security Considerations

1. **Secret in env only** — `MEKONG_JWT_SECRET=REDACTED` never logged, never in
   code. 32+ bytes recommended (`secrets.token_urlsafe(32)`).
2. **Short TTL** — default 24h; longer requires explicit `--ttl`.
3. **Audit log** — every successful verify emits `[scope, org, sub]` to
   stdout (uvicorn structlog catches it).
4. **No refresh tokens** — re-issue via CLI is the only path; keeps
   surface tiny.
5. **Org boundary enforcement** — even `founder` scope is org-scoped
   unless `allowed_orgs=["*"]`. This compartmentalizes blast radius
   if a partner-org token leaks.
6. **Legacy token isolation** — `MEKONG_ADMIN_TOKEN` and
   `MEKONG_JWT_SECRET=REDACTED` are independent env vars; compromise of one
   doesn't compromise the other.
7. **Signature algorithm pinning** — only accept `HS256`; reject
   `none` / `RS256` algorithm headers to prevent JWT confusion attacks.

## Rotation Procedure (Phase 8 ops)

```bash
# 1. Generate new JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Update launchd plist EnvironmentVariables: MEKONG_JWT_SECRET=REDACTED=<new>

# 3. Kickstart gateway
sudo launchctl kickstart -k system/com.mekong.gateway

# 4. Re-issue all active JWTs (old ones now invalid; legacy admin token
#    still works as backdoor while you re-issue):
python3 scripts/admin-token-issue.py --sub "founder" --scope founder --org "*" --ttl 24h
# → re-send to each contractor via Signal

# 5. Old JWTs all dead within seconds (no DB cleanup needed)
```

## Tradeoffs & Alternatives Considered

### 1. OAuth2 + IdP (Auth0, Clerk, Supabase Auth)

- ✅ Industry standard, scales to social login
- ❌ Adds external SaaS dependency (cost + latency + ToS)
- ❌ Overkill for 4-scope use case
- **Verdict:** revisit at Phase 12+ (consumer-facing OPC accounts)

### 2. Mutual TLS (client certs)

- ✅ Strong cryptographic identity
- ❌ Cert distribution painful for non-tech contractors
- ❌ No org/scope encoding without cert extensions
- **Verdict:** Reject — operational burden too high

### 3. Static API key per scope (no JWT)

- ✅ Simplest possible
- ❌ Can't encode org boundary
- ❌ Can't expire individual keys without rotating shared secret
- **Verdict:** Reject — Phase 4 org boundary requires per-token claims

### 4. Session cookies + server-side store

- ✅ Browser-friendly
- ❌ API clients (curl, Zapier) ill-suited
- ❌ Requires session store infra
- **Verdict:** Reject — API-first product

## Phase 9+ Triggers (when to re-evaluate this design)

| Signal | Action |
|--------|--------|
| Team ≥ 3 CS members | Switch JWT → random+lookup for instant revoke |
| Multiple partner orgs ≥ 5 | Add per-org JWT secret (multi-tenant isolation) |
| Compliance audit requires audit trail | Add structured audit log persistence |
| External API integrations (Zapier, Make) | Add OAuth2 client credentials flow |

## Unresolved Questions (for founder review)

1. **TTL default** — 24h vs 7d? Shorter = more secure but more re-issuance
   friction. Recommend 24h, override with `--ttl` when needed.
2. **Revocation strategy** — accept that revocation = wait for expiry (TTL
   bounded), or implement deny-list early?
3. **Multi-org JWTs** — should a single token be able to claim multiple
   orgs (`allowed_orgs: ["acme", "beta"]`) or always single-org?
4. **Audit log persistence** — stdout only (current), or `~/.mekong/admin-audit.jsonl`?
   The latter helps SOC2 prep if Phase 12+ pursues compliance.

## Related Documents

- `plans/260517-0944-vn-hub-phase-7-scale-100-pilots/phase-05-role-based-admin-scopes.md` — original phase spec
- `docs/vn-multi-tenant-design.md` — Phase 04 org_id design (referenced via `allowed_orgs` claim)
- `docs/handoff-shipping-playbook.md` — overall handoff chain
- CLAUDE.md § "Admin token (founder-only write endpoints)" — current Phase 6 auth doc
