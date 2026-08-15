"""Mekong CLI - Load Balancer.

Multiple load balancing strategies for distributing requests across healthy providers.
Supports round-robin, weighted, least-connections, and adaptive strategies.
"""

from __future__ import annotations

import logging
import random
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class LoadBalancerType(Enum):
    """Load balancer strategy types."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    ADAPTIVE = "adaptive"


@dataclass
class ProviderMetrics:
    """Runtime metrics for a provider."""
    name: str
    weight: int = 100
    active_requests: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    last_selected: float = 0.0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0

    def record_request_start(self) -> None:
        """Record request start."""
        self.active_requests += 1
        self.total_requests += 1
        self.last_selected = time.time()

    def record_request_end(self, success: bool, latency_ms: float) -> None:
        """Record request completion."""
        self.active_requests = max(0, self.active_requests - 1)
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_latency_ms += latency_ms
        if self.total_requests > 0:
            self.error_rate = self.failed_requests / self.total_requests
            self.avg_latency_ms = self.total_latency_ms / self.total_requests


@dataclass
class LoadBalancerConfig:
    """Configuration for load balancer."""
    type: LoadBalancerType = LoadBalancerType.WEIGHTED
    health_check_interval_sec: int = 30
    unhealthy_threshold: int = 3
    sticky_sessions: bool = False
    warmup_requests: int = 0  # Requests before provider gets full weight


class LoadBalancer(ABC):
    """Abstract load balancer base class."""

    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self._metrics: dict[str, ProviderMetrics] = {}
        self._lock = threading.RLock()
        self._round_robin_index = 0

    @abstractmethod
    def select(self, healthy_providers: list[str], provider_weights: dict[str, int]) -> Optional[str]:
        """Select a provider from healthy list. Returns None if no healthy providers."""
        pass

    def register_provider(self, name: str, weight: int = 100) -> None:
        """Register a provider with the load balancer."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = ProviderMetrics(name=name, weight=weight)
            else:
                self._metrics[name].weight = weight

    def unregister_provider(self, name: str) -> None:
        """Unregister a provider."""
        with self._lock:
            self._metrics.pop(name, None)

    def update_weight(self, name: str, weight: int) -> None:
        """Update provider weight."""
        with self._lock:
            if name in self._metrics:
                self._metrics[name].weight = weight

    def record_request_start(self, name: str) -> None:
        """Record request start for metrics."""
        with self._lock:
            if name in self._metrics:
                self._metrics[name].record_request_start()

    def record_request_end(self, name: str, success: bool, latency_ms: float) -> None:
        """Record request completion for metrics."""
        with self._lock:
            if name in self._metrics:
                self._metrics[name].record_request_end(success, latency_ms)

    def get_metrics(self, name: str) -> Optional[ProviderMetrics]:
        """Get provider metrics."""
        with self._lock:
            return self._metrics.get(name)

    def get_all_metrics(self) -> dict[str, ProviderMetrics]:
        """Get all provider metrics."""
        with self._lock:
            return dict(self._metrics)

    def get_healthiest_provider(self, healthy_providers: list[str]) -> Optional[str]:
        """Get provider with best metrics (lowest error rate, lowest latency)."""
        with self._lock:
            candidates = [
                (name, self._metrics[name])
                for name in healthy_providers
                if name in self._metrics
            ]
            if not candidates:
                return None

            # Score: lower is better (error_rate * 1000 + avg_latency_ms / 100)
            def score(m: ProviderMetrics) -> float:
                return m.error_rate * 1000 + m.avg_latency_ms / 100

            return min(candidates, key=lambda x: score(x[1]))[0]


class RoundRobinLoadBalancer(LoadBalancer):
    """Round-robin load balancer."""

    def select(self, healthy_providers: list[str], provider_weights: dict[str, int]) -> Optional[str]:
        with self._lock:
            if not healthy_providers:
                return None
            # Filter to only registered providers
            registered = [p for p in healthy_providers if p in self._metrics]
            if not registered:
                return None
            provider = registered[self._round_robin_index % len(registered)]
            self._round_robin_index += 1
            return provider


class WeightedLoadBalancer(LoadBalancer):
    """Weighted random load balancer."""

    def select(self, healthy_providers: list[str], provider_weights: dict[str, int]) -> Optional[str]:
        with self._lock:
            if not healthy_providers:
                return None

            # Filter to registered providers with weights
            candidates = []
            total_weight = 0
            for name in healthy_providers:
                if name in self._metrics:
                    weight = self._metrics[name].weight
                    if weight > 0:
                        candidates.append((name, weight))
                        total_weight += weight

            if not candidates:
                return None

            # Weighted random selection
            rand = random.uniform(0, total_weight)
            cumulative = 0
            for name, weight in candidates:
                cumulative += weight
                if rand <= cumulative:
                    return name

            return candidates[-1][0]


class LeastConnectionsLoadBalancer(LoadBalancer):
    """Least connections load balancer."""

    def select(self, healthy_providers: list[str], provider_weights: dict[str, int]) -> Optional[str]:
        with self._lock:
            if not healthy_providers:
                return None

            candidates = [
                (name, self._metrics[name])
                for name in healthy_providers
                if name in self._metrics
            ]
            if not candidates:
                return None

            # Select provider with fewest active connections
            return min(candidates, key=lambda x: x[1].active_requests)[0]


class AdaptiveLoadBalancer(LoadBalancer):
    """Adaptive load balancer - combines multiple strategies based on metrics.

    Uses weighted selection but adjusts weights based on:
    - Error rate (higher errors = lower effective weight)
    - Latency (higher latency = lower effective weight)
    - Active connections (fewer connections = higher priority)
    """

    def __init__(self, config: LoadBalancerConfig):
        super().__init__(config)
        self._base_weights: dict[str, int] = {}

    def register_provider(self, name: str, weight: int = 100) -> None:
        with self._lock:
            super().register_provider(name, weight)
            self._base_weights[name] = weight

    def update_weight(self, name: str, weight: int) -> None:
        with self._lock:
            super().update_weight(name, weight)
            self._base_weights[name] = weight

    def _calculate_effective_weight(self, metrics: ProviderMetrics) -> float:
        """Calculate effective weight based on runtime metrics."""
        base = self._base_weights.get(metrics.name, 100)

        # Penalize high error rate (exponential)
        error_penalty = 1.0
        if metrics.error_rate > 0:
            error_penalty = max(0.1, 1.0 - metrics.error_rate * 2)

        # Penalize high latency (linear)
        latency_penalty = 1.0
        if metrics.avg_latency_ms > 0:
            latency_penalty = max(0.2, 1.0 - metrics.avg_latency_ms / 10000)

        # Boost for fewer active connections
        connection_boost = 1.0
        if metrics.active_requests < 5:
            connection_boost = 1.5 - metrics.active_requests * 0.1

        return base * error_penalty * latency_penalty * connection_boost

    def select(self, healthy_providers: list[str], provider_weights: dict[str, int]) -> Optional[str]:
        with self._lock:
            if not healthy_providers:
                return None

            candidates = []
            total_weight = 0.0
            for name in healthy_providers:
                if name in self._metrics:
                    eff_weight = self._calculate_effective_weight(self._metrics[name])
                    if eff_weight > 0:
                        candidates.append((name, eff_weight))
                        total_weight += eff_weight

            if not candidates:
                # Fallback to least connections
                return self.get_healthiest_provider(healthy_providers)

            # Weighted random with effective weights
            rand = random.uniform(0, total_weight)
            cumulative = 0.0
            for name, weight in candidates:
                cumulative += weight
                if rand <= cumulative:
                    return name

            return candidates[-1][0]


def create_load_balancer(config: LoadBalancerConfig) -> LoadBalancer:
    """Factory function to create load balancer by type."""
    if config.type == LoadBalancerType.ROUND_ROBIN:
        return RoundRobinLoadBalancer(config)
    elif config.type == LoadBalancerType.WEIGHTED:
        return WeightedLoadBalancer(config)
    elif config.type == LoadBalancerType.LEAST_CONNECTIONS:
        return LeastConnectionsLoadBalancer(config)
    elif config.type == LoadBalancerType.ADAPTIVE:
        return AdaptiveLoadBalancer(config)
    else:
        logger.warning("Unknown load balancer type %s, defaulting to weighted", config.type)
        return WeightedLoadBalancer(config)