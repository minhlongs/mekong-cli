"""CashClaw SDK — customer-facing Python SDK for prediction trading signals.

Usage:
    from cashclaw import CashClaw

    client = CashClaw.init(api_key="sk-...", tier="pro")
    signals = client.signals()
    for signal in signals:
        print(f"{signal.market_id}: {signal.direction} edge={signal.edge:.1%}")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Optional httpx for API calls
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class Tier(Enum):
    """Subscription tiers with feature gating."""
    STARTER = "starter"
    PRO = "pro"
    ELITE = "elite"


@dataclass
class TierLimits:
    """Feature limits per tier."""
    signals_per_day: int
    ensemble_n: int
    dark_edge: bool
    custom_strategies: bool

    @classmethod
    def for_tier(cls, tier: Tier) -> TierLimits:
        limits = {
            Tier.STARTER: cls(signals_per_day=5, ensemble_n=1, dark_edge=False, custom_strategies=False),
            Tier.PRO: cls(signals_per_day=20, ensemble_n=3, dark_edge=True, custom_strategies=False),
            Tier.ELITE: cls(signals_per_day=999, ensemble_n=5, dark_edge=True, custom_strategies=True),
        }
        return limits.get(tier, limits[Tier.STARTER])


@dataclass
class SDKSignal:
    """A trading signal returned by the SDK."""
    market_id: str
    question: str
    direction: str
    predicted_probability: float
    market_price: float
    edge: float
    confidence: float
    kelly_fraction: float
    position_size_pct: float
    rank: int


@dataclass
class SDKMarket:
    """A market opportunity returned by the SDK."""
    market_id: str
    question: str
    volume_24h: float
    days_to_resolution: float
    yes_price: float
    no_price: float


@dataclass
class PaperStatus:
    """Paper trading status."""
    running: bool
    trades: int
    pnl: float
    win_rate: float
    capital: float
    brier_score: float


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
        self.base_url = base_url or os.getenv(
            "CASHCLAW_API_URL", "https://api.cashclaw.io"
        )
        self._signals_today = 0
        self._http: Optional[Any] = None

        if HAS_HTTPX:
            self._http = httpx.Client(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )

    @classmethod
    def init(
        cls,
        api_key: str = "",
        tier: str = "starter",
        base_url: str = "",
    ) -> CashClaw:
        """Initialize the CashClaw SDK.

        Args:
            api_key: API key from CashClaw dashboard
            tier: Subscription tier (starter/pro/elite)
            base_url: API base URL (defaults to production)
        """
        key = api_key or os.getenv("CASHCLAW_API_KEY", "")
        if not key:
            raise ValueError(
                "API key required. Set CASHCLAW_API_KEY or pass api_key parameter."
            )
        return cls(api_key=key, tier=tier, base_url=base_url)

    def scan(self) -> list[SDKMarket]:
        """Return market opportunities filtered by DNA strategy.

        Starter: basic filters only
        Pro: includes volume/liquidity scoring
        Elite: includes all filters + custom criteria
        """
        data = self._get("/v1/markets")
        return [
            SDKMarket(
                market_id=m["market_id"],
                question=m["question"],
                volume_24h=m["volume_24h"],
                days_to_resolution=m["days_to_resolution"],
                yes_price=m["yes_price"],
                no_price=m["no_price"],
            )
            for m in data.get("markets", [])
        ]

    def predict(self, market_id: str) -> dict:
        """Get AI probability estimate for a specific market.

        Returns prediction with probability, edge, and reasoning.
        """
        self._check_signal_limit()
        data = self._get(f"/v1/predict/{market_id}")
        self._signals_today += 1
        return data

    def signals(self) -> list[SDKSignal]:
        """Get ranked trading signals.

        Returns signals sorted by expected value.
        Tier-gated: Starter=5/day, Pro=20/day, Elite=unlimited.
        """
        remaining = self.limits.signals_per_day - self._signals_today
        if remaining <= 0:
            logger.warning(
                "Signal limit reached (%d/%d). Upgrade tier for more.",
                self._signals_today, self.limits.signals_per_day,
            )
            return []

        data = self._get("/v1/signals", params={"limit": remaining})
        self._signals_today += len(data.get("signals", []))

        return [
            SDKSignal(
                market_id=s["market_id"],
                question=s["question"],
                direction=s["direction"],
                predicted_probability=s["predicted_probability"],
                market_price=s["market_price"],
                edge=s["edge"],
                confidence=s["confidence"],
                kelly_fraction=s["kelly_fraction"],
                position_size_pct=s["position_size_pct"],
                rank=s["rank"],
            )
            for s in data.get("signals", [])
        ]

    def paper_start(self) -> dict:
        """Start paper trading loop on the server."""
        return self._post("/v1/paper/start")

    def paper_status(self) -> PaperStatus:
        """Get paper trading status."""
        data = self._get("/v1/paper/status")
        return PaperStatus(
            running=data.get("running", False),
            trades=data.get("trades", 0),
            pnl=data.get("pnl", 0.0),
            win_rate=data.get("win_rate", 0.0),
            capital=data.get("capital", 0.0),
            brier_score=data.get("brier_score", 0.0),
        )

    def paper_stop(self) -> dict:
        """Stop paper trading loop."""
        return self._post("/v1/paper/stop")

    @property
    def remaining_signals(self) -> int:
        """Number of signals remaining today."""
        return max(0, self.limits.signals_per_day - self._signals_today)

    def _check_signal_limit(self) -> None:
        """Check if signal limit exceeded."""
        if self._signals_today >= self.limits.signals_per_day:
            raise PermissionError(
                f"Daily signal limit reached ({self.limits.signals_per_day}). "
                f"Upgrade to {'Pro' if self.tier == Tier.STARTER else 'Elite'} "
                f"for more signals."
            )

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """Make authenticated GET request."""
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
        """Make authenticated POST request."""
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
        """Close HTTP client."""
        if self._http and hasattr(self._http, "close"):
            self._http.close()

    def __enter__(self) -> CashClaw:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
