# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Tracker Event-Bus Metering Mixin."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.core.anomaly_detector import (
    AnomalyCategory,
    AnomalyType,
    UsageAnomalyDetector,
    get_detector as _get_detector,
)
from src.core.event_bus import EventBus, EventType, Subscriber, get_event_bus
from src.usage.usage_models import UsageEvent, UsageEventType

logger = logging.getLogger(__name__)


class _UsageMeteringMixin:
    """Mixin adding event-bus + anomaly detection to UsageTracker."""

    def _ensure_metering(self) -> None:
        """Lazily set up event bus + anomaly detector + counters."""
        if hasattr(self, "_metering_ready"):
            return
        if not hasattr(self, "_event_bus"):
            self._event_bus: EventBus = get_event_bus()
        if not hasattr(self, "_detector"):
            self._detector: UsageAnomalyDetector = _get_detector(
                getattr(self, "_baseline_file", None)
            )
        for attr in ("_api_call_count", "_agent_spawn_count", "_llm_call_count", "_total_input_tokens", "_total_output_tokens"):
            if not hasattr(self, attr):
                setattr(self, attr, 0)
        if not hasattr(self, "_usage_subscribers"):
            self._usage_subscribers: dict[UsageEventType, list[Subscriber]] = {}
        self._metering_ready = True

    def subscribe(self, event_type: UsageEventType, callback: Subscriber) -> None:
        """Register a callback for a usage event type."""
        self._ensure_metering()
        self._usage_subscribers.setdefault(event_type, []).append(callback)

    def _emit_usage_event(self, event: UsageEvent) -> None:
        """Emit to event bus and anomaly detector."""
        self._ensure_metering()
        self._event_bus.emit(EventType(event.event_type.value), event.to_dict())
        for callback in self._usage_subscribers.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.debug("Usage subscriber callback failed: %s", e)
        self._check_usage_anomaly(event.category, event.metric, event.value)

    def _check_usage_anomaly(
        self, category: AnomalyCategory, metric: str, value: float
    ) -> Optional[AnomalyType]:
        """Run anomaly detection and emit if found."""
        self._ensure_metering()
        anomaly = self._detector.detect_anomaly(category, metric, value)
        if anomaly:
            self._event_bus.emit(EventType.USAGE_ANOMALY_DETECTED, anomaly.to_event_data())
            logger.warning("Usage anomaly: %s", anomaly._generate_message())
            return anomaly.anomaly_type
        return None

    def record_api_call(self, endpoint: str, method: str = "POST", status_code: int = 200) -> None:
        """Record an API call event."""
        self._ensure_metering()
        self._api_call_count += 1
        self._emit_usage_event(UsageEvent(
            event_type=UsageEventType.API_CALL, category=AnomalyCategory.API_CALLS,
            metric="requests", value=1.0,
            metadata={"endpoint": endpoint, "method": method, "status_code": status_code},
        ))
        self._check_usage_anomaly(AnomalyCategory.API_CALLS, "requests", float(self._api_call_count))

    def record_agent_spawn(self, agent_name: str, model: str = "", duration: float = 0.0) -> None:
        """Record an agent spawn event."""
        self._ensure_metering()
        self._agent_spawn_count += 1
        self._emit_usage_event(UsageEvent(
            event_type=UsageEventType.AGENT_SPAWN, category=AnomalyCategory.AGENT_SPAWNS,
            metric="spawns", value=1.0,
            metadata={"agent_name": agent_name, "model": model, "duration": duration},
        ))
        self._check_usage_anomaly(AnomalyCategory.AGENT_SPAWNS, "spawns", float(self._agent_spawn_count))

    def record_model_usage(
        self, model: str, input_tokens: int = 0, output_tokens: int = 0, cost: float = 0.0
    ) -> None:
        """Record model usage (total token event)."""
        self._ensure_metering()
        total_tokens = float(input_tokens + output_tokens)
        self._emit_usage_event(UsageEvent(
            event_type=UsageEventType.MODEL_USAGE, category=AnomalyCategory.MODEL_USAGE,
            metric=model, value=total_tokens,
            metadata={"input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost},
        ))
        self._detector.record_metric(AnomalyCategory.MODEL_USAGE, model, total_tokens)
        self._check_usage_anomaly(AnomalyCategory.MODEL_USAGE, model, total_tokens)

    def record_llm_call(
        self, model: str, input_tokens: int = 0, output_tokens: int = 0, duration: float = 0.0
    ) -> None:
        """Record an LLM call event."""
        self._ensure_metering()
        self._llm_call_count += 1
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._emit_usage_event(UsageEvent(
            event_type=UsageEventType.LLM_CALL, category=AnomalyCategory.LLM_CALLS,
            metric="calls", value=1.0,
            metadata={"model": model, "input_tokens": input_tokens, "output_tokens": output_tokens, "duration": duration},
        ))
        self._check_usage_anomaly(AnomalyCategory.LLM_CALLS, "calls", float(self._llm_call_count))

    def record_token_usage(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Record token usage for a model."""
        self._ensure_metering()
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        total = float(input_tokens + output_tokens)
        self._emit_usage_event(UsageEvent(
            event_type=UsageEventType.TOKEN_USAGE, category=AnomalyCategory.TOKEN_USAGE,
            metric=model, value=total,
            metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
        ))
        self._detector.record_metric(AnomalyCategory.TOKEN_USAGE, model, total)
        self._check_usage_anomaly(AnomalyCategory.TOKEN_USAGE, model, total)

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        self._ensure_metering()
        return {
            "api_calls": self._api_call_count,
            "agent_spawns": self._agent_spawn_count,
            "llm_calls": self._llm_call_count,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
        }

    def reset_counters(self) -> None:
        """Reset aggregate counters."""
        self._ensure_metering()
        self._api_call_count = 0
        self._agent_spawn_count = 0
        self._llm_call_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def get_detector(self) -> UsageAnomalyDetector:
        """Get the underlying anomaly detector."""
        self._ensure_metering()
        return self._detector
