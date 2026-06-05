"""VN Pilot — admin token auth dependencies.

Two gates:
- _require_admin_token : legacy single-token gate (unchanged, back-compat).
- _require_scope(...)  : JWT scope-based gate with legacy fallback.

Flow for _require_scope:
  1. Try legacy exact-match on MEKONG_ADMIN_TOKEN → allow (scope=legacy).
  2. Try JWT decode against MEKONG_JWT_SECRET=REDACTED.
  3. Check scope (ANY-of).
  4. Check org (wildcard or exact list).
  5. Emit structured audit log on success (stdout + ~/.mekong/admin-audit.jsonl).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Callable, Optional

from fastapi import Header, HTTPException, Request, status

from src.services.admin_token_service import (
    JWTExpiredError,
    JWTInvalidError,
    check_org,
    check_scope,
    decode_jwt,
)
from src.services.audit_logger import audit_admin_action

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


def _require_admin_token(authorization: Optional[str] = Header(default=None)) -> None:
    """Bearer-token gate for founder-only admin endpoints.

    Reads MEKONG_ADMIN_TOKEN at request time (so launchctl setenv updates
    take effect without code reload — useful for token rotation).

    - 503: env var not configured
    - 401: missing or malformed Authorization header
    - 403: token mismatch
    """
    expected = os.environ.get("MEKONG_ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoints disabled — MEKONG_ADMIN_TOKEN not set on gateway",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    received = authorization[len("Bearer "):].strip()
    if received != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )


def _require_scope(required: list[str]) -> Callable:
    """Factory returning a FastAPI dependency that enforces JWT scope + org access.

    Legacy MEKONG_ADMIN_TOKEN is tried first for back-compat.
    Falls through to JWT decode only if bearer token != legacy token.

    Args:
        required: List of scope strings — ANY match grants access (union semantics).

    Returns:
        Async FastAPI dependency function (no return value on success).

    HTTP error codes:
        401 — missing/malformed Authorization header, expired token, invalid token/sig.
        403 — insufficient scope, wrong org.
        503 — MEKONG_JWT_SECRET=REDACTED not set AND legacy token not configured.
    """
    async def _dependency(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ) -> None:
        legacy_token = os.environ.get("MEKONG_ADMIN_TOKEN")
        jwt_secret = os.environ.get("MEKONG_JWT_SECRET=REDACTED")

        # Must have at least one auth mechanism
        if not legacy_token and not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin auth disabled — neither MEKONG_ADMIN_TOKEN nor MEKONG_JWT_SECRET=REDACTED configured",
            )

        # Extract bearer token from header
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing 'Authorization: Bearer <token>' header",
            )
        raw_token = authorization[len("Bearer "):].strip()

    # --- Legacy token: allowed only when DEBUG=true, JWT path preferred ---
    if legacy_token and raw_token == legacy_token:
        if os.environ.get("DEBUG") != "true":
            logger.warning("Legacy admin token used without DEBUG=true — rejecting per security policy")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Legacy admin token is disabled in non-debug mode. Use JWT authentication instead.",
            )
        org_id = request.query_params.get("org_id", "default")
        _audit_log(scope="legacy_admin_debug", org=org_id, sub="legacy", endpoint=request.url.path)
        logger.warning("Legacy admin token bypass active (DEBUG=true) for %s on %s", org_id, request.url.path)
        claims_or_legacy = {"sub": "legacy_admin"}
        if not check_org(claims_or_legacy, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid org context for legacy admin token",
            )
        return  # admin scope, org-validated, debug-only

        try:
            claims = decode_jwt(raw_token, jwt_secret)
        except JWTExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except JWTInvalidError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        # Scope check (ANY-of)
        if not check_scope(claims, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope",
            )

        # Org check
        org_id = request.query_params.get("org_id", "default")
        if not check_org(claims, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wrong org",
            )

        _audit_log(
            scope=",".join(claims.get("scopes", [])),
            org=org_id,
            sub=claims.get("sub", "unknown"),
            endpoint=request.url.path,
        )

    return _dependency


def _audit_log(scope: str, org: str, sub: str, endpoint: str = "") -> None:
    """Emit a structured JSON audit line on every successful admin auth.

    Writes to both:
    - stdout via Python logging (for journalctl / live tail)
    - ~/.mekong/admin-audit.jsonl (persistent, flock-safe, founder-readable)
    """
    logger.info(json.dumps({"event": "admin_auth", "scope": scope, "org": org, "sub": sub}))
    audit_admin_action(scope=scope, org=org, sub=sub, endpoint=endpoint)
