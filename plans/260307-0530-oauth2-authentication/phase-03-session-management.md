---
title: "Phase 3: Session Management"
priority: P1
status: completed
effort: 1.5h
completed: 2026-03-07
---

# Phase 3: Session Management (JWT + HTTPOnly Cookies)

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Phase 2:** [phase-02-oauth2-providers.md](phase-02-oauth2-providers.md)
- **Report:** [plans/reports/fullstack-developer-260307-0603-session-rbac-implementation.md](../reports/fullstack-developer-260307-0603-session-rbac-implementation.md)

## Overview

Implement JWT-based session management with HTTPOnly cookies for secure authentication.

## Key Insights

- JWT tokens stored in HTTPOnly cookies (not localStorage)
- Short-lived access tokens + long-lived refresh tokens
- Session state tracked in database for revocation

## Requirements

### Functional
- JWT token generation with user claims
- Token validation middleware
- HTTPOnly cookie setup
- Session logout and cleanup
- Token refresh mechanism

### Non-functional
- Tokens expire after 15 minutes (access) / 7 days (refresh)
- Signature verification with RS256 or HS256
- Secure cookie settings for production

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     JWT Token Structure                      │
├─────────────────────────────────────────────────────────────┤
│ Header: { "alg": "HS256", "typ": "JWT" }                    │
│ Payload: {                                                   │
│   "sub": "user_id",                                         │
│   "email": "user@example.com",                              │
│   "role": "admin",                                          │
│   "iat": 1234567890,                                        │
│   "exp": 1234568790,                                        │
│   "jti": "session_id"                                       │
│ }                                                           │
│ Signature: HMACSHA256(base64(header) + base64(payload), key)│
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

1. **Install PyJWT**
   ```bash
   pip install PyJWT
   ```

2. **Create JWT utilities** `src/auth/jwt_utils.py`
   ```python
   import jwt
   from datetime import datetime, timedelta, timezone
   from uuid import UUID
   import secrets

   SECRET_KEY = os.getenv("JWT_SECRET=REDACTED_KEY", secrets.token_urlsafe(32))
   ALGORITHM = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES = 15
   REFRESH_TOKEN_EXPIRE_DAYS = 7

   def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
       to_encode = data.copy()
       expire = datetime.now(timezone.utc) + (
           expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
       )
       to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
       to_encode.setdefault("jti", secrets.token_urlsafe(16))
       return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

   def create_refresh_token(data: dict) -> str:
       return create_access_token(
           data,
           timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
       )

   def decode_token(token: str) -> dict:
       try:
           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
           return {"valid": True, "payload": payload}
       except jwt.ExpiredSignatureError:
           return {"valid": False, "error": "expired"}
       except jwt.InvalidTokenError:
           return {"valid": False, "error": "invalid"}
   ```

3. **Create session service** `src/auth/session_service.py`
   ```python
   from src.models.session import UserSession
   from src.auth.jwt_utils import create_access_token, create_refresh_token

   class SessionService:
       async def create_session(self, user: User) -> UserSession:
           access_token = create_access_token({
               "sub": str(user.id),
               "email": user.email,
           })
           refresh_token = create_refresh_token({
               "sub": str(user.id),
               "type": "refresh",
           })

           session = UserSession(
               user_id=user.id,
               jwt_token=access_token,
               expires_at=datetime.now(timezone.utc) + timedelta(days=7),
           )
           await session.save()
           return session

       async def invalidate_session(self, session_id: UUID) -> bool:
           session = await UserSession.get(session_id)
           if session:
               await session.delete()
               return True
           return False

       async def validate_session(self, token: str) -> Optional[User]:
           result = decode_token(token)
           if not result["valid"]:
               return None

           user_id = result["payload"]["sub"]
           return await User.get(user_id)
   ```

4. **Create session middleware** `src/auth/session_middleware.py`
   ```python
   from starlette.middleware.base import BaseHTTPMiddleware
   from src.auth.session_service import SessionService

   class SessionMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           token = request.cookies.get("session_token")

           if token:
               session_service = SessionService()
               user = await session_service.validate_session(token)
               if user:
                   request.state.user = user
                   request.state.authenticated = True
               else:
                   request.state.authenticated = False
           else:
               request.state.authenticated = False

           response = await call_next(request)
           return response
   ```

5. **Create logout route** `src/api/routes/auth_routes.py`
   ```python
   @router.post("/auth/logout")
   async def logout(request: Request, response: Response):
       session_token = request.cookies.get("session_token")
       if session_token:
           # Decode and invalidate session
           session_service = SessionService()
           # Invalidate in database

       response = RedirectResponse(url="/")
       response.delete_cookie("session_token")
       return response
   ```

## Todo List

- [x] Create `src/auth/jwt_utils.py` → Implemented as `src/auth/session_manager.py` (combined)
- [x] Create `src/auth/session_service.py` → Implemented as `src/auth/session_manager.py`
- [x] Create `src/auth/session_middleware.py` → Implemented as `src/auth/middleware.py`
- [x] Add logout route to auth_routes.py → Implemented as `src/auth/routes.py`
- [x] Register middleware in FastAPI app → Done in `src/api/dashboard/app.py`

## Success Criteria

- [x] JWT tokens generated correctly
- [x] HTTPOnly cookies set properly
- [x] Session validation works
- [x] Logout invalidates session
- [x] Token refresh mechanism implemented
- [x] Environment-aware config (dev/prod modes)

## Security Considerations

- JWT secret stored in environment variable
- Short token expiration (15 min)
- HTTPOnly prevents XSS attacks
- Secure flag required in production

## Next Steps

→ Phase 4: RBAC system implementation
