---
title: "Phase 8: Testing"
priority: P1
status: pending
effort: 2h
---

# Phase 8: Testing (OAuth2 + RBAC + Stripe)

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Previous phases:** All implementation phases complete

## Overview

Comprehensive test suite for OAuth2 flow, RBAC enforcement, and Stripe integration.

## Requirements

### Functional
- OAuth2 flow tests (Google, GitHub)
- RBAC enforcement tests
- Stripe integration tests
- Security tests (CORS, CSRF, XSS)

### Non-functional
- > 80% code coverage
- All critical paths tested
- Security vulnerabilities covered

## Test Coverage

```
┌─────────────────────────────────────────────────────────────┐
│                     Test Categories                         │
├─────────────────────────────────────────────────────────────┤
│ 1. OAuth2 Flow Tests                                        │
│    - Google login redirect                                  │
│    - GitHub login redirect                                  │
│    - Callback handling                                      │
│    - User creation on first login                           │
│    - User upsert on subsequent login                        │
│                                                             │
│ 2. Session Management Tests                                 │
│    - JWT token generation                                   │
│    - JWT token validation                                   │
│    - Cookie security settings                               │
│    - Session invalidation (logout)                          │
│                                                             │
│ 3. RBAC Enforcement Tests                                   │
│    - Role hierarchy enforcement                             │
│    - Permission decorator blocking                          │
│    - Middleware role injection                              │
│    - Unauthorized access handling                           │
│                                                             │
│ 4. Stripe Integration Tests                                 │
│    - Customer → User linking                                │
│    - Subscription → role sync                               │
│    - Webhook signature verification                         │
│    - Subscription cancellation (downgrade)                  │
│                                                             │
│ 5. Security Tests                                           │
│    - CSRF token validation                                  │
│    - CORS configuration                                     │
│    - XSS prevention                                         │
│    - Rate limiting                                          │
│                                                             │
│ 6. Environment Mode Tests                                   │
│    - Dev mode auth bypass                                   │
│    - Prod mode auth enforcement                             │
│    - Missing secrets error handling                         │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

1. **Create OAuth2 tests** `tests/test_oauth2.py`
   ```python
   import pytest
   from httpx import AsyncClient
   from src.main import app

   @pytest.mark.asyncio
   async def test_google_login_redirect():
       """Test Google OAuth2 redirect."""
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.get("/auth/google")
           assert response.status_code == 307
           assert "accounts.google.com" in response.headers["location"]

   @pytest.mark.asyncio
   async def test_github_login_redirect():
       """Test GitHub OAuth2 redirect."""
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.get("/auth/github")
           assert response.status_code == 307
           assert "github.com/login" in response.headers["location"]

   @pytest.mark.asyncio
   async def test_google_callback_creates_user():
       """Test user creation on Google OAuth callback."""
       # Mock OAuth2 token exchange
       # Mock user info response
       # Assert user created in database
       pass

   @pytest.mark.asyncio
   async def test_callback_sets_session_cookie():
       """Test session cookie set after OAuth callback."""
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.get("/auth/google/callback?code=test-code")
           assert "session_token" in response.cookies
           assert response.cookies["session_token"].httponly
   ```

2. **Create RBAC tests** `tests/test_rbac.py`
   ```python
   import pytest
   from src.auth.rbac_config import Role
   from src.auth.rbac_decorators import require_role

   @pytest.mark.asyncio
   async def test_role_hierarchy_owner():
       """Test owner role has all permissions."""
       # Owner can access admin routes
       pass

   @pytest.mark.asyncio
   async def test_role_hierarchy_viewer_blocked():
       """Test viewer cannot access write routes."""
       # Viewer blocked from POST/PUT/DELETE
       pass

   @pytest.mark.asyncio
   async def test_unauthorized_access():
       """Test unauthenticated access returns 401."""
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.get("/admin/users")
           assert response.status_code == 401

   @pytest.mark.asyncio
   async def test_forbidden_access():
       """Test insufficient role returns 403."""
       # Login as viewer, try admin route
       pass
   ```

3. **Create Stripe tests** `tests/test_stripe_integration.py`
   ```python
   import pytest
   from stripe import Webhook
   from src.stripe.sync_service import StripeSyncService

   @pytest.mark.asyncio
   async def test_webhook_signature_valid():
       """Test valid webhook signature."""
       payload = b'{"type": "customer.subscription.updated"}'
       sig_header = generate_test_signature(payload)
       event = Webhook.construct_event(
           payload, sig_header, "whsec_test_secret"
       )
       assert event["type"] == "customer.subscription.updated"

   @pytest.mark.asyncio
   async def test_webhook_signature_invalid():
       """Test invalid webhook signature rejected."""
       with pytest.raises(SignatureVerificationError):
           Webhook.construct_event(
               b"tampered payload", "invalid_sig", "whsec_test_secret"
           )

   @pytest.mark.asyncio
   async def test_subscription_sync_updates_role():
       """Test subscription sync updates user role."""
       # Create test user
       # Sync with Stripe subscription
       # Assert role matches subscription tier
       pass
   ```

4. **Create security tests** `tests/test_security.py`
   ```python
   import pytest
   from httpx import AsyncClient

   @pytest.mark.asyncio
   async def test_csrf_protection():
       """Test CSRF token required for mutations."""
       pass

   @pytest.mark.asyncio
   async def test_cors_configuration():
       """Test CORS headers correctly configured."""
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.options(
               "/api/test",
               headers={"Origin": "https://allowed-domain.com"}
           )
           assert response.headers.get("access-control-allow-origin")

   @pytest.mark.asyncio
   async def test_xss_prevention():
       """Test XSS input sanitization."""
       pass

   @pytest.mark.asyncio
   async def test_rate_limiting():
       """Test rate limiter blocks excess requests."""
       pass
   ```

5. **Create environment tests** `tests/test_auth_environment.py`
   ```python
   import pytest
   import os
   from src.config.auth_config import AuthConfig, AuthEnvironment

   def test_dev_mode_auth_disabled():
       """Test dev mode disables auth."""
       os.environ["AUTH_ENVIRONMENT"] = "dev"
       assert AuthConfig.AUTH_DISABLED is True

   def test_prod_mode_auth_enforced():
       """Test prod mode enforces auth."""
       os.environ["AUTH_ENVIRONMENT"] = "production"
       assert AuthConfig.AUTH_DISABLED is False
       assert AuthConfig.require_auth() is True

   def test_missing_oauth_secrets_prod():
       """Test error if OAuth secrets missing in prod."""
       os.environ["AUTH_ENVIRONMENT"] = "production"
       os.environ.pop("GOOGLE_CLIENT_ID", None)
       # Should raise ConfigurationError
   ```

## Todo List

- [ ] Create `tests/test_oauth2.py`
- [ ] Create `tests/test_rbac.py`
- [ ] Create `tests/test_stripe_integration.py`
- [ ] Create `tests/test_security.py`
- [ ] Create `tests/test_auth_environment.py`
- [ ] Run test suite and fix failures
- [ ] Generate coverage report

## Success Criteria

- [ ] All tests passing
- [ ] > 80% code coverage
- [ ] No critical security issues
- [ ] CI/CD pipeline green

## Test Commands

```bash
# Run all auth tests
python -m pytest tests/test_oauth2.py tests/test_rbac.py tests/test_stripe_integration.py -v

# Run with coverage
python -m pytest --cov=src/auth --cov=src/stripe --cov-report=html

# Security tests
python -m pytest tests/test_security.py -v
```

## Next Steps

→ Implementation complete! Deploy to staging for integration testing.
