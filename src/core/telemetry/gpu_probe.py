"""
core/telemetry/gpu_probe.py — M1 Max GPU utilisation sampler.

Strategy (sudo-less):
  A LaunchAgent (or cron) runs `sudo powermetrics --samplers gpu_power -i 10000 -n 1`
  and writes JSON to /tmp/mekong_gpu_metrics.json every 10s.
  GpuProbe reads that file and registers an OTel observable gauge callback.

Fallback: if the JSON file is absent or stale (> 30s old), reports -1 (unknown).

To set up the LaunchAgent on M1 Max, see observability/README.md.

Usage:
  from src.core.telemetry.gpu_probe import GpuProbe
  probe = GpuProbe()
  probe.start()          # registers OTel callback, launches background reader
  # ... run agents ...
  probe.stop()
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Iterable

from opentelemetry.metrics import CallbackOptions, Observation


logger = logging.getLogger(__name__)

# Path written by the LaunchAgent powermetrics wrapper
_GPU_METRICS_FILE = Path(os.getenv("MEKONG_GPU_METRICS_FILE", "/tmp/mekong_gpu_metrics.json"))
_STALE_THRESHOLD_S = 30  # seconds before reading is considered stale


def _read_gpu_util() -> float:
    """
    Read GPU active residency % from the JSON file.
    Returns -1.0 if file absent, unparseable, or stale.
    """
    if not _GPU_METRICS_FILE.exists():
        return -1.0

    try:
        stat = _GPU_METRICS_FILE.stat()
        age = time.time() - stat.st_mtime
        if age > _STALE_THRESHOLD_S:
            logger.debug("GPU metrics file stale (%.0fs old)", age)
            return -1.0

        data = json.loads(_GPU_METRICS_FILE.read_text())
        # powermetrics JSON structure: gpu.active_ratio (0.0–1.0)
        gpu_active_ratio = data.get("gpu", {}).get("active_ratio", -1.0)
        if gpu_active_ratio < 0:
            return -1.0
        return round(gpu_active_ratio * 100, 1)
    except Exception as exc:
        logger.debug("GPU metrics read error: %s", exc)
        return -1.0


class GpuProbe:
    """
    Registers an OTel ObservableGauge callback that reports M1 Max GPU util.

    The callback is invoked by the OTel SDK on each metrics collection cycle
    (every 15s per PeriodicExportingMetricReader interval).
    """

    def __init__(self) -> None:
        self._registered = False

    def _gpu_util_callback(self, options: CallbackOptions) -> Iterable[Observation]:
        util = _read_gpu_util()
        if util >= 0:
            yield Observation(util, {"host": "m1max"})
        # if -1 (unknown), yield nothing — avoids polluting dashboard with -1 spikes

    def start(self) -> None:
        """Register OTel callback. Safe to call multiple times (idempotent)."""
        if self._registered:
            return

        try:
            from opentelemetry import metrics as otel_metrics

            meter = otel_metrics.get_meter("mekong.agents", "1.0.0")
            meter.create_observable_gauge(
                name="mlx.gpu_utilization_percent",
                unit="%",
                description="M1 Max GPU utilisation sampled via powermetrics JSON file",
                callbacks=[self._gpu_util_callback],
            )
            self._registered = True
            logger.info("GpuProbe registered — reading from %s", _GPU_METRICS_FILE)
        except Exception as exc:
            logger.warning("GpuProbe registration failed (non-fatal): %s", exc)

    def stop(self) -> None:
        """No-op — OTel SDK handles cleanup on provider shutdown."""
        pass


# Convenience singleton
_DEFAULT_PROBE: GpuProbe | None = None


def get_default_probe() -> GpuProbe:
    global _DEFAULT_PROBE
    if _DEFAULT_PROBE is None:
        _DEFAULT_PROBE = GpuProbe()
    return _DEFAULT_PROBE
