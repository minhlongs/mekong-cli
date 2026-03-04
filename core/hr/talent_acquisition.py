"""
🔍 Talent Acquisition - Recruiting & Hiring (Proxy)
=============================================

This file is now a proxy for the modularized version in ./recruiting/
Please import from antigravity.core.hr.recruiting instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.hr.talent_acquisition is deprecated. "
    "Use core.hr.recruiting instead.",
    DeprecationWarning,
    stacklevel=2
)
