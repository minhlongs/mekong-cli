"""World Ports Environmental Ship Index (ESI) & Green Port Dues Incentive Engine.

Standards: IAPH World Ports Climate Initiative (WPCI) ESI Guidelines,
IMO MARPOL Annex VI, and Vietnam Circular 39/2023/TT-BGTVT Seaport Tariff Rebates.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class GreenPortTier(str, Enum):
    """Green Port tariff discount tier under Circular 39/2023/TT-BGTVT."""

    GOLD = "GOLD"  # ESI >= 50.0 -> 20% discount
    SILVER = "SILVER"  # 30.0 <= ESI < 50.0 -> 10% discount
    BRONZE = "BRONZE"  # 20.0 <= ESI < 30.0 -> 5% discount
    STANDARD = "STANDARD"  # ESI < 20.0 -> No discount


@dataclass
class EsiShipInput:
    vessel_imo: str
    vessel_name: str
    nox_reduction_pct: float = 30.0  # Reduction below IMO Tier I baseline (0-100%)
    fuel_sulfur_pct: float = 0.20  # Fuel sulfur content (e.g., 0.10% ECA or 0.50% global)
    co2_improvement_pct: float = 10.0  # Energy efficiency gain over EEOI baseline (0-50%)
    has_ops_cold_ironing: bool = False  # Equipped with Onshore Power Supply
    gross_tonnage: float = 10000.0


@dataclass
class EsiEvaluationReport:
    vessel_imo: str
    vessel_name: str
    esi_total_score: float
    esi_nox_score: float
    esi_sox_score: float
    esi_co2_score: float
    esi_ops_score: float
    tier: GreenPortTier
    port_dues_discount_pct: float
    eligible_incentives: List[str]
    metrics: Dict[str, float]


class PortEsiGreenIncentiveEngine:
    """Computes Environmental Ship Index and Green Port tariff rebates."""

    OPS_BONUS_POINTS: float = 35.0

    def compute_esi_nox(self, nox_reduction_pct: float) -> float:
        """Compute ESI NOx score (0 to 100)."""
        return round(min(100.0, max(0.0, nox_reduction_pct * 1.25)), 2)

    def compute_esi_sox(self, sulfur_pct: float) -> float:
        """Compute ESI SOx score based on fuel sulfur level vs 0.50% statutory baseline."""
        if sulfur_pct >= 0.50:
            return 0.0
        # Linear scale from 0.50% (score 0) down to 0.00% (score 100)
        score = 100.0 * (0.50 - max(0.0, sulfur_pct)) / 0.50
        return round(min(100.0, max(0.0, score)), 2)

    def compute_esi_co2(self, co2_gain_pct: float) -> float:
        """Compute ESI CO2 score from operational efficiency gain."""
        return round(min(100.0, max(0.0, co2_gain_pct * 3.33)), 2)

    def evaluate(self, ship: EsiShipInput) -> EsiEvaluationReport:
        esi_nox = self.compute_esi_nox(ship.nox_reduction_pct)
        esi_sox = self.compute_esi_sox(ship.fuel_sulfur_pct)
        esi_co2 = self.compute_esi_co2(ship.co2_improvement_pct)
        esi_ops = self.OPS_BONUS_POINTS if ship.has_ops_cold_ironing else 0.0

        # WPCI composite formula: (2*NOx + 2*SOx + CO2 + OPS) / 5
        raw_total = (2.0 * esi_nox + 2.0 * esi_sox + esi_co2 + esi_ops) / 5.0
        esi_total = round(min(100.0, max(0.0, raw_total)), 2)

        incentives: List[str] = []
        if esi_total >= 50.0:
            tier = GreenPortTier.GOLD
            discount_pct = 20.0
            incentives.append("20% discount on port tonnage dues and berthage")
            incentives.append("Priority green bunkering & zero-emission berth allocation")
        elif esi_total >= 30.0:
            tier = GreenPortTier.SILVER
            discount_pct = 10.0
            incentives.append("10% discount on port tonnage dues")
        elif esi_total >= 20.0:
            tier = GreenPortTier.BRONZE
            discount_pct = 5.0
            incentives.append("5% discount on port tonnage dues")
        else:
            tier = GreenPortTier.STANDARD
            discount_pct = 0.0

        if ship.has_ops_cold_ironing:
            incentives.append("Exemption from auxiliary engine harbor emission surcharge")

        return EsiEvaluationReport(
            vessel_imo=ship.vessel_imo,
            vessel_name=ship.vessel_name,
            esi_total_score=esi_total,
            esi_nox_score=esi_nox,
            esi_sox_score=esi_sox,
            esi_co2_score=esi_co2,
            esi_ops_score=esi_ops,
            tier=tier,
            port_dues_discount_pct=discount_pct,
            eligible_incentives=incentives,
            metrics={
                "esi_total": esi_total,
                "esi_nox": esi_nox,
                "esi_sox": esi_sox,
                "esi_co2": esi_co2,
                "esi_ops": esi_ops,
                "discount_pct": discount_pct,
            },
        )


__all__ = [
    "GreenPortTier",
    "EsiShipInput",
    "EsiEvaluationReport",
    "PortEsiGreenIncentiveEngine",
]
