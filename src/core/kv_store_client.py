# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""KV Store Client — Persistent Rate Limit State."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from src.core.gateway_client import GatewayClient, get_gateway_client
from src.core.raas_auth import get_auth_client

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    remaining: int
    limit: int
    reset_at: datetime
    synced_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.reset_at

    @property
    def seconds_until_reset(self) -> int:
        return max(0, int((self.reset_at - datetime.now(timezone.utc)).total_seconds()))

    def to_dict(self) -> dict[str, Any]:
        return {"remaining": self.remaining, "limit": self.limit, "reset_at": self.reset_at.isoformat(), "synced_at": self.synced_at.isoformat()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RateLimitState:
        return cls(
            remaining=data["remaining"], limit=data["limit"],
            reset_at=datetime.fromisoformat(data["reset_at"].replace("Z", "+00:00")),
            synced_at=datetime.fromisoformat(data.get("synced_at", datetime.now(timezone.utc).isoformat())),
        )


class KVStoreClient:
    KV_ENDPOINT = "/v1/kv/rate-limits"
    CACHE_TTL_SECONDS = 60

    def __init__(self, gateway_client: Optional[GatewayClient] = None):
        self.gateway = gateway_client or get_gateway_client()
        self.auth = get_auth_client()
        self._cache: Optional[RateLimitState] = None
        self._cache_time: float = 0.0

    def _is_cache_valid(self) -> bool:
        return self._cache is not None and (time.time() - self._cache_time) < self.CACHE_TTL_SECONDS

    def _get_token(self) -> Optional[str]:
        return self.auth._load_credentials().get("token") or os.getenv("RAAS_LICENSE_KEY")

    def get_rate_limit_state(self, force_refresh: bool = False) -> RateLimitState:
        if self._is_cache_valid() and not force_refresh:
            return self._cache  # type: ignore[return-value]
        try:
            token = self._get_token()
            response = self.gateway.get(self.KV_ENDPOINT, params={"license_key": token} if token else {})
            self._cache, self._cache_time = RateLimitState.from_dict(response.data), time.time()
            return self._cache
        except Exception as e:
            logging.debug(f"KV store fetch failed: {e}")
            now = datetime.now(timezone.utc)
            return RateLimitState(remaining=1000, limit=1000, reset_at=now.replace(hour=23, minute=59, second=59))

    def update_rate_limit_state(self, remaining: int) -> bool:
        try:
            payload = {"license_key": self._get_token(), "remaining": remaining, "updated_at": datetime.now(timezone.utc).isoformat()}
            response = self.gateway.put(f"{self.KV_ENDPOINT}/update", json=payload)
            self._cache, self._cache_time = None, 0.0
            return response.status_code == 200
        except Exception as e:
            logging.debug(f"KV update failed: {e}")
            return False

    def sync_state(self) -> tuple[bool, str]:
        try:
            remote = self.get_rate_limit_state(force_refresh=True)
            local = self._cache
            if local:
                if local.remaining != remote.remaining:
                    self._cache = remote
                    return True, f"Synced: local {local.remaining} → remote {remote.remaining}"
                return True, "Already in sync"
            self._cache = remote
            return True, f"Loaded from KV: {remote.remaining} remaining"
        except Exception as e:
            return False, f"Sync failed: {str(e)}"

    def get_health_status(self) -> dict[str, Any]:
        try:
            response = self.gateway.get(f"{self.KV_ENDPOINT}/health")
            return {"healthy": response.status_code == 200, "status": response.data.get("status"), "latency_ms": response.elapsed_ms, "gateway_url": response.gateway_url}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def get_usage_state(self) -> dict[str, Any]:
        try:
            response = self.gateway.get(f"{self.KV_ENDPOINT}/usage")
            return {"cached_count": response.data.get("cached_count", 0), "last_sync": response.data.get("last_sync"), "pending_events": response.data.get("pending_events", 0)}
        except Exception as e:
            logger.debug("KV store usage stats fetch failed: %s", e)
            return {"cached_count": 0, "last_sync": None, "pending_events": 0}

    def clear_rate_limit_state(self) -> bool:
        try:
            response = self.gateway.post(f"{self.KV_ENDPOINT}/clear", json={"license_key": self._get_token()})
            self._cache, self._cache_time = None, 0.0
            return response.status_code == 200
        except Exception as e:
            logger.warning("KV store rate limit clear failed: %s", e)
            return False


_kv_client: Optional[KVStoreClient] = None


def get_kv_client() -> KVStoreClient:
    global _kv_client
    if _kv_client is None:
        _kv_client = KVStoreClient()
    return _kv_client


def show_kv_status() -> None:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console, client = Console(), get_kv_client()
    console.print("[bold cyan]📊 KV Store Status[/bold cyan]\n")
    health = client.get_health_status()
    console.print("[green]✓ KV Store Healthy[/green]\n" if health["healthy"] else f"[red]✗ KV Store Unhealthy: {health.get('error', 'Unknown error')}[/red]\n")

    state = client.get_rate_limit_state()
    table = Table(title="Rate Limit State")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    for k, v in [("Remaining", str(state.remaining)), ("Limit", str(state.limit)), ("Reset In", f"{state.seconds_until_reset}s"), ("Synced At", state.synced_at.strftime("%H:%M:%S"))]:
        table.add_row(k, v)
    console.print(table)

    usage_pct = 1.0 - (state.remaining / state.limit) if state.limit > 0 else 0
    filled = int(usage_pct * 40)
    bar, color = "█" * filled + "░" * (40 - filled), "green" if usage_pct < 0.5 else ("yellow" if usage_pct < 0.8 else "red")
    console.print()
    console.print(Panel(f"[{color}]{bar}[/{color}]\n[dim]{usage_pct * 100:.1f}% of {state.limit} daily limit[/dim]\n[bold]{state.remaining}[/bold] commands remaining", title="Usage", border_style=color))


__all__ = ["RateLimitState", "KVStoreClient", "get_kv_client", "show_kv_status"]
