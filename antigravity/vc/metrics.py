"""
📊 VCMetrics - VC-ready Metrics Dashboard (Proxy)
=========================================
This file is now a proxy for the modularized version in ./metrics_logic/
Please import from antigravity.vc.metrics_logic instead.
"""
import warnings

from .metrics_logic import FundingStage, MetricsSnapshot, VCMetrics, calculate_readiness

__all__ = ["FundingStage", "MetricsSnapshot", "VCMetrics", "calculate_readiness"]

# Issue a deprecation warning
warnings.warn(
    "antigravity.vc.metrics is deprecated. "
    "Use antigravity.vc.metrics_logic package instead.",
    DeprecationWarning,
    stacklevel=2
)
