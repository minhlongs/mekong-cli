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
Wave 2 (delivered): OPC business packs and Zalo Official Account operations.
Wave 3 (delivered): C-Suite & Business Operations (founder, marketing, sales,
cto, ops, billing) and Vietnamese Legal & Statutory Operations (corporate,
labor, contract).
"""

from __future__ import annotations

from src.core.promise import checks_finance as _checks_finance  # noqa: F401  (registers finance checks)
from src.core.promise.contracts import REGISTRY
from src.core.promise.ops.csuite_bizops_vn import CSUITE_BIZOPS_OPERATIONS
from src.core.promise.ops.finance_vn import FINANCE_OPERATIONS
from src.core.promise.ops.legal_vn import LEGAL_VN_OPERATIONS
from src.core.promise.ops.opc_zalo_vn import OPC_ZALO_OPERATIONS

REGISTRY.register_all(FINANCE_OPERATIONS)
REGISTRY.register_all(OPC_ZALO_OPERATIONS)
REGISTRY.register_all(CSUITE_BIZOPS_OPERATIONS)
REGISTRY.register_all(LEGAL_VN_OPERATIONS)

WAVES: tuple[str, ...] = (
    "finance_vn",        # thue, ke-toan, bhxh, payroll, vietqr, adminsanction, taxadmin
    "opc_zalo_vn",       # opc, zalo-oa
    "csuite_bizops_vn",  # founder, marketing, sales, cto, ops, billing
    "legal_vn",          # corporate, labor, contract
)

__all__ = [
    "CSUITE_BIZOPS_OPERATIONS",
    "FINANCE_OPERATIONS",
    "LEGAL_VN_OPERATIONS",
    "OPC_ZALO_OPERATIONS",
    "REGISTRY",
    "WAVES",
]
