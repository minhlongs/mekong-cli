"""
🏯 DataMoat - Proprietary Intelligence System (Proxy)
============================================
This file is now a proxy for the modularized version in ./data_moat/
Please import from antigravity.platform.data_moat instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "antigravity.platform.data_moat is deprecated. "
    "Use antigravity.platform.data_moat package instead.",
    DeprecationWarning,
    stacklevel=2
)
