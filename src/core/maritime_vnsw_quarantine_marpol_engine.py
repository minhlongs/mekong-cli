"""Core Statutory Engines for Maritime Single Window, Seafarer Border Control, Health Quarantine & MARPOL (Phases 191-194).

Statutory References:
- Phase 191: Nghị định 58/2017/NĐ-CP, Nghị định 76/2021/NĐ-CP, Thông tư 261/2016/TT-BTC & Thông tư 12/2024/TT-BGTVT (VNSW & Port Clearance).
- Phase 192: Luật Xuất nhập cảnh 2014/2019/2023, Nghị định 77/2017/NĐ-CP, Thông tư 20/2023/TT-BGTVT & STCW 78/2010 Manila Amendments (Seafarer Manning & Shore Pass).
- Phase 193: Luật Phòng chống bệnh truyền nhiễm 2007, Nghị định 89/2018/NĐ-CP & Điều lệ Y tế Quốc tế IHR 2005 (Maritime Health Quarantine & Free Pratique).
- Phase 194: Luật Bảo vệ môi trường 2020, Nghị định 08/2022/NĐ-CP & MARPOL 73/78 Annexes I-VI (Marine Environmental Protection & PRF Waste).

Zero External Dependencies: Only Python Standard Library.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from enum import Enum
import hashlib
import json
import math
from typing import Dict, List, Optional, Tuple, Any


# ===========================================================================
# Phase 191: Maritime Single Window (VNSW) & Port Clearance Enums & Dataclasses
# ===========================================================================


class VNSWNotificationType(str, Enum):
    ARRIVAL_NOTICE_24H = "ARRIVAL_NOTICE_24H"
    ARRIVAL_CONFIRMATION_2H = "ARRIVAL_CONFIRMATION_2H"
    DEPARTURE_NOTICE_2H = "DEPARTURE_NOTICE_2H"
    TRANSIT_NOTICE_24H = "TRANSIT_NOTICE_24H"


class VesselVoyageType(str, Enum):
    INTERNATIONAL = "INTERNATIONAL"
    DOMESTIC = "DOMESTIC"


class ClearanceStatus(str, Enum):
    CLEARED = "CLEARED"
    CONDITIONAL_CLEARANCE = "CONDITIONAL_CLEARANCE"
    DETAINED_OR_REJECTED = "DETAINED_OR_REJECTED"


@dataclass
class PortClearanceResult:
    imo_number: str
    vessel_name: str
    call_sign: str
    voyage_type: VesselVoyageType
    gross_tonnage: float
    clearance_permit_no: str
    qr_verification_payload: str
    tonnage_dues_vnd: float
    maritime_safety_fee_vnd: float
    port_clearance_fee_vnd: float
    total_statutory_dues_vnd: float
    is_notification_timely: bool
    is_dossier_complete: bool
    status: ClearanceStatus
    missing_declarations: List[str] = field(default_factory=list)
    action_notes: List[str] = field(default_factory=list)


# ===========================================================================
# Phase 192: Seafarer Manning & Border Immigration Enums & Dataclasses
# ===========================================================================


class SeafarerRank(str, Enum):
    MASTER = "MASTER"
    CHIEF_MATE = "CHIEF_MATE"
    OFFICER_OF_WATCH_NAV = "OFFICER_OF_WATCH_NAV"
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    SECOND_ENGINEER = "SECOND_ENGINEER"
    OFFICER_OF_WATCH_ENG = "OFFICER_OF_WATCH_ENG"
    RATING_ABLE_SEAMAN = "RATING_ABLE_SEAMAN"
    RATING_OILER = "RATING_OILER"
    CHIEF_COOK = "CHIEF_COOK"


class ImmigrationPassType(str, Enum):
    SHORE_PASS_PERMITTED = "SHORE_PASS_PERMITTED"
    TRANSIT_VISA_REQUIRED = "TRANSIT_VISA_REQUIRED"
    BORDER_RESTRICTED = "BORDER_RESTRICTED"


@dataclass
class SeafarerCrewMember:
    full_name: str
    nationality: str
    passport_number: str
    seaman_book_number: str
    rank: SeafarerRank
    stcw_cert_valid_until_iso: str
    passport_valid_until_iso: str
    daily_rest_hours: float
    weekly_rest_hours: float


@dataclass
class CrewManningImmigrationResult:
    vessel_name: str
    total_crew_count: int
    is_safe_manning_compliant: bool
    is_stcw_rest_compliant: bool
    shore_pass_granted_count: int
    shore_pass_denied_count: int
    immigration_status: ImmigrationPassType
    deficiencies: List[str] = field(default_factory=list)
    crew_pass_details: List[Dict[str, Any]] = field(default_factory=list)


# ===========================================================================
# Phase 193: Maritime Health Quarantine Enums & Dataclasses
# ===========================================================================


class HealthQuarantineStatus(str, Enum):
    FREE_PRATIQUE_GRANTED = "FREE_PRATIQUE_GRANTED"
    RADIO_PRATIQUE_GRANTED = "RADIO_PRATIQUE_GRANTED"
    QUARANTINE_ANCHORAGE_REQUIRED = "QUARANTINE_ANCHORAGE_REQUIRED"
    ISOLATION_AND_DISINFECTION = "ISOLATION_AND_DISINFECTION"


@dataclass
class MaritimeHealthQuarantineResult:
    vessel_name: str
    sscec_valid_until_iso: str
    is_sscec_valid: bool
    communicable_cases_detected: int
    epidemiological_risk_score: float
    quarantine_status: HealthQuarantineStatus
    yellow_flag_required: bool
    free_pratique_certificate_no: Optional[str]
    mandatory_health_measures: List[str] = field(default_factory=list)


# ===========================================================================
# Phase 194: MARPOL & Port Reception Facilities Enums & Dataclasses
# ===========================================================================


class MARPOLAnnex(str, Enum):
    ANNEX_I_OIL = "ANNEX_I_OIL"
    ANNEX_IV_SEWAGE = "ANNEX_IV_SEWAGE"
    ANNEX_V_GARBAGE = "ANNEX_V_GARBAGE"
    ANNEX_VI_AIR_SOX = "ANNEX_VI_AIR_SOX"


@dataclass
class MARPOLComplianceResult:
    vessel_name: str
    ows_bilge_oil_content_ppm: float
    is_ows_compliant: bool
    fuel_sulfur_content_pct: float
    is_fuel_sulfur_compliant: bool
    prf_waste_delivery_receipt_no: Optional[str]
    sludge_delivered_m3: float
    garbage_delivered_m3: float
    is_marpol_fully_compliant: bool
    violations: List[str] = field(default_factory=list)
    environmental_levy_vnd: float = 0.0


# ===========================================================================
# Core Statutory Calculation Engines
# ===========================================================================


class MaritimeSingleWindowEngine:
    """Phase 191: Vietnam National Maritime Single Window (VNSW) Port Clearance Engine.

    Statutory Rates (Circular 261/2016/TT-BTC & Circular 12/2024/TT-BGTVT):
    - International Tonnage Dues: $0.034 / GT per entry/exit (Approx 850 VND / GT).
    - Maritime Safety Fee: ~$0.045 / GT (Approx 1,125 VND / GT).
    - Port Clearance Fee: 100,000 VND flat per voyage for international / 50,000 VND domestic.
    - USD/VND Fixed Exchange Benchmark: 25,000 VND / USD.
    """

    EXCHANGE_RATE_VND_PER_USD = 25000.0
    TONNAGE_DUE_USD_PER_GT = 0.034
    MARITIME_SAFETY_USD_PER_GT = 0.045
    PORT_CLEARANCE_FEE_INTL_VND = 100000.0
    PORT_CLEARANCE_FEE_DOM_VND = 50000.0

    @classmethod
    def evaluate_port_clearance(
        cls,
        imo_number: str,
        vessel_name: str,
        call_sign: str,
        voyage_type: VesselVoyageType,
        gross_tonnage: float,
        notification_type: VNSWNotificationType,
        hours_before_event: float,
        submitted_forms: List[str],
    ) -> PortClearanceResult:
        """Evaluate VNSW notification timeline, document checklist, and statutory dues."""
        # 1. Timeline Verification
        is_timely = True
        missing_declarations: List[str] = []
        action_notes: List[str] = []

        if notification_type == VNSWNotificationType.ARRIVAL_NOTICE_24H and hours_before_event < 24.0:
            is_timely = False
            action_notes.append(f"Arrival notice sent {hours_before_event:.1f}h before arrival (Minimum required: 24h).")
        elif notification_type in (VNSWNotificationType.ARRIVAL_CONFIRMATION_2H, VNSWNotificationType.DEPARTURE_NOTICE_2H) and hours_before_event < 2.0:
            is_timely = False
            action_notes.append(f"Notification sent {hours_before_event:.1f}h before event (Minimum required: 2h).")

        # 2. Mandatory Statutory FAL Forms Check
        mandatory_forms = {"FAL_1", "FAL_2", "FAL_3", "FAL_4", "FAL_5", "FAL_6", "FAL_7"}
        submitted_set = {f.upper().replace("-", "_").replace(" ", "_") for f in submitted_forms}

        for req in sorted(mandatory_forms):
            if req not in submitted_set and not (req == "FAL_6" and "NO_PASSENGERS" in submitted_set):
                missing_declarations.append(req)

        is_dossier_complete = len(missing_declarations) == 0

        # 3. Statutory Dues & Fee Math
        if voyage_type == VesselVoyageType.INTERNATIONAL:
            tonnage_dues_vnd = round(gross_tonnage * cls.TONNAGE_DUE_USD_PER_GT * cls.EXCHANGE_RATE_VND_PER_USD, 0)
            safety_fee_vnd = round(gross_tonnage * cls.MARITIME_SAFETY_USD_PER_GT * cls.EXCHANGE_RATE_VND_PER_USD, 0)
            clearance_fee_vnd = cls.PORT_CLEARANCE_FEE_INTL_VND
        else:
            tonnage_dues_vnd = round(gross_tonnage * 400.0, 0)
            safety_fee_vnd = round(gross_tonnage * 600.0, 0)
            clearance_fee_vnd = cls.PORT_CLEARANCE_FEE_DOM_VND

        total_dues_vnd = tonnage_dues_vnd + safety_fee_vnd + clearance_fee_vnd

        # 4. Clearance Status Resolution
        if is_timely and is_dossier_complete:
            status = ClearanceStatus.CLEARED
            action_notes.append("Electronic Port Clearance (e-PC) granted under Decree 58/2017/NĐ-CP.")
        elif not is_dossier_complete:
            status = ClearanceStatus.DETAINED_OR_REJECTED
            action_notes.append(f"Dossier incomplete: Missing {', '.join(missing_declarations)}.")
        else:
            status = ClearanceStatus.CONDITIONAL_CLEARANCE
            action_notes.append("Conditional clearance granted pending late-notification administrative review.")

        # 5. Cryptographic QR Verification Payload
        permit_seed = f"{imo_number}:{call_sign}:{gross_tonnage}:{status.value}:{datetime.now(timezone.utc).date()}"
        permit_hash = hashlib.sha256(permit_seed.encode("utf-8")).hexdigest()[:16].upper()
        clearance_permit_no = f"VN-VNSW-{datetime.now(timezone.utc).year}-{permit_hash}"
        qr_payload = f"https://vnsw.gov.vn/verify?permit={clearance_permit_no}&imo={imo_number}&status={status.value}"

        return PortClearanceResult(
            imo_number=imo_number,
            vessel_name=vessel_name,
            call_sign=call_sign,
            voyage_type=voyage_type,
            gross_tonnage=gross_tonnage,
            clearance_permit_no=clearance_permit_no,
            qr_verification_payload=qr_payload,
            tonnage_dues_vnd=tonnage_dues_vnd,
            maritime_safety_fee_vnd=safety_fee_vnd,
            port_clearance_fee_vnd=clearance_fee_vnd,
            total_statutory_dues_vnd=total_dues_vnd,
            is_notification_timely=is_timely,
            is_dossier_complete=is_dossier_complete,
            status=status,
            missing_declarations=missing_declarations,
            action_notes=action_notes,
        )


class SeafarerImmigrationEngine:
    """Phase 192: Seafarer Manning, STCW Certification & Immigration Border Control.

    Statutory Framework:
    - Minimum Safe Manning Document (MSMD) required roles: MASTER, CHIEF_MATE, CHIEF_ENGINEER, SECOND_ENGINEER, RATING_ABLE_SEAMAN.
    - STCW 78/2010 Rest Hours: Minimum 10h in any 24h period, Minimum 77h in any 7-day period.
    - Decree 77/2017/NĐ-CP: Shore Pass (Thẻ đi bờ) granted to valid seafarers during vessel port stay.
    """

    MANDATORY_RANKS = {
        SeafarerRank.MASTER,
        SeafarerRank.CHIEF_MATE,
        SeafarerRank.CHIEF_ENGINEER,
        SeafarerRank.SECOND_ENGINEER,
    }

    @classmethod
    def audit_crew_and_immigration(
        cls,
        vessel_name: str,
        crew_list: List[SeafarerCrewMember],
        assessment_date_iso: Optional[str] = None,
    ) -> CrewManningImmigrationResult:
        """Audit minimum safe manning, STCW rest hours, and issue Shore Passes."""
        ref_date = date.fromisoformat(assessment_date_iso) if assessment_date_iso else datetime.now(timezone.utc).date()

        ranks_present = {c.rank for c in crew_list}
        missing_roles = cls.MANDATORY_RANKS - ranks_present
        is_safe_manning_compliant = len(missing_roles) == 0

        deficiencies: List[str] = []
        if not is_safe_manning_compliant:
            deficiencies.append(f"Safe Manning Deficient: Missing critical ranks {[r.value for r in missing_roles]}.")

        stcw_rest_compliant = True
        shore_pass_granted = 0
        shore_pass_denied = 0
        pass_details: List[Dict[str, Any]] = []

        for crew in crew_list:
            # 1. Rest Hours Check
            if crew.daily_rest_hours < 10.0 or crew.weekly_rest_hours < 77.0:
                stcw_rest_compliant = False
                deficiencies.append(f"STCW Rest Hour Breach for {crew.full_name} ({crew.rank.value}): Daily {crew.daily_rest_hours}h (<10h) or Weekly {crew.weekly_rest_hours}h (<77h).")

            # 2. Document Validity Check
            stcw_expiry = date.fromisoformat(crew.stcw_cert_valid_until_iso)
            pass_expiry = date.fromisoformat(crew.passport_valid_until_iso)

            is_valid_docs = (stcw_expiry >= ref_date) and (pass_expiry >= ref_date)
            if is_valid_docs:
                shore_pass_granted += 1
                pass_status = "GRANTED_SHORE_PASS"
                notes = "Valid Seaman Book & Passport under Decree 77/2017/NĐ-CP."
            else:
                shore_pass_denied += 1
                pass_status = "DENIED"
                notes = "Expired Travel/STCW Document."
                deficiencies.append(f"Invalid document for {crew.full_name}: STCW expiry {crew.stcw_cert_valid_until_iso}, Passport expiry {crew.passport_valid_until_iso}.")

            pass_details.append({
                "name": crew.full_name,
                "rank": crew.rank.value,
                "nationality": crew.nationality,
                "status": pass_status,
                "notes": notes,
            })

        if shore_pass_denied == 0 and is_safe_manning_compliant:
            immigration_status = ImmigrationPassType.SHORE_PASS_PERMITTED
        elif shore_pass_denied > 0:
            immigration_status = ImmigrationPassType.BORDER_RESTRICTED
        else:
            immigration_status = ImmigrationPassType.TRANSIT_VISA_REQUIRED

        return CrewManningImmigrationResult(
            vessel_name=vessel_name,
            total_crew_count=len(crew_list),
            is_safe_manning_compliant=is_safe_manning_compliant,
            is_stcw_rest_compliant=stcw_rest_compliant,
            shore_pass_granted_count=shore_pass_granted,
            shore_pass_denied_count=shore_pass_denied,
            immigration_status=immigration_status,
            deficiencies=deficiencies,
            crew_pass_details=pass_details,
        )


class MaritimeHealthQuarantineEngine:
    """Phase 193: Maritime International Health Quarantine & Epidemic Surveillance.

    Statutory Framework:
    - IHR 2005 Annex 9 / Decree 89/2018/NĐ-CP.
    - Ship Sanitation Control Exemption Certificate (SSCEC): 6 months validity.
    - Risk Score: ERS = (Communicable_Cases * 3.0) + (Expired_SSCEC ? 2.0 : 0.0) + (High_Risk_Port ? 2.0 : 0.0).
    - If ERS >= 3.0 or Communicable_Cases > 0: Quarantine Anchorage Required (Yellow Flag 'Q' hoised).
    """

    @classmethod
    def evaluate_health_quarantine(
        cls,
        vessel_name: str,
        sscec_valid_until_iso: str,
        communicable_cases_detected: int = 0,
        has_visited_endemic_yellow_fever_port: bool = False,
        assessment_date_iso: Optional[str] = None,
    ) -> MaritimeHealthQuarantineResult:
        """Evaluate Maritime Declaration of Health, SSCEC validity, and Free Pratique."""
        ref_date = date.fromisoformat(assessment_date_iso) if assessment_date_iso else datetime.now(timezone.utc).date()
        sscec_exp = date.fromisoformat(sscec_valid_until_iso)
        is_sscec_valid = sscec_exp >= ref_date

        # Calculate Epidemiological Risk Score (ERS)
        ers = (communicable_cases_detected * 3.0) + (0.0 if is_sscec_valid else 2.5) + (2.0 if has_visited_endemic_yellow_fever_port else 0.0)

        mandatory_measures: List[str] = []
        free_pratique_no: Optional[str] = None

        if communicable_cases_detected > 0:
            quarantine_status = HealthQuarantineStatus.ISOLATION_AND_DISINFECTION
            yellow_flag = True
            mandatory_measures.append(f"Isolate {communicable_cases_detected} infected personnel; anchor at Quarantine Station.")
            mandatory_measures.append("Perform full chemical vector fumigation & medical disinsection under Decree 89/2018/NĐ-CP.")
        elif not is_sscec_valid or ers >= 3.0:
            quarantine_status = HealthQuarantineStatus.QUARANTINE_ANCHORAGE_REQUIRED
            yellow_flag = True
            mandatory_measures.append("SSCEC expired or high endemic risk: Port Health Inspector physical boarding required.")
        else:
            quarantine_status = HealthQuarantineStatus.FREE_PRATIQUE_GRANTED
            yellow_flag = False
            cert_hash = hashlib.sha256(f"{vessel_name}:{sscec_valid_until_iso}".encode("utf-8")).hexdigest()[:12].upper()
            free_pratique_no = f"VN-MDH-FP-{datetime.now(timezone.utc).year}-{cert_hash}"
            mandatory_measures.append("Radio Free Pratique granted. Vessel permitted to berth without physical quarantine delay.")

        return MaritimeHealthQuarantineResult(
            vessel_name=vessel_name,
            sscec_valid_until_iso=sscec_valid_until_iso,
            is_sscec_valid=is_sscec_valid,
            communicable_cases_detected=communicable_cases_detected,
            epidemiological_risk_score=round(ers, 2),
            quarantine_status=quarantine_status,
            yellow_flag_required=yellow_flag,
            free_pratique_certificate_no=free_pratique_no,
            mandatory_health_measures=mandatory_measures,
        )


class MARPOLPortReceptionEngine:
    """Phase 194: MARPOL 73/78 Environmental Compliance & Port Reception Facilities (PRF).

    Statutory Limits:
    - Annex I (Oil): OWS 15 ppm bilge oil alarm limit. Discharge > 15 ppm prohibited.
    - Annex VI (Air): Global fuel sulfur cap <= 0.50% m/m (0.10% in Emission Control Areas ECA).
    - Decree 08/2022/NĐ-CP: Mandatory delivery of hazardous ship-generated waste to certified PRF.
    """

    MAX_OWS_OIL_PPM = 15.0
    GLOBAL_SULFUR_CAP_PCT = 0.50

    @classmethod
    def evaluate_environmental_compliance(
        cls,
        vessel_name: str,
        ows_bilge_oil_content_ppm: float,
        fuel_sulfur_content_pct: float,
        sludge_delivered_m3: float = 0.0,
        garbage_delivered_m3: float = 0.0,
    ) -> MARPOLComplianceResult:
        """Evaluate OWS bilge separator, low-sulfur fuel, and PRF waste discharge."""
        violations: List[str] = []
        is_ows_compliant = ows_bilge_oil_content_ppm <= cls.MAX_OWS_OIL_PPM
        if not is_ows_compliant:
            violations.append(f"MARPOL Annex I Breach: OWS bilge oil content {ows_bilge_oil_content_ppm} ppm exceeds statutory limit of 15.0 ppm.")

        is_fuel_compliant = fuel_sulfur_content_pct <= cls.GLOBAL_SULFUR_CAP_PCT
        if not is_fuel_compliant:
            violations.append(f"MARPOL Annex VI Breach: Fuel sulfur content {fuel_sulfur_content_pct}% exceeds global cap of 0.50%.")

        is_compliant = is_ows_compliant and is_fuel_compliant
        prf_receipt_no = None
        levy_vnd = 0.0

        if sludge_delivered_m3 > 0.0 or garbage_delivered_m3 > 0.0:
            rec_hash = hashlib.sha256(f"{vessel_name}:{sludge_delivered_m3}:{garbage_delivered_m3}".encode("utf-8")).hexdigest()[:10].upper()
            prf_receipt_no = f"VN-PRF-WDR-{rec_hash}"
            # Standard PRF disposal tariff: 1,500,000 VND / m3 sludge + 400,000 VND / m3 garbage
            levy_vnd = (sludge_delivered_m3 * 1500000.0) + (garbage_delivered_m3 * 400000.0)

        return MARPOLComplianceResult(
            vessel_name=vessel_name,
            ows_bilge_oil_content_ppm=ows_bilge_oil_content_ppm,
            is_ows_compliant=is_ows_compliant,
            fuel_sulfur_content_pct=fuel_sulfur_content_pct,
            is_fuel_sulfur_compliant=is_fuel_compliant,
            prf_waste_delivery_receipt_no=prf_receipt_no,
            sludge_delivered_m3=sludge_delivered_m3,
            garbage_delivered_m3=garbage_delivered_m3,
            is_marpol_fully_compliant=is_compliant,
            violations=violations,
            environmental_levy_vnd=round(levy_vnd, 0),
        )
