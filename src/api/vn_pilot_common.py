"""VN Pilot — shared models, constants, JSONL helpers, and backend delegation.

Imports CONFIG_DIR / MAX_PILOTS from vn_pilot_state at call time
(inside function bodies) so monkeypatching vn_pilot_routes.CONFIG_DIR
propagates correctly via the __setattr__ proxy.

Storage delegation: _load_pilots/_load_conversions/_load_responses and
_credit_balance/_add_credits now delegate to storage_backend._backend()
so MEKONG_PILOT_STORAGE=sqlite transparently swaps the backing store.
Raw helpers (_append_jsonl, _load_jsonl, path helpers) remain exported
for tests + migration scripts that use them directly.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator

import src.api.vn_pilot_state as _state

# ---------- Constants ----------

INITIAL_FREE_CREDITS = 50
PILOT_DURATION_WEEKS = 8
SUPPORTED_TYPES = {
    "shop_online", "freelancer", "cafe_fnb", "giao_vien",
    "dich_vu", "ho_kinh_doanh", "opc",
}
_ZALO_RE = re.compile(r"^(\+84\d{9,10}|0\d{9})$")


# ---------- Pydantic models ----------

class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    zalo: str = Field(description="Số Zalo: +84xxx hoặc 0xxx")
    business_type: str
    city: str = "HCM"
    industry: Optional[str] = None
    source: Optional[str] = Field(default=None, description="Channel: fb|zalo_group|linkedin|email|web_form")
    org_id: str = Field(default="default", pattern=r"^[a-z0-9][a-z0-9-]{0,31}$")

    @field_validator("zalo")
    @classmethod
    def _validate_zalo(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not _ZALO_RE.match(cleaned):
            raise ValueError("Zalo phone invalid — phải là +84xxx hoặc 0xxx")
        return cleaned

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        """Strip control chars, reject HTML/script injection, cap at 200."""
        import re
        # Remove all control characters (U+0000-U+001F and U+007F-U+009F)
        cleaned = "".join(ch for ch in v if not (ord(ch) <= 0x1F or 0x7F <= ord(ch) <= 0x9F))
        # Reject if contains HTML/script tags
        if re.search(r"<[^>]+>", cleaned, re.IGNORECASE):
            raise ValueError("Tên không được chứa thẻ HTML hoặc script")
        return cleaned[:200]

    @field_validator("business_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        if v not in SUPPORTED_TYPES:
            raise ValueError(f"business_type không hỗ trợ; chọn: {sorted(SUPPORTED_TYPES)}")
        return v


class SignupResponse(BaseModel):
    user_id: str
    credits: int
    pilot_end_at: str
    is_new: bool


class PollResponseRequest(BaseModel):
    user_id: str = Field(min_length=4)
    score: int = Field(ge=1, le=5)
    comment: str = ""
    iso_week: Optional[str] = None  # vd "2026-W20" — default = current

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        if not v.startswith("opc_"):
            raise ValueError("user_id phải bắt đầu bằng 'opc_'")
        return v


class ConversionRequest(BaseModel):
    """Founder marks a pilot user as paid (Week 7-8 conversion phase).

    Idempotent on (user_id, started_at) — re-submitting same pair returns
    existing record without inflating MRR.
    """
    user_id: str = Field(min_length=4)
    tier: str = Field(min_length=1, max_length=40)
    monthly_vnd: int = Field(ge=0, le=100_000_000)
    started_at: Optional[str] = None

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        if not v.startswith("opc_"):
            raise ValueError("user_id phải bắt đầu bằng 'opc_'")
        return v


# ---------- Path helpers (read CONFIG_DIR from state at call time) ----------

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




# ---------- JSONL I/O ----------

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
    """Append one JSON record to a JSONL file with POSIX advisory lock.

    Multi-worker safety: uvicorn with workers>1 can race on open(append) —
    interleaved writes produce torn lines. fcntl.flock(LOCK_EX) serializes
    writes within the same host. Lock released implicitly on close.
    """
    _ensure_dir()
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


# ---------- Business helpers ----------

def _org_filter(records: list[dict], org_id: str) -> list[dict]:
    """Filter records by org_id, treating missing field as 'default'."""
    return [r for r in records if r.get("org_id", "default") == org_id]


def _find_by_zalo(zalo: str, org_id: str = "default") -> Optional[dict]:
    """Return pilot record matching zalo within the given org_id scope."""
    for p in _org_filter(_load_pilots(), org_id):
        if p.get("zalo") == zalo:
            return p
    return None


def _credit_balance(user_id: str) -> int:
    from src.services.storage_backend import _backend
    return _backend().get_credit_balance(user_id)


def _add_credits(user_id: str, delta: int) -> int:
    from src.services.storage_backend import _backend
    return _backend().add_credits(user_id, delta)


# ---------- Raw JSONL credit helpers (used by JsonlBackend internally) ----------

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


# ---------- Thin backend appenders (callsites use these) ----------

def _append_pilot(record: dict) -> None:
    """Append a pilot record via the active backend."""
    from src.services.storage_backend import _backend
    _backend().append_pilot(record)


def _append_conversion(record: dict) -> None:
    """Append a conversion record via the active backend."""
    from src.services.storage_backend import _backend
    _backend().append_conversion(record)


def _append_response(record: dict) -> None:
    """Append a poll response record via the active backend."""
    from src.services.storage_backend import _backend
    _backend().append_response(record)


def _current_iso_week() -> str:
    y, w, _ = datetime.now(timezone.utc).isocalendar()
    return f"{y}-W{w:02d}"


def _stable_user_id(name: str, zalo: str, seq: int, org_id: str = "default") -> str:
    digest = hashlib.sha256(f"{name.strip().lower()}|{zalo.strip()}".encode()).hexdigest()[:6]
    if org_id == "default":
        return f"opc_{seq:03d}_{digest}"
    return f"opc_{org_id}_{seq:03d}_{digest}"


def _count_by_key(records: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        v = r.get(key) or "unknown"
        counts[v] = counts.get(v, 0) + 1
    return counts
