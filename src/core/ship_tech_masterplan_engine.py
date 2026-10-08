"""Ship Technical, Registration, Dredging & Seaport Masterplan Engine (Phases 195-198).

Implements:
- Phase 195: Ship Classification & Survey Intervals (Vietnam Register VR HSSC, Circular 17/2023/TT-BGTVT).
- Phase 196: Ship Registration & Encumbrance (Decree 171/2016/NĐ-CP & Decree 86/2020/NĐ-CP).
- Phase 197: Maritime Channel Dredging & Dynamic UKC Squat (Decree 58/2017/NĐ-CP, Decree 57/2024/NĐ-CP, PIANC).
- Phase 198: Seaport Masterplan Capacity & Berth Allocation (Decision 1579/QĐ-TTg 2021).

Strict Invariant: Pure Python standard library only (ast zero-external-dependency compliant).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
import math
from typing import List, Optional


# ===========================================================================
# Phase 195: Ship Classification & HSSC Survey Enums & Dataclasses
# ===========================================================================

class SurveyType(str, Enum):
    INITIAL = "INITIAL"
    ANNUAL = "ANNUAL"
    INTERMEDIATE = "INTERMEDIATE"
    RENEWAL = "RENEWAL"
    BOTTOM_DRYDOCK = "BOTTOM_DRYDOCK"


class ClassStatus(str, Enum):
    IN_CLASS = "IN_CLASS"
    SURVEY_DUE = "SURVEY_DUE"
    SURVEY_OVERDUE = "SURVEY_OVERDUE"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"


@dataclass
class ConditionOfClass:
    coc_id: str
    description: str
    due_date_iso: str
    is_rectified: bool = False


@dataclass
class ShipClassificationAudit:
    imo_number: str
    vessel_name: str
    class_society: str
    class_status: ClassStatus
    is_in_class: bool
    current_cycle_year: int
    active_survey_windows: List[str]
    overdue_surveys: List[str]
    outstanding_cocs: List[ConditionOfClass]
    days_to_next_survey: int
    drydock_interval_months: float
    action_required: str


# ===========================================================================
# Phase 196: Ship Registration & Encumbrance Enums & Dataclasses
# ===========================================================================

class RegistryType(str, Enum):
    OFFICIAL = "OFFICIAL"               # Đăng ký chính thức (không thời hạn)
    PROVISIONAL = "PROVISIONAL"         # Đăng ký tạm thời (tối đa 1 năm)
    BAREBOAT_IN = "BAREBOAT_IN"         # Đăng ký tàu thuê mua / thuê trần vào VN
    BAREBOAT_OUT = "BAREBOAT_OUT"       # Tạm hoãn cờ VN cho thuê trần ra nước ngoài


class MortgagePriority(str, Enum):
    FIRST_RANK = "FIRST_RANK"
    SECOND_RANK = "SECOND_RANK"
    UNSECURED = "UNSECURED"


@dataclass
class MaritimeMortgage:
    mortgage_id: str
    mortgagee_name: str
    secured_amount_vnd: float
    registration_date_iso: str
    priority: MortgagePriority


@dataclass
class ShipRegistrationEvaluation:
    registration_no: str
    vessel_name: str
    registry_type: RegistryType
    flag_state: str
    is_valid_vietnamese_flag: bool
    required_dossier_complete: bool
    missing_documents: List[str]
    mortgages: List[MaritimeMortgage]
    total_encumbrance_vnd: float
    is_free_from_arrest: bool
    status_summary: str


# ===========================================================================
# Phase 197: Maritime Channel Dredging & UKC Enums & Dataclasses
# ===========================================================================

class ChannelType(str, Enum):
    CONFINED = "CONFINED"       # Luồng đào hẹp / sông nội địa (Kh = 2.0)
    OPEN_WATER = "OPEN_WATER"   # Vùng biển mở / luồng ngoài (Kh = 1.0)


@dataclass
class DynamicUKCEvaluation:
    channel_name: str
    channel_type: ChannelType
    designed_depth_m: float
    tide_height_m: float
    vessel_draft_m: float
    speed_knots: float
    block_coefficient: float
    calculated_squat_m: float
    wave_swell_allowance_m: float
    sediment_allowance_m: float
    gross_ukc_m: float
    net_ukc_m: float
    safety_margin_m: float
    is_passage_safe: bool
    clearance_verdict: str


# ===========================================================================
# Phase 198: Seaport Masterplan Capacity Enums & Dataclasses
# ===========================================================================

class SeaportCategory(str, Enum):
    SPECIAL = "SPECIAL"         # Cảng biển đặc biệt (Hải Phòng, Bà Rịa - Vũng Tàu)
    CLASS_I = "CLASS_I"         # Cảng biển loại I (Đà Nẵng, Quảng Ninh, Quy Nhơn, HCM, Cần Thơ...)
    CLASS_II = "CLASS_II"       # Cảng biển loại II
    CLASS_III = "CLASS_III"     # Cảng biển loại III (Cảng chuyên dùng)


@dataclass
class SeaportCapacityEvaluation:
    port_name: str
    category: SeaportCategory
    total_berths: int
    annual_actual_throughput_teu: float
    annual_capacity_teu: float
    occupancy_rate_pct: float
    queuing_utilization: float
    expected_queue_delay_hours: float
    is_within_masterplan_limit: bool
    expansion_headroom_pct: float
    recommendation: str


# ===========================================================================
# Core Logic Engines
# ===========================================================================

class ShipClassificationEngine:
    """Evaluates Harmonized System of Survey and Certification (HSSC) compliance under Circular 17/2023/TT-BGTVT."""

    @staticmethod
    def audit_classification(
        imo_number: str,
        vessel_name: str,
        class_society: str,
        certificate_issued_iso: str,
        last_renewal_survey_iso: str,
        last_drydock_survey_iso: str,
        assessment_date_iso: str,
        cocs: Optional[List[ConditionOfClass]] = None,
    ) -> ShipClassificationAudit:
        cocs = cocs or []
        today = date.fromisoformat(assessment_date_iso)
        renewal_base = date.fromisoformat(last_renewal_survey_iso)
        last_drydock = date.fromisoformat(last_drydock_survey_iso)

        # 5-year HSSC cycle
        cycle_days = (today - renewal_base).days
        cycle_years = max(1, min(5, (cycle_days // 365) + 1))

        # Drydock interval check (max 36 months / 3.0 years between 2 drydocks in 5-yr cycle)
        drydock_months = (today - last_drydock).days / 30.4375

        # Survey windows: Annual window is anniversary +/- 90 days
        active_windows: List[str] = []
        overdue_surveys: List[str] = []

        anniversary_this_year = renewal_base.replace(year=renewal_base.year + cycle_years)
        window_start = anniversary_this_year - timedelta(days=90)
        window_end = anniversary_this_year + timedelta(days=90)

        if window_start <= today <= window_end:
            active_windows.append(f"ANNUAL_YEAR_{cycle_years}_OPEN")
        elif today > window_end:
            overdue_surveys.append(f"ANNUAL_YEAR_{cycle_years}_OVERDUE")

        # Intermediate survey due in year 2 or 3 (between 24 and 36 months)
        if 2 <= cycle_years <= 3:
            active_windows.append("INTERMEDIATE_SURVEY_ELIGIBLE")

        # Drydock overdue if exceeds 36.0 months
        if drydock_months > 36.0:
            overdue_surveys.append("BOTTOM_DRYDOCK_OVERDUE")

        # Outstanding CoC overdue check
        overdue_cocs = [c for c in cocs if not c.is_rectified and date.fromisoformat(c.due_date_iso) < today]
        if overdue_cocs:
            overdue_surveys.append(f"{len(overdue_cocs)}_COC_OVERDUE")

        # State determination
        if overdue_surveys:
            class_status = ClassStatus.SUSPENDED if any("COC" in o or "OVERDUE" in o for o in overdue_surveys) else ClassStatus.SURVEY_OVERDUE
            is_in_class = False
            action = f"Vessel classification compromised: {', '.join(overdue_surveys)}. Immediate VR survey required."
        elif active_windows:
            class_status = ClassStatus.SURVEY_DUE
            is_in_class = True
            action = f"Survey window active: {', '.join(active_windows)}. Schedule inspection with VR."
        else:
            class_status = ClassStatus.IN_CLASS
            is_in_class = True
            action = "All statutory class certificates valid. In full compliance."

        days_to_next = max(0, (window_end - today).days)

        return ShipClassificationAudit(
            imo_number=imo_number,
            vessel_name=vessel_name,
            class_society=class_society,
            class_status=class_status,
            is_in_class=is_in_class,
            current_cycle_year=cycle_years,
            active_survey_windows=active_windows,
            overdue_surveys=overdue_surveys,
            outstanding_cocs=[c for c in cocs if not c.is_rectified],
            days_to_next_survey=days_to_next,
            drydock_interval_months=round(drydock_months, 1),
            action_required=action,
        )


class ShipRegistrationEngine:
    """Evaluates Ship Registry, Flag Eligibility, and Maritime Mortgages under Decree 171/2016/NĐ-CP."""

    STATUTORY_DOCS = {
        RegistryType.OFFICIAL: ["BILL_OF_SALE", "BUILDER_CERTIFICATE", "CLASS_CERTIFICATE", "TONNAGE_CERTIFICATE", "DELETION_CERTIFICATE"],
        RegistryType.PROVISIONAL: ["BILL_OF_SALE", "PROVISIONAL_TONNAGE_CERT", "CONSULAR_APPROVAL"],
        RegistryType.BAREBOAT_IN: ["BAREBOAT_CHARTER_CONTRACT", "FLAG_SUSPENSION_CERTIFICATE", "OWNER_CONSENT_LETTER"],
        RegistryType.BAREBOAT_OUT: ["BAREBOAT_CHARTER_CONTRACT", "VN_FLAG_SUSPENSION_APPLICATION", "MORTGAGEE_CONSENT"],
    }

    @staticmethod
    def evaluate_registration(
        registration_no: str,
        vessel_name: str,
        registry_type: RegistryType,
        submitted_documents: List[str],
        mortgages: Optional[List[MaritimeMortgage]] = None,
        is_arrested: bool = False,
    ) -> ShipRegistrationEvaluation:
        mortgages = mortgages or []
        required = ShipRegistrationEngine.STATUTORY_DOCS.get(registry_type, [])
        missing = [doc for doc in required if doc not in submitted_documents]

        total_encumbrance = sum(m.secured_amount_vnd for m in mortgages)
        is_dossier_complete = len(missing) == 0

        # Vietnamese flag validity
        if registry_type == RegistryType.BAREBOAT_OUT:
            is_valid_vn_flag = False  # Temporarily suspended to fly foreign flag
        else:
            is_valid_vn_flag = is_dossier_complete and not is_arrested

        if is_arrested:
            summary = "VESSEL UNDER JUDICIAL ARREST - Registration transfers and voyages prohibited."
        elif not is_dossier_complete:
            summary = f"INCOMPLETE DOSSIER - Missing {len(missing)} required documents for {registry_type.value}."
        else:
            summary = f"VALID REGISTRATION - Fully recorded under Decree 171/2016. Encumbrances: {total_encumbrance:,.0f} VND."

        return ShipRegistrationEvaluation(
            registration_no=registration_no,
            vessel_name=vessel_name,
            registry_type=registry_type,
            flag_state="VIETNAM" if is_valid_vn_flag else "SUSPENDED/FOREIGN",
            is_valid_vietnamese_flag=is_valid_vn_flag,
            required_dossier_complete=is_dossier_complete,
            missing_documents=missing,
            mortgages=mortgages,
            total_encumbrance_vnd=total_encumbrance,
            is_free_from_arrest=not is_arrested,
            status_summary=summary,
        )


class MaritimeDredgingUKCEngine:
    """Calculates Dynamic Under Keel Clearance (UKC) and Squat per PIANC & Decree 58/2017/NĐ-CP."""

    @staticmethod
    def calculate_ukc(
        channel_name: str,
        channel_type: ChannelType,
        designed_depth_m: float,
        tide_height_m: float,
        vessel_draft_m: float,
        speed_knots: float,
        block_coefficient: float = 0.80,
        wave_swell_allowance_m: float = 0.20,
        sediment_allowance_m: float = 0.15,
        safety_margin_m: float = 0.30,
    ) -> DynamicUKCEvaluation:
        # Barrass Squat Formula: Squat = (Cb * V^2 / 100) * Kh
        kh = 2.0 if channel_type == ChannelType.CONFINED else 1.0
        squat = (block_coefficient * (speed_knots ** 2) / 100.0) * kh

        water_depth = designed_depth_m + tide_height_m
        gross_ukc = water_depth - vessel_draft_m
        net_ukc = gross_ukc - (squat + wave_swell_allowance_m + sediment_allowance_m)

        is_safe = net_ukc >= safety_margin_m
        if is_safe:
            verdict = f"SAFE NAVIGATION: Net UKC {net_ukc:.2f}m complies with statutory limit ({safety_margin_m:.2f}m)."
        else:
            verdict = f"GROUNDING RISK: Net UKC {net_ukc:.2f}m violates minimum safety margin ({safety_margin_m:.2f}m). Reduce speed or wait for tide."

        return DynamicUKCEvaluation(
            channel_name=channel_name,
            channel_type=channel_type,
            designed_depth_m=round(designed_depth_m, 2),
            tide_height_m=round(tide_height_m, 2),
            vessel_draft_m=round(vessel_draft_m, 2),
            speed_knots=round(speed_knots, 1),
            block_coefficient=round(block_coefficient, 2),
            calculated_squat_m=round(squat, 2),
            wave_swell_allowance_m=round(wave_swell_allowance_m, 2),
            sediment_allowance_m=round(sediment_allowance_m, 2),
            gross_ukc_m=round(gross_ukc, 2),
            net_ukc_m=round(net_ukc, 2),
            safety_margin_m=round(safety_margin_m, 2),
            is_passage_safe=is_safe,
            clearance_verdict=verdict,
        )


class SeaportMasterplanEngine:
    """Evaluates Seaport Capacity, Berth Utilization and Queuing Delays under Decision 1579/QĐ-TTg."""

    @staticmethod
    def evaluate_port_capacity(
        port_name: str,
        category: SeaportCategory,
        total_berths: int,
        annual_actual_throughput_teu: float,
        crane_productivity_teu_per_hour: float = 30.0,
        operating_days_per_year: int = 350,
        working_hours_per_day: float = 20.0,
        utilization_limit_pct: float = 70.0,
    ) -> SeaportCapacityEvaluation:
        # Theoretical annual capacity: Berths * Days * Hours * Productivity
        annual_capacity = total_berths * operating_days_per_year * working_hours_per_day * crane_productivity_teu_per_hour
        occupancy_rate = (annual_actual_throughput_teu / annual_capacity) * 100.0 if annual_capacity > 0 else 0.0

        # M/M/c queuing model approximation for average waiting time
        rho = occupancy_rate / 100.0
        c = max(1, total_berths)
        if rho < 0.95:
            # Erlang-C approximation for Wq
            wq_hours = (rho ** math.sqrt(2 * (c + 1) - 1)) / (c * (1.0 - rho) * (crane_productivity_teu_per_hour / 20.0))
        else:
            wq_hours = 24.0 * (rho / (1.0 - min(0.99, rho)))

        is_within_limit = occupancy_rate <= utilization_limit_pct
        headroom = max(0.0, 100.0 - occupancy_rate)

        if is_within_limit:
            rec = f"CAPACITY OPTIMAL: Utilization {occupancy_rate:.1f}% within 70% threshold. Queuing delay {wq_hours:.2f}h."
        else:
            rec = f"CONGESTION WARNING: Utilization {occupancy_rate:.1f}% exceeds 70%. Capital expansion recommended per Decision 1579."

        return SeaportCapacityEvaluation(
            port_name=port_name,
            category=category,
            total_berths=total_berths,
            annual_actual_throughput_teu=round(annual_actual_throughput_teu, 0),
            annual_capacity_teu=round(annual_capacity, 0),
            occupancy_rate_pct=round(occupancy_rate, 2),
            queuing_utilization=round(rho, 3),
            expected_queue_delay_hours=round(wq_hours, 2),
            is_within_masterplan_limit=is_within_limit,
            expansion_headroom_pct=round(headroom, 2),
            recommendation=rec,
        )
