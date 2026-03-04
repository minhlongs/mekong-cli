"""
Enhanced Control Center - Remote Config & Analytics orchestration layer (Proxy)
==============================================================================

This file is now a facade for the modularized control orchestration logic.
Please import from .orchestration.orchestrator instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "antigravity.core.control.enhanced is deprecated. "
    "Use antigravity.core.control.orchestration.orchestrator instead.",
    DeprecationWarning,
    stacklevel=2
)
