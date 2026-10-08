"""Phases 279-282 Maritime Core Engine: BWMS, Ship Mortgage, Pilotage & Seaport FTZ Suite.

Legal and regulatory foundations:
- Phase 279: Ballast Water Management System (BWMS) D-2 & D-1 Standards (BWM Convention 2004, BWM.2/Circ.70/Rev.1, Circular 39/2023/TT-BGTVT).
- Phase 280: Ship Mortgage Enforcement, Private Sale vs Judicial Auction & Escrow Waterfall (Vietnam Maritime Code 2015 Arts. 31-36, Decree 58/2017/NĐ-CP, Civil Code 2015 Art. 468).
- Phase 281: Maritime Pilotage Service Allocation, Pilot Ladder Safety & Tariff Engine (VMC 2015 Arts. 246-258, Circular 39/2023/TT-BGTVT, SOLAS Reg. V/23, IMO Res. A.1045(27)).
- Phase 282: Seaport Free Trade Zone (FTZ) & Bonded Transshipment Cargo Supervision Engine (Law on Customs 2014 Arts. 42-44, Decree 08/2015/NĐ-CP, Circular 39/2018/TT-BTC).

Pure Python standard library implementation with zero external dependencies.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from enum import Enum
import hashlib
import math
from typing import Any, Dict, List, Optional


# ==============================================================================
# PHASE 279: BWMS D-2 COMPLIANCE & CHEMICAL NEUTRALIZATION ENGINE
# ==============================================================================

class BwmTreatmentMethod(str, Enum):
    ELECTRO_CHLORINATION = "ELECTRO_CHLORINATION"
    OZONATION = "OZONATION"
    UV_IRRADIATION = "UV_IRRADIATION"
    CHEMICAL_INJECTION = "CHEMICAL_INJECTION"
    DEBALLAST_RECEPTION_FACILITY = "DEBALLAST_RECEPTION_FACILITY"


class BwmExchangeMethod(str, Enum):
    SEQUENTIAL = "SEQUENTIAL"  # Empty-refill
    FLOW_THROUGH = "FLOW_THROUGH"  # Continuous pumping >= 3x volume
    DILUTION = "DILUTION"  # Top-fill bottom-discharge


class BwmComplianceStatus(str, Enum):
    D2_COMPLIANT = "D2_COMPLIANT"
    D1_COMPLIANT = "D1_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    CONTINGENCY_REQUIRED = "CONTINGENCY_REQUIRED"


@dataclasses.dataclass(frozen=True)
class BwmSampleInput:
    viable_organisms_ge_50um_per_m3: float
    viable_organisms_10_to_50um_per_ml: float
    vibrio_cholerae_cfu_per_100ml: float
    e_coli_cfu_per_100ml: float
    intestinal_enterococci_cfu_per_100ml: float
    raw_tro_mg_l: float = 0.0
    neutralized_tro_mg_l: float = 0.0
    discharge_flow_rate_m3_h: float = 500.0
    neutralizer_chemical: str = "NaHSO3"  # Sodium Bisulfite
    exchange_method: Optional[BwmExchangeMethod] = None
    exchange_volume_flushed_ratio: float = 0.0  # e.g., 3.0 for 3x flow-through
    distance_from_land_nm: float = 250.0
    water_depth_m: float = 300.0


@dataclasses.dataclass(frozen=True)
class BwmEvaluationResult:
    compliance_status: BwmComplianceStatus
    d2_biological_pass: bool
    d1_exchange_pass: bool
    tro_discharge_compliant: bool
    required_neutralizer_rate_kg_h: float
    calculated_dilution_efficiency_pct: float
    contingency_action: Optional[str]
    verification_hash: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compliance_status": self.compliance_status.value,
            "d2_biological_pass": self.d2_biological_pass,
            "d1_exchange_pass": self.d1_exchange_pass,
            "tro_discharge_compliant": self.tro_discharge_compliant,
            "required_neutralizer_rate_kg_h": round(self.required_neutralizer_rate_kg_h, 3),
            "calculated_dilution_efficiency_pct": round(self.calculated_dilution_efficiency_pct, 2),
            "contingency_action": self.contingency_action,
            "verification_hash": self.verification_hash,
            "details": self.details,
        }


class BwmsComplianceEngine:
    """Evaluates Ballast Water Management compliance under IMO Regs. D-1 & D-2."""

    # IMO Reg. D-2 maximum permissible biological limits
    MAX_ORG_GE_50UM = 10.0  # per m3
    MAX_ORG_10_50UM = 10.0  # per ml
    MAX_VIBRIO = 1.0        # cfu per 100 ml
    MAX_E_COLI = 250.0      # cfu per 100 ml
    MAX_ENTEROCOCCI = 100.0 # cfu per 100 ml

    # Statutory Maximum Allowable Discharge Concentration (MADC) for TRO
    MAX_DISCHARGE_TRO_MG_L = 0.10

    # Stoichiometric ratio: kg NaHSO3 per kg Cl2 equivalent = 1.465
    NAHSO3_TO_CL2_STOICH_RATIO = 1.465
    SAFETY_DOSING_FACTOR = 1.10

    @classmethod
    def evaluate_compliance(
        cls,
        vessel_name: str,
        imo_number: str,
        sample: BwmSampleInput,
    ) -> BwmEvaluationResult:
        # 1. Biological criteria check (Reg. D-2)
        d2_pass = (
            sample.viable_organisms_ge_50um_per_m3 < cls.MAX_ORG_GE_50UM
            and sample.viable_organisms_10_to_50um_per_ml < cls.MAX_ORG_10_50UM
            and sample.vibrio_cholerae_cfu_per_100ml < cls.MAX_VIBRIO
            and sample.e_coli_cfu_per_100ml < cls.MAX_E_COLI
            and sample.intestinal_enterococci_cfu_per_100ml < cls.MAX_ENTEROCOCCI
        )

        # 2. Chemical TRO neutralization dosing
        # Rate (kg/h) = flow (m3/h) * raw TRO (g/m3 = mg/L) * ratio * safety / 1000
        neutralizer_rate_kg_h = (
            sample.discharge_flow_rate_m3_h
            * sample.raw_tro_mg_l
            * cls.NAHSO3_TO_CL2_STOICH_RATIO
            * cls.SAFETY_DOSING_FACTOR
            / 1000.0
        )
        tro_compliant = sample.neutralized_tro_mg_l <= cls.MAX_DISCHARGE_TRO_MG_L

        # 3. Exchange criteria check (Reg. D-1)
        d1_geo_pass = (
            (sample.distance_from_land_nm >= 200.0 and sample.water_depth_m >= 200.0)
            or (sample.distance_from_land_nm >= 50.0 and sample.water_depth_m >= 200.0)
        )
        dilution_pct = 0.0
        if sample.exchange_method in (BwmExchangeMethod.FLOW_THROUGH, BwmExchangeMethod.DILUTION):
            dilution_pct = (1.0 - math.exp(-max(0.0, sample.exchange_volume_flushed_ratio))) * 100.0
        elif sample.exchange_method == BwmExchangeMethod.SEQUENTIAL:
            dilution_pct = 95.5

        d1_pass = d1_geo_pass and (dilution_pct >= 95.0)

        # 4. Status determination
        contingency: Optional[str] = None
        if d2_pass and tro_compliant:
            status = BwmComplianceStatus.D2_COMPLIANT
        elif d1_pass:
            status = BwmComplianceStatus.D1_COMPLIANT
            contingency = "D-2 không đạt; chấp thuận xả theo chuẩn trao đổi D-1 giữa đại dương."
        else:
            status = BwmComplianceStatus.NON_COMPLIANT
            contingency = (
                "Kích hoạt phương án khẩn cấp BWM.2/Circ.62: Cấm xả tại cảng; "
                "bơm chuyển về cơ sở tiếp nhận chất thải cảng (PRF) hoặc giữ lại trong két."
            )

        # 5. Cryptographic signature
        raw_token = f"{vessel_name}:{imo_number}:{status.value}:{sample.neutralized_tro_mg_l}:{d2_pass}"
        token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()[:24].upper()

        details = {
            "vessel": vessel_name,
            "imo": imo_number,
            "d2_details": {
                "org_ge_50um": sample.viable_organisms_ge_50um_per_m3,
                "org_10_50um": sample.viable_organisms_10_to_50um_per_ml,
                "vibrio": sample.vibrio_cholerae_cfu_per_100ml,
                "e_coli": sample.e_coli_cfu_per_100ml,
                "enterococci": sample.intestinal_enterococci_cfu_per_100ml,
            },
            "tro_details": {
                "raw_tro_mg_l": sample.raw_tro_mg_l,
                "neutralized_tro_mg_l": sample.neutralized_tro_mg_l,
                "max_allowed_mg_l": cls.MAX_DISCHARGE_TRO_MG_L,
            },
            "geo_exchange": {
                "distance_nm": sample.distance_from_land_nm,
                "depth_m": sample.water_depth_m,
                "flushed_ratio": sample.exchange_volume_flushed_ratio,
            },
        }

        return BwmEvaluationResult(
            compliance_status=status,
            d2_biological_pass=d2_pass,
            d1_exchange_pass=d1_pass,
            tro_discharge_compliant=tro_compliant,
            required_neutralizer_rate_kg_h=neutralizer_rate_kg_h,
            calculated_dilution_efficiency_pct=dilution_pct,
            contingency_action=contingency,
            verification_hash=token,
            details=details,
        )


# ==============================================================================
# PHASE 280: SHIP MORTGAGE ENFORCEMENT & ESCROW WATERFALL ENGINE
# ==============================================================================

class MortgageEnforcementMode(str, Enum):
    PRIVATE_SALE = "PRIVATE_SALE"  # Bán thỏa thuận (VMC Art. 35)
    JUDICIAL_AUCTION = "JUDICIAL_AUCTION"  # Bán đấu giá tư pháp (VMC Art. 35)


class MortgageClaimCategory(str, Enum):
    ENFORCEMENT_COSTS = "ENFORCEMENT_COSTS"  # Án phí, bảo quản, thẩm định, đấu giá
    MARITIME_LIEN = "MARITIME_LIEN"  # Quyền cầm giữ hàng hải luật định (Đ.37)
    REGISTERED_MORTGAGE = "REGISTERED_MORTGAGE"  # Thế chấp tàu biển đã đăng ký
    UNSECURED_CREDITOR = "UNSECURED_CREDITOR"  # Nợ không có tài sản bảo đảm


@dataclasses.dataclass
class ShipMortgageClaim:
    claim_id: str
    creditor_name: str
    category: MortgageClaimCategory
    registration_rank: int  # 1 for 1st mortgage, 2 for 2nd mortgage, etc.
    principal_vnd: float
    contractual_interest_vnd: float = 0.0
    penal_interest_vnd: float = 0.0
    annual_interest_rate_pct: float = 12.0
    registration_date: str = "2025-01-01"


@dataclasses.dataclass
class MortgageAllocationItem:
    claim_id: str
    creditor_name: str
    category: str
    claimed_amount_vnd: float
    admitted_amount_vnd: float
    allocated_amount_vnd: float
    interest_haircut_vnd: float
    unpaid_balance_vnd: float


@dataclasses.dataclass(frozen=True)
class MortgageEnforcementReport:
    vessel_name: str
    vessel_registry_no: str
    gross_proceeds_vnd: float
    enforcement_costs_deducted_vnd: float
    net_distributable_vnd: float
    statutory_notice_valid: bool
    notice_period_days: int
    interest_cap_enforced: bool
    total_claims_satisfied_vnd: float
    shipowner_residual_vnd: float
    allocations: List[MortgageAllocationItem]
    auth_token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "vessel_registry_no": self.vessel_registry_no,
            "gross_proceeds_vnd": self.gross_proceeds_vnd,
            "enforcement_costs_deducted_vnd": self.enforcement_costs_deducted_vnd,
            "net_distributable_vnd": self.net_distributable_vnd,
            "statutory_notice_valid": self.statutory_notice_valid,
            "notice_period_days": self.notice_period_days,
            "interest_cap_enforced": self.interest_cap_enforced,
            "total_claims_satisfied_vnd": self.total_claims_satisfied_vnd,
            "shipowner_residual_vnd": self.shipowner_residual_vnd,
            "allocations": [
                {
                    "claim_id": a.claim_id,
                    "creditor_name": a.creditor_name,
                    "category": a.category,
                    "claimed_amount_vnd": a.claimed_amount_vnd,
                    "admitted_amount_vnd": a.admitted_amount_vnd,
                    "allocated_amount_vnd": a.allocated_amount_vnd,
                    "interest_haircut_vnd": a.interest_haircut_vnd,
                    "unpaid_balance_vnd": a.unpaid_balance_vnd,
                }
                for a in self.allocations
            ],
            "auth_token": self.auth_token,
        }


class ShipMortgageEnforcementEngine:
    """Enforces ship mortgages and distributes liquidation proceeds under VMC 2015 Arts. 31-36."""

    STATUTORY_MIN_NOTICE_DAYS = 15  # VMC Art. 34
    CIVIL_CODE_MAX_INTEREST_RATE_PCT = 20.0  # Civil Code 2015 Art. 468

    @classmethod
    def process_enforcement_waterfall(
        cls,
        vessel_name: str,
        vessel_registry_no: str,
        gross_proceeds_vnd: float,
        notice_period_days: int,
        claims: List[ShipMortgageClaim],
        mode: MortgageEnforcementMode = MortgageEnforcementMode.JUDICIAL_AUCTION,
    ) -> MortgageEnforcementReport:
        notice_valid = notice_period_days >= cls.STATUTORY_MIN_NOTICE_DAYS
        remaining_pool = gross_proceeds_vnd
        allocated_items: List[MortgageAllocationItem] = []
        interest_cap_hit = False

        # Sort claims according to statutory hierarchy:
        # 1. Enforcement costs (Priority 0)
        # 2. Maritime liens (Priority 1)
        # 3. Registered mortgages (Priority 2, sorted by registration_rank ascending)
        # 4. Unsecured claims (Priority 3)
        def sort_key(c: ShipMortgageClaim) -> tuple:
            cat_order = {
                MortgageClaimCategory.ENFORCEMENT_COSTS: 0,
                MortgageClaimCategory.MARITIME_LIEN: 1,
                MortgageClaimCategory.REGISTERED_MORTGAGE: 2,
                MortgageClaimCategory.UNSECURED_CREDITOR: 3,
            }
            return (cat_order.get(c.category, 9), c.registration_rank, c.registration_date)

        sorted_claims = sorted(claims, key=sort_key)

        enforcement_costs_deducted = 0.0

        for c in sorted_claims:
            # Check statutory interest rate cap under Civil Code Art. 468
            haircut = 0.0
            admitted_interest = c.contractual_interest_vnd + c.penal_interest_vnd
            if c.annual_interest_rate_pct > cls.CIVIL_CODE_MAX_INTEREST_RATE_PCT:
                interest_cap_hit = True
                excess_ratio = (
                    c.annual_interest_rate_pct - cls.CIVIL_CODE_MAX_INTEREST_RATE_PCT
                ) / c.annual_interest_rate_pct
                haircut = admitted_interest * excess_ratio
                admitted_interest -= haircut

            total_claimed = c.principal_vnd + c.contractual_interest_vnd + c.penal_interest_vnd
            admitted_claim = c.principal_vnd + admitted_interest

            if c.category == MortgageClaimCategory.ENFORCEMENT_COSTS:
                allocated = min(remaining_pool, admitted_claim)
                enforcement_costs_deducted += allocated
                remaining_pool -= allocated
            else:
                allocated = min(remaining_pool, admitted_claim)
                remaining_pool -= allocated

            unpaid = admitted_claim - allocated
            allocated_items.append(
                MortgageAllocationItem(
                    claim_id=c.claim_id,
                    creditor_name=c.creditor_name,
                    category=c.category.value,
                    claimed_amount_vnd=total_claimed,
                    admitted_amount_vnd=admitted_claim,
                    allocated_amount_vnd=allocated,
                    interest_haircut_vnd=haircut,
                    unpaid_balance_vnd=unpaid,
                )
            )

        total_satisfied = sum(a.allocated_amount_vnd for a in allocated_items)
        residual = max(0.0, remaining_pool)
        net_distributable = gross_proceeds_vnd - enforcement_costs_deducted

        token_raw = f"{vessel_name}:{vessel_registry_no}:{gross_proceeds_vnd}:{total_satisfied}:{residual}"
        token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        return MortgageEnforcementReport(
            vessel_name=vessel_name,
            vessel_registry_no=vessel_registry_no,
            gross_proceeds_vnd=gross_proceeds_vnd,
            enforcement_costs_deducted_vnd=enforcement_costs_deducted,
            net_distributable_vnd=net_distributable,
            statutory_notice_valid=notice_valid,
            notice_period_days=notice_period_days,
            interest_cap_enforced=interest_cap_hit,
            total_claims_satisfied_vnd=total_satisfied,
            shipowner_residual_vnd=residual,
            allocations=allocated_items,
            auth_token=token,
        )


# ==============================================================================
# PHASE 281: MARITIME PILOTAGE SERVICE ALLOCATION & DUES ENGINE
# ==============================================================================

class PilotageZone(str, Enum):
    ZONE_I = "ZONE_I"  # Quảng Ninh - Hải Phòng
    ZONE_II = "ZONE_II"  # Đà Nẵng - Quy Nhơn
    ZONE_III = "ZONE_III"  # TP.HCM - Bà Rịa Vũng Tàu - Cần Thơ


class PilotLadderType(str, Enum):
    SINGLE_PILOT_LADDER = "SINGLE_PILOT_LADDER"
    COMBINATION_ARRANGEMENT = "COMBINATION_ARRANGEMENT"  # Accommodation ladder + pilot ladder


@dataclasses.dataclass(frozen=True)
class PilotLadderSafetyCheck:
    freeboard_m: float
    climbing_height_m: float
    accommodation_ladder_angle_deg: float
    is_safe: bool
    required_arrangement: PilotLadderType
    violations: List[str]


@dataclasses.dataclass(frozen=True)
class PilotageDuesCalculation:
    vessel_name: str
    gross_tonnage: float
    distance_nm: float
    zone: PilotageZone
    is_exempt: bool
    exemption_reason: Optional[str]
    ladder_safety: PilotLadderSafetyCheck
    base_charge_usd: float
    night_surcharge_usd: float
    weather_standby_charge_usd: float
    cancellation_penalty_usd: float
    total_dues_usd: float
    total_dues_vnd: float
    exchange_rate_vnd_usd: float
    receipt_code: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "gross_tonnage": self.gross_tonnage,
            "distance_nm": self.distance_nm,
            "zone": self.zone.value,
            "is_exempt": self.is_exempt,
            "exemption_reason": self.exemption_reason,
            "ladder_safety": {
                "freeboard_m": self.ladder_safety.freeboard_m,
                "climbing_height_m": self.ladder_safety.climbing_height_m,
                "angle_deg": self.ladder_safety.accommodation_ladder_angle_deg,
                "is_safe": self.ladder_safety.is_safe,
                "arrangement": self.ladder_safety.required_arrangement.value,
                "violations": self.ladder_safety.violations,
            },
            "base_charge_usd": round(self.base_charge_usd, 2),
            "night_surcharge_usd": round(self.night_surcharge_usd, 2),
            "weather_standby_charge_usd": round(self.weather_standby_charge_usd, 2),
            "cancellation_penalty_usd": round(self.cancellation_penalty_usd, 2),
            "total_dues_usd": round(self.total_dues_usd, 2),
            "total_dues_vnd": round(self.total_dues_vnd, 0),
            "exchange_rate_vnd_usd": self.exchange_rate_vnd_usd,
            "receipt_code": self.receipt_code,
        }


class MaritimePilotageDuesEngine:
    """Calculates pilotage service allocation and charges under Circular 39/2023/TT-BGTVT."""

    EXCHANGE_RATE_VND_USD = 25_000.0
    WEATHER_STANDBY_USD_PER_HOUR = 20.0
    NIGHT_SURCHARGE_RATE = 0.40  # +40% from 18:00 to 06:00

    # Circular 39/2023 unit rates (USD per GT per NM)
    ZONE_RATES = {
        PilotageZone.ZONE_I: 0.0035,
        PilotageZone.ZONE_II: 0.0032,
        PilotageZone.ZONE_III: 0.0030,
    }
    ZONE_MIN_CHARGE_USD = {
        PilotageZone.ZONE_I: 200.0,
        PilotageZone.ZONE_II: 150.0,
        PilotageZone.ZONE_III: 120.0,
    }

    @classmethod
    def evaluate_pilot_ladder(
        cls,
        freeboard_m: float,
        climbing_height_m: float,
        accommodation_angle_deg: float,
    ) -> PilotLadderSafetyCheck:
        violations: List[str] = []
        # SOLAS Reg. V/23: If freeboard > 9m, combination arrangement mandatory
        if freeboard_m > 9.0:
            arrangement = PilotLadderType.COMBINATION_ARRANGEMENT
            if accommodation_angle_deg > 45.0 and accommodation_angle_deg <= 55.0:
                # Allowed only with rest platform
                pass
            elif accommodation_angle_deg > 55.0:
                violations.append("Độ nghiêng cầu thang mạn vượt quá 55 độ quy chuẩn SOLAS.")
        else:
            arrangement = PilotLadderType.SINGLE_PILOT_LADDER

        if climbing_height_m > 9.0:
            violations.append("Chiều cao leo thang hoa tiêu đơn vượt quá 9.0m.")
        if climbing_height_m < 1.5:
            violations.append("Chiều cao thang cách mặt nước nhỏ hơn 1.5m không an toàn.")

        is_safe = len(violations) == 0
        return PilotLadderSafetyCheck(
            freeboard_m=freeboard_m,
            climbing_height_m=climbing_height_m,
            accommodation_ladder_angle_deg=accommodation_angle_deg,
            is_safe=is_safe,
            required_arrangement=arrangement,
            violations=violations,
        )

    @classmethod
    def calculate_pilotage_dues(
        cls,
        vessel_name: str,
        gross_tonnage: float,
        distance_nm: float,
        zone: PilotageZone,
        freeboard_m: float,
        climbing_height_m: float,
        accommodation_angle_deg: float = 40.0,
        is_night_transit: bool = False,
        weather_standby_hours: float = 0.0,
        is_domestic_exempt: bool = False,
        qualifying_calls_last_12m: int = 0,
        late_cancellation_hours: Optional[float] = None,
    ) -> PilotageDuesCalculation:
        ladder_check = cls.evaluate_pilot_ladder(
            freeboard_m=freeboard_m,
            climbing_height_m=climbing_height_m,
            accommodation_angle_deg=accommodation_angle_deg,
        )

        # Statutory exemption check under VMC 2015 Arts. 248-249
        is_exempt = False
        exemption_reason: Optional[str] = None
        if is_domestic_exempt and gross_tonnage < 2000.0:
            is_exempt = True
            exemption_reason = "Tàu biển Việt Nam dưới 2,000 GT tuyến nội địa được miễn hoa tiêu."
        elif qualifying_calls_last_12m >= 10:
            is_exempt = True
            exemption_reason = "Thuyền trưởng có Giấy chứng nhận khả năng chuyên môn hoa tiêu và đạt >= 10 chuyến."

        if is_exempt:
            return PilotageDuesCalculation(
                vessel_name=vessel_name,
                gross_tonnage=gross_tonnage,
                distance_nm=distance_nm,
                zone=zone,
                is_exempt=True,
                exemption_reason=exemption_reason,
                ladder_safety=ladder_check,
                base_charge_usd=0.0,
                night_surcharge_usd=0.0,
                weather_standby_charge_usd=0.0,
                cancellation_penalty_usd=0.0,
                total_dues_usd=0.0,
                total_dues_vnd=0.0,
                exchange_rate_vnd_usd=cls.EXCHANGE_RATE_VND_USD,
                receipt_code=f"EXEMPT-{vessel_name[:6].upper()}",
            )

        # Standard tariff calculation under Circular 39/2023
        rate = cls.ZONE_RATES.get(zone, 0.0035)
        raw_base = gross_tonnage * distance_nm * rate
        min_charge = cls.ZONE_MIN_CHARGE_USD.get(zone, 150.0)
        base_charge = max(raw_base, min_charge)

        night_surcharge = base_charge * cls.NIGHT_SURCHARGE_RATE if is_night_transit else 0.0
        weather_charge = max(0.0, weather_standby_hours) * cls.WEATHER_STANDBY_USD_PER_HOUR

        cancellation_penalty = 0.0
        if late_cancellation_hours is not None:
            if late_cancellation_hours < 2.0:
                cancellation_penalty = base_charge * 0.80  # 80% if cancelled < 2h before boarding
            else:
                cancellation_penalty = base_charge * 0.10  # 10% administrative fee

        total_usd = base_charge + night_surcharge + weather_charge + cancellation_penalty
        total_vnd = total_usd * cls.EXCHANGE_RATE_VND_USD

        raw_token = f"{vessel_name}:{zone.value}:{gross_tonnage}:{total_usd}"
        receipt = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()[:20].upper()

        return PilotageDuesCalculation(
            vessel_name=vessel_name,
            gross_tonnage=gross_tonnage,
            distance_nm=distance_nm,
            zone=zone,
            is_exempt=False,
            exemption_reason=None,
            ladder_safety=ladder_check,
            base_charge_usd=base_charge,
            night_surcharge_usd=night_surcharge,
            weather_standby_charge_usd=weather_charge,
            cancellation_penalty_usd=cancellation_penalty,
            total_dues_usd=total_usd,
            total_dues_vnd=total_vnd,
            exchange_rate_vnd_usd=cls.EXCHANGE_RATE_VND_USD,
            receipt_code=receipt,
        )


# ==============================================================================
# PHASE 282: SEAPORT FTZ & TRANSSHIPMENT CARGO E-SEAL SUPERVISION ENGINE
# ==============================================================================

class FtzDwellStatus(str, Enum):
    NORMAL = "NORMAL"  # Dwell < 20 days
    WARNING = "WARNING"  # 20 <= Dwell < 25 days
    URGENT = "URGENT"  # 25 <= Dwell <= 30 days
    EXTENDED = "EXTENDED"  # Approved extension up to 60 days
    OVERSTAY = "OVERSTAY"  # Dwell > 30 days without approved extension (or > 60 days with extension)


class ESealSecurityState(str, Enum):
    SECURE = "SECURE"
    TAMPERED_CUT = "TAMPERED_CUT"
    CORRIDOR_DEVIATION = "CORRIDOR_DEVIATION"
    BATTERY_CRITICAL = "BATTERY_CRITICAL"


@dataclasses.dataclass(frozen=True)
class GeoCoordinate:
    latitude: float
    longitude: float


@dataclasses.dataclass(frozen=True)
class TransshipmentCargoInput:
    declaration_no: str
    container_no: str
    discharge_date: str  # YYYY-MM-DD
    current_date: str  # YYYY-MM-DD
    extension_approved: bool = False
    approved_corridor_origin: GeoCoordinate = GeoCoordinate(10.5218, 107.0253)  # Cái Mép
    approved_corridor_dest: GeoCoordinate = GeoCoordinate(10.7626, 106.6601)  # Cát Lái
    current_coordinate: GeoCoordinate = GeoCoordinate(10.6420, 106.8427)
    e_seal_cable_intact: bool = True
    e_seal_tamper_switch: bool = False
    battery_level_pct: float = 85.0


@dataclasses.dataclass(frozen=True)
class TransshipmentSupervisionResult:
    declaration_no: str
    container_no: str
    dwell_days: int
    dwell_status: FtzDwellStatus
    e_seal_status: ESealSecurityState
    corridor_deviation_meters: float
    statutory_clearance_granted: bool
    action_required: str
    integrity_token: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "declaration_no": self.declaration_no,
            "container_no": self.container_no,
            "dwell_days": self.dwell_days,
            "dwell_status": self.dwell_status.value,
            "e_seal_status": self.e_seal_status.value,
            "corridor_deviation_meters": round(self.corridor_deviation_meters, 1),
            "statutory_clearance_granted": self.statutory_clearance_granted,
            "action_required": self.action_required,
            "integrity_token": self.integrity_token,
        }


class SeaportFtzTransshipmentEngine:
    """Supervises FTZ transshipment dwell limits and smart E-seal GPS corridors under Customs Law 2014."""

    STATUTORY_MAX_DWELL_DAYS = 30  # Decree 08/2015 Art. 44
    MAX_CORRIDOR_TOLERANCE_METERS = 500.0  # 500m allowable deviation

    @classmethod
    def _haversine_meters(cls, coord1: GeoCoordinate, coord2: GeoCoordinate) -> float:
        r = 6371000.0  # Earth radius in meters
        phi1 = math.radians(coord1.latitude)
        phi2 = math.radians(coord2.latitude)
        dphi = math.radians(coord2.latitude - coord1.latitude)
        dlam = math.radians(coord2.longitude - coord1.longitude)

        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

    @classmethod
    def _perpendicular_distance_to_corridor_meters(
        cls,
        point: GeoCoordinate,
        start: GeoCoordinate,
        end: GeoCoordinate,
    ) -> float:
        # Cross-track approximation using planar spherical projection
        d13 = cls._haversine_meters(start, point)
        d12 = cls._haversine_meters(start, end)
        d23 = cls._haversine_meters(end, point)

        if d12 <= 1.0:
            return d13

        # Heron's area to find height
        s = (d13 + d12 + d23) / 2.0
        area_sq = max(0.0, s * (s - d13) * (s - d12) * (s - d23))
        area = math.sqrt(area_sq)
        height = (2.0 * area) / d12
        return height

    @classmethod
    def supervise_transshipment(
        cls,
        cargo: TransshipmentCargoInput,
    ) -> TransshipmentSupervisionResult:
        # 1. Dwell time calculation
        d_format = "%Y-%m-%d"
        dt_start = datetime.strptime(cargo.discharge_date, d_format).replace(tzinfo=timezone.utc)
        dt_curr = datetime.strptime(cargo.current_date, d_format).replace(tzinfo=timezone.utc)
        dwell_days = max(0, (dt_curr - dt_start).days)

        max_allowed = cls.STATUTORY_MAX_DWELL_DAYS * 2 if cargo.extension_approved else cls.STATUTORY_MAX_DWELL_DAYS

        if dwell_days > max_allowed:
            dwell_status = FtzDwellStatus.OVERSTAY
            action = "Quá hạn lưu bãi trung chuyển quốc tế. Lập biên bản xử lý tịch thu hoặc tái xuất."
        elif cargo.extension_approved and dwell_days > cls.STATUTORY_MAX_DWELL_DAYS:
            dwell_status = FtzDwellStatus.EXTENDED
            action = "Hàng đang lưu bãi theo thời hạn gia hạn đã phê duyệt (tối đa 60 ngày)."
        elif dwell_days >= 25:
            dwell_status = FtzDwellStatus.URGENT
            action = "Cảnh báo khẩn cấp: Hàng sắp quá hạn 30 ngày. Yêu cầu làm thủ tục tái xuất ngay."
        elif dwell_days >= 20:
            dwell_status = FtzDwellStatus.WARNING
            action = "Cảnh báo mức 1: Đã lưu bãi >= 20 ngày. Đôn đốc hãng tàu đăng ký tàu xuất."
        else:
            dwell_status = FtzDwellStatus.NORMAL
            action = "Hàng trong thời hạn lưu bãi an toàn."

        # 2. E-seal telemetry verification
        deviation = cls._perpendicular_distance_to_corridor_meters(
            cargo.current_coordinate,
            cargo.approved_corridor_origin,
            cargo.approved_corridor_dest,
        )

        if not cargo.e_seal_cable_intact or cargo.e_seal_tamper_switch:
            seal_status = ESealSecurityState.TAMPERED_CUT
            action = "BÁO ĐỘNG HẢI QUAN: Phát hiện đứt cáp hoặc cạy mở niêm phong điện tử E-seal!"
        elif deviation > cls.MAX_CORRIDOR_TOLERANCE_METERS:
            seal_status = ESealSecurityState.CORRIDOR_DEVIATION
            action = f"CẢNH BÁO TUYẾN ĐƯỜNG: Phương tiện lệch khỏi hành lang {deviation:.1f}m > 500m."
        elif cargo.battery_level_pct < 15.0:
            seal_status = ESealSecurityState.BATTERY_CRITICAL
            action = "Cảnh báo pin E-seal yếu (< 15%). Cần sạc hoặc thay thế thiết bị."
        else:
            seal_status = ESealSecurityState.SECURE

        statutory_clearance = (
            dwell_status != FtzDwellStatus.OVERSTAY
            and seal_status == ESealSecurityState.SECURE
        )

        raw_token = f"{cargo.declaration_no}:{cargo.container_no}:{dwell_days}:{seal_status.value}:{statutory_clearance}"
        token = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()[:24].upper()

        return TransshipmentSupervisionResult(
            declaration_no=cargo.declaration_no,
            container_no=cargo.container_no,
            dwell_days=dwell_days,
            dwell_status=dwell_status,
            e_seal_status=seal_status,
            corridor_deviation_meters=deviation,
            statutory_clearance_granted=statutory_clearance,
            action_required=action,
            integrity_token=token,
        )
