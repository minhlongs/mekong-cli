"""
VN Pilot API Routes — thin facade + re-export contract.

This module is the public entry point. Tests import it as:
    from src.api import vn_pilot_routes as vpr

All route logic lives in focused sub-modules. This file:
1. Assembles the APIRouter from sub-routers
2. Re-exports all symbols that tests access directly
3. Intercepts setattr on CONFIG_DIR / MAX_PILOTS so monkeypatch
   and direct assignment propagate to vn_pilot_state (sub-modules
   read _state.CONFIG_DIR at call time).

STORAGE: MEKONG_PILOT_STORAGE=sqlite enables SqliteBackend (Phase 8 P05).
SqliteBackend raises RuntimeError at init if pilot.db is missing —
fail-fast at gateway boot, not mid-traffic. Run migration script first.
"""
from __future__ import annotations

import logging
import os
import sys
import types
from pathlib import Path

from fastapi import APIRouter

import src.api.vn_pilot_state as _state

# ---------- Storage backend selector ----------

PILOT_STORAGE = os.getenv("MEKONG_PILOT_STORAGE", "jsonl").lower()
if PILOT_STORAGE == "sqlite":
    # Eagerly attempt backend init so gateway fails at boot (not mid-traffic)
    # if pilot.db is missing. RuntimeError propagates to launchd stderr.
    try:
        from src.services.storage_backend import _backend
        _backend()  # raises RuntimeError if DB missing
        logging.info("MEKONG_PILOT_STORAGE=sqlite: SqliteBackend initialized OK")
    except RuntimeError as _exc:
        logging.error(
            "MEKONG_PILOT_STORAGE=sqlite: %s — "
            "run scripts/migrate-jsonl-to-sqlite.py then restart gateway",
            _exc,
        )
        raise

# ---------- Module-level CONFIG_DIR / MAX_PILOTS ----------
# Authoritative values, kept in sync with vn_pilot_state via
# the _ProxyModule.__setattr__ below.

CONFIG_DIR: Path = _state.CONFIG_DIR
MAX_PILOTS: int = _state.MAX_PILOTS

# ---------- Custom module class for attribute-write interception ----------
# Replaces the default module type so setattr(vpr, "CONFIG_DIR", x)
# goes through our __setattr__ and syncs _state.CONFIG_DIR.
# Required because Python 3.14 does NOT route setattr() through
# a module-level __setattr__ function (PEP 562 only works via
# module.__setattr__ when called directly, not via the setattr builtin
# on Python ≥ 3.14). Using __class__ replacement is the reliable way.


class _ProxyModule(types.ModuleType):
    """ModuleType subclass that syncs CONFIG_DIR/MAX_PILOTS to _state."""

    def __setattr__(self, name: str, value: object) -> None:
        if name == "CONFIG_DIR":
            _state.CONFIG_DIR = value  # type: ignore[assignment]
        elif name == "MAX_PILOTS":
            _state.MAX_PILOTS = value  # type: ignore[assignment]
        super().__setattr__(name, value)


# Install proxy — must run before any attribute reads in tests
sys.modules[__name__].__class__ = _ProxyModule


# ---------- Main router ----------

router = APIRouter(prefix="/v1/pilot", tags=["VN Pilot"])

from src.api.vn_pilot_aggregates import aggregates_router  # noqa: E402
from src.api.vn_pilot_conversions import conversions_router  # noqa: E402
from src.api.vn_pilot_export import export_router  # noqa: E402
from src.api.vn_pilot_polls import polls_router  # noqa: E402
from src.api.vn_pilot_signup import signup_router  # noqa: E402

from src.api.vn_pilot_billing import billing_router # noqa: E402
from src.api.vn_pilot_drip import drip_router # noqa: E402
from src.api.vn_pilot_outreach import outreach_router # noqa: E402
router.include_router(aggregates_router)
router.include_router(conversions_router)
router.include_router(export_router)
router.include_router(drip_router)
router.include_router(polls_router)
router.include_router(signup_router)
router.include_router(billing_router)
router.include_router(outreach_router)

# ---------- Re-export contract ----------
# Tests do: vpr.MAX_PILOTS, vpr._append_jsonl, vpr._record_conversion, etc.

from src.api.vn_pilot_auth import _require_admin_token, _require_scope  # noqa: E402, F401
from src.api.vn_pilot_conversions import _convert_auth  # noqa: E402, F401
from src.api.vn_pilot_export import _export_auth  # noqa: E402, F401
from src.api.vn_pilot_common import (  # noqa: E402, F401
    INITIAL_FREE_CREDITS,
    PILOT_DURATION_WEEKS,
    SUPPORTED_TYPES,
    ConversionRequest,
    PollResponseRequest,
    SignupRequest,
    SignupResponse,
    _ZALO_RE,
    _add_credits,
    _append_conversion,
    _append_jsonl,
    _append_pilot,
    _append_response,
    _conversions_path,
    _count_by_key,
    _credit_balance,
    _credits_path,
    _current_iso_week,
    _ensure_dir,
    _find_by_zalo,
    _jsonl_add_credits,
    _jsonl_credit_balance,
    _load_conversions,
    _load_jsonl,
    _load_pilots,
    _load_responses,
    _org_filter,
    _pilots_path,
    _responses_path,
    _stable_user_id,
)
from src.api.vn_pilot_conversions import _record_conversion  # noqa: E402, F401
from src.api.vn_pilot_signup import _notify_founder_signup  # noqa: E402, F401
