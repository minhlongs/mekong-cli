"""Phase 425: Machinery Bilge Water Vacuum Evaporator & Distillation.

Complies with MARPOL Annex I Reg 14 & 15, IMO MEPC.107(49), and ClassNK marine machinery rules.
Monitors vacuum distillation chamber pressure (0.15 - 0.30 bar), heating water temp (70 - 85°C),
foam level interlock (defoamer pump trigger > 150 mm), and distillate oil content (<= 5.0 ppm limit).
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BilgeEvaporatorTelemetry:
    """Telemetry readings for machinery bilge water vacuum evaporator."""
    chamber_pressure_bar: float = 0.22       # Vacuum operating pressure [0.15, 0.30] bar
    boiling_temp_c: float = 62.0             # Boiling temp at vacuum (54-69°C)
    ht_heating_water_temp_c: float = 78.0    # Engine jacket HT water (70-85°C)
    foam_level_mm: float = 40.0              # High foam threshold > 150 mm
    distillate_oil_ppm: float = 1.2          # Target <= 5.0 ppm, divert if > 5.0 ppm
    sludge_density_kg_m3: float = 1040.0     # Concentrated residue density
    evaporator_feed_active: bool = True
    distillate_discharge_open: bool = True


@dataclass(frozen=True)
class BilgeEvaporatorAssessment:
    """Operational assessment and automated divert valve status for bilge evaporator."""
    vacuum_nominal: bool
    defoamer_dosing_active: bool
    overboard_discharge_permitted: bool
    recirculation_valve_active: bool
    distillation_efficiency_pct: float
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class BilgeEvaporatorEngine:
    """Vacuum bilge evaporator process monitor and MARPOL discharge regulator."""

    MIN_VACUUM_BAR: float = 0.15
    MAX_VACUUM_BAR: float = 0.30
    MAX_FOAM_LEVEL_MM: float = 150.0
    MARPOL_LEGAL_PPM: float = 15.0
    INTERNAL_PURITY_LIMIT_PPM: float = 5.0

    def evaluate(self, telem: BilgeEvaporatorTelemetry) -> BilgeEvaporatorAssessment:
        warnings: List[str] = []
        compliance: Dict[str, bool] = {
            "MEPC_107_49_distillate_oil": True,
            "MARPOL_Annex_I_discharge": True,
            "vacuum_integrity": True,
        }

        # Vacuum operating envelope verification
        vac_ok = self.MIN_VACUUM_BAR <= telem.chamber_pressure_bar <= self.MAX_VACUUM_BAR
        if not vac_ok:
            warnings.append(
                f"Chamber pressure out of range: {telem.chamber_pressure_bar:.2f} bar not in [{self.MIN_VACUUM_BAR}, {self.MAX_VACUUM_BAR}]"
            )
            compliance["vacuum_integrity"] = False

        # HT waste heat energy check
        if telem.ht_heating_water_temp_c < 70.0:
            warnings.append(f"Insufficient HT heat source: {telem.ht_heating_water_temp_c:.1f}°C < 70.0°C")

        # Foam carryover prevention
        defoamer_active = telem.foam_level_mm > self.MAX_FOAM_LEVEL_MM
        if defoamer_active:
            warnings.append(f"Foam surge detected: {telem.foam_level_mm:.1f} mm > {self.MAX_FOAM_LEVEL_MM} mm, defoamer dosed")

        # Distillate purity evaluation
        overboard_permitted = telem.distillate_oil_ppm < self.INTERNAL_PURITY_LIMIT_PPM
        recirc_active = not overboard_permitted

        if telem.distillate_oil_ppm >= self.MARPOL_LEGAL_PPM:
            warnings.append(f"CRITICAL MARPOL VIOLATION: Distillate oil {telem.distillate_oil_ppm:.1f} ppm >= {self.MARPOL_LEGAL_PPM} ppm")
            compliance["MARPOL_Annex_I_discharge"] = False
            compliance["MEPC_107_49_distillate_oil"] = False
        elif telem.distillate_oil_ppm >= self.INTERNAL_PURITY_LIMIT_PPM:
            warnings.append(f"Distillate purity off-spec: {telem.distillate_oil_ppm:.1f} ppm >= {self.INTERNAL_PURITY_LIMIT_PPM} ppm (recirculating)")
            compliance["MEPC_107_49_distillate_oil"] = False

        # Distillation thermal efficiency index
        efficiency = 95.0
        if not vac_ok:
            efficiency -= 25.0
        if defoamer_active:
            efficiency -= 15.0
        if telem.distillate_oil_ppm > self.INTERNAL_PURITY_LIMIT_PPM:
            efficiency -= 20.0
        distillation_eff = round(max(10.0, min(100.0, efficiency)), 1)

        if telem.distillate_oil_ppm >= self.MARPOL_LEGAL_PPM or not compliance["vacuum_integrity"]:
            status = "EMERGENCY_DIVERT"
        elif recirc_active or defoamer_active:
            status = "WARNING_RECIRCULATE"
        else:
            status = "NOMINAL_DISTILLING"

        return BilgeEvaporatorAssessment(
            vacuum_nominal=vac_ok,
            defoamer_dosing_active=defoamer_active,
            overboard_discharge_permitted=overboard_permitted,
            recirculation_valve_active=recirc_active,
            distillation_efficiency_pct=distillation_eff,
            status=status,
            warnings=warnings,
            compliance_flags=compliance,
        )
