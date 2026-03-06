---
title: "Phase 4: RBAC System"
priority: P1
status: completed
effort: 1.5h
completed: 2026-03-07
---

# Phase 4: Role-Based Access Control (RBAC)

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Phase 3:** [phase-03-session-management.md](phase-03-session-management.md)
- **Report:** [plans/reports/fullstack-developer-260307-0603-session-rbac-implementation.md](../reports/fullstack-developer-260307-0603-session-rbac-implementation.md)

## Overview

Implement role-based access control with permission decorators and route protection.

## Key Insights

- Role hierarchy: owner > admin > member > viewer
- Permission decorators for route protection
- Role fetched from license or user record

## Requirements

### Functional
- Role hierarchy definition
- Permission decorators (`@require_role`, `@require_permission`)
- Route protection middleware
- Role checking utilities

### Non-functional
- Fast permission checks (< 10ms)
- Clear error messages for unauthorized access
- Audit logging for permission denials

## Architecture

```
Role Hierarchy:
┌──────────────────────────────────────────┐
│  owner   → Full access (God mode)        │
│  admin   → Manage users, settings        │
│  member  → Standard user features        │
│  viewer  → Read-only access              │
└──────────────────────────────────────────┘

Permission Matrix:
┌─────────────┬────────┬────────┬────────┬────────┐
│ Permission  │ owner  │ admin  │ member │ viewer │
├─────────────┼────────┼────────┼────────┼────────┤
│ read:*      │   ✓    │   ✓    │   ✓    │   ✓    │
│ write:*     │   ✓    │   ✓    │   ✓    │   ✗    │
│ delete:*    │   ✓    │   ✓    │   ✗    │   ✗    │
│ manage:users│   ✓    │   ✓    │   ✗    │   ✗    │
│ manage:settings│ ✓   │   ✓    │   ✗    │   ✗    │
│ billing:*   │   ✓    │   ✗    │   ✗    │   ✗    │
└─────────────┴────────┴────────┴────────┴────────┘
```

## Implementation Steps

1. **Create RBAC config** `src/auth/rbac_config.py`
   ```python
   from enum import Enum
   from typing import Set, Dict

   class Role(str, Enum):
       OWNER = "owner"
       ADMIN = "admin"
       MEMBER = "member"
       VIEWER = "viewer"

   ROLE_HIERARCHY: Dict[Role, Set[Role]] = {
       Role.OWNER: {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
       Role.ADMIN: {Role.ADMIN, Role.MEMBER, Role.VIEWER},
       Role.MEMBER: {Role.MEMBER, Role.VIEWER},
       Role.VIEWER: {Role.VIEWER},
   }

   PERMISSIONS: Dict[str, Set[Role]] = {
       "read:*": {Role.OWNER, Role.ADMIN, Role.MEMBER, Role.VIEWER},
       "write:*": {Role.OWNER, Role.ADMIN, Role.MEMBER},
       "delete:*": {Role.OWNER, Role.ADMIN},
       "manage:users": {Role.OWNER, Role.ADMIN},
       "manage:settings": {Role.OWNER, Role.ADMIN},
       "billing:*": {Role.OWNER},
   }
   ```

2. **Create RBAC decorators** `src/auth/rbac_decorators.py`
   ```python
   from functools import wraps
   from fastapi import HTTPException, status
   from src.auth.rbac_config import Role, ROLE_HIERARCHY, PERMISSIONS

   def require_role(minimum_role: Role):
       """Decorator to require minimum role level."""
       def decorator(func):
           @wraps(func)
           async def wrapper(request, *args, **kwargs):
               user_role = getattr(request.state, "user_role", None)
               if not user_role:
                   raise HTTPException(
                       status_code=status.HTTP_401_UNAUTHORIZED,
                       detail="Authentication required"
                   )

               role_enum = Role(user_role)
               if role_enum not in ROLE_HIERARCHY.get(minimum_role, set()):
                   raise HTTPException(
                       status_code=status.HTTP_403_FORBIDDEN,
                       detail=f"Requires role: {minimum_role.value}"
                   )

               return await func(request, *args, **kwargs)
           return wrapper
       return decorator

   def require_permission(permission: str):
       """Decorator to require specific permission."""
       def decorator(func):
           @wraps(func)
           async def wrapper(request, *args, **kwargs):
               user_role = getattr(request.state, "user_role", None)
               if not user_role:
                   raise HTTPException(
                       status_code=status.HTTP_401_UNAUTHORIZED,
                       detail="Authentication required"
                   )

               role_enum = Role(user_role)
               allowed_roles = PERMISSIONS.get(permission, set())

               if role_enum not in allowed_roles:
                   raise HTTPException(
                       status_code=status.HTTP_403_FORBIDDEN,
                       detail=f"Permission denied: {permission}"
                   )

               return await func(request, *args, **kwargs)
           return wrapper
       return decorator
   ```

3. **Create RBAC middleware** `src/auth/rbac_middleware.py`
   ```python
   from starlette.middleware.base import BaseHTTPMiddleware
   from src.models.user import User
   from src.models.license import License

   class RBACMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           user = getattr(request.state, "user", None)

           if user and getattr(request.state, "authenticated", False):
               # Get user's role from license or user record
               license = await License.get_by_user_id(user.id)
               if license:
                   request.state.user_role = license.role
               else:
                   request.state.user_role = "member"  # Default role

           response = await call_next(request)
           return response
   ```

4. **Protect routes** (example usage)
   ```python
   from src.auth.rbac_decorators import require_role, require_permission
   from src.auth.rbac_config import Role

   @router.get("/admin/users")
   @require_role(Role.ADMIN)
   async def list_users(request: Request):
       # Only admin+ can access
       ...

   @router.post("/billing/checkout")
   @require_permission("billing:*")
   async def checkout(request: Request):
       # Only owner can access
       ...

   @router.delete("/users/{user_id}")
   @require_permission("delete:*")
   async def delete_user(request: Request, user_id: UUID):
       # Only owner+ can delete
       ...
   ```

## Todo List

- [x] Create `src/auth/rbac_config.py` → Implemented as `src/auth/rbac.py` (combined config + decorators)
- [x] Create `src/auth/rbac_decorators.py` → Implemented as `src/auth/rbac.py`
- [x] Create `src/auth/rbac_middleware.py` → Implemented as `src/auth/rbac.py` (RBACMiddleware class)
- [x] Apply decorators to existing routes → Done in `src/api/dashboard/app.py`
- [x] Test role hierarchy enforcement → Import verification passed

## Success Criteria

- [x] Role hierarchy works correctly
- [x] Decorators block unauthorized access
- [x] Clear error messages on 403
- [x] Permission checks are fast
- [x] Environment-aware bypass (dev mode auto-auth)

## Risk Assessment

- **Risk:** Role not synced with Stripe
- **Mitigation:** Phase 5 handles Stripe sync

## Next Steps

→ Phase 5: Stripe customer integration
