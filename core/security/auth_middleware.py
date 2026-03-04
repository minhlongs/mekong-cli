"""
🔐 API Authentication Middleware (Proxy)
=================================
This file is now a proxy for the modularized version in ./middleware/
Please import from core.security.middleware instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.security.auth_middleware is deprecated. "
    "Use core.security.middleware instead.",
    DeprecationWarning,
    stacklevel=2
)
