"""Central Facade for Maritime Phases 355–358.

Combines:
- Phase 355: LPG Cargo Reliquefaction & Compressor Control Engine
- Phase 356: MARPOL Annex I Bilge Sludge Management & Incinerator Engine
- Phase 357: Smart Mooring Line Tension & Quay Berth Surge Engine
- Phase 358: Maritime Cyber Risk Management & OT/IT Network Resilience Engine

Strictly kept under 200 lines.
"""

from dataclasses import dataclass
from typing import Optional

from src.core.maritime.phase_355_lpg_reliquefaction_compressor import (
    LpgReliquefactionEngine,
    LpgReliquefactionInput,
    LpgReliquefactionResult,
)
from src.core.maritime.phase_356_marpol_sludge_incinerator import (
    SludgeIncineratorEngine,
    SludgeIncineratorInput,
    SludgeIncineratorResult,
)
from src.core.maritime.phase_357_smart_mooring_surge_meg4 import (
    SmartMooringEngine,
    SmartMooringInput,
    SmartMooringResult,
)
from src.core.maritime.phase_358_maritime_cyber_resilience import (
    MaritimeCyberEngine,
    MaritimeCyberInput,
    MaritimeCyberResult,
)


@dataclass
class MaritimeMultiDomain355To358Result:
    lpg: Optional[LpgReliquefactionResult] = None
    sludge: Optional[SludgeIncineratorResult] = None
    mooring: Optional[SmartMooringResult] = None
    cyber: Optional[MaritimeCyberResult] = None
    summary_status: str = "NOMINAL"


class MaritimeLpgSludgeMooringCyberFacade:
    """Unified Facade for Maritime Phases 355-358 operations."""

    @staticmethod
    def evaluate_lpg(inp: LpgReliquefactionInput) -> LpgReliquefactionResult:
        return LpgReliquefactionEngine.evaluate(inp)

    @staticmethod
    def evaluate_sludge(inp: SludgeIncineratorInput) -> SludgeIncineratorResult:
        return SludgeIncineratorEngine.evaluate(inp)

    @staticmethod
    def evaluate_mooring(inp: SmartMooringInput) -> SmartMooringResult:
        return SmartMooringEngine.evaluate(inp)

    @staticmethod
    def evaluate_cyber(inp: MaritimeCyberInput) -> MaritimeCyberResult:
        return MaritimeCyberEngine.evaluate(inp)

    @classmethod
    def run_all(
        cls,
        lpg_input: Optional[LpgReliquefactionInput] = None,
        sludge_input: Optional[SludgeIncineratorInput] = None,
        mooring_input: Optional[SmartMooringInput] = None,
        cyber_input: Optional[MaritimeCyberInput] = None,
    ) -> MaritimeMultiDomain355To358Result:
        res_lpg = cls.evaluate_lpg(lpg_input) if lpg_input else None
        res_sludge = cls.evaluate_sludge(sludge_input) if sludge_input else None
        res_mooring = cls.evaluate_mooring(mooring_input) if mooring_input else None
        res_cyber = cls.evaluate_cyber(cyber_input) if cyber_input else None

        statuses = [
            r.status
            for r in [res_lpg, res_sludge, res_mooring, res_cyber]
            if r is not None
        ]

        if any(
            "CRITICAL" in s
            or "PARTING" in s
            or "BREACH" in s
            or "CONTAINMENT" in s
            for s in statuses
        ):
            summary = "ACTION_REQUIRED_CRITICAL"
        elif any(
            "ALERT" in s
            or "WARNING" in s
            or "EXCEEDED" in s
            or "ATTENTION" in s
            or "DEFICIENT" in s
            for s in statuses
        ):
            summary = "ELEVATED_RISK"
        else:
            summary = "ALL_SYSTEMS_OPTIMAL"

        return MaritimeMultiDomain355To358Result(
            lpg=res_lpg,
            sludge=res_sludge,
            mooring=res_mooring,
            cyber=res_cyber,
            summary_status=summary,
        )


__all__ = [
    "LpgReliquefactionInput",
    "LpgReliquefactionResult",
    "LpgReliquefactionEngine",
    "SludgeIncineratorInput",
    "SludgeIncineratorResult",
    "SludgeIncineratorEngine",
    "SmartMooringInput",
    "SmartMooringResult",
    "SmartMooringEngine",
    "MaritimeCyberInput",
    "MaritimeCyberResult",
    "MaritimeCyberEngine",
    "MaritimeMultiDomain355To358Result",
    "MaritimeLpgSludgeMooringCyberFacade",
]
