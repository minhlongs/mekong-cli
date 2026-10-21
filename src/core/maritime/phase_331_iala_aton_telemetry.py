"""Phase 331: IALA Maritime Buoyage System & AIS AtoN Telemetry Engine.

Evaluates IALA Region A/B buoyage rules, cardinal/lateral light characters,
and AIS Message 21 aids-to-navigation telemetry (Real, Synthetic, Virtual).
Adheres strictly to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass
from typing import List, Optional
import math


@dataclass
class AtoNTelemetryInput:
    mmsi_aton: str
    region: str  # "A" or "B"
    mark_type: str  # "LATERAL_PORT", "LATERAL_STARBOARD", "CARDINAL_NORTH", "CARDINAL_SOUTH", "CARDINAL_EAST", "CARDINAL_WEST", "SAFE_WATER", "ISOLATED_DANGER"
    aton_type: str  # "REAL", "SYNTHETIC", "VIRTUAL"
    nominal_lat: float
    nominal_lon: float
    current_lat: float
    current_lon: float
    battery_voltage: float = 12.6  # Volts
    lantern_active: bool = True
    light_characteristic: Optional[str] = None
    off_position_threshold_m: float = 50.0


@dataclass
class AtoNTelemetryResult:
    mmsi_aton: str
    mark_type: str
    region: str
    drift_distance_m: float
    is_off_position: bool
    is_battery_low: bool
    is_lantern_fault: bool
    operational_status: str  # "OPERATIONAL", "DEGRADED", "CRITICAL_OFF_POSITION"
    expected_color: str
    expected_rhythm: str
    is_compliant: bool
    advisories: List[str]


class IalaAtoNEngine:
    MIN_VOLTAGE_NOMINAL = 11.5  # Below 11.5V considered battery low

    CARDINAL_RHYTHMS = {
        "CARDINAL_NORTH": "VQ or Q (Continuous white flash)",
        "CARDINAL_EAST": "VQ(3) 5s or Q(3) 10s (White)",
        "CARDINAL_SOUTH": "VQ(6)+LFl 10s or Q(6)+LFl 15s (White)",
        "CARDINAL_WEST": "VQ(9) 10s or Q(9) 15s (White)",
    }

    @staticmethod
    def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + (
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)

    @classmethod
    def get_lateral_color(cls, region: str, mark_type: str) -> str:
        reg = region.upper()
        if reg == "A":
            if mark_type == "LATERAL_PORT":
                return "RED"
            elif mark_type == "LATERAL_STARBOARD":
                return "GREEN"
        else:  # Region B
            if mark_type == "LATERAL_PORT":
                return "GREEN"
            elif mark_type == "LATERAL_STARBOARD":
                return "RED"
        return "SPECIAL/YELLOW"

    @classmethod
    def evaluate(cls, inp: AtoNTelemetryInput) -> AtoNTelemetryResult:
        advisories: List[str] = []
        drift_m = cls.haversine_distance_m(
            inp.nominal_lat, inp.nominal_lon, inp.current_lat, inp.current_lon
        )

        is_off_pos = False
        if inp.aton_type.upper() in ["REAL", "SYNTHETIC"]:
            if drift_m > inp.off_position_threshold_m:
                is_off_pos = True
                advisories.append(
                    f"AtoN drifted {drift_m}m exceeding threshold {inp.off_position_threshold_m}m"
                )
        elif inp.aton_type.upper() == "VIRTUAL" and drift_m > 5.0:
            is_off_pos = True
            advisories.append(f"Virtual AtoN broadcast coordinates deviate by {drift_m}m")

        is_bat_low = inp.battery_voltage < cls.MIN_VOLTAGE_NOMINAL
        if is_bat_low:
            advisories.append(f"Battery voltage critical: {inp.battery_voltage}V < 11.5V")

        is_lantern_err = not inp.lantern_active and inp.aton_type.upper() != "VIRTUAL"
        if is_lantern_err:
            advisories.append("Light lantern is reported inactive/faulty")

        # Determine expected color & rhythm
        mark = inp.mark_type.upper()
        if mark.startswith("LATERAL"):
            exp_color = cls.get_lateral_color(inp.region, mark)
            exp_rhythm = "Fl R or Fl G according to lateral side"
        elif mark in cls.CARDINAL_RHYTHMS:
            exp_color = "BLACK & YELLOW HORIZONTAL BANDS"
            exp_rhythm = cls.CARDINAL_RHYTHMS[mark]
        elif mark == "ISOLATED_DANGER":
            exp_color = "BLACK WITH HORIZONTAL RED BANDS (2 Black Spheres topmark)"
            exp_rhythm = "Fl(2) White"
        elif mark == "SAFE_WATER":
            exp_color = "RED AND WHITE VERTICAL STRIPES"
            exp_rhythm = "Iso, Occ, or Mo(A) White"
        else:
            exp_color = "YELLOW"
            exp_rhythm = "Fl Y (Special Mark)"

        # Determine overall status
        if is_off_pos:
            status = "CRITICAL_OFF_POSITION"
        elif is_bat_low or is_lantern_err:
            status = "DEGRADED"
        else:
            status = "OPERATIONAL"

        compliant = not is_off_pos and not is_bat_low and not is_lantern_err

        return AtoNTelemetryResult(
            mmsi_aton=inp.mmsi_aton,
            mark_type=mark,
            region=inp.region.upper(),
            drift_distance_m=drift_m,
            is_off_position=is_off_pos,
            is_battery_low=is_bat_low,
            is_lantern_fault=is_lantern_err,
            operational_status=status,
            expected_color=exp_color,
            expected_rhythm=exp_rhythm,
            is_compliant=compliant,
            advisories=advisories,
        )
