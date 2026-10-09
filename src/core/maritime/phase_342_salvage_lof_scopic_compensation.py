"""Phase 342: Lloyd's Open Form LOF 2024 & SCOPIC Clause Compensation Engine.

Calculates Article 13 salvage remuneration (No Cure - No Pay based on salved value),
evaluates SCOPIC special compensation (P&I Club tariff + 25% uplift), and applies
Article 14 discount penalty when Article 13 award exceeds SCOPIC costs.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SalvageClaimInput:
    incident_id: str
    vessel_name: str
    salved_value_usd: float  # Ship + Bunkers + Cargo + Freight
    is_scopic_invoked: bool
    scopic_tariff_costs_usd: float = 0.0
    environmental_danger_severity: str = "HIGH"  # "LOW", "MEDIUM", "HIGH"
    salvor_merit_score: float = 0.85  # Scale 0.0 to 1.0 based on skill, promptness, resources


@dataclass
class SalvageClaimResult:
    incident_id: str
    article_13_gross_award_usd: float
    scopic_remuneration_usd: float
    discount_penalty_usd: float
    net_salvor_payable_usd: float
    paying_party: str  # "PROPERTY_UNDERWRITERS", "P_AND_I_CLUB", "JOINT"
    advisories: List[str] = field(default_factory=list)


class SalvageLofScopicEngine:
    SCOPIC_UPLIFT_PCT = 0.25  # Standard 25% bonus on SCOPIC tariff
    ARTICLE_14_PENALTY_PCT = 0.25  # 25% discount on difference if Art 13 > SCOPIC
    BASE_ARTICLE_13_PCT = 0.12  # Standard ~12% base of salved value

    @classmethod
    def evaluate(cls, inp: SalvageClaimInput) -> SalvageClaimResult:
        advisories: List[str] = []

        # 1. Calculate Article 13 Gross Award
        # Factor environmental protection and salvor merit
        env_factor = 1.3 if inp.environmental_danger_severity == "HIGH" else (1.1 if inp.environmental_danger_severity == "MEDIUM" else 1.0)
        effective_pct = min(0.35, cls.BASE_ARTICLE_13_PCT * inp.salvor_merit_score * env_factor)
        art_13_gross = round(inp.salved_value_usd * effective_pct, 2)
        advisories.append(f"ARTICLE 13 SALVAGE: Award calculated at {effective_pct * 100:.1f}% of salved value (${art_13_gross:,.2f})")

        # 2. SCOPIC Clause Calculation
        scopic_total = 0.0
        discount_penalty = 0.0
        net_payable = art_13_gross
        paying_party = "PROPERTY_UNDERWRITERS"

        if inp.is_scopic_invoked:
            scopic_total = round(inp.scopic_tariff_costs_usd * (1.0 + cls.SCOPIC_UPLIFT_PCT), 2)
            advisories.append(f"SCOPIC INVOKED: Tariff costs ${inp.scopic_tariff_costs_usd:,.2f} + 25% uplift = ${scopic_total:,.2f}")

            if art_13_gross > scopic_total:
                # Article 14 Discount Penalty: 25% of difference
                diff = art_13_gross - scopic_total
                discount_penalty = round(diff * cls.ARTICLE_14_PENALTY_PCT, 2)
                net_payable = round(art_13_gross - discount_penalty, 2)
                paying_party = "PROPERTY_UNDERWRITERS"
                advisories.append(f"ARTICLE 14 DISCOUNT: Art 13 exceeds SCOPIC by ${diff:,.2f}. 25% penalty applied: -${discount_penalty:,.2f}")
                advisories.append(f"NET PAYABLE: Property underwriters liable for discounted award of ${net_payable:,.2f}")
            else:
                # SCOPIC exceeds Article 13: Salvor receives full SCOPIC
                net_payable = scopic_total
                paying_party = "P_AND_I_CLUB"
                advisories.append(f"SCOPIC PAYABLE: SCOPIC (${scopic_total:,.2f}) exceeds Art 13 (${art_13_gross:,.2f}). P&I Club liable for SCOPIC.")
        else:
            advisories.append("TRADITIONAL NO CURE - NO PAY: SCOPIC not invoked. Property underwriters pay full Article 13 award.")

        return SalvageClaimResult(
            incident_id=inp.incident_id,
            article_13_gross_award_usd=art_13_gross,
            scopic_remuneration_usd=scopic_total,
            discount_penalty_usd=discount_penalty,
            net_salvor_payable_usd=net_payable,
            paying_party=paying_party,
            advisories=advisories,
        )
