"""Mekong CLI - Health Monitor.

Periodic health checks for LLM providers with automatic isolation.
Supports parallel checks, configurable intervals, and provider state management.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    CHECKING = "checking"
    ISOLATED = "isolated"


@dataclass
class HealthCheckConfig:
    """Configuration for a single health check."""
    enabled: bool = True
    interval_sec: int = 60
    timeout_sec: int = 10
    endpoint: str = "/models"
    expected_status: int = 200
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ProviderHealthConfig:
    """Health check configuration per provider."""
    name: str
    base_url: str
    api_key: Optional[str] = None
    api_key_header: str = "Authorization"
    check_config: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    unhealthy_threshold: int = 3  # consecutive failures before unhealthy


@dataclass
class HealthResult:
    """Result of a health check."""
    provider_name: str
    status: HealthStatus
    latency_ms: float
    timestamp: float
    error: Optional[str] = None
    response_data: Optional[dict[str, Any]] = None


@dataclass
class ProviderState:
    """Current state of a provider."""
    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check: float = 0.0
    last_success: float = 0.0
    last_failure: float = 0.0
    total_checks: int = 0
    total_failures: int = 0
    avg_latency_ms: float = 0.0
    is_isolated: bool = False

    def record_success(self, latency_ms: float) -> None:
        """Record successful check."""
        self.consecutive_failures = 0
        self.consecutive_successes += 1
        self.last_check = time.time()
        self.last_success = time.time()
        self.total_checks += 1
        # Exponential moving average for latency
        if self.avg_latency_ms == 0:
            self.avg_latency_ms = latency_ms
        else:
            self.avg_latency_ms = 0.9 * self.avg_latency_ms + 0.1 * latency_ms

    def record_failure(self, error: str) -> None:
        """Record failed check."""
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_check = time.time()
        self.last_failure = time.time()
        self.total_checks += 1
        self.total_failures += 1


class HealthMonitor:
    """Monitors provider health with periodic checks."""

    def __init__(
        self,
        provider_configs: list[ProviderHealthConfig],
        check_interval_sec: int = 60,
        parallel_checks: bool = True,
        isolate_unhealthy: bool = True,
        min_healthy_providers: int = 1,
        on_status_change: Optional[Callable[[str, HealthStatus, HealthStatus], None]] = None,
    ):
        self.provider_configs = {cfg.name: cfg for cfg in provider_configs}
        self.check_interval_sec = check_interval_sec
        self.parallel_checks = parallel_checks
        self.isolate_unhealthy = isolate_unhealthy
        self.min_healthy_providers = min_healthy_providers
        self.on_status_change = on_status_change

        self._states: dict[str, ProviderState] = {
            name: ProviderState(name=name) for name in self.provider_configs
        }
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self) -> None:
        """Start the health monitor."""
        if self._running:
            return
        self._running = True
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        # Initial check
        await self.check_all()
        # Start periodic task
        self._task = asyncio.create_task(self._run_periodic())
        logger.info("Health monitor started for %d providers", len(self.provider_configs))

    async def stop(self) -> None:
        """Stop the health monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()
        logger.info("Health monitor stopped")

    async def check_all(self) -> list[HealthResult]:
        """Check all providers."""
        if self.parallel_checks:
            tasks = [self._check_provider(name) for name in self.provider_configs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [
                r for r in results
                if isinstance(r, HealthResult)
            ]
        else:
            results = []
            for name in self.provider_configs:
                result = await self._check_provider(name)
                results.append(result)
            return results

    async def _check_provider(self, name: str) -> HealthResult:
        """Check a single provider."""
        config = self.provider_configs[name]
        state = self._states[name]

        if not config.check_config.enabled:
            return HealthResult(
                provider_name=name,
                status=HealthStatus.UNKNOWN,
                latency_ms=0,
                timestamp=time.time(),
                error="Health checks disabled",
            )

        state.status = HealthStatus.CHECKING
        start = time.time()

        try:
            url = urljoin(config.base_url.rstrip("/") + "/", config.check_config.endpoint.lstrip("/"))
            headers = config.check_config.headers.copy()
            if config.api_key:
                headers[config.api_key_header] = f"Bearer {config.api_key}"

            response = await self._client.get(
                url,
                headers=headers,
                timeout=config.check_config.timeout_sec,
            )
            latency_ms = (time.time() - start) * 1000

            if response.status_code == config.check_config.expected_status:
                state.record_success(latency_ms)
                new_status = HealthStatus.HEALTHY
                error = None
                response_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            else:
                state.record_failure(f"HTTP {response.status_code}")
                new_status = self._determine_status(state, config)
                error = f"HTTP {response.status_code}"
                response_data = None

        except httpx.TimeoutException:
            latency_ms = (time.time() - start) * 1000
            state.record_failure("Timeout")
            new_status = self._determine_status(state, config)
            error = "Timeout"
            response_data = None
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            state.record_failure(str(e))
            new_status = self._determine_status(state, config)
            error = str(e)
            response_data = None

        old_status = state.status
        state.status = new_status

        if old_status != new_status and self.on_status_change:
            self.on_status_change(name, old_status, new_status)

        # Auto-isolate if unhealthy
        if self.isolate_unhealthy and new_status == HealthStatus.UNHEALTHY:
            healthy_count = sum(1 for s in self._states.values() if s.status == HealthStatus.HEALTHY)
            if healthy_count > self.min_healthy_providers:
                state.is_isolated = True
                new_status = HealthStatus.ISOLATED
                logger.warning("Provider %s isolated due to health failures", name)

        return HealthResult(
            provider_name=name,
            status=new_status,
            latency_ms=latency_ms,
            timestamp=time.time(),
            error=error,
            response_data=response_data,
        )

    def _determine_status(self, state: ProviderState, config: ProviderHealthConfig) -> HealthStatus:
        """Determine status based on failure count."""
        if state.consecutive_failures >= config.unhealthy_threshold:
            return HealthStatus.UNHEALTHY
        return HealthStatus.HEALTHY if state.consecutive_successes > 0 else HealthStatus.UNKNOWN

    async def _run_periodic(self) -> None:
        """Run periodic health checks."""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval_sec)
                if self._running:
                    await self.check_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Health check error: %s", e)

    def get_state(self, name: str) -> Optional[ProviderState]:
        """Get provider state."""
        return self._states.get(name)

    def get_all_states(self) -> dict[str, ProviderState]:
        """Get all provider states."""
        return dict(self._states)

    def get_healthy_providers(self) -> list[str]:
        """Get list of healthy provider names."""
        return [
            name for name, state in self._states.items()
            if state.status == HealthStatus.HEALTHY and not state.is_isolated
        ]

    def get_provider_status(self, name: str) -> HealthStatus:
        """Get provider status."""
        state = self._states.get(name)
        return state.status if state else HealthStatus.UNKNOWN

    def is_healthy(self, name: str) -> bool:
        """Check if provider is healthy."""
        state = self._states.get(name)
        return state is not None and state.status == HealthStatus.HEALTHY and not state.is_isolated

    def reset_provider(self, name: str) -> bool:
        """Manually reset provider state (e.g., after manual intervention)."""
        state = self._states.get(name)
        if state:
            state.consecutive_failures = 0
            state.consecutive_successes = 0
            state.is_isolated = False
            state.status = HealthStatus.UNKNOWN
            logger.info("Provider %s manually reset", name)
            return True
        return False


def create_health_monitor_from_config(
    providers_config: list[dict[str, Any]],
    health_config: dict[str, Any],
) -> HealthMonitor:
    """Create HealthMonitor from parsed YAML config."""
    provider_configs = []
    for p in providers_config:
        if not p.get("enabled", True):
            continue
        check_cfg = p.get("health_check", {})
        provider_configs.append(ProviderHealthConfig(
            name=p["name"],
            base_url=p.get("base_url") or p.get("base_url_env", ""),  # Will be resolved at runtime
            api_key=p.get("api_key") or None,  # Will be resolved at runtime
            check_config=HealthCheckConfig(
                enabled=check_cfg.get("enabled", True),
                interval_sec=check_cfg.get("interval_sec", 60),
                timeout_sec=check_cfg.get("timeout_sec", 10),
                endpoint=check_cfg.get("endpoint", "/models"),
                expected_status=check_cfg.get("expected_status", 200),
            ),
            unhealthy_threshold=health_config.get("unhealthy_threshold", 3),
        ))
    return HealthMonitor(
        provider_configs=provider_configs,
        check_interval_sec=health_config.get("check_interval_sec", 60),
        parallel_checks=health_config.get("parallel_checks", True),
        isolate_unhealthy=health_config.get("isolate_unhealthy", True),
        min_healthy_providers=health_config.get("min_healthy_providers", 1),
    )