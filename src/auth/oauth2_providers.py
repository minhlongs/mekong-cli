# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""OAuth2 Providers - Google and GitHub authentication."""

import base64
import hashlib
import inspect
import os
import secrets
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from src.auth.oauth2_github import (
    GitHubOAuthMixin,
    get_github_oauth_url,
    get_google_oauth_url,
    get_user_info,
    handle_github_callback,
    handle_google_callback,
)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8080/auth/callback")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL = "https://api.github.com/user"
GITHUB_EMAIL_URL = "https://api.github.com/user/emails"


def generate_state() -> str:
    """Generate cryptographically secure state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


def generate_pkce_verifier() -> str:
    """Generate PKCE code verifier."""
    return secrets.token_urlsafe(64)


def generate_pkce_challenge(verifier: str) -> str:
    """Generate PKCE code challenge from verifier (SHA256)."""
    sha256_hash = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(sha256_hash).rstrip(b"=").decode()


class OAuth2Client(GitHubOAuthMixin):
    """OAuth2 client for Google and GitHub authentication."""

    def __init__(self):
        self._client = None

    def _get_http_client(self):
        """Get or create the HTTP client (lazy init, requires httpx)."""
        if self._client is None:
            if not HTTPX_AVAILABLE:
                raise ImportError("httpx not installed. Run: pip install httpx")
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """Close the HTTP client if it was created."""
        if self._client is not None:
            result = self._client.aclose()
            if inspect.isawaitable(result):
                await result

    def get_google_oauth_url(
        self,
        state: Optional[str] = None,
        pkce_verifier: Optional[str] = None,
    ) -> str:
        """Generate Google OAuth2 authorization URL."""
        if state is None:
            state = generate_state()

        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        if pkce_verifier:
            params["code_challenge"] = generate_pkce_challenge(pkce_verifier)
            params["code_challenge_method"] = "S256"

        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def handle_google_callback(
        self,
        code: str,
        state: Optional[str] = None,
        pkce_verifier: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Handle Google OAuth2 callback."""
        token_data = await self._exchange_google_token(code, pkce_verifier)
        access_token = token_data["access_token"]
        user_info = await self._get_google_userinfo(access_token)
        return user_info, access_token

    async def _exchange_google_token(
        self,
        code: str,
        pkce_verifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }
        if pkce_verifier:
            data["code_verifier"] = pkce_verifier

        response = await self._get_http_client().post(GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json()

    async def _get_google_userinfo(self, access_token: str) -> Dict[str, Any]:
        """Fetch user info from Google."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._get_http_client().get(GOOGLE_USERINFO_URL, headers=headers)
        response.raise_for_status()
        data = response.json()

        return {
            "email": data.get("email"),
            "email_verified": data.get("email_verified", False),
            "name": data.get("name"),
            "picture": data.get("picture"),
            "oauth_id": data.get("id") or data.get("sub"),
            "provider": "google",
        }


__all__ = [
    "GITHUB_AUTH_URL",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "GITHUB_EMAIL_URL",
    "GITHUB_TOKEN_URL",
    "GITHUB_USERINFO_URL",
    "GOOGLE_AUTH_URL",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_TOKEN_URL",
    "GOOGLE_USERINFO_URL",
    "HTTPX_AVAILABLE",
    "OAuth2Client",
    "REDIRECT_URI",
    "generate_pkce_challenge",
    "generate_pkce_verifier",
    "generate_state",
    "get_github_oauth_url",
    "get_google_oauth_url",
    "get_user_info",
    "handle_github_callback",
    "handle_google_callback",
]
