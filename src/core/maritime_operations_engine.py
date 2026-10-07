"""
Mekong Maritime Operations, Husbandry, Marine Insurance & Tokyo MOU PSC Suite (Phases 183-186)

Zero-dependency standard library Python domain engine implementing:
1. Phase 183: Maritime Pilotage & Tugboat Assistance Tariffs (Circular 39/2023/TT-BGTVT)
2. Phase 184: Ship Husbandry Agency & Seafarer MLC 2006 Compliance (Decree 160/2016/NĐ-CP)
3. Phase 185: Marine Insurance (H&M / P&I) & Constructive Total Loss (ITC Hulls 83 & Bunkers 2001)
4. Phase 186: Tokyo MOU Port State Control (PSC) NIR Ship Risk Profiling & Code 30 Evaluator
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
import math
from typing import Dict, List, Optional


# =====================================================================
# Phase 183 Enums & Data Structures: Pilotage & Towage
# =====================================================================

class PilotageArea(str, Enum):
    AREA_I = "AREA_I"      # Quang Ninh, Hai Phong (Lach Huyen)
    AREA_II = "AREA_II"    # Da Nang, Quy Nhon, Van Phong
    AREA_III = "AREA_III"  # Cai Mep - Thi Vai, HCM, Dong Nai
    OFFSHORE = "OFFSHORE"  # Offshore Oil & Gas Terminals / SPM


class TugboatClass(str, Enum):
    CLASS_A = "CLASS_A"  # < 1,000 HP
    CLASS_B = "CLASS_B"  # 1,000 - 2,000 HP
    CLASS_C = "CLASS_C"  # 2,001 - 3,000 HP
    CLASS_D = "CLASS_D"  # 3,001 - 4,000 HP
    CLASS_E = "CLASS_E"  # > 4,000 HP


@dataclass
class PilotageTariffResult:
    vessel_gt: float
    billed_gt: float
    distance_nm: float
    pilotage_area: PilotageArea
    is_international: bool
    base_rate_usd_or_vnd: float
    is_night_shift: bool
    is_hazardous_cargo: bool
    is_dead_ship: bool
    detention_hours: float
    detention_fee_usd: float
    surcharge_multiplier: float
    total_pilotage_fee_usd: float
    total_pilotage_fee_vnd: float
    statutory_reference: str = "Circular 39/2023/TT-BGTVT Art. 5-8"


@dataclass
class TugboatServiceItem:
    tug_class: TugboatClass
    quantity: int
    duration_hours: float
    hourly_rate_usd: float
    line_total_usd: float


@dataclass
class TugboatTariffResult:
    vessel_gt: float
    vessel_loa_meters: float
    tugs: List[TugboatServiceItem]
    is_holiday_or_weekend: bool
    is_dead_ship_escort: bool
    surcharge_multiplier: float
    total_tugboat_fee_usd: float
    total_tugboat_fee_vnd: float
    statutory_reference: str = "Circular 39/2023/TT-BGTVT Art. 9-11"


# =====================================================================
# Phase 184 Enums & Data Structures: Ship Agency & MLC 2006
# =====================================================================

class SeafarerRank(str, Enum):
    MASTER = "MASTER"
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    OFFICER = "OFFICER"
    RATING = "RATING"
    CADET = "CADET"


class MLCComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    REST_HOURS_BREACH = "REST_HOURS_BREACH"
    CONTRACT_OVERDUE = "CONTRACT_OVERDUE"
    MANDATORY_REPATRIATION = "MANDATORY_REPATRIATION"


@dataclass
class DailyRestLog:
    log_date: str
    total_rest_hours_24h: float
    longest_continuous_rest_hours: float
    rest_periods_count: int


@dataclass
class MLCSeafarerAssessment:
    seafarer_name: str
    rank: SeafarerRank
    consecutive_sea_days: int
    status: MLCComplianceStatus
    violations: List[str]
    is_repatriation_due: bool
    is_rest_hours_valid: bool
    rolling_7d_rest_hours: float


@dataclass
class ShipAgencyDisbursementResult:
    vessel_name: str
    vessel_gt: float
    port_stay_days: int
    base_agency_fee_usd: float
    extra_day_husbandry_usd: float
    ctm_amount_usd: float
    ctm_commission_usd: float
    crew_changes_count: int
    crew_change_fee_usd: float
    total_agency_disbursement_usd: float
    total_agency_disbursement_vnd: float
    statutory_reference: str = "Decree 160/2016/NĐ-CP & Decree 86/2020/NĐ-CP"


# =====================================================================
# Phase 185 Enums & Data Structures: Marine Insurance & P&I
# =====================================================================

class MarineInsuranceClaimType(str, Enum):
    PARTICULAR_AVERAGE = "PARTICULAR_AVERAGE"
    CONSTRUCTIVE_TOTAL_LOSS = "CONSTRUCTIVE_TOTAL_LOSS"
    ACTUAL_TOTAL_LOSS = "ACTUAL_TOTAL_LOSS"
    PI_POLLUTION_BUNKER = "PI_POLLUTION_BUNKER"


@dataclass
class HullInsuranceClaimResult:
    policy_id: str
    agreed_insured_value_usd: float
    estimated_repair_and_salvage_usd: float
    policy_deductible_usd: float
    loss_ratio_percent: float
    claim_type: MarineInsuranceClaimType
    is_constructive_total_loss: bool
    net_payable_claim_usd: float
    notice_of_abandonment_required: bool
    notice_deadline_days_remaining: Optional[int] = None
    statutory_reference: str = "ITC Hulls 1/10/83 & VN Maritime Code 2015 Art. 326"


@dataclass
class PIPollutionLiabilityResult:
    vessel_gt: float
    oil_spill_tier: str
    liability_limit_sdr: float
    sdr_usd_exchange_rate: float
    liability_limit_usd: float
    liability_limit_vnd: float
    is_compulsory_clc_cert_required: bool
    statutory_reference: str = "Bunkers Convention 2001 & CLC 1992 Protocol"


# =====================================================================
# Phase 186 Enums & Data Structures: Tokyo MOU PSC
# =====================================================================

class PSCShipRiskProfile(str, Enum):
    LRS = "LOW_RISK_SHIP"
    SRS = "STANDARD_RISK_SHIP"
    HRS = "HIGH_RISK_SHIP"


class PSCFlagStateStatus(str, Enum):
    WHITE_LIST = "WHITE_LIST"
    GREY_LIST = "GREY_LIST"
    BLACK_LIST_MEDIUM = "BLACK_LIST_MEDIUM"
    BLACK_LIST_HIGH = "BLACK_LIST_HIGH"
    BLACK_LIST_VERY_HIGH = "BLACK_LIST_VERY_HIGH"


class PSCDetentionAction(str, Enum):
    NO_DEFICIENCIES = "NO_DEFICIENCIES"
    CODE_17_RECTIFY_BEFORE_DEPARTURE = "CODE_17"
    CODE_30_DETENTION = "CODE_30"


@dataclass
class PSCRiskProfileResult:
    vessel_imo: str
    vessel_type: str
    vessel_age_years: int
    flag_status: PSCFlagStateStatus
    ro_performance_low: bool
    company_performance_low: bool
    detentions_last_36m: int
    deficiencies_last_36m: int
    generic_risk_points: int
    historic_risk_points: int
    total_risk_points: int
    risk_profile: PSCShipRiskProfile
    next_inspection_window_months: str
    statutory_reference: str = "Tokyo MOU NIR Guidelines & IMO Res. A.1185(33)"


@dataclass
class PSCDeficiencyAssessment:
    vessel_imo: str
    deficiency_codes: List[str]
    has_solas_fire_or_lifesaving_breach: bool
    has_marpol_annex_i_oily_water_breach: bool
    has_mlc_wage_or_food_breach: bool
    recommended_action: PSCDetentionAction
    is_code_30_detention: bool
    action_notes: str


# =====================================================================
# Core Domain Engine Classes
# =====================================================================

class PilotageTugboatTariffEngine:
    """
    Engine for Vietnam Maritime Pilotage and Tugboat Assistance Tariffs
    governed by Circular 39/2023/TT-BGTVT.
    """

    MIN_GT_INTERNATIONAL = 2000.0
    MIN_GT_DOMESTIC = 500.0
    FX_USD_VND = 25400.0

    PILOTAGE_BASE_RATES_USD = {
        PilotageArea.AREA_I: 0.0034,
        PilotageArea.AREA_II: 0.0032,
        PilotageArea.AREA_III: 0.0031,
        PilotageArea.OFFSHORE: 0.0038,
    }

    PILOTAGE_BASE_RATES_VND = {
        PilotageArea.AREA_I: 45.0,
        PilotageArea.AREA_II: 42.0,
        PilotageArea.AREA_III: 40.0,
        PilotageArea.OFFSHORE: 50.0,
    }

    TUGBOAT_HOURLY_RATES_USD = {
        TugboatClass.CLASS_A: 80.0,
        TugboatClass.CLASS_B: 140.0,
        TugboatClass.CLASS_C: 210.0,
        TugboatClass.CLASS_D: 280.0,
        TugboatClass.CLASS_E: 370.0,
    }

    TUGBOAT_HOURLY_RATES_VND = {
        TugboatClass.CLASS_A: 1800000.0,
        TugboatClass.CLASS_B: 3200000.0,
        TugboatClass.CLASS_C: 4800000.0,
        TugboatClass.CLASS_D: 6500000.0,
        TugboatClass.CLASS_E: 8500000.0,
    }

    @classmethod
    def calculate_pilotage(
        cls,
        vessel_gt: float,
        distance_nm: float,
        area: PilotageArea = PilotageArea.AREA_III,
        is_international: bool = True,
        is_night_shift: bool = False,
        is_hazardous_cargo: bool = False,
        is_dead_ship: bool = False,
        detention_hours: float = 0.0,
        fx_usd_vnd: float = FX_USD_VND,
    ) -> PilotageTariffResult:
        min_gt = cls.MIN_GT_INTERNATIONAL if is_international else cls.MIN_GT_DOMESTIC
        billed_gt = max(float(vessel_gt), min_gt)

        multiplier = 1.0
        if is_dead_ship:
            multiplier *= 2.50
        else:
            if is_night_shift:
                multiplier *= 1.50
            if is_hazardous_cargo:
                multiplier *= 1.10

        detention_hours_billable = max(0.0, float(detention_hours) - 1.0)
        detention_fee_usd = detention_hours_billable * 10.0

        if is_international:
            base_rate = cls.PILOTAGE_BASE_RATES_USD.get(area, 0.0031)
            raw_fee_usd = billed_gt * distance_nm * base_rate * multiplier
            total_usd = raw_fee_usd + detention_fee_usd
            total_vnd = total_usd * fx_usd_vnd
        else:
            base_rate = cls.PILOTAGE_BASE_RATES_VND.get(area, 40.0)
            raw_fee_vnd = billed_gt * distance_nm * base_rate * multiplier
            detention_fee_vnd = detention_fee_usd * fx_usd_vnd
            total_vnd = raw_fee_vnd + detention_fee_vnd
            total_usd = total_vnd / fx_usd_vnd

        return PilotageTariffResult(
            vessel_gt=float(vessel_gt),
            billed_gt=billed_gt,
            distance_nm=float(distance_nm),
            pilotage_area=area,
            is_international=is_international,
            base_rate_usd_or_vnd=base_rate,
            is_night_shift=is_night_shift,
            is_hazardous_cargo=is_hazardous_cargo,
            is_dead_ship=is_dead_ship,
            detention_hours=float(detention_hours),
            detention_fee_usd=round(detention_fee_usd, 2),
            surcharge_multiplier=round(multiplier, 4),
            total_pilotage_fee_usd=round(total_usd, 2),
            total_pilotage_fee_vnd=round(total_vnd, 0),
        )

    @classmethod
    def calculate_tugboat_assistance(
        cls,
        vessel_gt: float,
        vessel_loa_meters: float,
        tugs_request: List[Dict[str, float]],
        is_holiday_or_weekend: bool = False,
        is_dead_ship_escort: bool = False,
        fx_usd_vnd: float = FX_USD_VND,
    ) -> TugboatTariffResult:
        multiplier = 1.0
        if is_holiday_or_weekend:
            multiplier *= 1.30
        if is_dead_ship_escort:
            multiplier *= 1.50

        service_items: List[TugboatServiceItem] = []
        total_usd = 0.0

        for req in tugs_request:
            tug_cls = TugboatClass(req.get("tug_class", TugboatClass.CLASS_C))
            qty = int(req.get("quantity", 1))
            raw_duration = float(req.get("duration_hours", 2.0))
            duration = max(2.0, raw_duration)  # Min 2 hours rule
            hourly_rate = cls.TUGBOAT_HOURLY_RATES_USD[tug_cls]

            line_total = qty * duration * hourly_rate * multiplier
            total_usd += line_total

            service_items.append(
                TugboatServiceItem(
                    tug_class=tug_cls,
                    quantity=qty,
                    duration_hours=duration,
                    hourly_rate_usd=hourly_rate,
                    line_total_usd=round(line_total, 2),
                )
            )

        total_vnd = total_usd * fx_usd_vnd
        return TugboatTariffResult(
            vessel_gt=float(vessel_gt),
            vessel_loa_meters=float(vessel_loa_meters),
            tugs=service_items,
            is_holiday_or_weekend=is_holiday_or_weekend,
            is_dead_ship_escort=is_dead_ship_escort,
            surcharge_multiplier=round(multiplier, 4),
            total_tugboat_fee_usd=round(total_usd, 2),
            total_tugboat_fee_vnd=round(total_vnd, 0),
        )


class ShipAgencyCrewMLCEngine:
    """
    Engine for Ship Husbandry Agency Disbursement and Seafarer MLC 2006 Compliance.
    """

    MAX_SEA_SERVICE_DAYS = 330  # 11 months under MLC 2006 Reg 2.1
    MIN_DAILY_REST_HOURS = 10.0
    MIN_WEEKLY_REST_HOURS = 77.0
    FX_USD_VND = 25400.0

    @classmethod
    def calculate_agency_disbursement(
        cls,
        vessel_name: str,
        vessel_gt: float,
        port_stay_days: int = 2,
        ctm_amount_usd: float = 0.0,
        crew_changes_count: int = 0,
        fx_usd_vnd: float = FX_USD_VND,
    ) -> ShipAgencyDisbursementResult:
        if vessel_gt <= 5000:
            base_fee = 600.0
        elif vessel_gt <= 15000:
            base_fee = 1000.0
        elif vessel_gt <= 35000:
            base_fee = 1500.0
        else:
            base_fee = 2200.0

        extra_days = max(0, port_stay_days - 3)
        extra_husbandry = extra_days * 150.0

        ctm_commission = max(50.0, ctm_amount_usd * 0.015) if ctm_amount_usd > 0 else 0.0
        crew_change_fee = crew_changes_count * 100.0

        total_usd = base_fee + extra_husbandry + ctm_commission + crew_change_fee
        total_vnd = total_usd * fx_usd_vnd

        return ShipAgencyDisbursementResult(
            vessel_name=vessel_name,
            vessel_gt=float(vessel_gt),
            port_stay_days=port_stay_days,
            base_agency_fee_usd=round(base_fee, 2),
            extra_day_husbandry_usd=round(extra_husbandry, 2),
            ctm_amount_usd=round(ctm_amount_usd, 2),
            ctm_commission_usd=round(ctm_commission, 2),
            crew_changes_count=crew_changes_count,
            crew_change_fee_usd=round(crew_change_fee, 2),
            total_agency_disbursement_usd=round(total_usd, 2),
            total_agency_disbursement_vnd=round(total_vnd, 0),
        )

    @classmethod
    def assess_seafarer_mlc(
        cls,
        seafarer_name: str,
        rank: SeafarerRank,
        consecutive_sea_days: int,
        daily_rest_logs: List[DailyRestLog],
    ) -> MLCSeafarerAssessment:
        violations: List[str] = []
        is_repatriation_due = False
        is_rest_hours_valid = True

        if consecutive_sea_days > cls.MAX_SEA_SERVICE_DAYS:
            violations.append(
                f"Exceeded 11-month statutory maximum sea service ({consecutive_sea_days} > {cls.MAX_SEA_SERVICE_DAYS} days). Repatriation required under MLC 2006 Reg. 2.1."
            )
            is_repatriation_due = True

        rolling_7d_rest = sum(log.total_rest_hours_24h for log in daily_rest_logs[-7:])
        if len(daily_rest_logs) >= 7 and rolling_7d_rest < cls.MIN_WEEKLY_REST_HOURS:
            violations.append(
                f"Breach of 7-day minimum rest requirement: {rolling_7d_rest:.1f}h < {cls.MIN_WEEKLY_REST_HOURS}h."
            )
            is_rest_hours_valid = False

        for log in daily_rest_logs:
            if log.total_rest_hours_24h < cls.MIN_DAILY_REST_HOURS:
                violations.append(
                    f"Date {log.log_date}: Daily rest ({log.total_rest_hours_24h:.1f}h) below statutory minimum 10.0h."
                )
                is_rest_hours_valid = False
            if log.rest_periods_count > 2:
                violations.append(
                    f"Date {log.log_date}: Rest divided into {log.rest_periods_count} intervals (max 2 allowed)."
                )
                is_rest_hours_valid = False
            if log.longest_continuous_rest_hours < 6.0:
                violations.append(
                    f"Date {log.log_date}: Longest rest block ({log.longest_continuous_rest_hours:.1f}h) is less than statutory 6.0h."
                )
                is_rest_hours_valid = False

        if is_repatriation_due:
            status = MLCComplianceStatus.MANDATORY_REPATRIATION
        elif not is_rest_hours_valid:
            status = MLCComplianceStatus.REST_HOURS_BREACH
        else:
            status = MLCComplianceStatus.COMPLIANT

        return MLCSeafarerAssessment(
            seafarer_name=seafarer_name,
            rank=rank,
            consecutive_sea_days=consecutive_sea_days,
            status=status,
            violations=violations,
            is_repatriation_due=is_repatriation_due,
            is_rest_hours_valid=is_rest_hours_valid,
            rolling_7d_rest_hours=round(rolling_7d_rest, 1),
        )


class MarineInsuranceRiskEngine:
    """
    Engine for Marine Hull & Machinery (H&M) and P&I Pollution Liabilities.
    """

    DEFAULT_SDR_USD_RATE = 1.34
    DEFAULT_FX_USD_VND = 25400.0

    @classmethod
    def assess_hull_claim(
        cls,
        policy_id: str,
        agreed_insured_value_usd: float,
        estimated_repair_and_salvage_usd: float,
        policy_deductible_usd: float = 50000.0,
        casualty_date_iso: Optional[str] = None,
        assessment_date_iso: Optional[str] = None,
    ) -> HullInsuranceClaimResult:
        loss_ratio = (estimated_repair_and_salvage_usd / agreed_insured_value_usd) * 100.0
        is_ctl = loss_ratio >= 80.0

        days_remaining = None
        if casualty_date_iso and assessment_date_iso:
            try:
                c_date = date.fromisoformat(casualty_date_iso)
                a_date = date.fromisoformat(assessment_date_iso)
                elapsed_days = (a_date - c_date).days
                days_remaining = max(0, 180 - elapsed_days)
            except ValueError:
                pass

        if is_ctl:
            claim_type = MarineInsuranceClaimType.CONSTRUCTIVE_TOTAL_LOSS
            net_claim = agreed_insured_value_usd
            abandonment_req = True
        else:
            claim_type = MarineInsuranceClaimType.PARTICULAR_AVERAGE
            net_claim = max(0.0, estimated_repair_and_salvage_usd - policy_deductible_usd)
            abandonment_req = False

        return HullInsuranceClaimResult(
            policy_id=policy_id,
            agreed_insured_value_usd=float(agreed_insured_value_usd),
            estimated_repair_and_salvage_usd=float(estimated_repair_and_salvage_usd),
            policy_deductible_usd=float(policy_deductible_usd),
            loss_ratio_percent=round(loss_ratio, 2),
            claim_type=claim_type,
            is_constructive_total_loss=is_ctl,
            net_payable_claim_usd=round(net_claim, 2),
            notice_of_abandonment_required=abandonment_req,
            notice_deadline_days_remaining=days_remaining,
        )

    @classmethod
    def calculate_pi_bunker_pollution_limit(
        cls,
        vessel_gt: float,
        sdr_usd_rate: float = DEFAULT_SDR_USD_RATE,
        fx_usd_vnd: float = DEFAULT_FX_USD_VND,
    ) -> PIPollutionLiabilityResult:
        gt = float(vessel_gt)
        if gt <= 2000:
            limit_sdr = 1510000.0
        else:
            tier2_gt = min(gt, 30000.0) - 2000.0
            tier3_gt = max(0.0, gt - 30000.0)
            limit_sdr = 1510000.0 + (tier2_gt * 604.0) + (tier3_gt * 453.0)

        limit_usd = limit_sdr * sdr_usd_rate
        limit_vnd = limit_usd * fx_usd_vnd

        return PIPollutionLiabilityResult(
            vessel_gt=gt,
            oil_spill_tier="TIER_3_MAJOR" if gt > 10000 else "TIER_2_MEDIUM",
            liability_limit_sdr=round(limit_sdr, 2),
            sdr_usd_exchange_rate=sdr_usd_rate,
            liability_limit_usd=round(limit_usd, 2),
            liability_limit_vnd=round(limit_vnd, 0),
            is_compulsory_clc_cert_required=gt >= 1000.0,
        )


class PortStateControlPSCEngine:
    """
    Engine for Tokyo MOU Port State Control (PSC) NIR Ship Risk Profiling
    and Code 30 Detention Risk Assessment.
    """

    HIGH_RISK_SHIP_TYPES = {"OIL_TANKER", "CHEMICAL_TANKER", "GAS_CARRIER", "PASSENGER_SHIP"}

    @classmethod
    def evaluate_ship_risk_profile(
        cls,
        vessel_imo: str,
        vessel_type: str,
        vessel_age_years: int,
        flag_status: PSCFlagStateStatus = PSCFlagStateStatus.WHITE_LIST,
        ro_performance_low: bool = False,
        company_performance_low: bool = False,
        detentions_last_36m: int = 0,
        deficiencies_last_36m: int = 0,
    ) -> PSCRiskProfileResult:
        g_points = 0
        h_points = 0

        v_type_upper = vessel_type.upper()
        if v_type_upper in cls.HIGH_RISK_SHIP_TYPES or (v_type_upper == "BULK_CARRIER" and vessel_age_years > 12):
            g_points += 2
        elif v_type_upper == "GENERAL_CARGO":
            g_points += 1

        if vessel_age_years > 25:
            g_points += 3
        elif vessel_age_years > 20:
            g_points += 2
        elif vessel_age_years > 12:
            g_points += 1

        if flag_status in (PSCFlagStateStatus.BLACK_LIST_HIGH, PSCFlagStateStatus.BLACK_LIST_VERY_HIGH):
            g_points += 3
        elif flag_status == PSCFlagStateStatus.BLACK_LIST_MEDIUM:
            g_points += 2
        elif flag_status == PSCFlagStateStatus.GREY_LIST:
            g_points += 1

        if ro_performance_low:
            g_points += 2
        if company_performance_low:
            g_points += 2

        h_points += detentions_last_36m * 3
        h_points += deficiencies_last_36m // 5

        total_pts = g_points + h_points

        if total_pts >= 6 or detentions_last_36m >= 2:
            profile = PSCShipRiskProfile.HRS
            inspection_window = "2 to 4 months"
        elif total_pts <= 1 and detentions_last_36m == 0:
            profile = PSCShipRiskProfile.LRS
            inspection_window = "9 to 18 months"
        else:
            profile = PSCShipRiskProfile.SRS
            inspection_window = "5 to 8 months"

        return PSCRiskProfileResult(
            vessel_imo=vessel_imo,
            vessel_type=vessel_type,
            vessel_age_years=vessel_age_years,
            flag_status=flag_status,
            ro_performance_low=ro_performance_low,
            company_performance_low=company_performance_low,
            detentions_last_36m=detentions_last_36m,
            deficiencies_last_36m=deficiencies_last_36m,
            generic_risk_points=g_points,
            historic_risk_points=h_points,
            total_risk_points=total_pts,
            risk_profile=profile,
            next_inspection_window_months=inspection_window,
        )

    @classmethod
    def evaluate_deficiencies(
        cls,
        vessel_imo: str,
        deficiency_codes: List[str],
        has_solas_fire_or_lifesaving_breach: bool = False,
        has_marpol_annex_i_oily_water_breach: bool = False,
        has_mlc_wage_or_food_breach: bool = False,
    ) -> PSCDeficiencyAssessment:
        is_detention = (
            has_solas_fire_or_lifesaving_breach
            or has_marpol_annex_i_oily_water_breach
            or has_mlc_wage_or_food_breach
            or len(deficiency_codes) >= 10
        )

        notes = []
        if has_solas_fire_or_lifesaving_breach:
            notes.append("Critical SOLAS Chapter II-2 fire safety / lifesaving appliance inoperable.")
        if has_marpol_annex_i_oily_water_breach:
            notes.append("MARPOL Annex I oily water separator / 15ppm alarm tampered or inoperative.")
        if has_mlc_wage_or_food_breach:
            notes.append("MLC 2006 seafarer wage arrears > 2 months or drinking water/food shortage.")

        if is_detention:
            action = PSCDetentionAction.CODE_30_DETENTION
            action_desc = f"Detention ordered under PSC Code 30. {' '.join(notes)}"
        elif len(deficiency_codes) > 0:
            action = PSCDetentionAction.CODE_17_RECTIFY_BEFORE_DEPARTURE
            action_desc = f"Rectify {len(deficiency_codes)} deficiencies prior to departure (Code 17)."
        else:
            action = PSCDetentionAction.NO_DEFICIENCIES
            action_desc = "Clean inspection without deficiencies."

        return PSCDeficiencyAssessment(
            vessel_imo=vessel_imo,
            deficiency_codes=deficiency_codes,
            has_solas_fire_or_lifesaving_breach=has_solas_fire_or_lifesaving_breach,
            has_marpol_annex_i_oily_water_breach=has_marpol_annex_i_oily_water_breach,
            has_mlc_wage_or_food_breach=has_mlc_wage_or_food_breach,
            recommended_action=action,
            is_code_30_detention=is_detention,
            action_notes=action_desc,
        )
