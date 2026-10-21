"""Marine Biofouling Risk Assessment & In-Water Cleaning Compliance Engine.

Standards: IMO Res. MEPC.378(80), BIMCO/ICS In-Water Cleaning Standard 2021,
and Vietnam QCVN 08-MT:2015/BTNMT Marine Coastal Water Quality.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class CleaningPermission(str, Enum):
    """Regulatory permission for hull cleaning operations in port."""

    GROOMING_ALLOWED = "GROOMING_ALLOWED"
    CAPTURE_CLEANING_PERMITTED = "CAPTURE_CLEANING_PERMITTED"
    DRYDOCK_MANDATORY = "DRYDOCK_MANDATORY"
    PROHIBITED_INADEQUATE_FILTER = "PROHIBITED_INADEQUATE_FILTER"


@dataclass
class BiofoulingInspection:
    vessel_id: str
    level_of_fouling: int  # LoF 0 to 5 (Floerl scale)
    hull_surface_area_m2: float
    baseline_propulsion_power_kw: float
    rov_capture_efficiency_pct: float  # e.g., 99.5%
    filtration_mesh_micron: float  # e.g., 5.0 um
    operating_days_per_year: float = 280.0
    sfoc_g_kwh: float = 175.0


@dataclass
class BiofoulingCleaningReport:
    vessel_id: str
    level_of_fouling: int
    permission: CleaningPermission
    power_penalty_pct: float
    added_propulsion_power_kw: float
    annual_excess_fuel_tonnes: float
    is_port_cleaning_allowed: bool
    warnings: List[str]
    metrics: Dict[str, float]


class BiofoulingHullCleaningEngine:
    """Evaluates hull biofouling penalty and in-water cleaning permissions."""

    MIN_CAPTURE_EFFICIENCY_PCT: float = 99.0  # BIMCO capture standard
    MAX_FILTRATION_MICRON: float = 5.0  # 5 um particulate filter
    # Powering penalty table mapped by LoF level (Floerl / IMO MEPC)
    LOF_POWER_PENALTY_PCT: Dict[int, float] = {
        0: 0.0,
        1: 2.5,
        2: 8.0,
        3: 15.0,
        4: 25.0,
        5: 35.0,
    }

    def evaluate(self, insp: BiofoulingInspection) -> BiofoulingCleaningReport:
        warnings: List[str] = []
        lof = max(0, min(5, insp.level_of_fouling))
        penalty_pct = self.LOF_POWER_PENALTY_PCT.get(lof, 0.0)

        added_power_kw = (
            insp.baseline_propulsion_power_kw * (penalty_pct / 100.0)
        )
        annual_excess_fuel_tonnes = (
            added_power_kw
            * (insp.sfoc_g_kwh / 1_000_000.0)
            * 24.0
            * insp.operating_days_per_year
        )

        permission = CleaningPermission.GROOMING_ALLOWED
        is_port_cleaning_allowed = True

        if lof <= 1:
            permission = CleaningPermission.GROOMING_ALLOWED
        elif lof in (2, 3):
            # Requires ROV active capture >= 99% and filter <= 5 um
            if (
                insp.rov_capture_efficiency_pct >= self.MIN_CAPTURE_EFFICIENCY_PCT
                and insp.filtration_mesh_micron <= self.MAX_FILTRATION_MICRON
            ):
                permission = CleaningPermission.CAPTURE_CLEANING_PERMITTED
            else:
                permission = CleaningPermission.PROHIBITED_INADEQUATE_FILTER
                is_port_cleaning_allowed = False
                warnings.append(
                    f"In-water cleaning rejected: Capture {insp.rov_capture_efficiency_pct:.1f}% "
                    f"< {self.MIN_CAPTURE_EFFICIENCY_PCT}% or Mesh {insp.filtration_mesh_micron}um "
                    f"> {self.MAX_FILTRATION_MICRON}um"
                )
        else:  # LoF >= 4
            permission = CleaningPermission.DRYDOCK_MANDATORY
            is_port_cleaning_allowed = False
            warnings.append(
                f"Severe fouling (LoF {lof}): In-water cleaning strictly prohibited in port "
                f"waters by IMO MEPC.378(80). Drydocking mandatory."
            )

        if penalty_pct >= 15.0:
            warnings.append(
                f"High hydrodynamic drag: Power penalty {penalty_pct}% adds "
                f"{added_power_kw:.1f} kW and {annual_excess_fuel_tonnes:.1f} t/yr fuel"
            )

        metrics = {
            "level_of_fouling": float(lof),
            "power_penalty_pct": round(penalty_pct, 2),
            "added_propulsion_power_kw": round(added_power_kw, 2),
            "annual_excess_fuel_tonnes": round(annual_excess_fuel_tonnes, 2),
            "rov_capture_efficiency_pct": insp.rov_capture_efficiency_pct,
            "filtration_mesh_micron": insp.filtration_mesh_micron,
        }

        return BiofoulingCleaningReport(
            vessel_id=insp.vessel_id,
            level_of_fouling=lof,
            permission=permission,
            power_penalty_pct=round(penalty_pct, 2),
            added_propulsion_power_kw=round(added_power_kw, 2),
            annual_excess_fuel_tonnes=round(annual_excess_fuel_tonnes, 2),
            is_port_cleaning_allowed=is_port_cleaning_allowed,
            warnings=warnings,
            metrics=metrics,
        )
