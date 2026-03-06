# License Management UI Plan - PHASE 2/5

**Date:** 2026-03-06
**Phase:** ROIaaS PHASE 2/5
**Goal:** Local web UI cho license management

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  mekong license-ui --port 8080                          │
│    │                                                     │
│    ▼ FastAPI server                                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │  src/api/license_ui.py                           │    │
│  │    - GET  /              → License Dashboard     │    │
│  │    - GET  /api/status    → License status JSON   │    │
│  │    - POST /api/activate  → Activate license      │    │
│  │    - POST /api/validate  → Validate license      │    │
│  └─────────────────────────────────────────────────┘    │
│    │                                                     │
│    ▼ HTML templates                                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │  src/api/templates/license_dashboard.html        │    │
│  │    - React-like UI với vanilla JS                │    │
│  │    - Real-time status updates                    │    │
│  │    - Form validation & feedback                  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Tasks

### Phase 1: API Endpoints
- [ ] Create `src/api/license_ui.py`
- [ ] GET `/` - Dashboard HTML
- [ ] GET `/api/status` - License status JSON
- [ ] POST `/api/activate` - Activate license key
- [ ] POST `/api/validate` - Validate license key

### Phase 2: HTML Template
- [ ] Create `src/api/templates/license_dashboard.html`
- [ ] License status card (valid/invalid/expired)
- [ ] Activation form with validation
- [ ] Visual feedback (success/error states)
- [ ] Tier features comparison table

### Phase 3: Persistence
- [ ] Save to `.env` file
- [ ] Update process.env.RAAS_LICENSE_KEY
- [ ] Clear license (deactivate)

### Phase 4: CLI Command
- [ ] Add `mekong license-ui` command
- [ ] Start FastAPI server
- [ ] Auto-open browser

### Phase 5: Testing
- [ ] Unit tests for API endpoints
- [ ] Integration tests
- [ ] UI validation tests

---

## Success Criteria

- [ ] `mekong license-ui` starts web server
- [ ] Browser opens automatically
- [ ] Status displays correctly
- [ ] Activate/deactivate works
- [ ] Persists to .env file
- [ ] Tests pass
