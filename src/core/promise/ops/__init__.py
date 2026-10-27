# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable operation contracts.

Importing this package registers every authored :class:`OperationSpec` into
:data:`src.core.promise.contracts.REGISTRY`, which is what
``load_default_registry()`` returns to the service, the API routes and the CLI.

Business groups are added wave by wave. Each wave must ship its handlers, its
postconditions and its tests together — a spec without a passing test is not a
delivered promise.

Wave 1 (delivered): Vietnamese finance, tax, social insurance, payroll,
VietQR payments, administrative sanctions and tax administration.
"""

from __future__ import annotations

from src.core.promise import checks_finance as _checks_finance  # noqa: F401  (registers finance checks)
from src.core.promise.contracts import REGISTRY
from src.core.promise.ops.finance_vn import FINANCE_OPERATIONS

REGISTRY.register_all(FINANCE_OPERATIONS)

WAVES: tuple[str, ...] = (
    "finance_vn",  # wave 1: thue, ke-toan, bhxh, payroll, vietqr, adminsanction, taxadmin
)

__all__ = ["FINANCE_OPERATIONS", "REGISTRY", "WAVES"]
