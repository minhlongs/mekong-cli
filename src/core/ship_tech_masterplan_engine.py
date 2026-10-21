"""Ship Technical, Registration, Dredging & Seaport Masterplan Engine (Phases 195-198).

Strict Invariant: Pure Python standard library only.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
import math
from typing import List, Optional


class SurveyType(str, Enum):
    INITIAL, ANNUAL, INTERMEDIATE, RENEWAL, BOTTOM_DRYDOCK = "INITIAL", "ANNUAL", "INTERMEDIATE", "RENEWAL", "BOTTOM_DRYDOCK"


class ClassStatus(str, Enum):
    IN_CLASS, SURVEY_DUE, SURVEY_OVERDUE, SUSPENDED, WITHDRAWN = "IN_CLASS", "SURVEY_DUE", "SURVEY_OVERDUE", "SUSPENDED", "WITHDRAWN"


class RegistryType(str, Enum):
    OFFICIAL, PROVISIONAL, BAREBOAT_IN, BAREBOAT_OUT = "OFFICIAL", "PROVISIONAL", "BAREBOAT_IN", "BAREBOAT_OUT"


class MortgagePriority(str, Enum):
    FIRST_RANK, SECOND_RANK, UNSECURED = "FIRST_RANK", "SECOND_RANK", "UNSECURED"


class ChannelType(str, Enum):
    CONFINED, OPEN_WATER = "CONFINED", "OPEN_WATER"


class SeaportCategory(str, Enum):
    SPECIAL, CLASS_I, CLASS_II, CLASS_III = "SPECIAL", "CLASS_I", "CLASS_II", "CLASS_III"


@dataclass
class ConditionOfClass:
    coc_id: str; description: str; due_date_iso: str; is_rectified: bool = False  # noqa: E702


@dataclass
class ShipClassificationAudit:
    imo_number: str; vessel_name: str; class_society: str; class_status: ClassStatus; is_in_class: bool  # noqa: E702
    current_cycle_year: int; active_survey_windows: List[str]; overdue_surveys: List[str]  # noqa: E702
    outstanding_cocs: List[ConditionOfClass]; days_to_next_survey: int; drydock_interval_months: float; action_required: str  # noqa: E702


@dataclass
class MaritimeMortgage:
    mortgage_id: str; mortgagee_name: str; secured_amount_vnd: float; registration_date_iso: str; priority: MortgagePriority  # noqa: E702


@dataclass
class ShipRegistrationEvaluation:
    registration_no: str; vessel_name: str; registry_type: RegistryType; flag_state: str; is_valid_vietnamese_flag: bool  # noqa: E702
    required_dossier_complete: bool; missing_documents: List[str]; mortgages: List[MaritimeMortgage]  # noqa: E702
    total_encumbrance_vnd: float; is_free_from_arrest: bool; status_summary: str  # noqa: E702


@dataclass
class DynamicUKCEvaluation:
    channel_name: str; channel_type: ChannelType; designed_depth_m: float; tide_height_m: float; vessel_draft_m: float  # noqa: E702
    speed_knots: float; block_coefficient: float; calculated_squat_m: float; wave_swell_allowance_m: float  # noqa: E702
    sediment_allowance_m: float; gross_ukc_m: float; net_ukc_m: float; safety_margin_m: float; is_passage_safe: bool; clearance_verdict: str  # noqa: E702


@dataclass
class SeaportCapacityEvaluation:
    port_name: str; category: SeaportCategory; total_berths: int; annual_actual_throughput_teu: float; annual_capacity_teu: float  # noqa: E702
    occupancy_rate_pct: float; queuing_utilization: float; expected_queue_delay_hours: float  # noqa: E702
    is_within_masterplan_limit: bool; expansion_headroom_pct: float; recommendation: str  # noqa: E702


class ShipClassificationEngine:
    @staticmethod
    def audit_classification(
        imo_number: str, vessel_name: str, class_society: str, certificate_issued_iso: str,
        last_renewal_survey_iso: str, last_drydock_survey_iso: str, assessment_date_iso: str, cocs: Optional[List[ConditionOfClass]] = None,
    ) -> ShipClassificationAudit:
        cocs = cocs or []
        today, renewal_base, last_drydock = date.fromisoformat(assessment_date_iso), date.fromisoformat(last_renewal_survey_iso), date.fromisoformat(last_drydock_survey_iso)
        cycle_years = max(1, min(5, ((today - renewal_base).days // 365) + 1))
        drydock_months = (today - last_drydock).days / 30.4375
        active_windows, overdue_surveys = [], []
        anniv = renewal_base.replace(year=renewal_base.year + cycle_years)
        window_start, window_end = anniv - timedelta(days=90), anniv + timedelta(days=90)
        if window_start <= today <= window_end:
            active_windows.append(f"ANNUAL_YEAR_{cycle_years}_OPEN")
        elif today > window_end:
            overdue_surveys.append(f"ANNUAL_YEAR_{cycle_years}_OVERDUE")
        if 2 <= cycle_years <= 3:
            active_windows.append("INTERMEDIATE_SURVEY_ELIGIBLE")
        if drydock_months > 36.0:
            overdue_surveys.append("BOTTOM_DRYDOCK_OVERDUE")
        if overdue_cocs := [c for c in cocs if not c.is_rectified and date.fromisoformat(c.due_date_iso) < today]:
            overdue_surveys.append(f"{len(overdue_cocs)}_COC_OVERDUE")

        if overdue_surveys:
            class_status = ClassStatus.SUSPENDED if any("COC" in o or "OVERDUE" in o for o in overdue_surveys) else ClassStatus.SURVEY_OVERDUE
            is_in_class, action = False, f"Vessel classification compromised: {', '.join(overdue_surveys)}. Immediate VR survey required."
        elif active_windows:
            class_status, is_in_class, action = ClassStatus.SURVEY_DUE, True, f"Survey window active: {', '.join(active_windows)}. Schedule inspection with VR."
        else:
            class_status, is_in_class, action = ClassStatus.IN_CLASS, True, "All statutory class certificates valid. In full compliance."
        return ShipClassificationAudit(imo_number, vessel_name, class_society, class_status, is_in_class, cycle_years, active_windows, overdue_surveys, [c for c in cocs if not c.is_rectified], max(0, (window_end - today).days), round(drydock_months, 1), action)


class ShipRegistrationEngine:
    STATUTORY_DOCS = {
        RegistryType.OFFICIAL: ["BILL_OF_SALE", "BUILDER_CERTIFICATE", "CLASS_CERTIFICATE", "TONNAGE_CERTIFICATE", "DELETION_CERTIFICATE"],
        RegistryType.PROVISIONAL: ["BILL_OF_SALE", "PROVISIONAL_TONNAGE_CERT", "CONSULAR_APPROVAL"],
        RegistryType.BAREBOAT_IN: ["BAREBOAT_CHARTER_CONTRACT", "FLAG_SUSPENSION_CERTIFICATE", "OWNER_CONSENT_LETTER"],
        RegistryType.BAREBOAT_OUT: ["BAREBOAT_CHARTER_CONTRACT", "VN_FLAG_SUSPENSION_APPLICATION", "MORTGAGEE_CONSENT"],
    }

    @staticmethod
    def evaluate_registration(registration_no: str, vessel_name: str, registry_type: RegistryType, submitted_documents: List[str], mortgages: Optional[List[MaritimeMortgage]] = None, is_arrested: bool = False) -> ShipRegistrationEvaluation:
        mortgages = mortgages or []
        missing = [doc for doc in ShipRegistrationEngine.STATUTORY_DOCS.get(registry_type, []) if doc not in submitted_documents]
        total_encumbrance, complete = sum(m.secured_amount_vnd for m in mortgages), len(missing) == 0
        valid_flag = False if registry_type == RegistryType.BAREBOAT_OUT else (complete and not is_arrested)
        summary = "VESSEL UNDER JUDICIAL ARREST - Registration transfers and voyages prohibited." if is_arrested else f"INCOMPLETE DOSSIER - Missing {len(missing)} required documents for {registry_type.value}." if not complete else f"VALID REGISTRATION - Fully recorded under Decree 171/2016. Encumbrances: {total_encumbrance:,.0f} VND."
        return ShipRegistrationEvaluation(registration_no, vessel_name, registry_type, "VIETNAM" if valid_flag else "SUSPENDED/FOREIGN", valid_flag, complete, missing, mortgages, total_encumbrance, not is_arrested, summary)


class MaritimeDredgingUKCEngine:
    @staticmethod
    def calculate_ukc(channel_name: str, channel_type: ChannelType, designed_depth_m: float, tide_height_m: float, vessel_draft_m: float, speed_knots: float, block_coefficient: float = 0.80, wave_swell_allowance_m: float = 0.20, sediment_allowance_m: float = 0.15, safety_margin_m: float = 0.30) -> DynamicUKCEvaluation:
        squat = (block_coefficient * (speed_knots ** 2) / 100.0) * (2.0 if channel_type == ChannelType.CONFINED else 1.0)
        gross_ukc = (designed_depth_m + tide_height_m) - vessel_draft_m
        net_ukc = gross_ukc - (squat + wave_swell_allowance_m + sediment_allowance_m)
        is_safe = net_ukc >= safety_margin_m
        verdict = f"SAFE NAVIGATION: Net UKC {net_ukc:.2f}m complies with statutory limit ({safety_margin_m:.2f}m)." if is_safe else f"GROUNDING RISK: Net UKC {net_ukc:.2f}m violates minimum safety margin ({safety_margin_m:.2f}m). Reduce speed or wait for tide."
        return DynamicUKCEvaluation(channel_name, channel_type, round(designed_depth_m, 2), round(tide_height_m, 2), round(vessel_draft_m, 2), round(speed_knots, 1), round(block_coefficient, 2), round(squat, 2), round(wave_swell_allowance_m, 2), round(sediment_allowance_m, 2), round(gross_ukc, 2), round(net_ukc, 2), round(safety_margin_m, 2), is_safe, verdict)


class SeaportMasterplanEngine:
    @staticmethod
    def evaluate_port_capacity(port_name: str, category: SeaportCategory, total_berths: int, annual_actual_throughput_teu: float, crane_productivity_teu_per_hour: float = 30.0, operating_days_per_year: int = 350, working_hours_per_day: float = 20.0, utilization_limit_pct: float = 70.0) -> SeaportCapacityEvaluation:
        annual_capacity = total_berths * operating_days_per_year * working_hours_per_day * crane_productivity_teu_per_hour
        occupancy_rate = (annual_actual_throughput_teu / annual_capacity) * 100.0 if annual_capacity > 0 else 0.0
        rho, c = occupancy_rate / 100.0, max(1, total_berths)
        wq_hours = (rho ** math.sqrt(2 * (c + 1) - 1)) / (c * (1.0 - rho) * (crane_productivity_teu_per_hour / 20.0)) if rho < 0.95 else 24.0 * (rho / (1.0 - min(0.99, rho)))
        within = occupancy_rate <= utilization_limit_pct
        rec = f"CAPACITY OPTIMAL: Utilization {occupancy_rate:.1f}% within 70% threshold. Queuing delay {wq_hours:.2f}h." if within else f"CONGESTION WARNING: Utilization {occupancy_rate:.1f}% exceeds 70%. Capital expansion recommended per Decision 1579."
        return SeaportCapacityEvaluation(port_name, category, total_berths, round(annual_actual_throughput_teu, 0), round(annual_capacity, 0), round(occupancy_rate, 2), round(rho, 3), round(wq_hours, 2), within, round(max(0.0, 100.0 - occupancy_rate), 2), rec)
