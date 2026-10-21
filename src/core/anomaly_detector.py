# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Usage Anomaly Detection."""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    SPIKE, DROP, PATTERN_BREAK = "spike", "drop", "pattern_break"


class AnomalyCategory(str, Enum):
    API_CALLS, AGENT_SPAWNS, MODEL_USAGE, LLM_CALLS, TOKEN_USAGE = "api_calls", "agent_spawns", "model_usage", "llm_calls", "token_usage"


@dataclass
class BaselineStats:
    metric: str; mean: float = 0.0; std_dev: float = 0.0; sample_count: int = 0; window_days: int = 7  # noqa: E702
    last_updated: float = field(default_factory=time.time); samples: list[float] = field(default_factory=list)  # noqa: E702

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric, "mean": self.mean, "std_dev": self.std_dev, "sample_count": self.sample_count,
            "window_days": self.window_days, "last_updated": self.last_updated, "samples": self.samples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaselineStats:
        return cls(
            metric=data.get("metric", ""), mean=data.get("mean", 0.0), std_dev=data.get("std_dev", 0.0),
            sample_count=data.get("sample_count", 0), window_days=data.get("window_days", 7),
            last_updated=data.get("last_updated", time.time()), samples=data.get("samples", []),
        )


@dataclass
class Anomaly:
    anomaly_type: AnomalyType; category: AnomalyCategory; metric: str; current_value: float  # noqa: E702
    baseline_mean: float; baseline_std_dev: float; z_score: float; severity: str  # noqa: E702
    timestamp: float = field(default_factory=time.time); details: dict[str, Any] = field(default_factory=dict)  # noqa: E702

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value, "category": self.category.value, "metric": self.metric,
            "current_value": self.current_value, "baseline_mean": self.baseline_mean, "baseline_std_dev": self.baseline_std_dev,
            "z_score": round(self.z_score, 2), "severity": self.severity, "timestamp": self.timestamp, "details": self.details,
        }

    def to_event_data(self) -> dict[str, Any]:
        return {
            "type": self.anomaly_type.value, "category": self.category.value, "metric": self.metric,
            "current": self.current_value, "baseline_mean": round(self.baseline_mean, 2),
            "baseline_std": round(self.baseline_std_dev, 2), "z_score": round(self.z_score, 2),
            "severity": self.severity, "message": self._generate_message(),
        }

    def _generate_message(self) -> str:
        desc = {AnomalyType.SPIKE: "Sudden increase detected", AnomalyType.DROP: "Sudden drop detected", AnomalyType.PATTERN_BREAK: "Pattern change detected"}.get(self.anomaly_type, "Anomaly")
        return f"{desc}: {self.metric} = {self.current_value:.2f} (baseline: {self.baseline_mean:.2f} ± {self.baseline_std_dev:.2f}, z-score: {self.z_score:.2f})"


class UsageAnomalyDetector:
    """Statistical anomaly detection for usage metrics using rolling 7-day Z-score."""

    Z_SCORE_THRESHOLD = 3.0
    MIN_SAMPLES = 3
    BASELINE_FILE = ".mekong/usage_baseline.json"
    MAX_SAMPLES = 168

    def __init__(self, baseline_file: str | None = None) -> None:
        self._baselines: dict[str, BaselineStats] = {}
        self._baseline_file = Path(baseline_file or self.BASELINE_FILE)
        self._load_baselines()

    def _load_baselines(self) -> None:
        if not self._baseline_file.exists():
            return
        try:
            for metric, bd in json.loads(self._baseline_file.read_text()).get("baselines", {}).items():
                self._baselines[metric] = BaselineStats.from_dict(bd)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to load baselines: %s", e)

    def _save_baselines(self) -> None:
        self._baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self._baseline_file.write_text(json.dumps({"version": 1, "last_updated": time.time(), "baselines": {m: b.to_dict() for m, b in self._baselines.items()}}, indent=2))

    def record_metric(self, category: AnomalyCategory | str, metric: str, value: float) -> None:
        cat_str = category.value if isinstance(category, AnomalyCategory) else str(category)
        key, ts = f"{cat_str}:{metric}", time.time()
        b = self._baselines.setdefault(key, BaselineStats(metric=key, window_days=7, last_updated=ts))
        b.samples = (b.samples + [value])[-self.MAX_SAMPLES:]
        b.sample_count, b.last_updated = len(b.samples), ts
        self._recalculate_stats(b)
        if b.sample_count % 10 == 0:
            self._save_baselines()

    def _recalculate_stats(self, baseline: BaselineStats) -> None:
        s = baseline.samples
        if not s:
            baseline.mean = baseline.std_dev = 0.0
            return
        baseline.mean = sum(s) / len(s)
        baseline.std_dev = math.sqrt(sum((x - baseline.mean) ** 2 for x in s) / (len(s) - 1)) if len(s) >= 2 else 0.0

    def detect_anomaly(self, category: AnomalyCategory | str, metric: str, current_value: float) -> Anomaly | None:
        cat_str = category.value if isinstance(category, AnomalyCategory) else str(category)
        key = f"{cat_str}:{metric}"
        b = self._baselines.get(key)
        if b is None or b.sample_count < self.MIN_SAMPLES:
            return None
        z_score = self._calculate_z_score(current_value, b.mean, b.std_dev)
        if abs(z_score) < self.Z_SCORE_THRESHOLD:
            return None
        norm_cat = category if isinstance(category, AnomalyCategory) else AnomalyCategory(cat_str)
        return Anomaly(
            anomaly_type=self._determine_anomaly_type(z_score), category=norm_cat, metric=key,
            current_value=current_value, baseline_mean=b.mean, baseline_std_dev=b.std_dev,
            z_score=z_score, severity=self._calculate_severity(abs(z_score)),
            details={"sample_count": b.sample_count, "window_days": b.window_days},
        )

    def _calculate_z_score(self, value: float, mean: float, std_dev: float) -> float:
        return (value - mean) / std_dev if std_dev != 0 else 0.0

    def _determine_anomaly_type(self, z_score: float) -> AnomalyType:
        return AnomalyType.SPIKE if z_score > 0 else AnomalyType.DROP if z_score < 0 else AnomalyType.PATTERN_BREAK

    def _calculate_severity(self, abs_z_score: float) -> str:
        return "critical" if abs_z_score >= 5.0 else "high" if abs_z_score >= 4.0 else "medium" if abs_z_score >= 3.5 else "low"

    def get_baseline(self, category: str, metric: str) -> BaselineStats | None:
        return self._baselines.get(f"{category if isinstance(category, str) else category.value}:{metric}")

    def get_all_baselines(self) -> dict[str, BaselineStats]:
        return self._baselines.copy()

    def reset_baseline(self, category: str, metric: str) -> None:
        if self._baselines.pop(f"{category if isinstance(category, str) else category.value}:{metric}", None) is not None:
            self._save_baselines()

    def reset_all_baselines(self) -> None:
        self._baselines.clear()
        if self._baseline_file.exists():
            self._baseline_file.unlink()


_detector: UsageAnomalyDetector | None = None


def get_detector(baseline_file: str | None = None) -> UsageAnomalyDetector:
    global _detector
    if _detector is None:
        _detector = UsageAnomalyDetector(baseline_file)
    return _detector


def reset_detector() -> None:
    global _detector
    _detector = None


__all__ = ["Anomaly", "AnomalyCategory", "AnomalyType", "BaselineStats", "UsageAnomalyDetector", "get_detector", "reset_detector"]
