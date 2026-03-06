---
title: "ROIaaS Phase 2 - License Admin Dashboard"
description: "Admin dashboard for license key CRUD operations with audit logs"
status: pending
priority: P1
effort: 6h
branch: master
tags: [roiaas, license, admin, dashboard, phase-2]
created: 2026-03-06
---

# ROIaaS Phase 2 - License Admin Dashboard

## Overview

Admin dashboard for managing license keys with full CRUD operations and audit logging.
Part of ROIaaS 5-phase delivery (Phase 2/5: LICENSE UI).

## Current State Analysis

**Existing Components:**
- `src/lib/license_generator.py` - Key generation with HMAC signing
- `src/api/license_server.py` - FastAPI validation API (port 8787)
- `src/api/license_ui.py` - Web UI for license activation (port 8080)
- `src/api/license_dashboard.html` - HTML template (basic activate/validate)
- `src/commands/license_commands.py` - CLI commands (generate, validate, revoke, status)
- `src/raas/license_cli.py` - Alternative CLI with tier management
- `src/db/schema.py` - PostgreSQL schema (licenses, usage_records, revocations, webhook_events)
- `src/db/repository.py` - CRUD operations with async PostgreSQL

**Gaps (Phase 2 Requirements):**
1. ❌ No admin dashboard for viewing ALL keys
2. ❌ No audit logs (who created/revoked when)
3. ❌ No bulk operations
4. ❌ No web-based admin UI (only user-facing activation UI exists)
5. ❌ Revocation uses JSON file, not PostgreSQL

## Requirements

### Functional
1. **Create License Keys** - Generate single or bulk keys (admin-only)
2. **Revoke License Keys** - Revoke with reason, logged to audit trail
3. **View All Keys** - Paginated table with filters (tier, status, date)
4. **Audit Logs** - Track all admin actions (create, revoke, update)
5. **Dashboard UI** - Web admin panel OR terminal dashboard

### Non-Functional
- Admin authentication required
- PostgreSQL for all data (no JSON files)
- Real-time status updates
- Export to CSV/JSON

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   License Admin Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Web Admin UI│  │Terminal Dash│  │ API Endpoints       │  │
│  │ (FastAPI)   │  │ (Rich/Typer)│  │ /admin/licenses/*   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┴─────────────────────┘            │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │ AdminService      │                    │
│                    │ - create_key()    │                    │
│                    │ - revoke_key()    │                    │
│                    │ - list_keys()     │                    │
│                    │ - get_audit_logs()│                    │
│                    └─────────┬─────────┘                    │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │ LicenseRepository │                    │
│                    └─────────┬─────────┘                    │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │   PostgreSQL DB   │                    │
│                    │ - licenses        │                    │
│                    │ - revocations     │                    │
│                    │ - audit_logs NEW  │                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Files to Create

### Core Backend
1. `src/api/admin_license_service.py` - Admin business logic
2. `src/api/admin_routes.py` - FastAPI admin endpoints
3. `src/api/templates/admin_dashboard.html` - Web admin UI

### Database
4. `src/db/schema.py` - Add `audit_logs` table migration
5. `src/db/repository.py` - Add audit log CRUD methods

### CLI
6. `src/commands/license_admin.py` - Terminal admin commands

### Tests
7. `tests/test_license_admin.py` - Admin API tests
8. `tests/test_audit_logs.py` - Audit logging tests

## Files to Modify

1. `src/api/license_ui.py` - Add admin route imports
2. `src/commands/license_commands.py` - Add admin subcommands
3. `src/db/migrate.py` - Add audit_logs migration

## Implementation Phases

### Phase 2.1: Database Schema (30 min)
- [ ] Add `audit_logs` table to schema
- [ ] Add `created_by` column to `licenses` table
- [ ] Create migration file

### Phase 2.2: Backend Service (1.5h)
- [ ] Create `AdminLicenseService` class
- [ ] Implement `create_key()` with audit logging
- [ ] Implement `revoke_key()` with reason tracking
- [ ] Implement `list_keys()` with pagination/filters
- [ ] Implement `get_audit_logs()` with filters

### Phase 2.3: API Endpoints (1h)
- [ ] POST `/api/admin/licenses` - Create key(s)
- [ ] GET `/api/admin/licenses` - List all keys
- [ ] GET `/api/admin/licenses/{key_id}` - Get single key
- [ ] POST `/api/admin/licenses/{key_id}/revoke` - Revoke key
- [ ] GET `/api/admin/audit-logs` - Get audit logs
- [ ] Add admin auth middleware

### Phase 2.4: Web Admin UI (2h)
- [ ] Create `admin_dashboard.html` template
- [ ] License keys table with filters
- [ ] Create/Revoke modals
- [ ] Audit logs viewer
- [ ] Export to CSV button

### Phase 2.5: Terminal Dashboard (1h)
- [ ] Create `license_admin.py` CLI commands
- [ ] `mekong license-admin list` - List all keys
- [ ] `mekong license-admin create` - Create key(s)
- [ ] `mekong license-admin revoke` - Revoke with reason
- [ ] `mekong license-admin audit` - View audit logs
- [ ] `mekong license-admin ui` - Launch terminal UI

### Phase 2.6: Testing & Polish (30 min)
- [ ] Write unit tests for service layer
- [ ] Write integration tests for API
- [ ] Manual testing of web UI
- [ ] Documentation in docs/

## Data Models

### Audit Log Schema
```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,        -- CREATE, REVOKE, UPDATE, VIEW
    entity_type VARCHAR(50) NOT NULL,   -- LICENSE, KEY, USER
    entity_id VARCHAR(255) NOT NULL,    -- key_id or license id
    actor_email VARCHAR(255) NOT NULL,  -- Who performed action
    actor_ip VARCHAR(45),               -- IP address
    details JSONB DEFAULT '{}',         -- Action-specific details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
```

### API Request/Response Types

```python
# Create License Request
class CreateLicenseRequest(BaseModel):
    tier: str  # free, trial, pro, enterprise
    email: str
    days: Optional[int] = None  # For trial
    quantity: int = 1  # Bulk create
    notes: Optional[str] = None

# Create License Response
class CreateLicenseResponse(BaseModel):
    keys: List[str]  # Generated keys
    license_ids: List[int]
    tier: str
    created_at: datetime

# List Licenses Response
class LicenseListResponse(BaseModel):
    items: List[LicenseInfo]
    total: int
    page: int
    page_size: int
    total_pages: int

class LicenseInfo(BaseModel):
    id: int
    key_id: str
    tier: str
    email: str
    status: str  # active, revoked, expired
    created_at: datetime
    created_by: str
    revoked_at: Optional[datetime]
    revoked_by: Optional[str]

# Revoke Request
class RevokeLicenseRequest(BaseModel):
    reason: str
    notes: Optional[str] = None
```

## Success Criteria

- [ ] Admin can create single/bulk license keys
- [ ] Admin can revoke keys with reason (logged)
- [ ] Admin can view all keys with filters
- [ ] All actions logged to audit_logs table
- [ ] Web dashboard accessible at `/admin`
- [ ] Terminal dashboard via `mekong license-admin`
- [ ] 100% test coverage for service layer
- [ ] No JSON file usage for revocation

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Admin auth bypass | High | Add API key middleware |
| Audit log tampering | High | Immutable append-only logs |
| Performance on large datasets | Medium | Pagination + indexes |
| Sensitive data exposure | High | Mask keys in responses |

## Security Considerations

1. **Admin Authentication**: API key or JWT required for `/api/admin/*`
2. **Audit Immutability**: Audit logs are append-only (no UPDATE/DELETE)
3. **Key Masking**: Show partial keys in UI (e.g., `raas-pro-abc***xyz`)
4. **IP Logging**: Log admin IP for all actions
5. **Rate Limiting**: Strict rate limits on admin endpoints

## Next Steps

1. Review and approve plan
2. Implement Phase 2.1 (Database Schema)
3. Implement Phase 2.2 (Backend Service)
4. Continue through remaining phases
5. Test and deploy

---

## Related Documents

- `docs/HIEN_PHAP_ROIAAS.md` - ROIaaS Constitution
- `src/db/schema.py` - Current database schema
- `src/api/license_ui.py` - Existing license UI
- `plans/reports/` - Research reports (if any)
