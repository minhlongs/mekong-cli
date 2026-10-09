"""Phase 356: MARPOL Annex I Bilge Sludge Management & Incinerator Control Engine.

Compliant with MARPOL Annex I Reg 12 & IMO MEPC.259(68) / MEPC.76(40).
Evaluates daily sludge generation, thermal dewatering, incinerator combustion chamber interlocks,
and OWS 15 ppm 3-way discharge diversion valves.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field


@dataclass
class SludgeIncineratorInput:
    vessel_id: str
    daily_hfo_consumed_m3: float = 35.0
    daily_mgo_consumed_m3: float = 5.0
    sludge_holding_tank_m3: float = 12.0
    sludge_tank_capacity_m3: float = 18.0
    settling_tank_temp_c: float = 85.0
    primary_chamber_temp_c: float = 870.0
    secondary_chamber_temp_c: float = 1120.0
    is_sludge_pump_running: bool = True
    oil_content_ppm: float = 12.0
    ows_3way_valve_open_to_sea: bool = True


@dataclass
class SludgeIncineratorResult:
    vessel_id: str
    estimated_daily_sludge_m3: float
    sludge_tank_fullness_percent: float
    days_to_tank_overflow: float
    is_thermal_dewatering_effective: bool
    is_incinerator_combustion_compliant: bool
    is_sludge_feed_permitted: bool
    is_ows_discharge_permitted: bool
    status: str
    advisories: list[str] = field(default_factory=list)


class SludgeIncineratorEngine:
    """Engine for bilge sludge handling and shipboard incinerator interlocks."""

    MIN_PRIMARY_TEMP_C = 850.0
    MIN_SECONDARY_TEMP_C = 1100.0
    MAX_OWS_PPM = 15.0

    @classmethod
    def evaluate(cls, inp: SludgeIncineratorInput) -> SludgeIncineratorResult:
        # MEPC.1/Circ.753 sludge generation norm: ~1.5% of HFO and ~0.5% of MGO
        daily_sludge = round(
            (inp.daily_hfo_consumed_m3 * 0.015) + (inp.daily_mgo_consumed_m3 * 0.005), 2
        )

        cap = max(1.0, inp.sludge_tank_capacity_m3)
        tank_pct = round((inp.sludge_holding_tank_m3 / cap) * 100.0, 1)

        remaining_vol = max(0.0, cap - inp.sludge_holding_tank_m3)
        days_left = round(remaining_vol / max(0.05, daily_sludge), 1)

        # Thermal dewatering requires >= 80 C
        dewatering_ok = inp.settling_tank_temp_c >= 80.0

        # Incinerator chamber temperature interlocks
        combustion_ok = (
            inp.primary_chamber_temp_c >= cls.MIN_PRIMARY_TEMP_C
            and inp.secondary_chamber_temp_c >= cls.MIN_SECONDARY_TEMP_C
        )

        # Sludge injection is permitted ONLY when primary chamber >= 850 C
        feed_permitted = inp.primary_chamber_temp_c >= cls.MIN_PRIMARY_TEMP_C

        # OWS overboard discharge permitted ONLY when oil content < 15 ppm
        ows_permitted = inp.oil_content_ppm < cls.MAX_OWS_PPM

        advisories: list[str] = []

        if not combustion_ok:
            advisories.append(
                f"INTERLOCK HAZARD: Chambers below required limits ({inp.primary_chamber_temp_c}C / {inp.secondary_chamber_temp_c}C). Target: >={cls.MIN_PRIMARY_TEMP_C}C / >={cls.MIN_SECONDARY_TEMP_C}C."
            )

        if inp.is_sludge_pump_running and not feed_permitted:
            advisories.append(
                "VIOLATION: Sludge feed pump running while primary chamber is below 850 C! Dioxin emission risk."
            )

        if inp.oil_content_ppm >= cls.MAX_OWS_PPM:
            advisories.append(
                f"MARPOL ALARM: OWS oil content ({inp.oil_content_ppm} ppm) >= 15 ppm! 3-way valve must divert back to bilge tank."
            )

        if tank_pct >= 85.0:
            advisories.append(
                f"HIGH LEVEL WARNING: Sludge holding tank at {tank_pct}%. Only {days_left} days before overflow."
            )

        # Status determination
        if (inp.is_sludge_pump_running and not feed_permitted) or (
            inp.ows_3way_valve_open_to_sea and not ows_permitted
        ):
            status = "NON_COMPLIANT_INTERLOCK_BREACH"
        elif tank_pct >= 90.0 or not combustion_ok:
            status = "ATTENTION_REQUIRED"
        else:
            status = "COMPLIANT"
            advisories.append(
                "NORMAL: Sludge generation within norms, temperatures compliant, OWS discharge legal."
            )

        return SludgeIncineratorResult(
            vessel_id=inp.vessel_id,
            estimated_daily_sludge_m3=daily_sludge,
            sludge_tank_fullness_percent=tank_pct,
            days_to_tank_overflow=days_left,
            is_thermal_dewatering_effective=dewatering_ok,
            is_incinerator_combustion_compliant=combustion_ok,
            is_sludge_feed_permitted=feed_permitted,
            is_ows_discharge_permitted=ows_permitted,
            status=status,
            advisories=advisories,
        )
