# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth Configuration Models & Templates."""

from dataclasses import dataclass
from enum import Enum


class AuthEnvironment(str, Enum):
    """Authentication environment modes."""

    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class OAuthProviderConfig:
    """OAuth provider configuration."""

    client_id: str
    client_secret: str
    redirect_uri: str
    enabled: bool = True


ENV_VARS = {
    "AUTH_ENVIRONMENT": "dev|staging|production",
    "JWT_SECRET_KEY": "JWT signing secret (required for production, min 32 characters)",
    "JWT_ACCESS_EXPIRY_MINUTES": "Access token expiry (default: 30)",
    "JWT_REFRESH_EXPIRY_DAYS": "Refresh token expiry (default: 7)",
    "SESSION_MAX_AGE_SECONDS": "Session cookie max age (default: 604800)",
    "GOOGLE_CLIENT_ID": "Google OAuth client ID",
    "GOOGLE_CLIENT_SECRET": "Google OAuth client secret",
    "GOOGLE_REDIRECT_URI": "Google OAuth redirect URI",
    "GITHUB_CLIENT_ID": "GitHub OAuth client ID",
    "GITHUB_CLIENT_SECRET": "GitHub OAuth client secret",
    "GITHUB_REDIRECT_URI": "GitHub OAuth redirect URI",
    "STRIPE_SECRET_KEY": "Stripe API secret key",
    "STRIPE_WEBHOOK_SECRET": "Stripe webhook signing secret",
    "STRIPE_PRICE_IDS": "JSON mapping of Stripe Price ID to role (owner/admin/member/viewer)",
}


def get_env_template() -> str:
    """Generate .env file template."""
    lines = [
        "# ====================================",
        "# Authentication Configuration",
        "# ====================================",
        "",
        "# Environment (dev|staging|production)",
        "AUTH_ENVIRONMENT=dev",
        "",
        "# JWT Settings",
        "# IMPORTANT: Set a secure random secret for production (min 32 characters)",
        "# Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'",
        "JWT_SECRET_KEY=",
        "JWT_ACCESS_EXPIRY_MINUTES=30",
        "JWT_REFRESH_EXPIRY_DAYS=7",
        "SESSION_MAX_AGE_SECONDS=604800",
        "",
        "# Google OAuth2",
        "GOOGLE_CLIENT_ID=",
        "GOOGLE_CLIENT_SECRET=",
        "GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback",
        "",
        "# GitHub OAuth2",
        "GITHUB_CLIENT_ID=",
        "GITHUB_CLIENT_SECRET=",
        "GITHUB_REDIRECT_URI=http://localhost:8080/auth/github/callback",
        "",
        "# Stripe (for billing)",
        "STRIPE_SECRET_KEY=",
        "STRIPE_WEBHOOK_SECRET=",
        'STRIPE_PRICE_IDS={"price_enterprise": "owner", "price_pro": "admin", "price_trial": "member", "price_free": "viewer"}',
        "",
    ]
    return "\n".join(lines)
