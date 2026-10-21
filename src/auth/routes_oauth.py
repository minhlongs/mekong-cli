# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth Route Handlers — Implementation for OAuth2, session, and Stripe webhook routes."""

import inspect
import sys
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse


def _facade():
    return sys.modules["src.auth.routes"]


async def handle_login_page(request: Request):
    """Render login page or redirect if already authenticated."""
    f = _facade()
    if getattr(request.state, "authenticated", False):
        return RedirectResponse(url="/dashboard")

    config = f.AuthConfig()
    google_url = None
    github_url = None

    oauth_config = config.get_oauth_config()
    if oauth_config["google"].enabled:
        google_url = "/auth/google/login"
    if oauth_config["github"].enabled:
        github_url = "/auth/github/login"

    is_dev = config.is_dev_mode()

    return f.templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "oauth_providers": {
                "google": {"enabled": bool(google_url), "url": google_url},
                "github": {"enabled": bool(github_url), "url": github_url},
            },
            "dev_mode": is_dev,
        },
    )


async def handle_dev_login(request: Request):
    """Development mode quick login (bypasses OAuth)."""
    f = _facade()
    config = f.AuthConfig()

    if not config.is_dev_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login only available in development mode",
        )

    user_repo = f.UserRepository()
    session_manager = f.SessionManager(user_repo)

    test_email = f"dev-{uuid4().hex[:8]}@localhost"
    user = await user_repo.find_or_create_user(
        email=test_email,
        provider="local",
        oauth_id="dev-local-user",
        defaults={"name": "Dev User", "role": "developer"},
    )

    _session, jwt_token, _refresh = await session_manager.create_session(
        user=user,
        role="developer",
    )

    response = JSONResponse({
        "success": True,
        "message": "Dev login successful",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": "developer",
        },
    })

    session_manager.set_session_cookie(response, jwt_token)
    return response


async def handle_google_login(request: Request):
    """Initiate Google OAuth2 flow."""
    f = _facade()
    state = f.os.urandom(16).hex()
    client = f.OAuth2Client()
    try:
        auth_url = client.get_google_oauth_url(state=state)
        response = RedirectResponse(url=auth_url)
    finally:
        _close = client.close()
        if inspect.isawaitable(_close):
            await _close
    response.set_cookie(
        "oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/auth",
    )
    return response


async def handle_google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle Google OAuth2 callback."""
    f = _facade()
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}",
        )
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided",
        )
    stored_state = request.cookies.get("oauth_state")
    if not state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    client = f.OAuth2Client()
    try:
        user_info, _access_token = await client.handle_google_callback(code)
        user_repo = f.UserRepository()
        user = await user_repo.find_or_create_user(
            email=user_info["email"],
            provider="google",
            oauth_id=user_info["oauth_id"],
        )
        session_manager = f.SessionManager(user_repo)
        _session, jwt_token, _refresh = await session_manager.create_session(
            user=user,
            role="member",
        )
        response = RedirectResponse(url="/dashboard")
        session_manager.set_session_cookie(response, jwt_token)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )
    finally:
        _close = client.close()
        if inspect.isawaitable(_close):
            await _close
