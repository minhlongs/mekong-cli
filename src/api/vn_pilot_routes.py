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

import fcntl  # POSIX advisory lock — see _append_jsonl for Windows fallback note
import hashlib
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/v1/pilot", tags=["VN Pilot"])

# Test-isolation hook: tests can override via monkeypatch of this module-level
# var without touching ~/.mekong/ on the dev machine.
CONFIG_DIR = Path(os.getenv("MEKONG_PILOT_DIR", str(Path.home() / ".mekong")))

INITIAL_FREE_CREDITS = 50
PILOT_DURATION_WEEKS = 8
# Phase 7 stage 1: cap=50 (founder override). Phase 01b bumps to 100 after
# 1-week monitoring. Tests override via MEKONG_MAX_PILOTS env var.
MAX_PILOTS = int(os.getenv("MEKONG_MAX_PILOTS", "50"))
# Storage backend selector — Phase 7 scaffolding only. jsonl path is active;
# sqlite path is reserved for Phase 8 migration. Log a warning if anyone
# sets sqlite now so it's not silently ignored.
PILOT_STORAGE = os.getenv("MEKONG_PILOT_STORAGE", "jsonl").lower()
if PILOT_STORAGE == "sqlite":
    logging.warning(
        "MEKONG_PILOT_STORAGE=sqlite requested but unimplemented in Phase 7 — "
        "falling back to jsonl. SQLite migration scheduled for Phase 8."
    )
    PILOT_STORAGE = "jsonl"
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


class ConversionRequest(BaseModel):
    """Founder marks a pilot user as paid (Week 7-8 conversion phase).

    Idempotent on (user_id, started_at) — re-submitting same pair returns
    existing record without inflating MRR.
    """
    user_id: str = Field(min_length=4)
    tier: str = Field(min_length=1, max_length=40)  # vd "starter_vnd", "growth_vnd"
    monthly_vnd: int = Field(ge=0, le=100_000_000)  # ≤100M VND sanity cap
    started_at: Optional[str] = None  # ISO date; default = today

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        if not v.startswith("opc_"):
            raise ValueError("user_id phải bắt đầu bằng 'opc_'")
        return v


# ---------- Auth (admin endpoints) ----------

def _require_admin_token(authorization: Optional[str] = Header(default=None)) -> None:
    """Bearer-token gate for founder-only admin endpoints.

    Reads MEKONG_ADMIN_TOKEN at request time (so launchctl setenv updates
    take effect without code reload — useful for token rotation).

    - 503: env var not configured (feature locked at gateway level)
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


# ---------- Helpers ----------

def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _pilots_path() -> Path:
    return CONFIG_DIR / "pilots.jsonl"


def _credits_path() -> Path:
    return CONFIG_DIR / "pilot_credits.json"


def _responses_path() -> Path:
    return CONFIG_DIR / "poll_responses.jsonl"


def _conversions_path() -> Path:
    return CONFIG_DIR / "conversions.jsonl"


def _stable_user_id(name: str, zalo: str, seq: int) -> str:
    digest = hashlib.sha256(f"{name.strip().lower()}|{zalo.strip()}".encode()).hexdigest()[:6]
    return f"opc_{seq:03d}_{digest}"


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
    return _load_jsonl(_pilots_path())


def _load_responses() -> list[dict]:
    return _load_jsonl(_responses_path())


def _load_conversions() -> list[dict]:
    return _load_jsonl(_conversions_path())


def _find_by_zalo(zalo: str) -> Optional[dict]:
    for p in _load_pilots():
        if p.get("zalo") == zalo:
            return p
    return None


def _append_jsonl(path: Path, record: dict) -> None:
    """Append one JSON record to a JSONL file with POSIX advisory lock.

    Multi-worker safety: uvicorn with workers>1 can race on open(append) —
    interleaved writes produce torn lines. fcntl.flock(LOCK_EX) serializes
    writes within the same host. Lock released implicitly on close.

    Limitation: fcntl is POSIX-only. On Windows this raises AttributeError
    at import time; the gateway is launchd-managed on macOS so this is
    acceptable. If Windows support is added later, swap to a portable
    portalocker.lock() call here.
    """
    _ensure_dir()
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()  # push to kernel before lock release
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


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


async def _notify_founder_signup(record: dict) -> None:
    """Fire founder webhook on new pilot signup. Non-blocking, resilient.

    Env vars (both optional):
    - MEKONG_SIGNUP_WEBHOOK_URL: target endpoint (Zapier/Pipedream/Telegram bot)
    - MEKONG_SIGNUP_WEBHOOK_AUTH: optional Authorization header value

    Payload includes PII (name, zalo) because founder needs to call user.
    Webhook URL must point to a PRIVATE endpoint, not a public broadcast
    channel — same security posture as MEKONG_ADMIN_TOKEN.

    Failures logged at WARNING but never raised — signup response must
    succeed even if Slack/Zapier is down.
    """
    url = os.environ.get("MEKONG_SIGNUP_WEBHOOK_URL")
    if not url:
        return
    headers = {"Content-Type": "application/json"}
    auth = os.environ.get("MEKONG_SIGNUP_WEBHOOK_AUTH")
    if auth:
        headers["Authorization"] = auth
    payload = {
        "event": "pilot.signup.new",
        "user_id": record.get("user_id"),
        "name": record.get("name"),
        "zalo": record.get("zalo"),
        "business_type": record.get("business_type"),
        "city": record.get("city"),
        "industry": record.get("industry"),
        "source": record.get("source"),
        "onboarded_at": record.get("onboarded_at"),
    }
    try:
        import httpx  # local import keeps cold-start cheap when feature unused
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                logging.warning(
                    "Founder signup webhook returned %d: %s",
                    resp.status_code, resp.text[:200],
                )
    except Exception as exc:  # noqa: BLE001 — fire-and-forget, never raise
        logging.warning("Founder signup webhook failed: %s", exc)


# ---------- Routes ----------

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "vn-pilot"}


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest, background_tasks: BackgroundTasks) -> SignupResponse:
    """Onboard 1 pilot user. Idempotent: same Zalo → return existing user_id.

    Source channels: web form / Zalo bot webhook / Zapier / Google Forms /
    LinkedIn DM follow-up — all funnel here.

    On is_new=True signups, schedules a fire-and-forget founder webhook
    (see _notify_founder_signup). Repeat submissions don't re-fire — avoids
    notification spam when a user re-opens the form.
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
    if seq > MAX_PILOTS:
        # Pilot capped at MAX_PILOTS (Phase 7 stage 1 = 50). Reject gracefully.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pilot đã đủ {MAX_PILOTS} user. Subscribe waitlist: hello@mekongmind.com",
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

    # Notify founder out-of-band (won't delay this response). Tests inject a
    # mock by monkeypatching this module's _notify_founder_signup.
    background_tasks.add_task(_notify_founder_signup, record)

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


@router.post(
    "/convert",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_require_admin_token)],
)
async def convert(req: ConversionRequest) -> dict[str, object]:
    """Mark a pilot user as paid. Records tier + MRR contribution.

    Phase 6 Week 7-8 conversion phase: founder calls this after Polar.sh
    payment confirms (or manual VietQR transfer). Idempotent on
    (user_id, started_at) — re-call returns existing record.

    Requires `Authorization: Bearer <MEKONG_ADMIN_TOKEN>` header. Errors:
    - 401 / 403 / 503: auth (see _require_admin_token docstring)
    - 404 if user_id not in pilots.jsonl
    """
    pilots = _load_pilots()
    if not any(p["user_id"] == req.user_id for p in pilots):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown user_id: {req.user_id}",
        )
    started_at = req.started_at or datetime.now(timezone.utc).date().isoformat()
    existing = next(
        (
            c for c in _load_conversions()
            if c.get("user_id") == req.user_id and c.get("started_at") == started_at
        ),
        None,
    )
    if existing:
        return {"is_new": False, **existing}
    record = {
        "user_id": req.user_id,
        "tier": req.tier,
        "monthly_vnd": req.monthly_vnd,
        "started_at": started_at,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _append_jsonl(_conversions_path(), record)
    return {"is_new": True, **record}


@router.get("/revenue")
async def revenue() -> dict[str, object]:
    """Conversion + MRR snapshot for founder dashboard.

    MRR = sum of monthly_vnd across all conversion records. If a single
    user appears twice (eg restart at higher tier), both contribute — the
    founder is responsible for closing old conversions before adding new.
    """
    pilots = _load_pilots()
    conversions = _load_conversions()
    total_pilots = len(pilots)
    converted_user_ids = {c["user_id"] for c in conversions}
    mrr_vnd = sum(c.get("monthly_vnd", 0) for c in conversions)
    by_tier: dict[str, int] = {}
    for c in conversions:
        by_tier[c.get("tier") or "unknown"] = by_tier.get(c.get("tier") or "unknown", 0) + 1
    return {
        "conversions": len(conversions),
        "unique_converted_users": len(converted_user_ids),
        "conversion_rate": (
            round(len(converted_user_ids) / total_pilots, 3) if total_pilots else 0.0
        ),
        "mrr_vnd": mrr_vnd,
        "by_tier": by_tier,
        "target_mrr_vnd": 1_000_000,  # Phase 6 goal: 5 × 199K ≈ 1M VND
        "target_conversions": 5,
    }


@router.get("/stats")
async def stats() -> dict[str, object]:
    """Aggregate stats — for founder dashboard.

    Cross-references conversions.jsonl to split active pilots into:
    - trial_pilots: signed up + status active + NOT in conversions
    - converted_pilots: at least one conversion record (regardless of status)

    active_pilots kept for backward compat = users with status==active
    (includes converted — they're still active users, just paying ones).
    """
    pilots = _load_pilots()
    active = [p for p in pilots if p.get("status", "active") == "active"]
    pilot_user_ids = {p.get("user_id") for p in pilots}
    converted_user_ids = {c["user_id"] for c in _load_conversions()} & pilot_user_ids
    trial = [p for p in active if p.get("user_id") not in converted_user_ids]
    return {
        "total_pilots": len(pilots),
        "active_pilots": len(active),
        "converted_pilots": len(converted_user_ids),
        "trial_pilots": len(trial),
        "capacity_remaining": max(0, MAX_PILOTS - len(pilots)),
        "by_type": _count_by_key(pilots, "business_type"),
        "by_source": _count_by_key(pilots, "source"),
    }


def _count_by_key(records: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in records:
        v = r.get(key) or "unknown"
        counts[v] = counts.get(v, 0) + 1
    return counts


@router.get("/recent")
async def recent(limit: int = Query(default=10, ge=1, le=100)) -> dict[str, list]:
    """Recent signups + NPS responses for founder dashboard. No PII exposed.

    Strips name + zalo from signups; truncates comment to 80 chars.
    Sorted newest-first by timestamp. Used by mekong-pilot-admin dashboard.
    """
    pilots = sorted(_load_pilots(), key=lambda p: p.get("onboarded_at", ""), reverse=True)
    responses = sorted(_load_responses(), key=lambda r: r.get("recorded_at", ""), reverse=True)
    return {
        "signups": [
            {
                "business_type": p.get("business_type"),
                "city": p.get("city"),
                "source": p.get("source"),
                "onboarded_at": p.get("onboarded_at"),
            }
            for p in pilots[:limit]
        ],
        "nps_responses": [
            {
                "score": r.get("score"),
                "iso_week": r.get("iso_week"),
                "recorded_at": r.get("recorded_at"),
                "comment_preview": (r.get("comment") or "")[:80],
            }
            for r in responses[:limit]
        ],
    }
