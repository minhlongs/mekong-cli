# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Database, logging, and JWT extraction helpers for Polar.sh billing routes."""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import src.api.vn_pilot_state as _state
from fastapi import HTTPException, Request, status

from src.services.org_service import _db_path
from src.services.sqlite_migrations import ensure_schema


def _facade() -> Any:
    """Return the parent billing_routes module if loaded."""
    return sys.modules.get("src.api.billing_routes")


def _webhook_log_path() -> Path:
    """Resolve webhook log path at call time (respects CONFIG_DIR monkeypatch)."""
    return _state.CONFIG_DIR / "polar_webhook.log"


def _log_webhook_error(msg: str) -> None:
    """Append error to polar_webhook.log (mode 0600)."""
    try:
        _state.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        facade = _facade()
        log_path_fn = getattr(facade, "_webhook_log_path", _webhook_log_path) if facade else _webhook_log_path
        log_path = log_path_fn()
        if not log_path.exists():
            log_path.touch(mode=0o600)
        ts = datetime.now(timezone.utc).isoformat()
        from src.core.file_lock import locked_append

        with locked_append(log_path) as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass


def _open_db_conn():
    """Open SQLite connection with schema ensured."""
    db = _db_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    ensure_schema(conn)
    return conn


def _extract_email_from_request(request: Request) -> str:
    """Decode bearer JWT and return sub (email) claim."""
    from src.api.vn_pilot_auth import JWTExpiredError, JWTInvalidError
    from src.services.admin_token_service import decode_jwt

    jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT auth disabled — MEKONG_JWT_SECRET not set",
        )

    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    raw_token = auth[len("Bearer "):].strip()

    legacy = os.environ.get("MEKONG_ADMIN_TOKEN")
    if legacy and raw_token == legacy:
        return "admin@legacy"

    try:
        claims = decode_jwt(raw_token, jwt_secret)
    except JWTExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTInvalidError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = claims.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT missing sub claim")
    return email


__all__ = [
    "_extract_email_from_request",
    "_facade",
    "_log_webhook_error",
    "_open_db_conn",
    "_state",
    "_webhook_log_path",
]
