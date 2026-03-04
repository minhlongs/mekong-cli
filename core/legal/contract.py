"""
📄 Contract Generator (Proxy)
===========================
This file is now a proxy for the modularized version in ./logic/
Please import from core.legal.logic instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.legal.contract is deprecated. "
    "Use core.legal.logic instead.",
    DeprecationWarning,
    stacklevel=2
)
