# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""HTTPOnly session cookie helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request, Response
from starlette.responses import RedirectResponse


class SessionCookieMixin:
    """Cookie behavior for JWT-backed sessions."""

    def create_session_cookie(
        self,
        token: str,
        expires_in_days: int = 7,
    ) -> Dict[str, Any]:
        import src.auth.session_manager as config

        return {
            "key": config._cookie_name(),
            "value": token,
            "httponly": config.COOKIE_HTTPONLY,
            "secure": config._is_production(),
            "samesite": config._cookie_samesite(),
            "max_age": expires_in_days * 24 * 60 * 60,
            "path": "/",
        }

    def set_session_cookie(
        self,
        response: Response,
        token: str,
        expires_in_days: int = 7,
    ) -> Response:
        response.set_cookie(**self.create_session_cookie(token, expires_in_days))
        return response

    def get_session_cookie(self, request: Request) -> Optional[str]:
        import src.auth.session_manager as config

        return request.cookies.get(config._cookie_name())

    def delete_session_cookie(self, response: Response) -> Response:
        import src.auth.session_manager as config

        response.delete_cookie(
            key=config._cookie_name(),
            path="/",
            domain=None,
        )
        return response

    def create_logout_redirect(
        self,
        response: Response,
        redirect_to: str = "/",
    ) -> RedirectResponse:
        redirect = RedirectResponse(url=redirect_to, status_code=303)
        self.delete_session_cookie(redirect)
        return redirect


__all__ = ["SessionCookieMixin"]
