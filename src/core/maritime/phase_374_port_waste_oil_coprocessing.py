"""Port Circular Waste Oil Recovery & MARPOL Annex I Co-Processing Engine.

Standards: MARPOL Annex I Reg 12/13, Basel Convention,
Circular 02/2022/TT-BTNMT, and Circular 39/2023/TT-BGTVT.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class WasteOilComplianceStatus(str, Enum):
    """Compliance state for received oily sludge / slops."""

    ACCEPTED_FOR_COPROCESSING = "ACCEPTED_FOR_COPROCESSING"
    REJECTED_LOW_FLASH_POINT = "REJECTED_LOW_FLASH_POINT"
    REJECTED_HIGH_EFFLUENT_PPM = "REJECTED_HIGH_EFFLUENT_PPM"
    OFF_SPEC_RFO = "OFF_SPEC_RFO"


@dataclass
class WasteOilBatch:
    batch_id: str
    volume_m3: float
    density_kg_m3: float = 950.0
    flash_point_c: float = 65.0  # Pensky-Martens closed cup
    water_content_pct: float = 30.0
    separation_efficiency_pct: float = 96.0
    effluent_oil_ppm: float = 12.0  # Must be <= 15 ppm
    rfo_lhv_mj_kg: float = 40.0  # Lower Heating Value >= 38 MJ/kg
    rfo_sediment_pct: float = 0.3  # Max 0.5%
    rfo_ash_pct: float = 0.1  # Max 0.15%


@dataclass
class WasteOilCoprocessingReport:
    batch_id: str
    status: WasteOilComplianceStatus
    is_safe_to_receive: bool
    recovered_fuel_oil_tonnes: float
    recovered_fuel_energy_gj: float
    co2_offset_tonnes: float
    effluent_compliant: bool
    warnings: List[str]
    metrics: Dict[str, float]


class PortWasteOilCoprocessingEngine:
    """Manages port reception of sludges, centrifugal dewatering, and clinker co-processing."""

    MIN_FLASH_POINT_C: float = 60.0  # SOLAS/MARPOL flash point safety floor
    MAX_EFFLUENT_OIL_PPM: float = 15.0  # MARPOL Annex I discharge threshold
    MIN_RFO_LHV_MJ_KG: float = 38.0  # Cement kiln co-processing specification
    MAX_RFO_SEDIMENT_PCT: float = 0.5
    MAX_RFO_ASH_PCT: float = 0.15
    CO2_OFFSET_KG_PER_KG_RFO: float = 1.2  # Net carbon offset in cement clinker

    def evaluate(self, batch: WasteOilBatch) -> WasteOilCoprocessingReport:
        warnings: List[str] = []
        is_safe = True
        effluent_ok = batch.effluent_oil_ppm <= self.MAX_EFFLUENT_OIL_PPM

        # 1. Reception safety gate: Flash point >= 60°C
        if batch.flash_point_c < self.MIN_FLASH_POINT_C:
            is_safe = False
            status = WasteOilComplianceStatus.REJECTED_LOW_FLASH_POINT
            warnings.append(
                f"Flash point {batch.flash_point_c:.1f}°C < mandatory {self.MIN_FLASH_POINT_C}°C: "
                "Explosion hazard! Auto-rejecting reception into port storage."
            )
            return WasteOilCoprocessingReport(
                batch_id=batch.batch_id,
                status=status,
                is_safe_to_receive=False,
                recovered_fuel_oil_tonnes=0.0,
                recovered_fuel_energy_gj=0.0,
                co2_offset_tonnes=0.0,
                effluent_compliant=effluent_ok,
                warnings=warnings,
                metrics={"flash_point_c": batch.flash_point_c},
            )

        # 2. Separation mass balance
        total_mass_tonnes = (batch.volume_m3 * batch.density_kg_m3) / 1000.0
        oil_fraction = max(0.0, 1.0 - (batch.water_content_pct / 100.0))
        potential_oil_tonnes = total_mass_tonnes * oil_fraction
        rfo_tonnes = potential_oil_tonnes * (batch.separation_efficiency_pct / 100.0)

        # 3. Effluent water check
        if not effluent_ok:
            warnings.append(
                f"Centrifugal effluent {batch.effluent_oil_ppm:.1f} ppm exceeds "
                f"MARPOL 15 ppm limit: Secondary DAF/adsorption filtration required."
            )

        # 4. RFO quality check
        status = WasteOilComplianceStatus.ACCEPTED_FOR_COPROCESSING
        if batch.rfo_lhv_mj_kg < self.MIN_RFO_LHV_MJ_KG:
            status = WasteOilComplianceStatus.OFF_SPEC_RFO
            warnings.append(
                f"RFO LHV {batch.rfo_lhv_mj_kg:.1f} MJ/kg < required {self.MIN_RFO_LHV_MJ_KG} MJ/kg"
            )
        elif batch.rfo_sediment_pct > self.MAX_RFO_SEDIMENT_PCT:
            status = WasteOilComplianceStatus.OFF_SPEC_RFO
            warnings.append(
                f"Sediment {batch.rfo_sediment_pct:.2f}% > limit {self.MAX_RFO_SEDIMENT_PCT}%"
            )
        elif batch.rfo_ash_pct > self.MAX_RFO_ASH_PCT:
            status = WasteOilComplianceStatus.OFF_SPEC_RFO
            warnings.append(
                f"Ash content {batch.rfo_ash_pct:.2f}% > limit {self.MAX_RFO_ASH_PCT}%"
            )

        if not effluent_ok and status == WasteOilComplianceStatus.ACCEPTED_FOR_COPROCESSING:
            status = WasteOilComplianceStatus.REJECTED_HIGH_EFFLUENT_PPM

        # Energy & Carbon Offsets
        energy_gj = (rfo_tonnes * 1000.0 * batch.rfo_lhv_mj_kg) / 1000.0
        co2_offset_tonnes = (rfo_tonnes * 1000.0 * self.CO2_OFFSET_KG_PER_KG_RFO) / 1000.0

        metrics = {
            "total_mass_tonnes": round(total_mass_tonnes, 2),
            "recovered_fuel_oil_tonnes": round(rfo_tonnes, 2),
            "recovered_energy_gj": round(energy_gj, 2),
            "co2_offset_tonnes": round(co2_offset_tonnes, 2),
            "effluent_oil_ppm": batch.effluent_oil_ppm,
            "flash_point_c": batch.flash_point_c,
        }

        return WasteOilCoprocessingReport(
            batch_id=batch.batch_id,
            status=status,
            is_safe_to_receive=is_safe,
            recovered_fuel_oil_tonnes=round(rfo_tonnes, 2),
            recovered_fuel_energy_gj=round(energy_gj, 2),
            co2_offset_tonnes=round(co2_offset_tonnes, 2),
            effluent_compliant=effluent_ok,
            warnings=warnings,
            metrics=metrics,
        )
