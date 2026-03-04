"""
License validation module for Agency OS (Proxy).
============================================

This file is now a proxy for the modularized version in ./validation/
Please import from core.licensing.validation instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.licensing.validator is deprecated. "
    "Use core.licensing.validation instead.",
    DeprecationWarning,
    stacklevel=2
)
