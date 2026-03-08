---
title: "Phase 6: Testing"
priority: P1
status: pending
effort: 1.25h
---

# Phase 6: Testing

## Overview

Create comprehensive unit and integration tests for trial extension system, following the existing test pattern from `kv-suspension-checker.test.js`.

## Test Files to Create

### `tests/kv-trial-extension.test.js`

**Test Suites:**

1. **checkTrialExtension()**
   - Returns false when KV not configured
   - Returns false when no extension exists
   - Returns true when extension exists and not expired
   - Returns false when extension expired
   - Calculates expiresIn correctly
   - Handles KV read errors (fail-open)

2. **grantTrialExtension()**
   - Writes to KV with correct key format
   - Sets correct TTL
   - Returns extendedUntil date
   - Handles KV write errors

3. **revokeTrialExtension()**
   - Deletes from KV
   - Returns success true
   - Handles KV delete errors

4. **getTrialExtension()**
   - Returns full extension object
   - Returns null when no extension
   - Calculates expiresIn correctly

5. **buildTrialStatusHeader()**
   - Returns correct headers for active trial
   - Returns correct headers for no trial

### `tests/kv-trial-extension-integration.test.js`

**Integration Tests:**

1. Full flow: grant → check → revoke
2. Expiration handling
3. Admin API endpoint tests
4. Suspension bypass prevention test

## Test Patterns

Follow existing pattern from `kv-suspension-checker.test.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  checkTrialExtension,
  grantTrialExtension,
  revokeTrialExtension,
  getTrialExtension,
  buildTrialStatusHeader
} from '../src/kv-trial-extension.js';

describe('checkTrialExtension', () => {
  it('should return false when KV not configured', async () => {
    const result = await checkTrialExtension({}, 'tenant-123');
    expect(result.hasExtension).toBe(false);
  });

  it('should return false when no extension exists', async () => {
    const mockKV = { get: vi.fn().mockResolvedValue(null) };
    const result = await checkTrialExtension({ TRIAL_EXTENSIONS: mockKV }, 'tenant-123');
    expect(result.hasExtension).toBe(false);
  });

  it('should return true when extension exists and not expired', async () => {
    const futureDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const mockKV = {
      get: vi.fn().mockResolvedValue({ extendedUntil: futureDate })
    };
    const result = await checkTrialExtension({ TRIAL_EXTENSIONS: mockKV }, 'tenant-123');
    expect(result.hasExtension).toBe(true);
    expect(result.expiresIn).toBeGreaterThan(0);
  });
});
```

## Implementation Steps

- [ ] Read `kv-suspension-checker.test.js` for pattern
- [ ] Create `tests/kv-trial-extension.test.js` with unit tests
- [ ] Create `tests/kv-trial-extension-integration.test.js` with integration tests
- [ ] Run tests with `npm test` or `vitest run`
- [ ] Fix any failing tests

## Test Coverage Targets

| Function | Min Coverage |
|----------|--------------|
| checkTrialExtension | 90% |
| grantTrialExtension | 90% |
| revokeTrialExtension | 90% |
| getTrialExtension | 90% |
| buildTrialStatusHeader | 100% |

## Success Criteria

```bash
# Test files exist
ls -la tests/kv-trial-extension*.test.js

# All tests pass
vitest run tests/kv-trial-extension.test.js

# Coverage report shows targets met
vitest run --coverage tests/kv-trial-extension.test.js
```

## Manual Testing

```bash
# 1. Grant extension
curl -X POST http://localhost:8787/api/admin/trial/extend \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"tenantId":"test-123","extensionPeriodDays":7,"reason":"Test","extendedBy":"test-admin"}'

# 2. Check extension via auth validate
curl -X POST http://localhost:8787/v1/auth/validate \
  -H "Authorization: Bearer valid-jwt" \
  -H "X-User-Id: test-123"

# 3. Get extension details
curl -X GET http://localhost:8787/api/admin/trial/test-123 \
  -H "Authorization: Bearer test-token"

# 4. Revoke extension
curl -X DELETE http://localhost:8787/api/admin/trial/test-123 \
  -H "Authorization: Bearer test-token"

# 5. Verify revoked
curl -X GET http://localhost:8787/api/admin/trial/test-123 \
  -H "Authorization: Bearer test-token"
# Should return 404
```

## Dependencies

- Phases 1-5 complete
- Vitest configured in project

## Risks

- KV testing requires mocks → Mitigation: Use vi.fn() for KV operations
- Time-based tests flaky → Mitigation: Use fixed timestamps in tests
