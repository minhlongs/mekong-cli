"""Phase 338: BIMCO Charterparty Performance & Maritime Arbitration Engine.

Evaluates speed and fuel warranties with good weather exclusion (Beaufort <= 4, Douglas <= 3),
calculates laytime/demurrage/despatch, and formats settlement for LMAA or VMAC proceedings.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CharterpartyDisputeInput:
    fixture_id: str
    vessel_name: str
    charter_type: str  # "TIME_CHARTER" or "VOYAGE_CHARTER"
    daily_hire_or_demurrage_usd: float
    bunker_price_usd_per_mt: float = 650.0
    # Time Charter Warranty Inputs
    voyage_distance_nm: Optional[float] = None
    warranted_speed_knots: Optional[float] = None
    recorded_speed_knots: Optional[float] = None
    warranted_fuel_mt_day: Optional[float] = None
    recorded_fuel_mt_day: Optional[float] = None
    beaufort_scale: int = 3
    douglas_sea_state: int = 2
    # Voyage Charter Laytime Inputs
    allowed_laytime_hours: Optional[float] = None
    actual_laytime_used_hours: Optional[float] = None
    laytime_type: str = "SHINC"  # "SHINC" or "SHEX"
    arbitration_forum: str = "LMAA_ICP"  # "LMAA_ICP", "LMAA_SCP", "VMAC"


@dataclass
class CharterpartyDisputeResult:
    fixture_id: str
    arbitration_forum: str
    is_good_weather: bool
    weather_excluded: bool
    speed_underperformance_knots: float
    time_lost_hours: float
    excess_bunker_mt: float
    warranty_claim_usd: float
    laytime_saved_or_exceeded_hours: float
    demurrage_due_usd: float
    despatch_due_usd: float
    net_award_payable_usd: float
    favored_party: str  # "CHARTERER", "OWNER", "NEUTRAL"
    advisories: List[str]


class CharterpartyArbitrationEngine:
    BEAUFORT_MAX_GOOD_WEATHER = 4
    DOUGLAS_MAX_GOOD_WEATHER = 3

    @classmethod
    def evaluate(cls, inp: CharterpartyDisputeInput) -> CharterpartyDisputeResult:
        advisories: List[str] = []

        # 1. Good Weather Assessment
        is_good_weather = (
            inp.beaufort_scale <= cls.BEAUFORT_MAX_GOOD_WEATHER
            and inp.douglas_sea_state <= cls.DOUGLAS_MAX_GOOD_WEATHER
        )
        weather_excluded = not is_good_weather

        speed_deficit = 0.0
        time_lost_hrs = 0.0
        excess_fuel_mt = 0.0
        tc_claim_usd = 0.0

        if inp.charter_type.upper() == "TIME_CHARTER":
            if weather_excluded:
                advisories.append(
                    f"WEATHER EXCLUSION: Beaufort {inp.beaufort_scale} or Sea State {inp.douglas_sea_state} exceeds good weather threshold. Speed warranty claim barred."
                )
            elif (
                inp.voyage_distance_nm
                and inp.warranted_speed_knots
                and inp.recorded_speed_knots
            ):
                if inp.recorded_speed_knots < inp.warranted_speed_knots:
                    speed_deficit = round(
                        inp.warranted_speed_knots - inp.recorded_speed_knots, 2
                    )
                    expected_time_hrs = inp.voyage_distance_nm / inp.warranted_speed_knots
                    actual_time_hrs = inp.voyage_distance_nm / inp.recorded_speed_knots
                    time_lost_hrs = round(actual_time_hrs - expected_time_hrs, 2)

                    # Loss of time hire claim
                    tc_claim_usd += (time_lost_hrs / 24.0) * inp.daily_hire_or_demurrage_usd

                # Excess fuel calculation
                if inp.warranted_fuel_mt_day and inp.recorded_fuel_mt_day:
                    voyage_days = (inp.voyage_distance_nm / inp.recorded_speed_knots) / 24.0
                    fuel_diff_day = inp.recorded_fuel_mt_day - inp.warranted_fuel_mt_day
                    excess_fuel_mt = round(fuel_diff_day * voyage_days, 2)
                    if excess_fuel_mt > 0.0:
                        tc_claim_usd += excess_fuel_mt * inp.bunker_price_usd_per_mt

        # 2. Voyage Charter Laytime Demurrage / Despatch
        laytime_diff = 0.0
        demurrage_usd = 0.0
        despatch_usd = 0.0

        if inp.charter_type.upper() == "VOYAGE_CHARTER":
            if (
                inp.allowed_laytime_hours is not None
                and inp.actual_laytime_used_hours is not None
            ):
                laytime_diff = round(
                    inp.actual_laytime_used_hours - inp.allowed_laytime_hours, 2
                )
                if laytime_diff > 0:  # Demurrage
                    demurrage_days = laytime_diff / 24.0
                    demurrage_usd = round(
                        demurrage_days * inp.daily_hire_or_demurrage_usd, 2
                    )
                    advisories.append(
                        f"DEMURRAGE: Vessel exceeded laytime by {laytime_diff} hours (${demurrage_usd})"
                    )
                else:  # Despatch (ordinarily 50% demurrage rate)
                    despatch_days = abs(laytime_diff) / 24.0
                    despatch_rate = inp.daily_hire_or_demurrage_usd * 0.5
                    despatch_usd = round(despatch_days * despatch_rate, 2)
                    advisories.append(
                        f"DESPATCH: Vessel saved {abs(laytime_diff)} hours laytime (${despatch_usd})"
                    )

        # 3. Net Financial Award & Favored Party
        net_payable = 0.0
        favored_party = "NEUTRAL"

        if inp.charter_type.upper() == "TIME_CHARTER":
            net_payable = round(tc_claim_usd, 2)
            if net_payable > 0.0:
                favored_party = "CHARTERER"
                advisories.append(f"AWARD: Charterers entitled to recover ${net_payable}")
        else:
            if demurrage_usd > 0.0:
                net_payable = demurrage_usd
                favored_party = "OWNER"
            elif despatch_usd > 0.0:
                net_payable = despatch_usd
                favored_party = "CHARTERER"

        if inp.arbitration_forum == "VMAC":
            advisories.append("DISPUTE: Jurisdiction submitted to Vietnam Maritime Arbitration Center (VMAC Rules).")
        elif "LMAA" in inp.arbitration_forum:
            advisories.append(f"DISPUTE: Reference subject to {inp.arbitration_forum} terms.")

        return CharterpartyDisputeResult(
            fixture_id=inp.fixture_id,
            arbitration_forum=inp.arbitration_forum,
            is_good_weather=is_good_weather,
            weather_excluded=weather_excluded,
            speed_underperformance_knots=speed_deficit,
            time_lost_hours=time_lost_hrs,
            excess_bunker_mt=excess_fuel_mt,
            warranty_claim_usd=round(tc_claim_usd, 2),
            laytime_saved_or_exceeded_hours=laytime_diff,
            demurrage_due_usd=demurrage_usd,
            despatch_due_usd=despatch_usd,
            net_award_payable_usd=net_payable,
            favored_party=favored_party,
            advisories=advisories,
        )
