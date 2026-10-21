# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth Routes - OAuth2 callback and session management

Handles OAuth2 callbacks, login/logout, and session endpoints.
"""

import inspect  # noqa: F401
import os  # noqa: F401
from typing import Optional
from uuid import uuid4  # noqa: F401

from fastapi import APIRouter, HTTPException, Request, status  # noqa: F401
from fastapi.responses import JSONResponse, RedirectResponse  # noqa: F401
from fastapi.templating import Jinja2Templates

from src.auth.config import AuthConfig  # noqa: F401
from src.auth.oauth2_providers import OAuth2Client  # noqa: F401
from src.auth.rate_limit_decorator import (
    rate_limit,
    rate_limit_auth_callback,
    rate_limit_auth_login,
    rate_limit_auth_refresh,
)
from src.auth.rbac import Role, get_current_user, require_role
from src.auth.routes_oauth import (
    handle_dev_login,
    handle_google_callback,
    handle_google_login,
    handle_login_page,
)
from src.auth.routes_session import (
    handle_github_callback,
    handle_github_login,
    handle_logout,
    handle_refresh_token,
    handle_stripe_webhook,
)
from src.auth.session_manager import SessionManager  # noqa: F401
from src.auth.stripe_integration import (  # noqa: F401
    process_stripe_webhook,
    verify_stripe_webhook,
)
from src.auth.user_repository import UserRepository  # noqa: F401

router = APIRouter(prefix="/auth", tags=["authentication"])

templates = Jinja2Templates(directory="src/api/templates")


@router.get("/login")
async def login_page(request: Request):
    """Render login page or redirect if already authenticated."""
    return await handle_login_page(request)


@router.post("/dev-login")
@rate_limit(limit="10/minute", bypass_dev=True)
async def dev_login(request: Request):
    """Development mode quick login (bypasses OAuth)."""
    return await handle_dev_login(request)


@router.get("/google/login")
@rate_limit_auth_login()
async def google_login(request: Request):
    """Initiate Google OAuth2 flow."""
    return await handle_google_login(request)


@router.get("/google/callback")
@rate_limit_auth_callback()
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle Google OAuth2 callback."""
    return await handle_google_callback(request, code, state, error)


@router.get("/github/login")
@rate_limit_auth_login()
async def github_login(request: Request):
    """Initiate GitHub OAuth2 flow."""
    return await handle_github_login(request)


@router.get("/github/callback")
@rate_limit_auth_callback()
async def github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle GitHub OAuth2 callback."""
    return await handle_github_callback(request, code, state, error)


@router.post("/logout")
@rate_limit(limit="30/hour", bypass_dev=True)
async def logout(request: Request):
    """Logout user and revoke session."""
    return await handle_logout(request)


@router.get("/me")
async def get_current_user_info(request: Request):
    """Get current authenticated user info."""
    user_info = get_current_user(request)
    if not user_info or not user_info.get("id"):
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user_info}


@router.get("/refresh")
@rate_limit_auth_refresh()
async def refresh_token(request: Request):
    """Refresh session token."""
    return await handle_refresh_token(request)


@router.get("/admin")
@require_role(Role.ADMIN, Role.OWNER)
async def admin_dashboard(request: Request):
    """Admin-only dashboard endpoint."""
    user_info = get_current_user(request)
    return {
        "message": "Admin dashboard accessed",
        "user": user_info,
        "admin_access": True,
    }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook endpoint for real-time subscription updates."""
    return await handle_stripe_webhook(request)
