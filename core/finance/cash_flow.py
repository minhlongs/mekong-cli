"""
💵 Cash Flow Tracker - Money Movement (Proxy)
=======================================

This file is now a proxy for the modularized version in ./cashflow_opt/
Please import from core.finance.cashflow_opt instead.
"""
import warnings


# Issue a deprecation warning
warnings.warn(
    "core.finance.cash_flow is deprecated. "
    "Use core.finance.cashflow_opt instead.",
    DeprecationWarning,
    stacklevel=2
)
