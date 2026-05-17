"""
VN Pilot API Routes — recruitment + telemetry intake.

POST /v1/pilot/signup    → onboard mới (web form, Zalo webhook, Zapier...)
POST /v1/pilot/response  → poll response auto-capture (NPS 1-5)
GET  /v1/pilot/health    → router sanity check

Persist:
    ~/.mekong/pilots.jsonl          (append, shared với scripts/pilot-onboard.py)
    ~/.mekong/pilot_credits.json    (JSON dict)
    ~/.mekong/poll_responses.jsonl  (shared với scripts/pilot-weekly-poll.py)

Idempotency: same {name + zalo} → same user_id (hash-based).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/v1/pilot", tags=["VN Pilot"])

# Test-isolation hook: tests can override via monkeypatch of this module-level
# var without touching ~/.mekong/ on the dev machine.
CONFIG_DIR = Path(os.getenv("MEKONG_PILOT_DIR", str(Path.home() / ".mekong")))

INITIAL_FREE_CREDITS = 50
PILOT_DURATION_WEEKS = 8
SUPPORTED_TYPES = {
    "shop_online", "freelancer", "cafe_fnb", "giao_vien",
    "dich_vu", "ho_kinh_doanh", "opc",
}
# E.164 với prefix +84 hoặc số VN dạng 0xxxxxxxxx (10 digits)
_ZALO_RE = re.compile(r"^(\+84\d{9,10}|0\d{9})$")


# ---------- Pydantic models ----------

class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    zalo: str = Field(description="Số Zalo: +84xxx hoặc 0xxx")
    business_type: str
    city: str = "HCM"
    industry: Optional[str] = None
    source: Optional[str] = Field(default=None, description="Channel: fb|zalo_group|linkedin|email|web_form")

    @field_validator("zalo")
    @classmethod
    def _validate_zalo(cls, v: str) -> str:
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not _ZALO_RE.match(cleaned):
            raise ValueError("Zalo phone invalid — phải là +84xxx hoặc 0xxx")
        return cleaned

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


# ---------- Helpers ----------

def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _pilots_path() -> Path:
    return CONFIG_DIR / "pilots.jsonl"


def _credits_path() -> Path:
    return CONFIG_DIR / "pilot_credits.json"


def _responses_path() -> Path:
    return CONFIG_DIR / "poll_responses.jsonl"


def _stable_user_id(name: str, zalo: str, seq: int) -> str:
    digest = hashlib.sha256(f"{name.strip().lower()}|{zalo.strip()}".encode()).hexdigest()[:6]
    return f"opc_{seq:03d}_{digest}"


def _load_pilots() -> list[dict]:
    p = _pilots_path()
    if not p.exists():
        return []
    out = []
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _find_by_zalo(zalo: str) -> Optional[dict]:
    for p in _load_pilots():
        if p.get("zalo") == zalo:
            return p
    return None


def _append_jsonl(path: Path, record: dict) -> None:
    _ensure_dir()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _credit_balance(user_id: str) -> int:
    path = _credits_path()
    if not path.exists():
        return 0
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get(user_id, 0))
    except json.JSONDecodeError:
        return 0


def _add_credits(user_id: str, delta: int) -> int:
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


def _current_iso_week() -> str:
    y, w, _ = datetime.now(timezone.utc).isocalendar()
    return f"{y}-W{w:02d}"


# ---------- Routes ----------

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "vn-pilot"}


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest) -> SignupResponse:
    """Onboard 1 pilot user. Idempotent: same Zalo → return existing user_id.

    Source channels: web form / Zalo bot webhook / Zapier / Google Forms /
    LinkedIn DM follow-up — all funnel here.
    """
    existing = _find_by_zalo(req.zalo)
    if existing:
        # Idempotent — same person re-submitting form
        return SignupResponse(
            user_id=existing["user_id"],
            credits=_credit_balance(existing["user_id"]),
            pilot_end_at=existing["pilot_end_at"],
            is_new=False,
        )

    pilots = _load_pilots()
    seq = len(pilots) + 1
    if seq > 10:
        # Pilot capped at 10 users (per Phase 6 plan). Reject gracefully.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pilot đã đủ 10 user. Subscribe waitlist: hello@mekongmind.com",
        )

    user_id = _stable_user_id(req.name, req.zalo, seq)
    now = datetime.now(timezone.utc)
    record = {
        "user_id": user_id,
        "name": req.name,
        "zalo": req.zalo,
        "business_type": req.business_type,
        "city": req.city,
        "industry": req.industry,
        "source": req.source,
        "onboarded_at": now.isoformat(timespec="seconds"),
        "pilot_end_at": (now + timedelta(weeks=PILOT_DURATION_WEEKS)).isoformat(timespec="seconds"),
        "status": "active",
    }
    _append_jsonl(_pilots_path(), record)
    balance = _add_credits(user_id, INITIAL_FREE_CREDITS)

    return SignupResponse(
        user_id=user_id,
        credits=balance,
        pilot_end_at=record["pilot_end_at"],
        is_new=True,
    )


@router.post("/response", status_code=status.HTTP_201_CREATED)
async def poll_response(req: PollResponseRequest) -> dict[str, object]:
    """Capture poll response from Zalo webhook / web form.

    Bypasses CLI `pilot-weekly-poll.py record` — useful when Zalo OA forwards
    user replies to your webhook URL automatically.
    """
    # Sanity check user exists (don't accept responses for unknown users)
    if not any(p["user_id"] == req.user_id for p in _load_pilots()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown user_id: {req.user_id}",
        )
    iso_week = req.iso_week or _current_iso_week()
    record = {
        "user_id": req.user_id,
        "score": req.score,
        "comment": req.comment,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "iso_week": iso_week,
    }
    _append_jsonl(_responses_path(), record)
    return {
        "recorded": True,
        "user_id": req.user_id,
        "score": req.score,
        "iso_week": iso_week,
        "low_nps_alert": req.score < 4,  # founder follow-up signal
    }


@router.get("/stats")
async def stats() -> dict[str, object]:
    """Aggregate stats — for founder dashboard."""
    pilots = _load_pilots()
    active = [p for p in pilots if p.get("status", "active") == "active"]
    return {
        "total_pilots": len(pilots),
        "active_pilots": len(active),
        "capacity_remaining": max(0, 10 - len(pilots)),
        "by_type": _count_by_key(pilots, "business_type"),
        "by_source": _count_by_key(pilots, "source"),
    }


def _count_by_key(records: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        v = r.get(key) or "unknown"
        counts[v] = counts.get(v, 0) + 1
    return counts
