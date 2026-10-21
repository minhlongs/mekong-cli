# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VietQR recurring billing — storage helpers, tier maps, and status refresh."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

_TIER_CREDITS: dict[str, int] = {
    "starter_vnd": 300,   # 199K VND / month
    "growth_vnd": 1200,   # 299K VND / month
    "pro_vnd": 3500,      # 499K VND / month
}

_TIER_PRICES_VND: dict[int, str] = {
    199_000: "starter_vnd",
    299_000: "growth_vnd",
    499_000: "pro_vnd",
}


def _ensure_dir() -> None:
    import src.api.vn_pilot_state as _state

    _state.CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _subscriptions_path():
    """Legacy path helper (kept for backwards compat). Writes go via backend."""
    import src.api.vn_pilot_state as _state

    return _state.CONFIG_DIR / "subscriptions.jsonl"


def _load_subscriptions() -> list[dict]:
    from src.services.storage_backend import _backend

    b = _backend()
    return b.load_subscriptions() if hasattr(b, "load_subscriptions") else []


def _append_subscription(record: dict) -> None:
    import src.services.vietqr_recurring as _vqr

    _vqr._ensure_dir()
    from src.services.storage_backend import _backend

    _backend().append_subscription(record)


def _load_subs() -> list[dict]:
    """Load all subscription records for a user. Uses storage backend."""
    from src.services.storage_backend import _backend

    backend = _backend()
    if hasattr(backend, "load_subscriptions"):
        return backend.load_subscriptions()

    import src.services.vietqr_recurring as _vqr

    path = _vqr._subscriptions_path()
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _latest_subscription(subs: list[dict], user_id: str) -> Optional[dict]:
    """Return the LAST subscription record for a user (most recent state)."""
    matching = [s for s in subs if s.get("user_id") == user_id]
    return matching[-1] if matching else None


def _refresh_subscription_status(sub: dict) -> None:
    """Mutate sub in-place with effective status — no append (read-only)."""
    today = datetime.now(timezone.utc).date().isoformat()
    next_due = sub.get("next_due_at", "")
    if next_due and next_due < today and sub.get("status") not in ("cancelled", "expired"):
        sub["_effective_status"] = "overdue"
    else:
        sub["_effective_status"] = sub.get("status", "active")


__all__ = [
    "_TIER_CREDITS",
    "_TIER_PRICES_VND",
    "_ensure_dir",
    "_subscriptions_path",
    "_load_subscriptions",
    "_append_subscription",
    "_load_subs",
    "_latest_subscription",
    "_refresh_subscription_status",
]
