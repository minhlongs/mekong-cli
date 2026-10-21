# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VN Pilot — shared models, constants, JSONL helpers, and backend delegation.

Imports CONFIG_DIR / MAX_PILOTS from vn_pilot_state at call time
(inside function bodies) so monkeypatching vn_pilot_routes.CONFIG_DIR
propagates correctly via the __setattr__ proxy.
"""
from __future__ import annotations

import fcntl
import json
from pathlib import Path
from typing import Optional

import src.api.vn_pilot_state as _state
from src.api.vn_pilot_models import (  # noqa: F401
    INITIAL_FREE_CREDITS,
    PILOT_DURATION_WEEKS,
    SUPPORTED_TYPES,
    ConversionRequest,
    PollResponseRequest,
    SignupRequest,
    SignupResponse,
    _count_by_key,
    _current_iso_week,
    _stable_user_id,
    _validate_email,
    _ZALO_RE,
)


def _ensure_dir() -> None:
    _state.CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _pilots_path() -> Path:
    return _state.CONFIG_DIR / "pilots.jsonl"


def _credits_path() -> Path:
    return _state.CONFIG_DIR / "pilot_credits.json"


def _responses_path() -> Path:
    return _state.CONFIG_DIR / "poll_responses.jsonl"


def _conversions_path() -> Path:
    return _state.CONFIG_DIR / "conversions.jsonl"


def _subscriptions_path() -> Path:
    """Path to the subscriptions JSONL file (used by storage_backend.SqliteBackend)."""
    return _state.CONFIG_DIR / "subscriptions.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    """Load newline-delimited JSON file, skipping malformed lines."""
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _load_pilots() -> list[dict]:
    from src.services.storage_backend import _backend
    return _backend().load_pilots()


def _load_responses() -> list[dict]:
    from src.services.storage_backend import _backend
    return _backend().load_responses()


def _load_conversions() -> list[dict]:
    from src.services.storage_backend import _backend
    return _backend().load_conversions()


def _append_jsonl(path: Path, record: dict) -> None:
    """Append one JSON record to a JSONL file with POSIX advisory lock."""
    _ensure_dir()
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _org_filter(records: list[dict], org_id: str) -> list[dict]:
    """Filter records by org_id, treating missing field as 'default'."""
    return [r for r in records if r.get("org_id", "default") == org_id]


def _find_by_zalo(zalo: str, org_id: str = "default") -> Optional[dict]:
    """Return pilot record matching zalo within the given org_id scope."""
    for p in _org_filter(_load_pilots(), org_id):
        if p.get("zalo") == zalo:
            return p
    return None


def _find_by_email(email: str, org_id: str = "default") -> Optional[dict]:
    """Return pilot record matching email within the given org_id scope."""
    normalized = email.strip().lower()
    for p in _org_filter(_load_pilots(), org_id):
        if (p.get("email") or "").strip().lower() == normalized:
            return p
    return None


def _credit_balance(user_id: str) -> int:
    from src.services.storage_backend import _backend
    return _backend().get_credit_balance(user_id)


def _add_credits(user_id: str, delta: int) -> int:
    from src.services.storage_backend import _backend
    return _backend().add_credits(user_id, delta)


def _jsonl_credit_balance(user_id: str) -> int:
    """Direct JSONL credit read — used by JsonlBackend. Not delegated."""
    path = _credits_path()
    if not path.exists():
        return 0
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get(user_id, 0))
    except json.JSONDecodeError:
        return 0


def _jsonl_add_credits(user_id: str, delta: int) -> int:
    """Direct JSONL credit write — used by JsonlBackend. Not delegated."""
    path = _credits_path()
    balances: dict[str, int] = {}
    if path.exists():
        try:
            balances = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            balances = {}
    balances[user_id] = max(0, balances.get(user_id, 0) + delta)
    _ensure_dir()
    path.write_text(json.dumps(balances, ensure_ascii=False, indent=2), encoding="utf-8")
    return balances[user_id]


def _append_pilot(record: dict) -> None:
    from src.services.storage_backend import _backend
    _backend().append_pilot(record)


def _append_conversion(record: dict) -> None:
    from src.services.storage_backend import _backend
    _backend().append_conversion(record)


def _append_response(record: dict) -> None:
    from src.services.storage_backend import _backend
    _backend().append_response(record)
