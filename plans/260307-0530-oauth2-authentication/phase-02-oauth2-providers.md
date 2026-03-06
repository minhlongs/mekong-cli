---
title: "Phase 2: OAuth2 Providers"
priority: P1
status: completed
effort: 2h
---

# Phase 2: OAuth2 Providers (Google + GitHub)

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Phase 1:** [phase-01-database-schema.md](phase-01-database-schema.md)
- **Research:** Authlib documentation

## Overview

Implement OAuth2 authentication with Google and GitHub using Authlib.

## Key Insights

- Authlib supports both providers with unified interface
- Need separate OAuth2 clients for each provider
- Callback routes handle user creation/upsert

## Requirements

### Functional
- Google OAuth2 client configuration
- GitHub OAuth2 client configuration
- Callback routes `/auth/google/callback`, `/auth/github/callback`
- User creation on first login
- User upsert on subsequent logins

### Non-functional
- OAuth2 state parameter for CSRF protection
- PKCE for public clients
- Secure token storage

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  FastAPI    │────▶│  Google/    │
│   Browser   │     │  Backend    │     │  GitHub     │
└─────────────┘     └─────────────┘     └─────────────┘
     │                    │                    │
     │ 1. Click Login     │                    │
     │───────────────────▶│                    │
     │                    │ 2. OAuth2 Request  │
     │                    │───────────────────▶│
     │ 3. Redirect        │                    │
     │◀───────────────────│                    │
     │────────────────────────────────────────▶│
     │                    │                    │
     │ 4. Callback with code                   │
     │───────────────────▶│                    │
     │                    │ 5. Exchange code   │
     │                    │───────────────────▶│
     │                    │ 6. Access token    │
     │                    │◀───────────────────│
     │                    │ 7. Fetch user info │
     │                    │───────────────────▶│
     │                    │ 8. User data       │
     │                    │◀───────────────────│
     │                    │ 9. Create/Update   │
     │                    │    user_sessions   │
     │ 10. JWT Cookie     │                    │
     │◀───────────────────│                    │
```

## Implementation Steps

1. **Install Authlib**
   ```bash
   pip install authlib httpx
   ```

2. **Create OAuth2 config** `src/auth/oauth2_config.py`
   ```python
   GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
   GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
   GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "/auth/google/callback")

   GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
   GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
   GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "/auth/github/callback")
   ```

3. **Create OAuth2 clients** `src/auth/oauth2_clients.py`
   ```python
   from authlib.integrations.httpx_client import AsyncHttpxClient
   from authlib.integrations.starlette_client import StarletteOAuth2App

   class OAuth2Clients:
       google: StarletteOAuth2App
       github: StarletteOAuth2App

       @staticmethod
       def init_google(app, config):
           return StarletteOAuth2App(
               client_id=config.GOOGLE_CLIENT_ID,
               client_secret=config.GOOGLE_CLIENT_SECRET,
               server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
               client_kwargs={"scope": "openid email profile"},
           )

       @staticmethod
       def init_github(app, config):
           return StarletteOAuth2App(
               client_id=config.GITHUB_CLIENT_ID,
               client_secret=config.GITHUB_CLIENT_SECRET,
               access_token_url="https://github.com/login/oauth/access_token",
               authorize_url="https://github.com/login/oauth/authorize",
               api_base_url="https://api.github.com/",
               client_kwargs={"scope": "user:email"},
           )
   ```

4. **Create auth routes** `src/api/routes/auth_routes.py`
   ```python
   @router.get("/auth/google")
   async def google_login(request: Request):
       redirect_uri = request.url_for("google_callback")
       return await oauth.google.authorize_redirect(request, redirect_uri)

   @router.get("/auth/google/callback")
   async def google_callback(request: Request):
       token = await oauth.google.authorize_access_token(request)
       user_info = token.get("userinfo")
       return await handle_oauth_callback(request, user_info, "google")

   @router.get("/auth/github")
   async def github_login(request: Request):
       redirect_uri = request.url_for("github_callback")
       return await oauth.github.authorize_redirect(request, redirect_uri)

   @router.get("/auth/github/callback")
   async def github_callback(request: Request):
       token = await await oauth.github.authorize_access_token(request)
       user_info = await oauth.github.get("user", token=token)
       return await handle_oauth_callback(request, user_info.model_dump(), "github")
   ```

5. **Create callback handler** `src/auth/oauth2_handler.py`
   ```python
   async def handle_oauth_callback(
       request: Request,
       user_info: dict,
       provider: str
   ) -> RedirectResponse:
       email = user_info["email"]
       oauth_id = user_info["id"] if provider == "github" else user_info["sub"]

       # Find or create user
       user = await get_or_create_user(email, oauth_id, provider)

       # Generate JWT session
       session = await create_session(user)

       # Set HTTPOnly cookie
       response = RedirectResponse(url="/dashboard")
       response.set_cookie(
           key="session_token",
           value=session.jwt_token,
           httponly=True,
           secure=True,
           samesite="lax",
           max_age=SESSION_MAX_AGE,
       )
       return response
   ```

## Todo List

- [x] Add authlib to pyproject.toml dependencies
- [x] Create `src/auth/oauth2_providers.py` with OAuth2Client class
- [x] Implement `get_google_oauth_url()` - Generate Google OAuth URL
- [x] Implement `get_github_oauth_url()` - Generate GitHub OAuth URL
- [x] Implement `handle_google_callback(code)` - Exchange code for token
- [x] Implement `handle_github_callback(code)` - Exchange code for token
- [x] Implement `get_user_info(provider, token)` - Fetch user email/profile
- [x] Create `src/auth/user_repository.py` with find_or_create_user()
- [x] Add environment variables to `.env.example`

## Implementation Summary

Created files:
- `src/auth/oauth2_providers.py` - OAuth2Client with Google + GitHub providers
- `src/auth/user_repository.py` - UserRepository with find_or_create_user()
- `src/auth/__init__.py` - Module exports

Features implemented:
- State parameter for CSRF protection
- PKCE support for public clients
- Secure token hashing (SHA256) for storage
- User info normalization across providers
- Auto email fetching for GitHub (handles private emails)

## Success Criteria

- [x] Google OAuth2 URL generation works
- [x] GitHub OAuth2 URL generation works
- [x] Token exchange implemented for both providers
- [x] User info fetching implemented
- [x] find_or_create_user() in UserRepository

## Risk Assessment

- **Risk:** OAuth2 tokens exposed in logs
- **Mitigation:** Never log token values, use secure storage

## Security Considerations

- State parameter for CSRF protection
- PKCE for public clients
- HTTPS required for production
- Secure cookie settings (HTTPOnly, Secure, SameSite)

## Next Steps

→ Phase 3: Session management with JWT
