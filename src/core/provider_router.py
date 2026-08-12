"""Mekong CLI - Provider Router.

Centralized routing logic with weighted selection, health checks, circuit breakers,
and failover chains. Integrates load balancing, health monitoring, and circuit breaking.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import yaml

from .circuit_breaker import CircuitBreaker, CircuitOpenError, get_circuit_breaker
from .health_monitor import HealthMonitor, HealthStatus, ProviderHealthConfig, HealthCheckConfig, create_health_monitor_from_config
from .load_balancer import LoadBalancer, LoadBalancerConfig, LoadBalancerType, ProviderMetrics, create_load_balancer
from .providers import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategy types."""
    PRIORITY = "priority"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    ROUND_ROBIN = "round_robin"
    ADAPTIVE = "adaptive"


@dataclass
class ProviderConfig:
    """Full provider configuration from YAML."""
    name: str
    type: str
    enabled: bool = True
    priority: int = 100
    weight: int = 100
    base_url: str = ""
    base_url_env: str = ""
    api_key_env: str = ""
    api_key: str = ""
    default_model: str = ""
    models: list[str] = field(default_factory=list)
    timeout_sec: int = 30
    max_retries: int = 3
    retry_backoff_sec: float = 1.0
    circuit_breaker: dict[str, Any] = field(default_factory=dict)
    health_check: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolve_base_url(self) -> str:
        """Resolve base URL from env var if needed."""
        if self.base_url_env and not self.base_url:
            return os.getenv(self.base_url_env, "")
        return self.base_url

    def resolve_api_key(self) -> str:
        """Resolve API key from env var if needed."""
        if self.api_key_env and not self.api_key:
            return os.getenv(self.api_key_env, "")
        return self.api_key


@dataclass
class RoutingConfig:
    """Routing configuration."""
    strategy: RoutingStrategy = RoutingStrategy.ADAPTIVE
    fallback_chain: list[str] = field(default_factory=list)
    load_balancer: LoadBalancerConfig = field(default_factory=LoadBalancerConfig)
    failover: dict[str, Any] = field(default_factory=dict)
    circuit_breaker: dict[str, Any] = field(default_factory=dict)
    health_monitor: dict[str, Any] = field(default_factory=dict)
    cost_optimizer: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricsConfig:
    """Metrics collection configuration."""
    enabled: bool = True
    collection_interval_sec: int = 10
    retention_hours: int = 24
    export: dict[str, Any] = field(default_factory=dict)
    track: list[str] = field(default_factory=list)


@dataclass
class RouterMetrics:
    """Aggregated router metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    provider_metrics: dict[str, ProviderMetrics] = field(default_factory=dict)
    fallback_count: int = 0
    circuit_breaker_opens: int = 0

    def record_request(self, provider: str, success: bool, latency_ms: float, fallback: bool = False) -> None:
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_latency_ms += latency_ms
        if fallback:
            self.fallback_count += 1

    def record_circuit_open(self) -> None:
        self.circuit_breaker_opens += 1

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


class ProviderRouter:
    """Main provider router with failover, load balancing, and health monitoring."""

    def __init__(
        self,
        provider_configs: list[ProviderConfig],
        routing_config: RoutingConfig,
        metrics_config: MetricsConfig,
        provider_factory: Callable[[ProviderConfig], LLMProvider],
    ):
        self.provider_configs = {p.name: p for p in provider_configs if p.enabled}
        self.routing_config = routing_config
        self.metrics_config = metrics_config
        self.provider_factory = provider_factory

        # Provider instances (lazy initialization)
        self._providers: dict[str, LLMProvider] = {}
        self._provider_lock = threading.RLock()

        # Load balancer
        self.load_balancer = create_load_balancer(routing_config.load_balancer)
        for name, config in self.provider_configs.items():
            self.load_balancer.register_provider(name, config.weight)

        # Circuit breakers
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        for name, config in self.provider_configs.items():
            cb_config = config.circuit_breaker
            self._circuit_breakers[name] = CircuitBreaker(
                service_name=name,
                failure_threshold=cb_config.get("failure_threshold", 3),
                recovery_timeout=cb_config.get("recovery_timeout_sec", 30),
            )

        # Health monitor
        health_provider_configs = []
        for name, config in self.provider_configs.items():
            hc = config.health_check
            health_provider_configs.append(ProviderHealthConfig(
                name=name,
                base_url=config.resolve_base_url(),
                api_key=config.resolve_api_key(),
                check_config=HealthCheckConfig(
                    enabled=hc.get("enabled", True),
                    interval_sec=hc.get("interval_sec", 60),
                    timeout_sec=hc.get("timeout_sec", 10),
                    endpoint=hc.get("endpoint", "/models"),
                    expected_status=hc.get("expected_status", 200),
                ),
                unhealthy_threshold=routing_config.health_monitor.get("unhealthy_threshold", 3),
            ))
        self.health_monitor = HealthMonitor(
            provider_configs=health_provider_configs,
            check_interval_sec=routing_config.health_monitor.get("check_interval_sec", 60),
            parallel_checks=routing_config.health_monitor.get("parallel_checks", True),
            isolate_unhealthy=routing_config.health_monitor.get("isolate_unhealthy", True),
            min_healthy_providers=routing_config.health_monitor.get("min_healthy_providers", 1),
            on_status_change=self._on_health_status_change,
        )

        # Metrics
        self.metrics = RouterMetrics()

        # Fallback chain
        self.fallback_chain = routing_config.fallback_chain or [
            name for name, config in sorted(self.provider_configs.items(), key=lambda x: x[1].priority)
        ]

        # Failover settings
        self.failover_enabled = routing_config.failover.get("enabled", True)
        self.max_retries_per_provider = routing_config.failover.get("max_retries_per_provider", 3)
        self.total_max_retries = routing_config.failover.get("total_max_retries", 5)
        self.retry_on = set(routing_config.failover.get("retry_on", ["timeout", "connection_error", "rate_limit", "server_error"]))
        self.exclude_on = set(routing_config.failover.get("exclude_on", ["authentication_error", "bad_request"]))

        # Cost optimizer
        self.cost_optimizer_enabled = routing_config.cost_optimizer.get("enabled", True)
        self.max_cost_per_request = routing_config.cost_optimizer.get("max_cost_per_request_usd", 0.10)
        self.prefer_cheaper = routing_config.cost_optimizer.get("prefer_cheaper_when", "latency_within_threshold")
        self.latency_threshold_ms = routing_config.cost_optimizer.get("latency_threshold_ms", 5000)

        self._running = False
        self._metrics_task: Optional[threading.Thread] = None

    def _on_health_status_change(self, name: str, old_status: HealthStatus, new_status: HealthStatus) -> None:
        """Callback when provider health status changes."""
        logger.info("Provider %s health changed: %s -> %s", name, old_status.value, new_status.value)
        if new_status == HealthStatus.UNHEALTHY or new_status == HealthStatus.ISOLATED:
            # Could trigger alerts or adjust routing
            pass

    async def start(self) -> None:
        """Start the router (health monitor, metrics collection)."""
        if self._running:
            return
        self._running = True
        await self.health_monitor.start()
        if self.metrics_config.enabled:
            self._metrics_task = threading.Thread(target=self._metrics_loop, daemon=True)
            self._metrics_task.start()
        logger.info("Provider router started with %d providers", len(self.provider_configs))

    async def stop(self) -> None:
        """Stop the router."""
        self._running = False
        await self.health_monitor.stop()
        logger.info("Provider router stopped")

    def _get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get or create provider instance."""
        with self._provider_lock:
            if name not in self._providers:
                config = self.provider_configs.get(name)
                if config:
                    self._providers[name] = self.provider_factory(config)
            return self._providers.get(name)

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable based on failover config."""
        error_str = str(error).lower()
        # Check excluded errors first
        for excluded in self.exclude_on:
            if excluded in error_str:
                return False
        # Check retryable errors
        for retryable in self.retry_on:
            if retryable in error_str:
                return True
        # Default: retry on connection/timeout errors
        return any(kw in error_str for kw in ["timeout", "connection", "connect", "network"])

    def _select_provider(self, preferred: Optional[str] = None) -> Optional[str]:
        """Select next provider based on routing strategy."""
        healthy = self.health_monitor.get_healthy_providers()

        # Filter to providers that have circuit breakers closed
        available = []
        for name in healthy:
            cb = self._circuit_breakers.get(name)
            if cb and cb.is_available():
                available.append(name)

        if not available:
            return None

        # If preferred provider is available and healthy, use it
        if preferred and preferred in available:
            return preferred

        # Apply routing strategy
        strategy = self.routing_config.strategy
        if strategy == RoutingStrategy.PRIORITY:
            # Sort by priority (lower = higher priority)
            return min(available, key=lambda n: self.provider_configs[n].priority)
        elif strategy == RoutingStrategy.WEIGHTED:
            weights = {n: self.provider_configs[n].weight for n in available}
            return self.load_balancer.select(available, weights)
        elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self.load_balancer.select(available, {})
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            return self.load_balancer.select(available, {})
        elif strategy == RoutingStrategy.ADAPTIVE:
            return self.load_balancer.select(available, {})
        else:
            return available[0]

    def _get_fallback_providers(self, failed: str) -> list[str]:
        """Get fallback providers after a failure."""
        try:
            idx = self.fallback_chain.index(failed)
            return self.fallback_chain[idx + 1:]
        except ValueError:
            return self.fallback_chain

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send chat completion with automatic failover."""
        start_time = time.time()
        last_error = ""
        tried_providers: set[str] = set()
        total_retries = 0

        # First attempt with preferred or selected provider
        current_provider = preferred_provider or self._select_provider(preferred_provider)

        while current_provider and total_retries < self.total_max_retries:
            if current_provider in tried_providers:
                # Already tried this provider, move to fallback
                fallbacks = self._get_fallback_providers(current_provider)
                current_provider = next((f for f in fallbacks if f not in tried_providers), None)
                continue

            tried_providers.add(current_provider)
            provider = self._get_provider(current_provider)
            cb = self._circuit_breakers.get(current_provider)

            if not provider:
                last_error = f"Provider {current_provider} not found"
                logger.warning(last_error)
                current_provider = self._select_provider()
                continue

            # Check circuit breaker
            if cb and not cb.is_available():
                logger.warning("Circuit breaker open for %s, skipping", current_provider)
                self.metrics.record_circuit_open()
                current_provider = self._select_provider()
                continue

            # Attempt request
            for attempt in range(self.max_retries_per_provider):
                if total_retries >= self.total_max_retries:
                    break

                try:
                    response = await provider.chat(messages, model=model or self.provider_configs[current_provider].default_model, **kwargs)
                    latency_ms = (time.time() - start_time) * 1000

                    # Record success
                    self.load_balancer.record_request_end(current_provider, True, latency_ms)
                    if cb:
                        cb.record_success()
                    self.metrics.record_request(current_provider, True, latency_ms, fallback=len(tried_providers) > 1)

                    return response

                except CircuitOpenError:
                    # Circuit breaker opened during call
                    self.metrics.record_circuit_open()
                    last_error = f"Circuit open for {current_provider}"
                    break

                except Exception as e:
                    latency_ms = (time.time() - start_time) * 1000
                    last_error = f"{current_provider}: {e}"
                    logger.warning("Provider %s attempt %d failed: %s", current_provider, attempt + 1, e)

                    # Record failure
                    self.load_balancer.record_request_end(current_provider, False, latency_ms)
                    if cb:
                        cb.record_failure()

                    if not self._is_retryable_error(e):
                        # Non-retryable error, don't retry this provider
                        break

                    total_retries += 1
                    if attempt < self.max_retries_per_provider - 1:
                        # Wait before retry
                        backoff = self.provider_configs[current_provider].retry_backoff_sec * (attempt + 1)
                        await asyncio.sleep(backoff)

            # Move to fallback provider
            if self.failover_enabled:
                fallbacks = self._get_fallback_providers(current_provider)
                current_provider = next((f for f in fallbacks if f not in tried_providers), None)
            else:
                break

        # All providers failed
        latency_ms = (time.time() - start_time) * 1000
        self.metrics.record_request("none", False, latency_ms)

        # Return offline response
        return LLMResponse(
            content=f"All providers failed. Last error: {last_error}",
            model="offline",
            provider="offline",
            usage={},
            error=last_error,
        )

    def get_healthy_providers(self) -> list[str]:
        """Get list of currently healthy providers."""
        return self.health_monitor.get_healthy_providers()

    def get_provider_status(self, name: str) -> HealthStatus:
        """Get provider health status."""
        return self.health_monitor.get_provider_status(name)

    def get_metrics(self) -> RouterMetrics:
        """Get router metrics."""
        # Update provider metrics from load balancer
        for name, metrics in self.load_balancer.get_all_metrics().items():
            self.metrics.provider_metrics[name] = metrics
        return self.metrics

    def reset_provider(self, name: str) -> bool:
        """Reset provider state (circuit breaker, health)."""
        cb = self._circuit_breakers.get(name)
        if cb:
            cb.reset()
        return self.health_monitor.reset_provider(name)


def load_provider_configs(config_path: str) -> tuple[list[ProviderConfig], RoutingConfig, MetricsConfig]:
    """Load provider configurations from YAML file."""
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    # Parse providers
    providers = []
    for p in data.get("providers", []):
        providers.append(ProviderConfig(**p))

    # Parse routing config
    routing_data = data.get("routing", {})
    routing_config = RoutingConfig(
        strategy=RoutingStrategy(routing_data.get("strategy", "adaptive")),
        fallback_chain=routing_data.get("fallback_chain", []),
        load_balancer=LoadBalancerConfig(
            type=LoadBalancerType(routing_data.get("load_balancer", {}).get("type", "weighted")),
            health_check_interval_sec=routing_data.get("load_balancer", {}).get("health_check_interval_sec", 30),
            unhealthy_threshold=routing_data.get("load_balancer", {}).get("unhealthy_threshold", 3),
        ),
        failover=routing_data.get("failover", {}),
        circuit_breaker=routing_data.get("circuit_breaker", {}),
        health_monitor=routing_data.get("health_monitor", {}),
        cost_optimizer=routing_data.get("cost_optimizer", {}),
    )

    # Parse metrics config
    metrics_data = data.get("metrics", {})
    metrics_config = MetricsConfig(
        enabled=metrics_data.get("enabled", True),
        collection_interval_sec=metrics_data.get("collection_interval_sec", 10),
        retention_hours=metrics_data.get("retention_hours", 24),
        export=metrics_data.get("export", {}),
        track=metrics_data.get("track", []),
    )

    return providers, routing_config, metrics_config


import asyncio  # noqa: E402

__all__ = [
    "ProviderConfig",
    "RoutingConfig",
    "MetricsConfig",
    "RoutingStrategy",
    "ProviderRouter",
    "RouterMetrics",
    "load_provider_configs",
]