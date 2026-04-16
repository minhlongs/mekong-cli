"""
core/telemetry/meters.py — 5 MVP metric instruments for Mekong CLI.

Instruments (lazy-initialised on first access):
  METERS.invocation_ms   — Histogram: agent invocation latency (ms)
  METERS.token_cost_usd  — Counter:   cumulative USD token cost per agent
  METERS.gpu_util        — Gauge:     M1 Max GPU utilisation (0-100 %)
  METERS.model_drift     — Gauge:     semantic drift score vs baseline (0-1)
  METERS.retry_total     — Counter:   retry attempts after failure

Usage:
  from src.core.telemetry.meters import METERS
  METERS.invocation_ms.record(elapsed_ms, {"agent_name": "planner"})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from opentelemetry import metrics

_METER_NAME = "mekong.agents"
_METER_VERSION = "1.0.0"


def _get_meter() -> metrics.Meter:
    return metrics.get_meter(_METER_NAME, _METER_VERSION)


@dataclass
class _Meters:
    """Lazy container — instruments created on first access after OTel setup."""

    _invocation_ms: Optional[metrics.Histogram] = field(default=None, repr=False)
    _token_cost_usd: Optional[metrics.Counter] = field(default=None, repr=False)
    _gpu_util: Optional[metrics.ObservableGauge] = field(default=None, repr=False)
    _model_drift: Optional[metrics.ObservableGauge] = field(default=None, repr=False)
    _retry_total: Optional[metrics.Counter] = field(default=None, repr=False)

    # --- invocation latency ---
    @property
    def invocation_ms(self) -> metrics.Histogram:
        if self._invocation_ms is None:
            self._invocation_ms = _get_meter().create_histogram(
                name="agent.invocation_ms",
                unit="ms",
                description="Wall-clock time per agent invocation (entry → result)",
            )
        return self._invocation_ms

    # --- token cost ---
    @property
    def token_cost_usd(self) -> metrics.Counter:
        if self._token_cost_usd is None:
            self._token_cost_usd = _get_meter().create_counter(
                name="agent.token_cost_usd",
                unit="USD",
                description="Cumulative token cost per agent call (OpenRouter pricing)",
            )
        return self._token_cost_usd

    # --- GPU utilisation (observable — updated by GpuProbe background thread) ---
    @property
    def gpu_util(self) -> metrics.ObservableGauge:
        if self._gpu_util is None:
            self._gpu_util = _get_meter().create_observable_gauge(
                name="mlx.gpu_utilization_percent",
                unit="%",
                description="M1 Max GPU utilisation sampled via powermetrics",
                callbacks=[],  # callbacks registered by GpuProbe
            )
        return self._gpu_util

    # --- model drift (observable) ---
    @property
    def model_drift(self) -> metrics.ObservableGauge:
        if self._model_drift is None:
            self._model_drift = _get_meter().create_observable_gauge(
                name="agent.model_drift_score",
                unit="1",
                description="Semantic similarity drift vs baseline (0=identical, 1=max drift)",
                callbacks=[],
            )
        return self._model_drift

    # --- retry count ---
    @property
    def retry_total(self) -> metrics.Counter:
        if self._retry_total is None:
            self._retry_total = _get_meter().create_counter(
                name="agent.retry_total",
                unit="1",
                description="Total retry attempts after transient agent failure",
            )
        return self._retry_total


# Singleton — import and use directly
METERS = _Meters()
