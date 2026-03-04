"""
🔑 License Key Generator - Unified Implementation (Proxy)
=================================================

This file is now a proxy for the modularized version in ./logic/
Please import from core.licensing.logic instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.licensing.generator is deprecated. "
    "Use core.licensing.logic instead.",
    DeprecationWarning,
    stacklevel=2
)
