# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Admin token service — JWT decode, scope check, org check helpers.

Algorithm pinning: HS256 only. Rejects none/RS256/ES256 per security design.
Scope semantics: ANY-of (union) — any matching scope grants access.
Org semantics: "*" wildcard or exact-match list.
"""
from __future__ import annotations

import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
)

__all__ = [
    "decode_jwt",
    "check_scope",
    "check_org",
    "JWTExpiredError",
    "JWTInvalidError",
]


class JWTExpiredError(Exception):
    """Raised when JWT exp claim has passed."""


class JWTInvalidError(Exception):
    """Raised on any other JWT verification failure (bad sig, wrong alg, etc.)."""


def decode_jwt(token: str, secret: str) -> dict:
    """Decode and verify a JWT token.

    Args:
        token: Raw JWT string (without 'Bearer ' prefix).
        secret: HMAC secret for HS256 verification.

    Returns:
        Verified claims dict.

    Raises:
        JWTExpiredError: if exp claim is in the past.
        JWTInvalidError: if signature invalid, algorithm rejected, or malformed.
    """
    try:
        claims: dict = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],  # explicit allowlist — rejects none/RS256/ES256
            leeway=30,  # 30-second clock skew tolerance (founder laptop → gateway)
        )
    except ExpiredSignatureError as exc:
        raise JWTExpiredError("Token expired") from exc
    except (InvalidSignatureError, InvalidTokenError) as exc:
        raise JWTInvalidError(f"Invalid token: {exc}") from exc
    return claims


def check_scope(claims: dict, required: list[str]) -> bool:
    """Return True if claims contain ANY of the required scopes (union semantics).

    Args:
        claims: Decoded JWT payload dict.
        required: List of scope strings; access granted if intersection non-empty.

    Returns:
        True if at least one required scope is present in claims["scopes"].
    """
    token_scopes: list[str] = claims.get("scopes", [])
    return bool(set(token_scopes) & set(required))


def check_org(claims: dict, request_org_id: str) -> bool:
    """Return True if the token is permitted to act on request_org_id.

    Args:
        claims: Decoded JWT payload dict.
        request_org_id: org_id from query param (or "default").

    Returns:
        True if allowed_orgs contains "*" (wildcard) or request_org_id explicitly.
    """
    allowed: list[str] = claims.get("allowed_orgs", [])
    if "*" in allowed:
        return True
    return request_org_id in allowed
