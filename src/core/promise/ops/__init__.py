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
Wave 4 (delivered): Department & C-Suite Operations (build, code, support,
collab, memory, recall, benchmark, eval-agent, company, cfo, cmo, cso) and
Vietnamese Digital, E-Commerce & IP Legal Operations (privacy, ecom, ip).
Wave 5 (delivered): C-Suite & Business Operations (idea, goal, governance,
binh-phap, csuite, zenpay, revenue, usage, consulting, content, copywriting,
vendor) and Vietnamese Commercial, Financial & Cyber Statutory Operations
(etransaction, cyber, fdi, customs, banking, aml).
"""

from __future__ import annotations

from src.core.promise import checks_finance as _checks_finance  # noqa: F401  (registers finance checks)
from src.core.promise.contracts import REGISTRY
from src.core.promise.ops.csuite_bizops_vn import CSUITE_BIZOPS_OPERATIONS
from src.core.promise.ops.csuite_bizops_wave5_vn import CSUITE_BIZOPS_WAVE5_VN_OPERATIONS
from src.core.promise.ops.departments_wave4_vn import DEPARTMENTS_WAVE4_OPERATIONS
from src.core.promise.ops.finance_vn import FINANCE_OPERATIONS
from src.core.promise.ops.legal_commercial_cyber_vn import LEGAL_COMMERCIAL_CYBER_VN_OPERATIONS
from src.core.promise.ops.legal_digital_vn import LEGAL_DIGITAL_VN_OPERATIONS
from src.core.promise.ops.legal_vn import LEGAL_VN_OPERATIONS
from src.core.promise.ops.opc_zalo_vn import OPC_ZALO_OPERATIONS

REGISTRY.register_all(FINANCE_OPERATIONS)
REGISTRY.register_all(OPC_ZALO_OPERATIONS)
REGISTRY.register_all(CSUITE_BIZOPS_OPERATIONS)
REGISTRY.register_all(LEGAL_VN_OPERATIONS)
REGISTRY.register_all(DEPARTMENTS_WAVE4_OPERATIONS)
REGISTRY.register_all(LEGAL_DIGITAL_VN_OPERATIONS)
REGISTRY.register_all(CSUITE_BIZOPS_WAVE5_VN_OPERATIONS)
REGISTRY.register_all(LEGAL_COMMERCIAL_CYBER_VN_OPERATIONS)

WAVES: tuple[str, ...] = (
    "finance_vn",                   # thue, ke-toan, bhxh, payroll, vietqr, adminsanction, taxadmin
    "opc_zalo_vn",                  # opc, zalo-oa
    "csuite_bizops_vn",             # founder, marketing, sales, cto, ops, billing
    "legal_vn",                     # corporate, labor, contract
    "departments_wave4_vn",         # build, code, support, collab, memory, recall, benchmark, eval-agent, company, cfo, cmo, cso
    "legal_digital_vn",             # privacy, ecom, ip
    "csuite_bizops_wave5_vn",       # idea, goal, governance, binh-phap, csuite, zenpay, revenue, usage, consulting, content, copywriting, vendor
    "legal_commercial_cyber_vn",    # etransaction, cyber, fdi, customs, banking, aml
)

__all__ = [
    "CSUITE_BIZOPS_OPERATIONS",
    "CSUITE_BIZOPS_WAVE5_VN_OPERATIONS",
    "DEPARTMENTS_WAVE4_OPERATIONS",
    "FINANCE_OPERATIONS",
    "LEGAL_COMMERCIAL_CYBER_VN_OPERATIONS",
    "LEGAL_DIGITAL_VN_OPERATIONS",
    "LEGAL_VN_OPERATIONS",
    "OPC_ZALO_OPERATIONS",
    "REGISTRY",
    "WAVES",
]
