"""
🤖 AI Wingman Templates - Response Templates (Proxy)
============================================
This file is now a proxy for the modularized version in ./templates/
Please import from core.services.templates instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.services.template_engine is deprecated. "
    "Use core.services.templates instead.",
    DeprecationWarning,
    stacklevel=2
)
