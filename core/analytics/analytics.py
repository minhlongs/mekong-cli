"""
📊 Refactored Analytics Dashboard - Main Interface (Proxy)
==================================================

This file is now a proxy for the modularized version in ./dashboard/
Please import from core.analytics.dashboard instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.analytics.analytics is deprecated. "
    "Use core.analytics.dashboard instead.",
    DeprecationWarning,
    stacklevel=2
)
