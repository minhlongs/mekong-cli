# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth Session & GitHub/Stripe Route Handlers."""

import inspect
import json
import sys
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse


def _facade():
    return sys.modules["src.auth.routes"]


async def handle_github_login(request: Request):
    """Initiate GitHub OAuth2 flow."""
    f = _facade()
    state = f.os.urandom(16).hex()
    request.session["oauth_state"] = state

    client = f.OAuth2Client()
    try:
        auth_url = client.get_github_oauth_url(state=state)
        return RedirectResponse(url=auth_url)
    finally:
        _close = client.close()
        if inspect.isawaitable(_close):
            await _close


async def handle_github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Handle GitHub OAuth2 callback."""
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
        user_info, _access_token = await client.handle_github_callback(code)
        user_repo = f.UserRepository()
        user = await user_repo.find_or_create_user(
            email=user_info["email"],
            provider="github",
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


async def handle_logout(request: Request):
    """Logout user and revoke session."""
    f = _facade()
    session_manager = f.SessionManager()
    user_repo = f.UserRepository()

    token = session_manager.get_session_cookie(request)
    if token:
        user = await session_manager.validate_session(token)
        if user:
            session = await user_repo.find_session_by_token(token)
            if session:
                await session_manager.revoke_session(session.id)

        response = RedirectResponse(url="/")
        session_manager.delete_session_cookie(response)
        return response


async def handle_refresh_token(request: Request):
    """Refresh session token."""
    f = _facade()
    session_manager = f.SessionManager()
    token = session_manager.get_session_cookie(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session token found",
        )

    user = await session_manager.validate_session(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    new_access = session_manager.create_access_token(user)
    response = JSONResponse({
        "success": True,
        "message": "Token refreshed",
    })
    session_manager.set_session_cookie(response, new_access)
    return response


async def handle_stripe_webhook(request: Request):
    """Stripe webhook endpoint for real-time subscription updates."""
    f = _facade()
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    if not f.verify_stripe_webhook(payload, sig_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        event = json.loads(payload.decode("utf-8"))
        event_type = event.get("type")
        event_data = event.get("data", {})

        if not event_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event type not found",
            )

        result = await f.process_stripe_webhook(event_type, event_data)
        if result.get("success"):
            return JSONResponse(
                status_code=200,
                content={"received": True, "message": result.get("message")},
            )
        return JSONResponse(
            status_code=400,
            content={"received": True, "error": result.get("message")},
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={"received": True, "error": f"Processing error: {str(e)}"},
        )
