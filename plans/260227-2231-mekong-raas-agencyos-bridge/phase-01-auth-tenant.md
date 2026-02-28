# Phase 01: Auth & Multi-Tenant Isolation

## Context Links
- [Research: Open Core Models](research/researcher-01-open-core-raas-models.md)
- [Existing gateway auth](../../src/core/gateway.py) — `verify_token()` line 223
- [AGI Bridge](../../src/agents/agi_bridge.py) — single-tenant dispatch

## Overview
- **Priority:** P1
- **Status:** pending
- **Group:** A (parallel with Phase 02, 03)
- **Est:** 3h

API key auth + tenant context propagation. Each agency gets isolated task namespace.

## Key Insights
- Current auth = single `MEKONG_API_TOKEN` env var (gateway.py:223)
- Multi-tenant needs: API key -> tenant_id lookup -> namespace isolation in tasks/
- Keep simple: no OAuth/SSO for v1. Bearer token per tenant.
- Tenant isolation via directory prefix: `tasks/{tenant_id}/mission_*.txt`

## Requirements

### Functional
- Generate API keys per tenant (uuid4 + prefix `mk_`)
- Validate Bearer token on every RaaS endpoint
- Inject `tenant_id` into request context (Pydantic model)
- Tenant-scoped task directories: `tasks/{tenant_id}/`

### Non-Functional
- Key validation < 5ms (in-memory dict, loaded from SQLite)
- Max 1000 tenants for v1 (SQLite sufficient)
- No secrets in codebase

## Architecture

```
Request (Bearer mk_xxx)
    -> auth middleware extracts tenant_id
    -> injects TenantContext into handler
    -> missions scoped to tasks/{tenant_id}/
```

## File Ownership (EXCLUSIVE)

| Action | File |
|--------|------|
| CREATE | `src/raas/__init__.py` |
| CREATE | `src/raas/auth.py` |
| CREATE | `src/raas/tenant.py` |

## Implementation Steps

1. Create `src/raas/__init__.py` — package init, version
2. Create `src/raas/tenant.py`:
   - `Tenant` dataclass: id, name, api_key, credits_balance, created_at, is_active
   - `TenantStore` class: SQLite-backed CRUD
   - `create_tenant(name) -> Tenant` — generates `mk_` prefixed API key
   - `get_by_api_key(key) -> Optional[Tenant]`
   - `list_tenants() -> List[Tenant]`
   - SQLite path: `~/.mekong/raas/tenants.db`
3. Create `src/raas/auth.py`:
   - `TenantContext` Pydantic model: tenant_id, tenant_name, api_key
   - `get_tenant_context(request) -> TenantContext` — FastAPI dependency
   - Extracts `Authorization: Bearer mk_xxx`, looks up in TenantStore
   - Returns 401 if invalid, 403 if tenant disabled
   - Caches recent lookups in LRU (maxsize=256)

## Todo List
- [ ] Create `src/raas/` package
- [ ] Implement `TenantStore` with SQLite backend
- [ ] Implement `auth.py` with FastAPI dependency injection
- [ ] Add tenant creation CLI command (`mekong raas tenant create <name>`)
- [ ] Unit tests: `tests/test_raas_auth.py`

## Success Criteria
- `TenantStore.create_tenant("84tea")` returns valid Tenant with `mk_` key
- Bearer token auth rejects invalid keys with 401
- Disabled tenants return 403
- Tests pass: `pytest tests/test_raas_auth.py`

## Risk Assessment
- **SQLite concurrency:** Low risk — single writer, reads cached. Mitigate: WAL mode.
- **Key rotation:** Deferred to v2. v1 = regenerate key = new key, old invalidated.

## Security Considerations
- API keys stored hashed (sha256) in SQLite; plaintext shown only at creation
- Rate limiting per tenant deferred to Phase 04 (dashboard layer)
- No PII in tenant record beyond name
