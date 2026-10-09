"""Phase 406: Marine Sewage Treatment Plant (STP) Membrane Bioreactor & Nutrient Removal.

Complies with IMO Resolution MEPC.227(64) including Section 4.2 nutrient removal for MARPOL Annex IV Special Areas.
Monitors BOD5, COD, TSS, coliform count, total nitrogen (TN), total phosphorus (TP), and MBR TMP fouling.
Strictly < 180 LOC, zero-mock deterministic biochemical engineering.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class SewageDischargeStatus(str, Enum):
    """Compliance classification for effluent discharge into sea."""
    DISCHARGE_COMPLIANT_GLOBAL = "DISCHARGE_COMPLIANT_GLOBAL"
    DISCHARGE_COMPLIANT_SPECIAL_AREA = "DISCHARGE_COMPLIANT_SPECIAL_AREA"
    NUTRIENT_NON_COMPLIANT = "NUTRIENT_NON_COMPLIANT"
    EFFLUENT_QUALITY_FAIL = "EFFLUENT_QUALITY_FAIL"
    MEMBRANE_FOULING_TRIP = "MEMBRANE_FOULING_TRIP"


@dataclass
class SewageTreatmentInput:
    """Telemetry and effluent quality sensor readings from marine STP."""
    bod5_mg_l: float = 12.0  # Biochemical Oxygen Demand (MEPC.227(64) limit <= 25 mg/L)
    cod_mg_l: float = 85.0  # Chemical Oxygen Demand (limit <= 125 mg/L)
    tss_mg_l: float = 15.0  # Total Suspended Solids (limit <= 35 mg/L)
    coliform_cfu_100ml: float = 40.0  # Thermotolerant coliforms (limit <= 100 CFU/100 mL)
    total_nitrogen_mg_l: float = 14.0  # Total N (Sec 4.2 Special Area limit <= 20 mg/L)
    total_phosphorus_mg_l: float = 0.7  # Total P (Sec 4.2 Special Area limit <= 1.0 mg/L)
    transmembrane_pressure_bar: float = 0.18  # MBR TMP (backwash trigger >= 0.35 bar, trip >= 0.50 bar)
    operating_in_special_area: bool = True  # e.g., Baltic Sea passenger ship zone
    aeration_blower_running: bool = True  # Activated sludge aerobic chamber blower


@dataclass
class SewageTreatmentResult:
    """Evaluation result for marine sewage treatment plant effluent."""
    status: SewageDischargeStatus
    overboard_discharge_permitted: bool
    standard_effluent_pass: bool
    nutrient_removal_pass: bool
    membrane_fouling_safe: bool
    backwash_recommended: bool
    warnings: List[str] = field(default_factory=list)


class SewageTreatmentEngine:
    """Biochemical and regulatory compliance engine for marine STP."""

    MAX_BOD5_MG_L = 25.0
    MAX_COD_MG_L = 125.0
    MAX_TSS_MG_L = 35.0
    MAX_COLIFORM_CFU = 100.0
    MAX_SPECIAL_AREA_TN_MG_L = 20.0
    MAX_SPECIAL_AREA_TP_MG_L = 1.0
    WARN_TMP_BAR = 0.35
    TRIP_TMP_BAR = 0.50

    def evaluate(self, telemetry: SewageTreatmentInput) -> SewageTreatmentResult:
        warnings: List[str] = []

        standard_effluent_pass = (
            telemetry.bod5_mg_l <= self.MAX_BOD5_MG_L
            and telemetry.cod_mg_l <= self.MAX_COD_MG_L
            and telemetry.tss_mg_l <= self.MAX_TSS_MG_L
            and telemetry.coliform_cfu_100ml <= self.MAX_COLIFORM_CFU
            and telemetry.aeration_blower_running
        )

        if telemetry.bod5_mg_l > self.MAX_BOD5_MG_L:
            warnings.append(f"Effluent BOD5 {telemetry.bod5_mg_l} mg/L exceeds limit {self.MAX_BOD5_MG_L} mg/L")
        if telemetry.cod_mg_l > self.MAX_COD_MG_L:
            warnings.append(f"Effluent COD {telemetry.cod_mg_l} mg/L exceeds limit {self.MAX_COD_MG_L} mg/L")
        if telemetry.tss_mg_l > self.MAX_TSS_MG_L:
            warnings.append(f"Effluent TSS {telemetry.tss_mg_l} mg/L exceeds limit {self.MAX_TSS_MG_L} mg/L")
        if telemetry.coliform_cfu_100ml > self.MAX_COLIFORM_CFU:
            warnings.append(f"Coliform count {telemetry.coliform_cfu_100ml} CFU exceeds limit {self.MAX_COLIFORM_CFU} CFU/100 mL")
        if not telemetry.aeration_blower_running:
            warnings.append("Aeration blower stopped: Aerobic bacterial digestion failure.")

        nutrient_removal_pass = (
            telemetry.total_nitrogen_mg_l <= self.MAX_SPECIAL_AREA_TN_MG_L
            and telemetry.total_phosphorus_mg_l <= self.MAX_SPECIAL_AREA_TP_MG_L
        )

        if telemetry.operating_in_special_area and not nutrient_removal_pass:
            warnings.append(
                f"Special Area nutrient limit breached: TN={telemetry.total_nitrogen_mg_l} mg/L (limit {self.MAX_SPECIAL_AREA_TN_MG_L}), "
                f"TP={telemetry.total_phosphorus_mg_l} mg/L (limit {self.MAX_SPECIAL_AREA_TP_MG_L})"
            )

        backwash_recommended = telemetry.transmembrane_pressure_bar >= self.WARN_TMP_BAR
        membrane_fouling_safe = telemetry.transmembrane_pressure_bar < self.TRIP_TMP_BAR

        if backwash_recommended:
            warnings.append(
                f"MBR Transmembrane Pressure {telemetry.transmembrane_pressure_bar} bar >= {self.WARN_TMP_BAR} bar. "
                "Membrane backwash cycle required."
            )
        if not membrane_fouling_safe:
            warnings.append(
                f"Critical MBR fouling: TMP {telemetry.transmembrane_pressure_bar} bar >= {self.TRIP_TMP_BAR} bar. Discharge tripped."
            )

        if not standard_effluent_pass:
            status = SewageDischargeStatus.EFFLUENT_QUALITY_FAIL
            overboard_discharge_permitted = False
        elif not membrane_fouling_safe:
            status = SewageDischargeStatus.MEMBRANE_FOULING_TRIP
            overboard_discharge_permitted = False
        elif telemetry.operating_in_special_area and not nutrient_removal_pass:
            status = SewageDischargeStatus.NUTRIENT_NON_COMPLIANT
            overboard_discharge_permitted = False
        elif telemetry.operating_in_special_area and nutrient_removal_pass:
            status = SewageDischargeStatus.DISCHARGE_COMPLIANT_SPECIAL_AREA
            overboard_discharge_permitted = True
        else:
            status = SewageDischargeStatus.DISCHARGE_COMPLIANT_GLOBAL
            overboard_discharge_permitted = True

        return SewageTreatmentResult(
            status=status,
            overboard_discharge_permitted=overboard_discharge_permitted,
            standard_effluent_pass=standard_effluent_pass,
            nutrient_removal_pass=nutrient_removal_pass,
            membrane_fouling_safe=membrane_fouling_safe,
            backwash_recommended=backwash_recommended,
            warnings=warnings,
        )
