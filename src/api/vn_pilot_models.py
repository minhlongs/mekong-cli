# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VN Pilot — shared Pydantic models, constants, and pure utility helpers."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator

INITIAL_FREE_CREDITS = 50
PILOT_DURATION_WEEKS = 8
SUPPORTED_TYPES = {
    "shop_online", "freelancer", "cafe_fnb", "giao_vien",
    "dich_vu", "ho_kinh_doanh", "opc",
}
_ZALO_RE = re.compile(r"^(\+84\d{9,10}|0\d{9})$")


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    zalo: str = Field(description="Số Zalo: +84xxx hoặc 0xxx")
    email: Optional[str] = Field(
        default=None, description="Email để gửi welcome + onboarding (optional)"
    )
    business_type: str
    city: str = "HCM"
    industry: Optional[str] = None
    source: Optional[str] = Field(
        default=None, description="Channel: fb|zalo_group|linkedin|email|web_form"
    )
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
        cleaned = "".join(
            ch for ch in v if not (ord(ch) <= 0x1F or 0x7F <= ord(ch) <= 0x9F)
        )
        if re.search(r"<[^>]+>", cleaned, re.IGNORECASE):
            raise ValueError("Tên không được chứa thẻ HTML hoặc script")
        return cleaned[:200]

    @field_validator("business_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        if v not in SUPPORTED_TYPES:
            raise ValueError(
                f"business_type không hỗ trợ; chọn: {sorted(SUPPORTED_TYPES)}"
            )
        return v


@field_validator("email")
@classmethod
def _validate_email(cls, v: Optional[str]) -> Optional[str]:
    if v is None or v == "":
        return None
    cleaned = v.strip().lower()
    if "@" not in cleaned or cleaned.index("@") == 0:
        raise ValueError("Email khong hop le")
    local, domain = cleaned.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        raise ValueError("Email khong hop le")
    if len(cleaned) > 254:
        raise ValueError("Email qua dai (max 254 ki tu)")
    return cleaned


class SignupResponse(BaseModel):
    user_id: str
    credits: int
    pilot_end_at: str
    is_new: bool


class PollResponseRequest(BaseModel):
    user_id: str = Field(min_length=4)
    score: int = Field(ge=1, le=5)
    comment: str = ""
    iso_week: Optional[str] = None

    @field_validator("user_id")
    @classmethod
    def _validate_user_id(cls, v: str) -> str:
        if not v.startswith("opc_"):
            raise ValueError("user_id phải bắt đầu bằng 'opc_'")
        return v


class ConversionRequest(BaseModel):
    """Founder marks a pilot user as paid (Week 7-8 conversion phase)."""

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


__all__ = [
    "INITIAL_FREE_CREDITS",
    "PILOT_DURATION_WEEKS",
    "SUPPORTED_TYPES",
    "_ZALO_RE",
    "SignupRequest",
    "_validate_email",
    "SignupResponse",
    "PollResponseRequest",
    "ConversionRequest",
    "_current_iso_week",
    "_stable_user_id",
    "_count_by_key",
]
