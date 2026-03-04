"""
👥 Client Portal Repository - Data Access Layer (Proxy)
================================================

This file is now a proxy for the modularized version in ./client_portal/
Please import from antigravity.core.repositories.client_portal instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.repositories.client_portal_repository is deprecated. "
    "Use core.repositories.client_portal instead.",
    DeprecationWarning,
    stacklevel=2
)
