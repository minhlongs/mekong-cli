"""
LLM Router — Routes tasks to the correct model with circuit breaker.

Features:
- Capability-based routing (fast tasks → Nemotron, deep tasks → DeepSeek R1)
- Health check via GET /v1/models
- Circuit breaker: open after N failures, auto-recover after cooldown
- Fallback to fast model when primary is unhealthy
"""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

from .llm_config import (
    ModelConfig,
    FALLBACK_MODEL,
    get_model_for_capability,
)
from .task_router import Task

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------

@dataclass
class CircuitBreaker:
    """
    Simple circuit breaker for a single LLM endpoint.

    States: CLOSED (normal) → OPEN (failing) → HALF-OPEN (testing recovery)
    """

    failure_threshold: int = 3          # failures before opening
    recovery_timeout: float = 60.0      # seconds before trying again
    _failures: int = field(default=0, init=False, repr=False)
    _opened_at: float = field(default=0.0, init=False, repr=False)
    _state: str = field(default="CLOSED", init=False, repr=False)

    @property
    def is_open(self) -> bool:
        """Return True if circuit is open (endpoint considered unhealthy)."""
        if self._state != "OPEN":
            return False
        # Auto-recover after cooldown
        if time.time() - self._opened_at >= self.recovery_timeout:
            logger.info("[CircuitBreaker] Entering HALF-OPEN state")
            self._state = "HALF-OPEN"
            return False
        return True

    def record_success(self) -> None:
        """Record a successful call — reset failure counter."""
        self._failures = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        """Record a failed call — open circuit after threshold."""
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = "OPEN"
            self._opened_at = time.time()
            logger.warning(
                f"[CircuitBreaker] Circuit OPENED after {self._failures} failures"
            )


# ---------------------------------------------------------------------------
# LLM Router
# ---------------------------------------------------------------------------

class LLMRouter:
    """
    Routes a Task to the appropriate ModelConfig based on capability.

    Usage:
        router = LLMRouter()
        config = router.route(task)
        # config is ready to use for HTTP POST to config.chat_url
    """

    def __init__(
        self,
        health_check_timeout: int = 5,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ) -> None:
        self._health_check_timeout = health_check_timeout
        self._breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        # Cache last health check result to avoid hammering the server
        self._last_health_check: float = 0.0
        self._health_cache_ttl: float = 30.0
        self._local_healthy: Optional[bool] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, task: Task) -> ModelConfig:
        """Select ModelConfig for task: capability map (local) or Bailian fallback."""
        if self._breaker.is_open:
            logger.warning(
                f"[LLMRouter] Circuit open, routing task {task.task_id} to fallback"
            )
            return FALLBACK_MODEL

        local_config = get_model_for_capability(task.capability)

        # Re-validate health every TTL seconds
        if self._should_recheck_health():
            self._local_healthy = self._check_health(local_config)

        if not self._local_healthy:
            logger.warning(
                f"[LLMRouter] Local MLX unhealthy, routing {task.task_id} to Bailian fallback"
            )
            return FALLBACK_MODEL

        logger.debug(
            f"[LLMRouter] Routing {task.task_id} (cap={task.capability}) → {local_config.name}"
        )
        return local_config

    def record_success(self, model_config: ModelConfig) -> None:
        """Notify router of a successful LLM call."""
        if model_config is not FALLBACK_MODEL:
            self._breaker.record_success()
            self._local_healthy = True

    def record_failure(self, model_config: ModelConfig) -> None:
        """Notify router of a failed LLM call."""
        if model_config is not FALLBACK_MODEL:
            self._breaker.record_failure()
            self._local_healthy = False

    def get_status(self) -> dict:
        """Return current router status for diagnostics."""
        return {
            "circuit_state": self._breaker._state,
            "local_healthy": self._local_healthy,
            "failures": self._breaker._failures,
            "last_health_check": self._last_health_check,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_recheck_health(self) -> bool:
        """True if health cache has expired."""
        return (time.time() - self._last_health_check) >= self._health_cache_ttl

    def _check_health(self, config: ModelConfig) -> bool:
        """
        Perform GET /v1/models health check.

        Returns True if endpoint responds with HTTP 200, False otherwise.
        """
        self._last_health_check = time.time()
        try:
            req = urllib.request.Request(
                config.models_url,
                method="GET",
                headers={"Authorization": f"Bearer {config.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=self._health_check_timeout) as resp:
                healthy = resp.status == 200
                logger.debug(f"[LLMRouter] Health check {config.base_url}: {resp.status}")
                return healthy
        except urllib.error.URLError as exc:
            logger.warning(f"[LLMRouter] Health check failed for {config.base_url}: {exc}")
            return False
        except Exception as exc:
            logger.warning(f"[LLMRouter] Health check error: {exc}")
            return False


__all__ = ["LLMRouter", "CircuitBreaker"]
