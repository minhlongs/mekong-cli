"""
Maritime Sewage MARPOL IV, Seafarer Medical Fitness STCW/MLC,
Port Stevedoring Tariffs & Customs Bonded Warehouse Engine.
Phases 291-294.

Statutory References:
- Phase 291: MARPOL Annex IV Regs 9-11, IMO Res. MEPC.227(64), VN Maritime Code 2015 Arts 107-111, Circular 41/2020/TT-BGTVT.
- Phase 292: STCW 2010 Manila Reg. I/9, MLC 2006 Standard A1.2, Circular 22/2017/TT-BYT, Circular 23/2017/TT-BGTVT.
- Phase 293: Circular 39/2023/TT-BGTVT & Circular 12/2024/TT-BGTVT (Stevedoring / Container Handling Tariffs).
- Phase 294: Law on Customs 2014 Arts 61 & 63, Decree 08/2015/ND-CP Arts 83-84, Circular 38/2015/TT-BTC & 39/2018/TT-BTC.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional


# ============================================================================
# Phase 291: MARPOL Annex IV Sewage Discharge & STP MEPC.227(64)
# ============================================================================

class SewageTreatmentType(str, Enum):
    APPROVED_STP = "APPROVED_STP"                          # IMO MEPC.227(64) certified
    COMMINUTED_AND_DISINFECTED = "COMMINUTED_AND_DISINFECTED" # Comminuted & chlorination/disinfected
    UNTREATED_HOLDING_TANK = "UNTREATED_HOLDING_TANK"      # Raw sewage in holding tank


class SewageDischargeVerdict(str, Enum):
    PERMITTED_STP_OPERATIONAL = "PERMITTED_STP_OPERATIONAL"
    PERMITTED_COMMINUTED_EN_ROUTE = "PERMITTED_COMMINUTED_EN_ROUTE"
    PERMITTED_UNTREATED_EN_ROUTE = "PERMITTED_UNTREATED_EN_ROUTE"
    PROHIBITED_TOO_CLOSE_TO_SHORE = "PROHIBITED_TOO_CLOSE_TO_SHORE"
    PROHIBITED_VESSEL_NOT_EN_ROUTE = "PROHIBITED_VESSEL_NOT_EN_ROUTE"
    PROHIBITED_EFFLUENT_STANDARDS_EXCEEDED = "PROHIBITED_EFFLUENT_STANDARDS_EXCEEDED"
    PROHIBITED_PORT_WATER_RESTRICTION = "PROHIBITED_PORT_WATER_RESTRICTION"


@dataclass
class SewageDischargeInput:
    vessel_name: str
    imo_number: str
    distance_to_shore_nm: float
    vessel_speed_knots: float
    treatment_type: SewageTreatmentType
    is_in_port_waters: bool = False
    is_special_area: bool = False
    is_passenger_ship: bool = False
    coliform_cfu_per_100ml: float = 50.0       # Limit <= 100
    tss_mg_l: float = 25.0                     # Limit <= 35
    bod5_mg_l: float = 20.0                    # Limit <= 25
    cod_mg_l: float = 100.0                    # Limit <= 125
    ph_value: float = 7.2                      # Range 6.0 - 8.5
    chlorine_residual_mg_l: float = 0.3        # Limit <= 0.5
    nitrogen_mg_l: float = 15.0                # Special area passenger limit <= 20
    phosphorus_mg_l: float = 0.8               # Special area passenger limit <= 1.0


@dataclass
class SewageDischargeResult:
    verdict: SewageDischargeVerdict
    is_discharge_permitted: bool
    required_min_distance_nm: float
    required_min_speed_knots: float
    effluent_compliant: bool
    effluent_violations: List[str]
    remarks: str
    verification_token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "is_discharge_permitted": self.is_discharge_permitted,
            "required_min_distance_nm": self.required_min_distance_nm,
            "required_min_speed_knots": self.required_min_speed_knots,
            "effluent_compliant": self.effluent_compliant,
            "effluent_violations": self.effluent_violations,
            "remarks": self.remarks,
            "verification_token": self.verification_token,
        }


class SewageDischargeEngine:
    """Evaluates MARPOL Annex IV Sewage Discharge compliance and MEPC.227(64) standards."""

    @classmethod
    def evaluate(cls, sample: SewageDischargeInput) -> SewageDischargeResult:
        violations: List[str] = []

        # If using approved STP, check effluent water parameters under MEPC.227(64)
        if sample.treatment_type == SewageTreatmentType.APPROVED_STP:
            if sample.coliform_cfu_per_100ml > 100.0:
                violations.append(f"Coliform {sample.coliform_cfu_per_100ml} CFU/100ml exceeds MEPC.227(64) limit (100)")
            if sample.tss_mg_l > 35.0:
                violations.append(f"TSS {sample.tss_mg_l} mg/l exceeds limit (35 mg/l)")
            if sample.bod5_mg_l > 25.0:
                violations.append(f"BOD5 {sample.bod5_mg_l} mg/l exceeds limit (25 mg/l)")
            if sample.cod_mg_l > 125.0:
                violations.append(f"COD {sample.cod_mg_l} mg/l exceeds limit (125 mg/l)")
            if sample.ph_value < 6.0 or sample.ph_value > 8.5:
                violations.append(f"pH {sample.ph_value} outside statutory range (6.0 - 8.5)")
            if sample.chlorine_residual_mg_l > 0.5:
                violations.append(f"Chlorine residual {sample.chlorine_residual_mg_l} mg/l exceeds limit (0.5 mg/l)")

            # Passenger vessel in Special Area nitrogen/phosphorus checks
            if sample.is_special_area and sample.is_passenger_ship:
                if sample.nitrogen_mg_l > 20.0:
                    violations.append(f"Total Nitrogen {sample.nitrogen_mg_l} mg/l exceeds Special Area limit (20 mg/l)")
                if sample.phosphorus_mg_l > 1.0:
                    violations.append(f"Total Phosphorus {sample.phosphorus_mg_l} mg/l exceeds Special Area limit (1.0 mg/l)")

            effluent_ok = (len(violations) == 0)
            if not effluent_ok:
                return SewageDischargeResult(
                    verdict=SewageDischargeVerdict.PROHIBITED_EFFLUENT_STANDARDS_EXCEEDED,
                    is_discharge_permitted=False,
                    required_min_distance_nm=0.0,
                    required_min_speed_knots=0.0,
                    effluent_compliant=False,
                    effluent_violations=violations,
                    remarks="STP effluent parameters violate IMO MEPC.227(64). Must retain on board or repair STP.",
                    verification_token=cls._generate_token(sample, "FAIL-EFFLUENT"),
                )

            # In port waters, national port authorities can restrict even STP
            if sample.is_in_port_waters:
                return SewageDischargeResult(
                    verdict=SewageDischargeVerdict.PROHIBITED_PORT_WATER_RESTRICTION,
                    is_discharge_permitted=False,
                    required_min_distance_nm=0.0,
                    required_min_speed_knots=0.0,
                    effluent_compliant=True,
                    effluent_violations=[],
                    remarks="Vessel inside port waters; local port regulations prohibit sewage discharge at berth.",
                    verification_token=cls._generate_token(sample, "PROHIBITED-PORT"),
                )

            return SewageDischargeResult(
                verdict=SewageDischargeVerdict.PERMITTED_STP_OPERATIONAL,
                is_discharge_permitted=True,
                required_min_distance_nm=0.0,
                required_min_speed_knots=0.0,
                effluent_compliant=True,
                effluent_violations=[],
                remarks="Approved STP meets IMO MEPC.227(64) standards. Continuous discharge permitted.",
                verification_token=cls._generate_token(sample, "PASS-STP"),
            )

        # Comminuted and disinfected sewage (CDS): requires distance >= 3 NM, speed >= 4.0 knots
        elif sample.treatment_type == SewageTreatmentType.COMMINUTED_AND_DISINFECTED:
            if sample.distance_to_shore_nm < 3.0:
                return SewageDischargeResult(
                    verdict=SewageDischargeVerdict.PROHIBITED_TOO_CLOSE_TO_SHORE,
                    is_discharge_permitted=False,
                    required_min_distance_nm=3.0,
                    required_min_speed_knots=4.0,
                    effluent_compliant=True,
                    effluent_violations=[],
                    remarks="Comminuted and disinfected sewage requires distance >= 3.0 NM from nearest land.",
                    verification_token=cls._generate_token(sample, "PROHIBITED-DIST-3NM"),
                )
            if sample.vessel_speed_knots < 4.0:
                return SewageDischargeResult(
                    verdict=SewageDischargeVerdict.PROHIBITED_VESSEL_NOT_EN_ROUTE,
                    is_discharge_permitted=False,
                    required_min_distance_nm=3.0,
                    required_min_speed_knots=4.0,
                    effluent_compliant=True,
                    effluent_violations=[],
                    remarks="Comminuted sewage discharge requires vessel proceeding en-route at speed >= 4.0 knots.",
                    verification_token=cls._generate_token(sample, "PROHIBITED-SPEED-CDS"),
                )

            return SewageDischargeResult(
                verdict=SewageDischargeVerdict.PERMITTED_COMMINUTED_EN_ROUTE,
                is_discharge_permitted=True,
                required_min_distance_nm=3.0,
                required_min_speed_knots=4.0,
                effluent_compliant=True,
                effluent_violations=[],
                remarks="Comminuted and disinfected sewage permitted outside 3 NM at speed >= 4.0 knots.",
                verification_token=cls._generate_token(sample, "PASS-CDS"),
            )

        # Untreated holding tank sewage: requires distance >= 12 NM, speed >= 4.0 knots
        else:
            if sample.distance_to_shore_nm < 12.0:
                return SewageDischargeResult(
                    verdict=SewageDischargeVerdict.PROHIBITED_TOO_CLOSE_TO_SHORE,
                    is_discharge_permitted=False,
                    required_min_distance_nm=12.0,
                    required_min_speed_knots=4.0,
                    effluent_compliant=True,
                    effluent_violations=[],
                    remarks="Untreated sewage requires distance >= 12.0 NM from nearest land.",
                    verification_token=cls._generate_token(sample, "PROHIBITED-DIST-12NM"),
                )
            if sample.vessel_speed_knots < 4.0:
                return SewageDischargeResult(
                    verdict=SewageDischargeVerdict.PROHIBITED_VESSEL_NOT_EN_ROUTE,
                    is_discharge_permitted=False,
                    required_min_distance_nm=12.0,
                    required_min_speed_knots=4.0,
                    effluent_compliant=True,
                    effluent_violations=[],
                    remarks="Untreated sewage requires vessel proceeding en-route at speed >= 4.0 knots at moderate rate.",
                    verification_token=cls._generate_token(sample, "PROHIBITED-SPEED-RAW"),
                )

            return SewageDischargeResult(
                verdict=SewageDischargeVerdict.PERMITTED_UNTREATED_EN_ROUTE,
                is_discharge_permitted=True,
                required_min_distance_nm=12.0,
                required_min_speed_knots=4.0,
                effluent_compliant=True,
                effluent_violations=[],
                remarks="Untreated sewage permitted outside 12 NM en-route at moderate discharge rate (MEPC.157(55)).",
                verification_token=cls._generate_token(sample, "PASS-RAW"),
            )

    @classmethod
    def _generate_token(cls, sample: SewageDischargeInput, code: str) -> str:
        payload = f"{sample.vessel_name}:{sample.imo_number}:{sample.treatment_type}:{sample.distance_to_shore_nm}:{code}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24].upper()


# ============================================================================
# Phase 292: STCW Manila I/9 & MLC 2006 Seafarer Medical Fitness
# ============================================================================

class DepartmentRole(str, Enum):
    DECK_WATCHKEEPING = "DECK_WATCHKEEPING"              # Master, Mates, Deck Ratings
    ENGINE_WATCHKEEPING = "ENGINE_WATCHKEEPING"          # Chief Eng, Engineers, Oiler
    RADIO_OPERATOR = "RADIO_OPERATOR"                    # GMDSS Radio Operators
    GENERAL_CREW_CATERING = "GENERAL_CREW_CATERING"      # Cooks, Stewards, Support Crew


class MedicalVerdict(str, Enum):
    FIT_UNRESTRICTED = "FIT_UNRESTRICTED"
    FIT_WITH_RESTRICTIONS = "FIT_WITH_RESTRICTIONS"
    UNFIT_TEMPORARY = "UNFIT_TEMPORARY"
    UNFIT_PERMANENT = "UNFIT_PERMANENT"


@dataclass
class MedicalAssessmentInput:
    seafarer_name: str
    passport_or_sid: str
    age: int
    department: DepartmentRole
    visual_acuity_right: float
    visual_acuity_left: float
    visual_acuity_both_eyes: float
    is_color_vision_passed: bool
    hearing_whisper_m: float
    hearing_normal_m: float
    has_severe_cardiovascular: bool = False
    has_epilepsy_or_seizures: bool = False
    has_uncontrolled_diabetes: bool = False
    has_severe_psychiatric_disorder: bool = False
    has_active_infectious_disease: bool = False
    requires_corrective_lenses: bool = False
    is_appeal_review: bool = False


@dataclass
class MedicalAssessmentResult:
    verdict: MedicalVerdict
    certificate_validity_months: int
    visual_status: str
    hearing_status: str
    disqualifications: List[str]
    restrictions: List[str]
    remarks: str
    verification_token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "certificate_validity_months": self.certificate_validity_months,
            "visual_status": self.visual_status,
            "hearing_status": self.hearing_status,
            "disqualifications": self.disqualifications,
            "restrictions": self.restrictions,
            "remarks": self.remarks,
            "verification_token": self.verification_token,
        }


class SeafarerMedicalEngine:
    """Verifies Seafarer Medical Fitness according to STCW 2010 Manila I/9, MLC 2006 & Circular 22/2017/TT-BYT."""

    @classmethod
    def evaluate(cls, candidate: MedicalAssessmentInput) -> MedicalAssessmentResult:
        disqualifications: List[str] = []
        restrictions: List[str] = []

        # 1. Critical Disqualifying Medical Conditions
        if candidate.has_severe_cardiovascular:
            disqualifications.append("Severe cardiovascular disease (Heart Failure grade II+, active ischemic heart disease)")
        if candidate.has_epilepsy_or_seizures:
            disqualifications.append("History of epilepsy, uncontrolled seizures, or recurrent unprovoked syncopal attacks")
        if candidate.has_uncontrolled_diabetes:
            disqualifications.append("Uncontrolled diabetes mellitus with frequent hypoglycemia (HbA1c > 8.5%)")
        if candidate.has_severe_psychiatric_disorder:
            disqualifications.append("Severe psychiatric disorder, psychosis, or active substance dependence")
        if candidate.has_active_infectious_disease:
            disqualifications.append("Active contagious disease posing maritime quarantine threat (Active TB, Cholera)")

        # 2. Visual Standards (STCW Table A-I/9)
        visual_ok = True
        visual_status = "Visual Acuity Compliant"

        if candidate.department == DepartmentRole.DECK_WATCHKEEPING:
            # Deck: Better eye >= 0.5, both eyes >= 0.8, color vision mandatory
            if candidate.visual_acuity_both_eyes < 0.8 or max(candidate.visual_acuity_right, candidate.visual_acuity_left) < 0.5:
                disqualifications.append(f"Deck watchkeeping visual acuity failed (Both eyes: {candidate.visual_acuity_both_eyes} < 0.8)")
                visual_ok = False
            if not candidate.is_color_vision_passed:
                disqualifications.append("Deck navigation color vision failed: Red-Green color blindness is prohibited")
                visual_ok = False
        else:
            # Engine / Radio / Catering: Better eye >= 0.4, both eyes >= 0.6
            if candidate.visual_acuity_both_eyes < 0.6 or max(candidate.visual_acuity_right, candidate.visual_acuity_left) < 0.4:
                disqualifications.append(f"Visual acuity failed (Both eyes: {candidate.visual_acuity_both_eyes} < 0.6)")
                visual_ok = False

        if candidate.requires_corrective_lenses:
            restrictions.append("Must wear corrective lenses and carry one spare pair on board")

        # 3. Hearing Standards (Circular 22/2017/TT-BYT)
        hearing_ok = True
        hearing_status = "Hearing Acuity Compliant"
        if candidate.hearing_whisper_m < 3.0:
            hearing_ok = False
            hearing_status = f"Whisper hearing deficient ({candidate.hearing_whisper_m}m < 3.0m)"
            disqualifications.append("Hearing failure: Inability to perceive whispered speech at 3.0m distance")
        if candidate.hearing_normal_m < 5.0:
            hearing_ok = False
            hearing_status = f"Normal conversational hearing deficient ({candidate.hearing_normal_m}m < 5.0m)"
            disqualifications.append("Hearing failure: Inability to perceive conversational speech at 5.0m distance")

        # 4. Formulate Verdict & Validity Period
        if len(disqualifications) > 0:
            is_permanent = any("epilepsy" in d.lower() or "cardiovascular" in d.lower() for d in disqualifications)
            verdict = MedicalVerdict.UNFIT_PERMANENT if is_permanent else MedicalVerdict.UNFIT_TEMPORARY
            return MedicalAssessmentResult(
                verdict=verdict,
                certificate_validity_months=0,
                visual_status="FAIL" if not visual_ok else visual_status,
                hearing_status=hearing_status if not hearing_ok else "PASS",
                disqualifications=disqualifications,
                restrictions=restrictions,
                remarks="Unfit for seafaring service under STCW I/9 & Circular 22/2017/TT-BYT standards.",
                verification_token=cls._generate_token(candidate, "UNFIT"),
            )

        # Candidate is FIT
        # Statutory validity: 24 months for >= 18 years old, 12 months for < 18 years old
        validity = 24 if candidate.age >= 18 else 12

        if len(restrictions) > 0:
            verdict = MedicalVerdict.FIT_WITH_RESTRICTIONS
            remarks = "Fit for seafaring duty subject to stated visual or operational restrictions."
        else:
            verdict = MedicalVerdict.FIT_UNRESTRICTED
            remarks = "Fully fit for worldwide seafaring duty under STCW 2010 Manila & MLC 2006."

        return MedicalAssessmentResult(
            verdict=verdict,
            certificate_validity_months=validity,
            visual_status=visual_status,
            hearing_status=hearing_status,
            disqualifications=[],
            restrictions=restrictions,
            remarks=remarks,
            verification_token=cls._generate_token(candidate, "FIT"),
        )

    @classmethod
    def _generate_token(cls, candidate: MedicalAssessmentInput, verdict_tag: str) -> str:
        payload = f"{candidate.seafarer_name}:{candidate.passport_or_sid}:{candidate.department}:{candidate.age}:{verdict_tag}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24].upper()


# ============================================================================
# Phase 293: Seaport Stevedoring & Cargo Handling Tariffs (TT 39/2023 & TT 12/2024)
# ============================================================================

class PortZone(str, Enum):
    ZONE_I_NORTH = "ZONE_I_NORTH"                      # Hai Phong standard, Quang Ninh
    ZONE_I_DEEPWATER = "ZONE_I_DEEPWATER"              # Lach Huyen Deepwater Hub
    ZONE_II_CENTRAL = "ZONE_II_CENTRAL"                # Da Nang, Quy Nhon
    ZONE_III_SOUTH = "ZONE_III_SOUTH"                  # Cat Lai, Hiep Phuoc, Dong Nai
    ZONE_III_DEEPWATER = "ZONE_III_DEEPWATER"          # Cai Mep - Thi Vai Deepwater Hub


class ContainerSize(str, Enum):
    CONT_20FT = "CONT_20FT"
    CONT_40FT = "CONT_40FT"
    CONT_45FT = "CONT_45FT"


class CargoStatus(str, Enum):
    LADEN = "LADEN"                                    # Cont co hang
    EMPTY = "EMPTY"                                    # Cont rong


class HandlingOperation(str, Enum):
    VESSEL_TO_CY = "VESSEL_TO_CY"                      # Tau <-> Bai cang (CY)
    VESSEL_TO_BARGE_TRUCK = "VESSEL_TO_BARGE_TRUCK"    # Tau <-> Sa lan / O to
    CY_TO_TRUCK = "CY_TO_TRUCK"                        # Bai cang <-> O to giao nhan


class CargoHazardCategory(str, Enum):
    NORMAL_GENERAL = "NORMAL_GENERAL"                  # Hang hoa thong thuong
    IMDG_STANDARD = "IMDG_STANDARD"                    # IMDG Class 3, 4, 6, 8, 9 (+30%)
    IMDG_HIGH_HAZARD = "IMDG_HIGH_HAZARD"              # IMDG Class 1, 2, 5, 7 (+50%)
    OOG_OVERSIZED = "OOG_OVERSIZED"                    # Container qua kho qua tai (+50%)
    REEFER_TEMPERATURE_CONTROLLED = "REEFER_TEMPERATURE_CONTROLLED" # Cont lanh (+15%)


@dataclass
class StevedoringTariffInput:
    port_zone: PortZone
    container_size: ContainerSize
    cargo_status: CargoStatus
    handling_operation: HandlingOperation
    hazard_category: CargoHazardCategory = CargoHazardCategory.NORMAL_GENERAL
    quantity: int = 1
    is_international_vessel: bool = True               # True = USD tariff; False = VND tariff


@dataclass
class StevedoringTariffResult:
    port_zone: PortZone
    container_size: ContainerSize
    cargo_status: CargoStatus
    base_rate: float
    operation_factor: float
    hazard_surcharge_rate: float
    rate_per_container: float
    total_charge: float
    currency: str
    itemized_breakdown: Dict[str, Any]
    invoice_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port_zone": self.port_zone.value,
            "container_size": self.container_size.value,
            "cargo_status": self.cargo_status.value,
            "base_rate": self.base_rate,
            "operation_factor": self.operation_factor,
            "hazard_surcharge_rate": self.hazard_surcharge_rate,
            "rate_per_container": round(self.rate_per_container, 2),
            "total_charge": round(self.total_charge, 2),
            "currency": self.currency,
            "itemized_breakdown": self.itemized_breakdown,
            "invoice_hash": self.invoice_hash,
        }


class StevedoringTariffEngine:
    """Calculates stevedoring service charges under Circular 39/2023/TT-BGTVT & Circular 12/2024/TT-BGTVT."""

    # Base Rates Table for Vessel <-> CY (Laden Container)
    # International (USD/cont)
    RATES_USD_LADEN = {
        PortZone.ZONE_I_NORTH: {ContainerSize.CONT_20FT: 48.0, ContainerSize.CONT_40FT: 72.0, ContainerSize.CONT_45FT: 80.0},
        PortZone.ZONE_I_DEEPWATER: {ContainerSize.CONT_20FT: 60.0, ContainerSize.CONT_40FT: 90.0, ContainerSize.CONT_45FT: 100.0},
        PortZone.ZONE_II_CENTRAL: {ContainerSize.CONT_20FT: 42.0, ContainerSize.CONT_40FT: 62.0, ContainerSize.CONT_45FT: 70.0},
        PortZone.ZONE_III_SOUTH: {ContainerSize.CONT_20FT: 52.0, ContainerSize.CONT_40FT: 78.0, ContainerSize.CONT_45FT: 86.0},
        PortZone.ZONE_III_DEEPWATER: {ContainerSize.CONT_20FT: 60.0, ContainerSize.CONT_40FT: 90.0, ContainerSize.CONT_45FT: 100.0},
    }

    # Domestic (VND/cont)
    RATES_VND_LADEN = {
        PortZone.ZONE_I_NORTH: {ContainerSize.CONT_20FT: 280000.0, ContainerSize.CONT_40FT: 440000.0, ContainerSize.CONT_45FT: 500000.0},
        PortZone.ZONE_I_DEEPWATER: {ContainerSize.CONT_20FT: 360000.0, ContainerSize.CONT_40FT: 560000.0, ContainerSize.CONT_45FT: 640000.0},
        PortZone.ZONE_II_CENTRAL: {ContainerSize.CONT_20FT: 250000.0, ContainerSize.CONT_40FT: 390000.0, ContainerSize.CONT_45FT: 450000.0},
        PortZone.ZONE_III_SOUTH: {ContainerSize.CONT_20FT: 300000.0, ContainerSize.CONT_40FT: 470000.0, ContainerSize.CONT_45FT: 540000.0},
        PortZone.ZONE_III_DEEPWATER: {ContainerSize.CONT_20FT: 360000.0, ContainerSize.CONT_40FT: 560000.0, ContainerSize.CONT_45FT: 640000.0},
    }

    @classmethod
    def calculate(cls, req: StevedoringTariffInput) -> StevedoringTariffResult:
        currency = "USD" if req.is_international_vessel else "VND"
        rates_table = cls.RATES_USD_LADEN if req.is_international_vessel else cls.RATES_VND_LADEN

        # 1. Base rate lookup for laden container
        base_rate = rates_table[req.port_zone][req.container_size]

        # 2. Empty container adjustment: 65% of laden container rate
        status_factor = 0.65 if req.cargo_status == CargoStatus.EMPTY else 1.00
        adjusted_base = base_rate * status_factor

        # 3. Operation method factor
        # Vessel <-> Barge/Truck = 0.85x; CY <-> Truck = 0.50x; Vessel <-> CY = 1.00x
        if req.handling_operation == HandlingOperation.VESSEL_TO_BARGE_TRUCK:
            operation_factor = 0.85
        elif req.handling_operation == HandlingOperation.CY_TO_TRUCK:
            operation_factor = 0.50
        else:
            operation_factor = 1.00

        operation_rate = adjusted_base * operation_factor

        # 4. Surcharge for hazardous, reefer, or OOG cargo
        surcharge_rate = 0.0
        if req.hazard_category == CargoHazardCategory.IMDG_STANDARD:
            surcharge_rate = 0.30
        elif req.hazard_category == CargoHazardCategory.IMDG_HIGH_HAZARD:
            surcharge_rate = 0.50
        elif req.hazard_category == CargoHazardCategory.OOG_OVERSIZED:
            surcharge_rate = 0.50
        elif req.hazard_category == CargoHazardCategory.REEFER_TEMPERATURE_CONTROLLED:
            surcharge_rate = 0.15

        hazard_surcharge_amount = operation_rate * surcharge_rate
        rate_per_cont = operation_rate + hazard_surcharge_amount
        total_amount = rate_per_cont * max(1, req.quantity)

        invoice_hash = hashlib.sha256(
            f"{req.port_zone}:{req.container_size}:{req.quantity}:{total_amount}:{currency}".encode("utf-8")
        ).hexdigest()[:24].upper()

        itemized = {
            "base_laden_rate": base_rate,
            "status_factor": status_factor,
            "operation_factor": operation_factor,
            "hazard_surcharge_percentage": surcharge_rate * 100.0,
            "hazard_surcharge_amount_per_unit": round(hazard_surcharge_amount, 2),
            "quantity": req.quantity,
        }

        return StevedoringTariffResult(
            port_zone=req.port_zone,
            container_size=req.container_size,
            cargo_status=req.cargo_status,
            base_rate=base_rate,
            operation_factor=operation_factor,
            hazard_surcharge_rate=surcharge_rate,
            rate_per_container=rate_per_cont,
            total_charge=total_amount,
            currency=currency,
            itemized_breakdown=itemized,
            invoice_hash=invoice_hash,
        )


# ============================================================================
# Phase 294: Customs Bonded Warehouse (Kho Ngoại Quan) Dwell Time & Seizure
# ============================================================================

class BondedWarehouseStatus(str, Enum):
    NORMAL_STORAGE = "NORMAL_STORAGE"                          # Under 12 months
    EXTENDED_STORAGE = "EXTENDED_STORAGE"                      # Under 24 months with official extension
    WARNING_EXPIRING_SOON = "WARNING_EXPIRING_SOON"            # Within 30 days of statutory expiration
    OVERSTAY_NOTICE_ISSUED = "OVERSTAY_NOTICE_ISSUED"          # Overstay <= 90 days, mandatory removal notice
    SEIZURE_LIQUIDATION_REQUIRED = "SEIZURE_LIQUIDATION_REQUIRED" # Overstay > 90 days, confiscated under Customs Law Art 63


@dataclass
class BondedWarehouseInput:
    declaration_number: str
    entry_date_str: str                                        # Format: YYYY-MM-DD
    check_date_str: str                                        # Format: YYYY-MM-DD
    is_extension_granted: bool = False
    warehouse_name: str = "TAN_CANG_BONDED_WH"
    goods_description: str = "Electronics & Component Parts"
    cif_value_usd: float = 50000.0


@dataclass
class BondedWarehouseResult:
    status: BondedWarehouseStatus
    days_in_storage: int
    allowed_max_days: int
    remaining_days: int
    overstay_days: int
    is_seizure_mandated: bool
    recommended_action: str
    audit_token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "days_in_storage": self.days_in_storage,
            "allowed_max_days": self.allowed_max_days,
            "remaining_days": self.remaining_days,
            "overstay_days": self.overstay_days,
            "is_seizure_mandated": self.is_seizure_mandated,
            "recommended_action": self.recommended_action,
            "audit_token": self.audit_token,
        }


class BondedWarehouseEngine:
    """Monitors Bonded Warehouse (Kho Ngoại Quan) dwell limits, extensions and seizure conditions under Law on Customs 2014."""

    @classmethod
    def supervise(cls, record: BondedWarehouseInput) -> BondedWarehouseResult:
        d_entry = datetime.strptime(record.entry_date_str, "%Y-%m-%d")
        d_check = datetime.strptime(record.check_date_str, "%Y-%m-%d")

        days_stored = (d_check - d_entry).days
        if days_stored < 0:
            days_stored = 0

        # Maximum allowed days: 365 days for initial term, 730 days (24 months) if extended
        max_allowed_days = 730 if record.is_extension_granted else 365
        remaining_days = max_allowed_days - days_stored

        if remaining_days > 30:
            status = BondedWarehouseStatus.EXTENDED_STORAGE if record.is_extension_granted else BondedWarehouseStatus.NORMAL_STORAGE
            action = "Storage fully compliant with Customs Law 2014 Art. 61. Normal warehousing operations permitted."
            is_seizure = False
            overstay = 0
        elif 0 <= remaining_days <= 30:
            status = BondedWarehouseStatus.WARNING_EXPIRING_SOON
            action = f"WARNING: Dwell time expiring in {remaining_days} days. Submit extension request or clear goods."
            is_seizure = False
            overstay = 0
        else:
            # Overstayed beyond statutory limit
            overstay = abs(remaining_days)
            if overstay <= 90:
                status = BondedWarehouseStatus.OVERSTAY_NOTICE_ISSUED
                action = f"OVERSTAY NOTICE: Overdue by {overstay} days. Customs authority issues removal order within 90 days."
                is_seizure = False
            else:
                status = BondedWarehouseStatus.SEIZURE_LIQUIDATION_REQUIRED
                action = f"MANDATORY SEIZURE: Overdue exceeds 90 days ({overstay} days). Confiscate and auction/destroy under Art. 63."
                is_seizure = True

        token = hashlib.sha256(
            f"{record.declaration_number}:{record.entry_date_str}:{days_stored}:{status}".encode("utf-8")
        ).hexdigest()[:24].upper()

        return BondedWarehouseResult(
            status=status,
            days_in_storage=days_stored,
            allowed_max_days=max_allowed_days,
            remaining_days=max(0, remaining_days),
            overstay_days=overstay,
            is_seizure_mandated=is_seizure,
            recommended_action=action,
            audit_token=token,
        )
