# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""OAuth2 Helpers & GitHub Provider Mixin."""

import sys
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode


def _facade():
    return sys.modules["src.auth.oauth2_providers"]


class GitHubOAuthMixin:
    """GitHub OAuth2 methods for OAuth2Client."""

    def get_github_oauth_url(
        self,
        state: Optional[str] = None,
    ) -> str:
        """Generate GitHub OAuth2 authorization URL."""
        f = _facade()
        if state is None:
            state = f.generate_state()

        params = {
            "client_id": f.GITHUB_CLIENT_ID,
            "redirect_uri": f.REDIRECT_URI,
            "scope": "user:email",
            "state": state,
        }
        return f"{f.GITHUB_AUTH_URL}?{urlencode(params)}"

    async def handle_github_callback(
        self,
        code: str,
        state: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Handle GitHub OAuth2 callback."""
        token_data = await self._exchange_github_token(code)
        access_token = token_data["access_token"]
        user_info = await self._get_github_userinfo(access_token)
        return user_info, access_token

    async def _exchange_github_token(
        self,
        code: str,
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        f = _facade()
        headers = {"Accept": "application/json"}
        data = {
            "client_id": f.GITHUB_CLIENT_ID,
            "client_secret": f.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": f.REDIRECT_URI,
        }
        response = await self._get_http_client().post(
            f.GITHUB_TOKEN_URL,
            headers=headers,
            data=data,
        )
        response.raise_for_status()
        return response.json()

    async def _get_github_userinfo(self, access_token: str) -> Dict[str, Any]:
        """Fetch user info from GitHub."""
        f = _facade()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        response = await self._get_http_client().get(f.GITHUB_USERINFO_URL, headers=headers)
        response.raise_for_status()
        data = response.json()

        email = data.get("email")
        if not email:
            email = await self._get_github_primary_email(access_token)

        return {
            "email": email,
            "email_verified": True,
            "name": data.get("name") or data.get("login"),
            "picture": data.get("avatar_url"),
            "oauth_id": str(data.get("id")),
            "provider": "github",
            "login": data.get("login"),
        }

    async def _get_github_primary_email(self, access_token: str) -> str:
        """Get primary email from GitHub emails endpoint."""
        f = _facade()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        response = await self._get_http_client().get(f.GITHUB_EMAIL_URL, headers=headers)
        response.raise_for_status()
        emails = response.json()

        for email_data in emails:
            if email_data.get("primary"):
                return email_data["email"]
            if email_data.get("verified"):
                return email_data["email"]

        if emails:
            return emails[0]["email"]

        raise ValueError("No email found for GitHub user")


async def get_google_oauth_url() -> str:
    """Get Google OAuth2 URL."""
    f = _facade()
    client = f.OAuth2Client()
    try:
        return client.get_google_oauth_url()
    finally:
        await client.close()


async def get_github_oauth_url() -> str:
    """Get GitHub OAuth2 URL."""
    f = _facade()
    client = f.OAuth2Client()
    try:
        return client.get_github_oauth_url()
    finally:
        await client.close()


async def handle_google_callback(code: str) -> Tuple[Dict[str, Any], str]:
    """Handle Google OAuth2 callback."""
    f = _facade()
    client = f.OAuth2Client()
    try:
        return await client.handle_google_callback(code)
    finally:
        await client.close()


async def handle_github_callback(code: str) -> Tuple[Dict[str, Any], str]:
    """Handle GitHub OAuth2 callback."""
    f = _facade()
    client = f.OAuth2Client()
    try:
        return await client.handle_github_callback(code)
    finally:
        await client.close()


async def get_user_info(provider: str, token: str) -> Dict[str, Any]:
    """Fetch user info from provider using access token."""
    f = _facade()
    client = f.OAuth2Client()
    try:
        if provider == "google":
            return await client._get_google_userinfo(token)
        if provider == "github":
            return await client._get_github_userinfo(token)
        raise ValueError(f"Unknown provider: {provider}")
    finally:
        await client.close()
