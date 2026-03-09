---
title: "Phase 6: Tests and Validation"
description: "Comprehensive tests for all Phase 6 components"
status: pending
priority: P1
effort: 1.5h
branch: master
tags: [phase-6, testing, validation]
created: 2026-03-09
---

# Phase 6: Tests and Validation

## Overview

Write comprehensive tests for all Phase 6 components and validate end-to-end flow.

## Requirements

1. Unit tests for each component
2. Integration tests for Gateway ↔ CLI flow
3. End-to-end test with mock server
4. Security tests for signature verification
5. All existing tests must pass (62 tests)

## Test Plan

### Unit Tests

| Module | Tests |
|--------|-------|
| `UpdateChecker` | should_check(), check_version(), notify_if_available() |
| `Ed25519Verifier` | verify_valid_signature(), verify_invalid_signature() |
| `UsageTracker` | track_update_event() deduplication |
| Critical enforcement | block_on_critical(), bypass_for_help() |

### Integration Tests

| Flow | Tests |
|------|-------|
| Gateway version endpoint | Auth, rate limiting, usage tracking |
| CLI startup check | Cache, async behavior, notification |
| Update download + verify | Full flow with mock release |

### End-to-End Tests

| Scenario | Expected |
|----------|----------|
| Normal update available | Notification shown, install works |
| Critical update | CLI blocked until update |
| No internet | Fail silent, use cached |
| Invalid signature | Block update, error message |
| Gateway down | Fallback to GitHub Releases |

## Context Links

- Existing tests: `/Users/macbookprom1/mekong-cli/tests/`
- Test runner: `python3 -m pytest`

## Implementation Steps

1. **Create test files** for new modules
2. **Mock Gateway responses** for offline testing
3. **Add integration tests** with test server
4. **Run full test suite**
5. **Fix any failures**

## Related Code Files

**To Create:**
- `tests/core/test_update_checker.py`
- `tests/core/test_signature_verifier.py`
- `tests/cli/test_update_flow.py`
- `tests/integration/test_gateway_version.py`

**To Modify:**
- (None - new tests only)

## Todo List

- [ ] Create `test_update_checker.py` with unit tests
- [ ] Create `test_signature_verifier.py` with crypto tests
- [ ] Create `test_update_flow.py` with integration tests
- [ ] Create `test_gateway_version.py` for endpoint
- [ ] Add mock server for e2e tests
- [ ] Run full test suite (`python3 -m pytest`)
- [ ] Fix any failures
- [ ] Verify 100% test pass rate

## Success Criteria

- [ ] All new tests pass
- [ ] All existing 62 tests pass
- [ ] No test takes > 10s
- [ ] Coverage maintained or improved
- [ ] E2E flow works with mock server

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tests flaky | Medium | Retry logic, stable mocks |
| Crypto tests slow | Low | Small test data, cache keys |
| Gateway tests need network | Medium | Mock responses, skip if offline |

## Security Considerations

- Use test-only keys for signature tests
- Don't expose real private keys in tests
- Mock sensitive operations

## Unresolved Questions

1. Should e2e tests run in CI or only locally?
2. How to test critical update enforcement without blocking test runner?
