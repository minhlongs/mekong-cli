---
title: "Phase 6: Environment Configuration"
priority: P1
status: pending
effort: 1h
---

# Phase 6: Environment Configuration (Dev/Prod Modes)

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Phase 2:** [phase-02-oauth2-providers.md](phase-02-oauth2-providers.md)

## Overview

Implement environment-aware authentication: disabled in dev, enforced in production.

## Key Insights

- `AUTH_ENVIRONMENT` variable controls auth mode
- Dev mode: skip auth checks, auto-login as test user
- Prod mode: enforce all auth requirements

## Requirements

### Functional
- `AUTH_ENVIRONMENT` detection (dev/staging/prod)
- Dev mode: auth disabled, auto-login
- Prod mode: auth fully enforced
- Secure secrets management

### Non-functional
- Zero friction in dev mode
- Maximum security in prod mode
- Clear indicators of current mode

## Architecture

```
Environment Detection:
┌────────────────┬─────────────────┬────────────────────────────┐
│ AUTH_ENVIRONMENT│ Auth Mode       │ Behavior                  │
├────────────────┼─────────────────┼────────────────────────────┤
│ dev            │ Disabled        │ Skip checks, auto-login    │
│ staging        │ Enabled (soft)  │ Warn but allow             │
│ production     │ Enabled (hard)  │ Enforce all checks         │
└────────────────┴─────────────────┴────────────────────────────┘
```

## Implementation Steps

1. **Create environment config** `src/config/auth_config.py`
   ```python
   import os
   from enum import Enum

   class AuthEnvironment(str, Enum):
       DEV = "dev"
       STAGING = "staging"
       PRODUCTION = "production"

   class AuthConfig:
       ENVIRONMENT = AuthEnvironment(os.getenv("AUTH_ENVIRONMENT", "dev"))
       AUTH_DISABLED = ENVIRONMENT == AuthEnvironment.DEV

       # OAuth2 settings
       GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
       GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
       GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
       GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

       # JWT settings
       JWT_SECRET=REDACTED_KEY = os.getenv("JWT_SECRET=REDACTED_KEY", "dev-secret-change-in-prod")
       SESSION_COOKIE_SECURE = ENVIRONMENT == AuthEnvironment.PRODUCTION
       SESSION_COOKIE_SAMESITE = "lax" if ENVIRONMENT == AuthEnvironment.DEV else "strict"

       @classmethod
       def is_dev_mode(cls) -> bool:
           return cls.ENVIRONMENT == AuthEnvironment.DEV

       @classmethod
       def is_production_mode(cls) -> bool:
           return cls.ENVIRONMENT == AuthEnvironment.PRODUCTION

       @classmethod
       def require_auth(cls) -> bool:
           return not cls.AUTH_DISABLED
   ```

2. **Create auth bypass decorator** `src/auth/auth_bypass.py`
   ```python
   from functools import wraps
   from src.config.auth_config import AuthConfig

   def optional_auth(func):
       """Skip auth check in dev mode."""
       @wraps(func)
       async def wrapper(*args, **kwargs):
           if AuthConfig.is_dev_mode():
               # Auto-inject test user context
               from unittest.mock import MagicMock
               request = args[0] if args else kwargs.get("request")
               if request:
                   request.state.user = MagicMock(id="test-user", email="test@dev.local")
                   request.state.authenticated = True
                   request.state.user_role = "owner"
               return await func(*args, **kwargs)

           # Normal auth enforcement in prod
           return await func(*args, **kwargs)
       return wrapper
   ```

3. **Update middleware** `src/auth/session_middleware.py`
   ```python
   from src.config.auth_config import AuthConfig

   class SessionMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           # Skip auth in dev mode
           if AuthConfig.is_dev_mode():
               request.state.authenticated = True
               request.state.user_role = "owner"
               response = await call_next(request)
               return response

           # Normal auth flow in prod
           token = request.cookies.get("session_token")
           # ... existing auth logic
   ```

4. **Add environment indicator** `src/api/routes/health.py`
   ```python
   @router.get("/health")
   async def health_check():
       from src.config.auth_config import AuthConfig
       return {
           "status": "healthy",
           "auth_environment": AuthConfig.ENVIRONMENT.value,
           "auth_enabled": AuthConfig.require_auth(),
       }
   ```

5. **Update `.env.example`**
   ```bash
   # Auth Environment
   AUTH_ENVIRONMENT=dev  # dev|staging|production

   # OAuth2 - Google
   GOOGLE_CLIENT_ID=
   GOOGLE_CLIENT_SECRET=
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

   # OAuth2 - GitHub
   GITHUB_CLIENT_ID=
   GITHUB_CLIENT_SECRET=
   GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

   # JWT
   JWT_SECRET=REDACTED_KEY=change-this-in-production

   # Stripe
   STRIPE_SECRET_KEY=
   STRIPE_WEBHOOK_SECRET=
   ```

## Todo List

- [ ] Create `src/config/auth_config.py`
- [ ] Create `src/auth/auth_bypass.py`
- [ ] Update session middleware for dev mode
- [ ] Add health check endpoint
- [ ] Update `.env.example`

## Success Criteria

- [ ] Dev mode skips all auth checks
- [ ] Prod mode enforces all auth checks
- [ ] Health endpoint shows current mode
- [ ] Clear error if OAuth secrets missing in prod

## Risk Assessment

- **Risk:** Dev mode accidentally enabled in prod
- **Mitigation:** CI/CD check for `AUTH_ENVIRONMENT=production`

## Security Considerations

- Default JWT secret only for dev
- Cookie security settings vary by environment
- OAuth secrets required in production

## Next Steps

→ Phase 7: UI Components
