"""Phase 346: Port Agency Disbursements Account (PDA/FDA) Engine.

Implements FONASBA Standard Port Agency Agreement principles, Circular 39/2023
port tariff reconciliation, advance receipt balancing, and PDA vs FDA variance auditing.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class PortAgencyDisbursementInput:
    call_id: str
    vessel_name: str
    advance_received_usd: float = 35000.0
    tonnage_dues_usd: float = 4500.0
    pilotage_dues_usd: float = 5200.0
    towage_dues_usd: float = 8500.0
    berthage_dues_usd: float = 3800.0
    linesmen_and_mooring_usd: float = 1200.0
    garbage_freshwater_usd: float = 1500.0
    agency_fee_usd: float = 3000.0
    proforma_total_usd: float = 34000.0


@dataclass
class PortAgencyDisbursementResult:
    call_id: str
    vessel_name: str
    actual_port_costs_usd: float
    total_fda_amount_usd: float
    balance_amount_usd: float  # Absolute balance
    settlement_status: str  # "REFUND_TO_PRINCIPAL", "DUE_FROM_PRINCIPAL", "BALANCED"
    variance_from_pda_pct: float
    audit_flag: bool
    advisories: List[str] = field(default_factory=list)


class PortAgencyDisbursementEngine:
    VARIANCE_THRESHOLD_PCT = 5.0

    @classmethod
    def evaluate(cls, inp: PortAgencyDisbursementInput) -> PortAgencyDisbursementResult:
        advisories: List[str] = []

        # 1. Sum actual port statutory and operational disbursements
        port_costs = round(
            inp.tonnage_dues_usd
            + inp.pilotage_dues_usd
            + inp.towage_dues_usd
            + inp.berthage_dues_usd
            + inp.linesmen_and_mooring_usd
            + inp.garbage_freshwater_usd,
            2,
        )

        # 2. Total FDA amount = port costs + agreed agency fee
        fda_total = round(port_costs + inp.agency_fee_usd, 2)

        # 3. Variance against Proforma Disbursement Account (PDA)
        if inp.proforma_total_usd > 0:
            var_pct = round(((fda_total - inp.proforma_total_usd) / inp.proforma_total_usd) * 100.0, 2)
        else:
            var_pct = 0.0

        audit_flag = abs(var_pct) > cls.VARIANCE_THRESHOLD_PCT
        if audit_flag:
            advisories.append(
                f"BUDGET VARIANCE WARNING: Final FDA ${fda_total:,.2f} deviates {var_pct:+.2f}% "
                f"from initial PDA ${inp.proforma_total_usd:,.2f} (> +/-5% threshold). Vouchers required."
            )

        # 4. Net settlement calculation
        net_diff = round(inp.advance_received_usd - fda_total, 2)
        balance_amount = abs(net_diff)

        if net_diff > 0:
            status = "REFUND_TO_PRINCIPAL"
            advisories.append(f"SETTLEMENT: Surplus funds of ${balance_amount:,.2f} refundable to Shipowner / Principal.")
        elif net_diff < 0:
            status = "DUE_FROM_PRINCIPAL"
            advisories.append(f"SETTLEMENT: Outstanding deficit of ${balance_amount:,.2f} payable by Shipowner / Principal.")
        else:
            status = "BALANCED"
            advisories.append("SETTLEMENT: Exact match between advance funds and final disbursement account.")

        return PortAgencyDisbursementResult(
            call_id=inp.call_id,
            vessel_name=inp.vessel_name,
            actual_port_costs_usd=port_costs,
            total_fda_amount_usd=fda_total,
            balance_amount_usd=balance_amount,
            settlement_status=status,
            variance_from_pda_pct=var_pct,
            audit_flag=audit_flag,
            advisories=advisories,
        )
