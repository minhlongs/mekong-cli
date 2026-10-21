# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Diagnostic Commands — Phase 6 CLI Integration with RaaS Gateway

Connectivity diagnostics for RaaS Gateway and AgencyOS services.
"""

from __future__ import annotations

from src.cli.diagnostic_commands.auth_rate import check_auth, check_rate_limit
from src.cli.diagnostic_commands.gateway import app, check_gateway, console
from src.cli.diagnostic_commands.suite import (
    check_auth_impl,
    check_gateway_impl,
    check_rate_limit_impl,
    run_all_diagnostics,
)

__all__ = [
    "app",
    "check_auth",
    "check_auth_impl",
    "check_gateway",
    "check_gateway_impl",
    "check_rate_limit",
    "check_rate_limit_impl",
    "console",
    "run_all_diagnostics",
]
