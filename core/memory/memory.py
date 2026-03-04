"""
AgencyOS Memory System (Proxy)
=============================

This file is now a proxy for the modularized version in ./system/
Please import from antigravity.core.memory.system instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.memory.memory is deprecated. "
    "Use core.memory.system instead.",
    DeprecationWarning,
    stacklevel=2
)
