"""
❤️ Client Health Score - Proactive Client Management (Proxy)
======================================================

This file is now a proxy for the modularized version in ./health/
Please import from core.crm.health instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.crm.client_health is deprecated. "
    "Use core.crm.health instead.",
    DeprecationWarning,
    stacklevel=2
)
