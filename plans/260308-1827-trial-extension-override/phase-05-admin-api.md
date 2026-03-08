---
title: "Phase 5: Admin API Endpoints"
priority: P1
status: pending
effort: 1.5h
---

# Phase 5: Admin API Endpoints

## Overview

Create admin-only API endpoints for managing trial extensions, following the existing pattern from `/internal/sync-suspension` endpoint.

## Endpoints

### POST /api/admin/trial/extend

**Purpose:** Grant trial extension to tenant

**Auth:** Service token (Bearer token in Authorization header)

**Request Body:**
```json
{
  "tenantId": "tenant-123",
  "extensionPeriodDays": 7,
  "reason": "Payment plan upgrade",
  "extendedBy": "admin-user-id"
}
```

**Response (200):**
```json
{
  "success": true,
  "tenantId": "tenant-123",
  "extendedUntil": "2026-03-15T18:30:00.000Z",
  "extensionPeriodDays": 7
}
```

**Response (400):**
```json
{
  "error": "Invalid request",
  "details": "Missing tenantId or extensionPeriodDays"
}
```

**Response (401):**
```json
{
  "error": "Unauthorized"
}
```

---

### GET /api/admin/trial/:tenantId

**Purpose:** Get trial extension status for tenant

**Auth:** Service token

**Response (200):**
```json
{
  "tenantId": "tenant-123",
  "hasExtension": true,
  "extendedUntil": "2026-03-15T18:30:00.000Z",
  "expiresIn": 518400,
  "reason": "Payment plan upgrade",
  "extendedBy": "admin-user-id",
  "createdAt": "2026-03-08T18:30:00.000Z"
}
```

**Response (404):**
```json
{
  "hasExtension": false,
  "tenantId": "tenant-123"
}
```

---

### DELETE /api/admin/trial/:tenantId

**Purpose:** Revoke trial extension

**Auth:** Service token

**Request Body (optional):**
```json
{
  "revokedBy": "admin-user-id",
  "reason": "Terms violation"
}
```

**Response (200):**
```json
{
  "success": true,
  "tenantId": "tenant-123",
  "revokedAt": "2026-03-08T19:00:00.000Z"
}
```

## Files to Modify

### `index.js`

Add new routes before the `/v1/*` proxy (before line 445):

```javascript
// --- ADMIN API: POST /api/admin/trial/extend ---
if (path === '/api/admin/trial/extend' && request.method === 'POST') {
  // Verify service token
  const authHeader = request.headers.get('Authorization') || '';
  const serviceToken = env.SERVICE_TOKEN || env.RAAS_SERVICE_TOKEN;

  if (!authHeader.startsWith('Bearer ') || authHeader.slice(7) !== serviceToken) {
    return jsonResponse({ error: 'Unauthorized' }, 401, corsHeaders);
  }

  try {
    const body = await request.json();
    const { tenantId, extensionPeriodDays, reason, extendedBy } = body;

    if (!tenantId || !extensionPeriodDays) {
      return jsonResponse({ error: 'Missing tenantId or extensionPeriodDays' }, 400, corsHeaders);
    }

    const result = await grantTrialExtension(env, tenantId, extensionPeriodDays, extendedBy, reason);

    return jsonResponse({
      success: true,
      tenantId,
      extendedUntil: result.extendedUntil,
      extensionPeriodDays
    }, 200, corsHeaders);
  } catch (error) {
    return jsonResponse({ error: 'Invalid request', details: error.message }, 400, corsHeaders);
  }
}

// --- ADMIN API: GET /api/admin/trial/:tenantId ---
if (path.startsWith('/api/admin/trial/') && request.method === 'GET') {
  // Verify service token
  const authHeader = request.headers.get('Authorization') || '';
  const serviceToken = env.SERVICE_TOKEN || env.RAAS_SERVICE_TOKEN;

  if (!authHeader.startsWith('Bearer ') || authHeader.slice(7) !== serviceToken) {
    return jsonResponse({ error: 'Unauthorized' }, 401, corsHeaders);
  }

  const tenantId = path.split('/').pop();

  return getTrialExtension(env, tenantId).then(result => {
    if (!result.extension) {
      return jsonResponse({ hasExtension: false, tenantId }, 404, corsHeaders);
    }
    return jsonResponse({
      tenantId,
      hasExtension: true,
      ...result.extension,
      expiresIn: result.expiresIn
    }, 200, corsHeaders);
  });
}

// --- ADMIN API: DELETE /api/admin/trial/:tenantId ---
if (path.startsWith('/api/admin/trial/') && request.method === 'DELETE') {
  // Verify service token
  const authHeader = request.headers.get('Authorization') || '';
  const serviceToken = env.SERVICE_TOKEN || env.RAAS_SERVICE_TOKEN;

  if (!authHeader.startsWith('Bearer ') || authHeader.slice(7) !== serviceToken) {
    return jsonResponse({ error: 'Unauthorized' }, 401, corsHeaders);
  }

  const tenantId = path.split('/').pop();

  return revokeTrialExtension(env, tenantId).then(result => {
    return jsonResponse({
      success: result.success,
      tenantId,
      revokedAt: new Date().toISOString()
    }, result.success ? 200 : 500, corsHeaders);
  });
}
```

## Implementation Steps

- [ ] Add imports at top of `index.js`:
  ```javascript
  import { grantTrialExtension, getTrialExtension, revokeTrialExtension } from './src/kv-trial-extension.js';
  ```
- [ ] Add POST /api/admin/trial/extend route
- [ ] Add GET /api/admin/trial/:tenantId route
- [ ] Add DELETE /api/admin/trial/:tenantId route
- [ ] Test with curl commands

## Testing Commands

```bash
# Extend trial
curl -X POST https://raas.agencyos.network/api/admin/trial/extend \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenantId":"test-tenant","extensionPeriodDays":7,"reason":"Test","extendedBy":"admin"}'

# Get trial status
curl -X GET https://raas.agencyos.network/api/admin/trial/test-tenant \
  -H "Authorization: Bearer $SERVICE_TOKEN"

# Revoke trial
curl -X DELETE https://raas.agencyos.network/api/admin/trial/test-tenant \
  -H "Authorization: Bearer $SERVICE_TOKEN"
```

## Success Criteria

```bash
# Admin routes added
grep -c "/api/admin/trial" index.js
# Should be >= 3

# Service token auth in each route
grep -A5 "api/admin/trial" index.js | grep -c "SERVICE_TOKEN"
# Should be >= 3

# No syntax errors
node --check index.js
```

## Dependencies

- Phase 1 complete (trial extension functions)
- SERVICE_TOKEN configured in environment

## Security Notes

- Service token required for all admin endpoints
- No tenant can manage their own trial extension
- All actions logged via analytics (Phase 4)
