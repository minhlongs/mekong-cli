"""
Service Credits Lookup — Đếm credits tiêu thụ mỗi command.

Đọc factory/contracts/pricing.json để tính credits per command.
Hỗ trợ cả services USD và vn_services VN.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

_PRICING_FILE = Path(__file__).resolve().parents[2] / "factory" / "contracts" / "pricing.json"

DEFAULT_CREDIT_COST = 1


@lru_cache(maxsize=1)
def _load_pricing() -> dict:
    if not _PRICING_FILE.exists():
        return {}
    try:
        with _PRICING_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=256)
def credits_for_command(command: str) -> int:
    """
    Trả về credits cost cho 1 command.

    Tìm trong vn_services trước (1 credit dịch vụ VN), sau đó services USD.
    Fallback DEFAULT_CREDIT_COST nếu không tìm thấy.
    """
    if not command:
        return DEFAULT_CREDIT_COST

    data = _load_pricing()
    cmd = command.strip().lower().lstrip("/")

    for svc in data.get("vn_services", []):
        if svc.get("command", "").lower() == cmd:
            return int(svc.get("credits", DEFAULT_CREDIT_COST))

    for svc in data.get("services", []):
        if svc.get("command", "").lower() == cmd:
            return int(svc.get("credits", DEFAULT_CREDIT_COST))

    return DEFAULT_CREDIT_COST


def is_vn_command(command: str) -> bool:
    """True nếu command thuộc vn_services."""
    data = _load_pricing()
    cmd = command.strip().lower().lstrip("/")
    return any(s.get("command", "").lower() == cmd for s in data.get("vn_services", []))


def list_vn_commands() -> list[str]:
    """Danh sách commands VN-specific."""
    data = _load_pricing()
    return [s.get("command", "") for s in data.get("vn_services", []) if s.get("command")]


def get_vn_tier(tier_key: str) -> Optional[dict]:
    """Lấy thông tin 1 tier VN (starter_vn/growth_vn/pro_vn)."""
    data = _load_pricing()
    return data.get("vn_products", {}).get(tier_key)


__all__ = [
    "credits_for_command",
    "is_vn_command",
    "list_vn_commands",
    "get_vn_tier",
    "DEFAULT_CREDIT_COST",
]
