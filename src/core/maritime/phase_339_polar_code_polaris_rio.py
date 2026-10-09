"""Phase 339: IMO Polar Code & POLARIS Risk Index Outcome (RIO) Engine.

Evaluates navigation risk in ice conditions per IMO MSC.1/Circ.1519,
computes Risk Index Outcome (RIO), Polar Service Temperature (PST), and operational status.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class IceRegimeComponent:
    ice_type: str  # "ICE_FREE", "OPEN_WATER", "THIN_FIRST_YEAR", "MEDIUM_FIRST_YEAR", "THICK_FIRST_YEAR", "MULTI_YEAR"
    concentration_tenths: int  # 0 to 10


@dataclass
class PolarNavigationInput:
    vessel_name: str
    polar_class: str  # "PC1" to "PC7", or "NON_POLAR"
    ice_components: List[IceRegimeComponent]
    mdlt_celsius: float  # Mean Daily Low Temperature
    ship_speed_knots: float
    is_escorted: bool = False


@dataclass
class PolarNavigationResult:
    vessel_name: str
    polar_class: str
    rio_score: float
    operational_status: str  # "NORMAL_OPERATION", "ELEVATED_RISK", "PROHIBITED"
    pst_celsius: float  # Polar Service Temperature
    speed_permitted: bool
    recommended_max_speed_knots: float
    advisories: List[str] = field(default_factory=list)


class PolarCodePolarisEngine:
    # RIV Table per IMO MSC.1/Circ.1519: Ice Class vs Ice Types
    RIV_TABLE: Dict[str, Dict[str, int]] = {
        "PC1": {"ICE_FREE": 3, "OPEN_WATER": 3, "THIN_FIRST_YEAR": 3, "MEDIUM_FIRST_YEAR": 2, "THICK_FIRST_YEAR": 2, "MULTI_YEAR": 1},
        "PC3": {"ICE_FREE": 3, "OPEN_WATER": 3, "THIN_FIRST_YEAR": 2, "MEDIUM_FIRST_YEAR": 1, "THICK_FIRST_YEAR": 0, "MULTI_YEAR": -2},
        "PC5": {"ICE_FREE": 3, "OPEN_WATER": 3, "THIN_FIRST_YEAR": 2, "MEDIUM_FIRST_YEAR": 0, "THICK_FIRST_YEAR": -2, "MULTI_YEAR": -4},
        "PC7": {"ICE_FREE": 3, "OPEN_WATER": 2, "THIN_FIRST_YEAR": 1, "MEDIUM_FIRST_YEAR": -1, "THICK_FIRST_YEAR": -3, "MULTI_YEAR": -6},
        "NON_POLAR": {"ICE_FREE": 3, "OPEN_WATER": 1, "THIN_FIRST_YEAR": -2, "MEDIUM_FIRST_YEAR": -4, "THICK_FIRST_YEAR": -6, "MULTI_YEAR": -8},
    }

    @classmethod
    def evaluate(cls, inp: PolarNavigationInput) -> PolarNavigationResult:
        advisories: List[str] = []
        p_class = inp.polar_class.upper()
        if p_class not in cls.RIV_TABLE:
            p_class = "NON_POLAR"

        riv_map = cls.RIV_TABLE[p_class]
        rio_total = 0.0
        total_conc = sum(c.concentration_tenths for c in inp.ice_components)

        for comp in inp.ice_components:
            ice_key = comp.ice_type.upper()
            riv = riv_map.get(ice_key, -5)
            rio_total += comp.concentration_tenths * riv

        # PST per IMO Polar Code: PST = MDLT - 10°C
        pst = round(inp.mdlt_celsius - 10.0, 1)
        advisories.append(f"POLAR SERVICE TEMP: MDLT {inp.mdlt_celsius}°C yields PST {pst}°C (Material & life-saving threshold)")

        # Operational Criteria per MSC.1/Circ.1519
        if rio_total >= 0.0:
            status = "NORMAL_OPERATION"
            max_speed = 12.0
            speed_permitted = inp.ship_speed_knots <= max_speed
            advisories.append(f"RIO {rio_total:.1f} >= 0: Normal operation permitted in ice regime.")
        elif -10.0 <= rio_total < 0.0:
            status = "ELEVATED_RISK"
            max_speed = 5.0 if not inp.is_escorted else 8.0
            speed_permitted = inp.ship_speed_knots <= max_speed
            advisories.append(f"ELEVATED RISK: RIO {rio_total:.1f}. Speed restricted to <= {max_speed} kts or requires escort.")
        else:
            status = "PROHIBITED"
            max_speed = 0.0
            speed_permitted = False
            advisories.append(f"PROHIBITED: RIO {rio_total:.1f} < -10. Ice regime exceeds structural capability. Immediate exit required.")

        if total_conc > 10:
            advisories.append(f"WARNING: Total ice concentration {total_conc}/10 exceeds 10/10 tenths scale.")

        return PolarNavigationResult(
            vessel_name=inp.vessel_name,
            polar_class=p_class,
            rio_score=round(rio_total, 2),
            operational_status=status,
            pst_celsius=pst,
            speed_permitted=speed_permitted,
            recommended_max_speed_knots=max_speed,
            advisories=advisories,
        )
