# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CashClaw SDK — customer-facing Python SDK for prediction trading signals."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from src.polymarket.sdk_models import (
    PaperStatus,
    SDKMarket,
    SDKSignal,
    Tier,
    TierLimits,
)

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class CashClaw:
    """CashClaw SDK client for prediction market trading signals."""

    def __init__(
        self,
        api_key: str,
        tier: str = "starter",
        base_url: str = "",
    ) -> None:
        self.api_key = api_key
        self.tier = Tier(tier.lower())
        self.limits = TierLimits.for_tier(self.tier)
        self.base_url = base_url or os.getenv("CASHCLAW_API_URL", "https://api.cashclaw.io")
        self._signals_today = 0
        self._http: Optional[Any] = None

        if HAS_HTTPX:
            self._http = httpx.Client(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )

    @classmethod
    def init(cls, api_key: str = "", tier: str = "starter", base_url: str = "") -> CashClaw:
        key = api_key or os.getenv("CASHCLAW_API_KEY", "")
        if not key:
            raise ValueError("API key required. Set CASHCLAW_API_KEY or pass api_key parameter.")
        return cls(api_key=key, tier=tier, base_url=base_url)

    def scan(self) -> list[SDKMarket]:
        data = self._get("/v1/markets")
        return [
            SDKMarket(
                market_id=m["market_id"], question=m["question"], volume_24h=m["volume_24h"],
                days_to_resolution=m["days_to_resolution"], yes_price=m["yes_price"], no_price=m["no_price"],
            )
            for m in data.get("markets", [])
        ]

    def predict(self, market_id: str) -> dict:
        self._check_signal_limit()
        data = self._get(f"/v1/predict/{market_id}")
        self._signals_today += 1
        return data

    def signals(self) -> list[SDKSignal]:
        remaining = self.limits.signals_per_day - self._signals_today
        if remaining <= 0:
            logger.warning("Signal limit reached (%d/%d). Upgrade tier for more.", self._signals_today, self.limits.signals_per_day)
            return []

        data = self._get("/v1/signals", params={"limit": remaining})
        self._signals_today += len(data.get("signals", []))

        return [
            SDKSignal(
                market_id=s["market_id"], question=s["question"], direction=s["direction"],
                predicted_probability=s["predicted_probability"], market_price=s["market_price"],
                edge=s["edge"], confidence=s["confidence"], kelly_fraction=s["kelly_fraction"],
                position_size_pct=s["position_size_pct"], rank=s["rank"],
            )
            for s in data.get("signals", [])
        ]

    def paper_start(self) -> dict:
        return self._post("/v1/paper/start")

    def paper_status(self) -> PaperStatus:
        data = self._get("/v1/paper/status")
        return PaperStatus(
            running=data.get("running", False), trades=data.get("trades", 0),
            pnl=data.get("pnl", 0.0), win_rate=data.get("win_rate", 0.0),
            capital=data.get("capital", 0.0), brier_score=data.get("brier_score", 0.0),
        )

    def paper_stop(self) -> dict:
        return self._post("/v1/paper/stop")

    @property
    def remaining_signals(self) -> int:
        return max(0, self.limits.signals_per_day - self._signals_today)

    def _check_signal_limit(self) -> None:
        if self._signals_today >= self.limits.signals_per_day:
            tier_name = "Pro" if self.tier == Tier.STARTER else "Elite"
            raise PermissionError(f"Daily signal limit reached ({self.limits.signals_per_day}). Upgrade to {tier_name} for more signals.")

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        if self._http is None:
            return {"error": "httpx not installed", "markets": [], "signals": []}
        try:
            resp = self._http.get(path, params=params)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("API request failed: %s %s", path, e)
            return {"error": str(e), "markets": [], "signals": []}

    def _post(self, path: str, data: Optional[dict] = None) -> dict:
        if self._http is None:
            return {"error": "httpx not installed"}
        try:
            resp = self._http.post(path, json=data or {})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("API request failed: %s %s", path, e)
            return {"error": str(e)}

    def close(self) -> None:
        if self._http and hasattr(self._http, "close"):
            self._http.close()

    def __enter__(self) -> CashClaw:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


__all__ = [
    "CashClaw", "HAS_HTTPX", "PaperStatus", "SDKMarket",
    "SDKSignal", "Tier", "TierLimits",
]
