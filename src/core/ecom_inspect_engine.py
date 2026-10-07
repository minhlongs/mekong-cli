"""Mekong E-Commerce, Specialized Inspection, Hazardous Chemicals & CBAM Suite.

Phases 175-178 Domain Engine:
- Phase 175: Cross-Border E-Commerce Customs Management (Draft Decree, Decision 78 Repeal, Platform Withholding)
- Phase 176: Hazardous Chemicals Import Declaration via NSW & Dangerous Goods (Decree 113/2017 & 82/2022, IMDG/IATA)
- Phase 177: Specialized Food Safety & Quarantine Inspection (Decree 15/2018, Circular 25/2016, Circular 33/2014)
- Phase 178: EU CBAM & EUDR Green Supply Chain Export Compliance (EU Reg 2023/956, EU Reg 2023/1115)

100% Python Standard Library — Zero External Runtime Dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# =====================================================================
# DOMAIN EXCEPTIONS
# =====================================================================

class EcomComplianceError(Exception):
    """Base exception for e-commerce and specialized inspection compliance."""
    pass


class BannedChemicalClearanceError(EcomComplianceError):
    """Raised when an Annex III banned chemical attempts customs clearance."""
    pass


class IncompatibleChemicalSegregationError(EcomComplianceError):
    """Raised when dangerous goods co-loading violates IMDG/IATA segregation."""
    pass


class DeforestationViolationError(EcomComplianceError):
    """Raised when commodity originates from deforested land after 2020-12-31."""
    pass


class InvalidPolygonCoordinateError(EcomComplianceError):
    """Raised when EUDR geolocation polygon is unclosed or invalid."""
    pass


# =====================================================================
# PHASE 175: CROSS-BORDER E-COMMERCE CUSTOMS MANAGEMENT
# =====================================================================

class EcomPlatform(str, Enum):
    SHOPEE = "SHOPEE"
    LAZADA = "LAZADA"
    TIKTOK_SHOP = "TIKTOK_SHOP"
    AMAZON = "AMAZON"
    TEMU = "TEMU"
    TAOBAO = "TAOBAO"
    OTHER = "OTHER"


@dataclass(frozen=True)
class EcomOrderItem:
    item_id: str
    product_name: str
    hs_code: str
    unit_price_vnd: float
    quantity: int
    seller_id: str
    platform: EcomPlatform
    direct_seller_discount_vnd: float = 0.0
    platform_subsidy_voucher_vnd: float = 0.0
    import_duty_rate: float = 10.0
    sct_rate: float = 0.0
    vat_rate: float = 10.0


@dataclass(frozen=True)
class EcomConsignmentResult:
    order_id: str
    platform: EcomPlatform
    buyer_id: str
    declared_items_value_vnd: float
    intl_freight_insurance_vnd: float
    direct_discount_allowed_vnd: float
    platform_voucher_disallowed_vnd: float
    customs_value_vnd: float
    is_de_minimis_duty_free: bool
    import_duty_vnd: float
    sct_vnd: float
    vat_vnd: float
    total_tax_liability_vnd: float
    platform_withholding_payable_vnd: float
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "platform": self.platform.value,
            "buyer_id": self.buyer_id,
            "declared_items_value_vnd": self.declared_items_value_vnd,
            "intl_freight_insurance_vnd": self.intl_freight_insurance_vnd,
            "direct_discount_allowed_vnd": self.direct_discount_allowed_vnd,
            "platform_voucher_disallowed_vnd": self.platform_voucher_disallowed_vnd,
            "customs_value_vnd": self.customs_value_vnd,
            "is_de_minimis_duty_free": self.is_de_minimis_duty_free,
            "import_duty_vnd": self.import_duty_vnd,
            "sct_vnd": self.sct_vnd,
            "vat_vnd": self.vat_vnd,
            "total_tax_liability_vnd": self.total_tax_liability_vnd,
            "platform_withholding_payable_vnd": self.platform_withholding_payable_vnd,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SplitConsignmentRiskAssessment:
    buyer_id: str
    recipient_phone: str
    recipient_address: str
    window_hours: float
    order_count: int
    total_aggregate_value_vnd: float
    similarity_score: float
    risk_score: float
    is_split_fraud_detected: bool
    recommended_channel: str
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "buyer_id": self.buyer_id,
            "recipient_phone": self.recipient_phone,
            "recipient_address": self.recipient_address,
            "window_hours": self.window_hours,
            "order_count": self.order_count,
            "total_aggregate_value_vnd": self.total_aggregate_value_vnd,
            "similarity_score": self.similarity_score,
            "risk_score": self.risk_score,
            "is_split_fraud_detected": self.is_split_fraud_detected,
            "recommended_channel": self.recommended_channel,
            "recommended_action": self.recommended_action,
        }


class CrossBorderEcomEngine:
    """Core calculation engine for Cross-Border E-Commerce Customs Management (Phase 175).

    Governed by:
    - Draft Decree on Customs Management for Cross-Border E-Commerce
    - Law on Value-Added Tax (repeal of Decision 78/2010/QĐ-TTg VAT exemption under 1M VND)
    - Decree 134/2016/NĐ-CP (Article 29: Import duty exemption for low-value express under 1M VND)
    - Circular 80/2021/TT-BTC & Decree 91/2022/NĐ-CP (Platform tax withholding liability at source)
    """

    DUTY_DE_MINIMIS_CEILING_VND: float = 1_000_000.0

    @classmethod
    def calculate_customs_tax(
        cls,
        order_id: str,
        platform: EcomPlatform,
        buyer_id: str,
        items: List[EcomOrderItem],
        intl_freight_vnd: float = 0.0,
        intl_insurance_vnd: float = 0.0,
    ) -> EcomConsignmentResult:
        if not items:
            raise EcomComplianceError("E-commerce consignment must contain at least one item.")

        items_total_price = 0.0
        total_direct_discount = 0.0
        total_platform_voucher = 0.0
        total_import_duty = 0.0
        total_sct = 0.0
        total_vat = 0.0

        notes: List[str] = []

        # 1. Customs valuation base
        for item in items:
            item_gross = item.unit_price_vnd * item.quantity
            items_total_price += item_gross
            total_direct_discount += item.direct_seller_discount_vnd
            total_platform_voucher += item.platform_subsidy_voucher_vnd

        freight_ins = max(0.0, intl_freight_vnd + intl_insurance_vnd)
        allowed_discount = max(0.0, total_direct_discount)
        customs_value = max(0.0, items_total_price + freight_ins - allowed_discount)

        if total_platform_voucher > 0:
            notes.append(
                f"Platform voucher subsidy {total_platform_voucher:,.0f} VND is not deductible under customs valuation."
            )

        # 2. Duty de minimis under Decree 134/2016 Article 29
        is_de_minimis = customs_value <= cls.DUTY_DE_MINIMIS_CEILING_VND

        # Apportion customs value across items for tax rates
        for item in items:
            item_gross = item.unit_price_vnd * item.quantity
            weight = (item_gross / items_total_price) if items_total_price > 0 else (1.0 / len(items))
            item_cv = customs_value * weight

            # Import duty
            if is_de_minimis:
                item_duty = 0.0
            else:
                item_duty = item_cv * (item.import_duty_rate / 100.0)

            # Special consumption tax
            item_sct = (item_cv + item_duty) * (item.sct_rate / 100.0)

            # VAT: Post-repeal of Decision 78/2010/QĐ-TTg, VAT is collected from 0 VND
            item_vat = (item_cv + item_duty + item_sct) * (item.vat_rate / 100.0)

            total_import_duty += item_duty
            total_sct += item_sct
            total_vat += item_vat

        if is_de_minimis:
            notes.append("Exempt from import duty under Decree 134/2016/ND-CP (Value <= 1,000,000 VND).")
        else:
            notes.append("Standard import duty applied (Value > 1,000,000 VND).")

        notes.append("VAT collected from 0 VND following repeal of Decision 78/2010/QD-TTg.")

        total_tax = total_import_duty + total_sct + total_vat
        platform_payable = total_tax  # Platform is required to withhold 100% of tax liabilities

        return EcomConsignmentResult(
            order_id=order_id,
            platform=platform,
            buyer_id=buyer_id,
            declared_items_value_vnd=items_total_price,
            intl_freight_insurance_vnd=freight_ins,
            direct_discount_allowed_vnd=allowed_discount,
            platform_voucher_disallowed_vnd=total_platform_voucher,
            customs_value_vnd=customs_value,
            is_de_minimis_duty_free=is_de_minimis,
            import_duty_vnd=round(total_import_duty, 2),
            sct_vnd=round(total_sct, 2),
            vat_vnd=round(total_vat, 2),
            total_tax_liability_vnd=round(total_tax, 2),
            platform_withholding_payable_vnd=round(platform_payable, 2),
            notes=notes,
        )

    @classmethod
    def evaluate_split_consignment_risk(
        cls,
        buyer_id: str,
        orders: List[Dict[str, Any]],
        window_hours: float = 72.0,
    ) -> SplitConsignmentRiskAssessment:
        """Evaluates whether orders have been artificially fragmented to abuse de minimis.

        Formula:
        R_split = min(1.0, 0.40 * Sim + 0.30 * (k / k_max) + 0.30 * I(Sum > 1M and all individual <= 1M))
        """
        if not orders:
            return SplitConsignmentRiskAssessment(
                buyer_id=buyer_id,
                recipient_phone="",
                recipient_address="",
                window_hours=window_hours,
                order_count=0,
                total_aggregate_value_vnd=0.0,
                similarity_score=0.0,
                risk_score=0.0,
                is_split_fraud_detected=False,
                recommended_channel="GREEN",
                recommended_action="Normal automatic clearance.",
            )

        k = len(orders)
        k_max = 5.0
        total_val = sum(float(o.get("customs_value_vnd", 0.0)) for o in orders)
        all_individual_under_1m = all(float(o.get("customs_value_vnd", 0.0)) <= 1_000_000.0 for o in orders)
        sum_over_1m = total_val > 1_000_000.0

        phone = str(orders[0].get("phone", ""))
        address = str(orders[0].get("address", ""))

        # Address & phone identity consistency
        exact_phone_matches = sum(1 for o in orders if str(o.get("phone", "")) == phone)
        phone_ratio = exact_phone_matches / k if k > 0 else 0.0

        sim_score = 0.5 * phone_ratio + 0.5 * (1.0 if len(address) > 5 else 0.0)

        structuring_indicator = 1.0 if (sum_over_1m and all_individual_under_1m and k >= 2) else 0.0
        frequency_factor = min(1.0, k / k_max)

        risk_score = min(1.0, 0.40 * sim_score + 0.30 * frequency_factor + 0.30 * structuring_indicator)
        is_split = risk_score >= 0.70

        if is_split:
            channel = "RED"
            action = "ALERT: Suspected split consignment fraud. Consolidate orders, revoke de minimis, mandate physical check."
        elif risk_score >= 0.40:
            channel = "YELLOW"
            action = "WARNING: Moderate order concentration. Review invoices and seller identity."
        else:
            channel = "GREEN"
            action = "PASS: Low structuring risk. Normal clearance."

        return SplitConsignmentRiskAssessment(
            buyer_id=buyer_id,
            recipient_phone=phone,
            recipient_address=address,
            window_hours=window_hours,
            order_count=k,
            total_aggregate_value_vnd=total_val,
            similarity_score=round(sim_score, 3),
            risk_score=round(risk_score, 3),
            is_split_fraud_detected=is_split,
            recommended_channel=channel,
            recommended_action=action,
        )


# =====================================================================
# PHASE 176: HAZARDOUS CHEMICALS NSW & DANGEROUS GOODS
# =====================================================================

class ChemicalAnnex(str, Enum):
    ANNEX_I_CONDITIONAL = "ANNEX_I"          # Conditional chemical production/trading
    ANNEX_II_RESTRICTED = "ANNEX_II"         # Restricted - Requires MOIT special license
    ANNEX_III_BANNED = "ANNEX_III"           # Banned chemicals - Immediate prohibition
    ANNEX_IV_PLAN = "ANNEX_IV"               # Chemical accident prevention & response plan
    ANNEX_V_MANDATORY_NSW = "ANNEX_V"        # Mandatory declaration on National Single Window


class IMDGSegregationClass(int, Enum):
    COMPATIBLE = 0       # No segregation needed
    AWAY_FROM = 1        # Segregation 1: >= 3m
    SEPARATED_FROM = 2   # Segregation 2: >= 6m or bulkhead
    COMPARTMENT = 3      # Segregation 3: complete compartment
    LONGITUDINAL = 4     # Segregation 4: longitudinal separation
    FORBIDDEN = 9        # Incompatible - Co-loading strictly forbidden


@dataclass(frozen=True)
class ChemicalItem:
    cas_number: str
    chemical_name: str
    hs_code: str
    quantity_kg: float
    annexes: List[ChemicalAnnex]
    un_number: Optional[str] = None
    dg_class: Optional[float] = None
    accident_plan_threshold_kg: float = 50_000.0
    moit_license_number: Optional[str] = None
    vnsw_declaration_id: Optional[str] = None


@dataclass(frozen=True)
class ChemicalNSWDeclarationResult:
    cas_number: str
    chemical_name: str
    is_banned: bool
    requires_moit_license: bool
    moit_license_valid: bool
    requires_accident_plan: bool
    accident_document_type: str
    requires_nsw_declaration: bool
    is_nsw_exempt: bool
    nsw_token: Optional[str]
    customs_status: str
    action_required: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cas_number": self.cas_number,
            "chemical_name": self.chemical_name,
            "is_banned": self.is_banned,
            "requires_moit_license": self.requires_moit_license,
            "moit_license_valid": self.moit_license_valid,
            "requires_accident_plan": self.requires_accident_plan,
            "accident_document_type": self.accident_document_type,
            "requires_nsw_declaration": self.requires_nsw_declaration,
            "is_nsw_exempt": self.is_nsw_exempt,
            "nsw_token": self.nsw_token,
            "customs_status": self.customs_status,
            "action_required": self.action_required,
        }


@dataclass(frozen=True)
class DGSegregationResult:
    un_a: str
    dg_class_a: float
    un_b: str
    dg_class_b: float
    segregation_requirement: IMDGSegregationClass
    is_coloading_permitted: bool
    min_distance_meters: float
    statutory_rule: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "un_a": self.un_a,
            "dg_class_a": self.dg_class_a,
            "un_b": self.un_b,
            "dg_class_b": self.dg_class_b,
            "segregation_requirement": self.segregation_requirement.value,
            "is_coloading_permitted": self.is_coloading_permitted,
            "min_distance_meters": self.min_distance_meters,
            "statutory_rule": self.statutory_rule,
        }


class HazardousChemicalNSWEngine:
    """Core domain engine for Hazardous Chemicals Import Declaration via NSW & Dangerous Goods (Phase 176).

    Governed by:
    - Law on Chemicals 2007 (06/2007/QH12)
    - Decree 113/2017/NĐ-CP & Decree 82/2022/NĐ-CP (Annexes I, II, III, IV, V)
    - Circular 32/2017/TT-BCT & Circular 17/2022/TT-BCT
    - IMO IMDG Code 41-22 (Table 7.2.4 Segregation Matrix) & IATA DGR
    """

    # Static Segregation Matrix for primary classes: 1, 2.1, 2.2, 2.3, 3, 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 8, 9
    # Key: (int(class_a*10), int(class_b*10)) -> IMDGSegregationClass
    _SEGREGATION_RULES: Dict[Tuple[int, int], IMDGSegregationClass] = {
        # Class 1 (Explosives) is forbidden with almost all other classes
        (10, 30): IMDGSegregationClass.FORBIDDEN,
        (10, 51): IMDGSegregationClass.FORBIDDEN,
        (10, 52): IMDGSegregationClass.FORBIDDEN,
        (10, 80): IMDGSegregationClass.FORBIDDEN,

        # Class 3 (Flammable Liquids) vs Class 5.1 (Oxidizing Substances) -> Segregation 2 (>= 6m)
        (30, 51): IMDGSegregationClass.SEPARATED_FROM,
        (51, 30): IMDGSegregationClass.SEPARATED_FROM,

        # Class 3 vs Class 5.2 (Organic Peroxides) -> Segregation 2
        (30, 52): IMDGSegregationClass.SEPARATED_FROM,
        (52, 30): IMDGSegregationClass.SEPARATED_FROM,

        # Class 3 vs Class 8 (Corrosives) -> Segregation 1 (Away from)
        (30, 80): IMDGSegregationClass.AWAY_FROM,
        (80, 30): IMDGSegregationClass.AWAY_FROM,

        # Class 4.2 (Spontaneously Combustible) vs Class 5.1 -> Segregation 2
        (42, 51): IMDGSegregationClass.SEPARATED_FROM,
        (51, 42): IMDGSegregationClass.SEPARATED_FROM,

        # Class 5.1 (Oxidizers) vs Class 8 (Corrosives) -> Segregation 2
        (51, 80): IMDGSegregationClass.SEPARATED_FROM,
        (80, 51): IMDGSegregationClass.SEPARATED_FROM,
    }

    @classmethod
    def evaluate_chemical_compliance(cls, chemical: ChemicalItem) -> ChemicalNSWDeclarationResult:
        # 1. Banned chemicals check (Annex III)
        if ChemicalAnnex.ANNEX_III_BANNED in chemical.annexes:
            return ChemicalNSWDeclarationResult(
                cas_number=chemical.cas_number,
                chemical_name=chemical.chemical_name,
                is_banned=True,
                requires_moit_license=False,
                moit_license_valid=False,
                requires_accident_plan=False,
                accident_document_type="NONE",
                requires_nsw_declaration=False,
                is_nsw_exempt=False,
                nsw_token=None,
                customs_status="REJECTED_BANNED",
                action_required="HALT: Annex III Banned Chemical under Decree 113/2017/ND-CP. Customs clearance prohibited.",
            )

        # 2. Restricted chemicals check (Annex II)
        requires_license = ChemicalAnnex.ANNEX_II_RESTRICTED in chemical.annexes
        license_valid = bool(chemical.moit_license_number and len(chemical.moit_license_number) > 3)

        # 3. Chemical accident prevention document (Annex IV)
        is_annex_iv = ChemicalAnnex.ANNEX_IV_PLAN in chemical.annexes
        if is_annex_iv:
            if chemical.quantity_kg >= chemical.accident_plan_threshold_kg:
                requires_plan = True
                accident_doc = "PLAN_MOIT_APPROVED"
            else:
                requires_plan = False
                accident_doc = "MEASURE_ENTERPRISE_INTERNAL"
        else:
            requires_plan = False
            accident_doc = "NOT_APPLICABLE"

        # 4. Mandatory declaration via NSW (Annex V)
        # Exemption rule: quantity < 10 kg AND not in Annex II
        is_nsw_exempt = (
            chemical.quantity_kg < 10.0
            and not requires_license
            and ChemicalAnnex.ANNEX_V_MANDATORY_NSW in chemical.annexes
        )
        requires_nsw = ChemicalAnnex.ANNEX_V_MANDATORY_NSW in chemical.annexes and not is_nsw_exempt

        token = None
        if requires_nsw:
            # Generate deterministic NSW feedback token if declaration id is provided
            decl_id = chemical.vnsw_declaration_id or f"NSW-{chemical.cas_number.replace('-', '')}"
            token = f"VNSW-CLR-{decl_id[:12]}"

        # Evaluate customs clearance status
        if requires_license and not license_valid:
            status = "BLOCKED_MISSING_LICENSE"
            action = "Mandatory MOIT Import License required for Annex II chemical prior to clearance."
        elif requires_nsw and not chemical.vnsw_declaration_id:
            status = "PENDING_NSW_DECLARATION"
            action = "Submit electronic chemical declaration on National Single Window (vnsw.gov.vn)."
        else:
            status = "CLEARED_ELIGIBLE"
            action = "All statutory criteria satisfied. Cleared for customs declaration."

        return ChemicalNSWDeclarationResult(
            cas_number=chemical.cas_number,
            chemical_name=chemical.chemical_name,
            is_banned=False,
            requires_moit_license=requires_license,
            moit_license_valid=license_valid,
            requires_accident_plan=requires_plan,
            accident_document_type=accident_doc,
            requires_nsw_declaration=requires_nsw,
            is_nsw_exempt=is_nsw_exempt,
            nsw_token=token,
            customs_status=status,
            action_required=action,
        )

    @classmethod
    def check_dg_segregation(
        cls,
        un_a: str,
        dg_class_a: float,
        un_b: str,
        dg_class_b: float,
    ) -> DGSegregationResult:
        key = (int(round(dg_class_a * 10)), int(round(dg_class_b * 10)))
        reverse_key = (int(round(dg_class_b * 10)), int(round(dg_class_a * 10)))

        rule = cls._SEGREGATION_RULES.get(key) or cls._SEGREGATION_RULES.get(reverse_key, IMDGSegregationClass.COMPATIBLE)

        is_permitted = rule != IMDGSegregationClass.FORBIDDEN

        if rule == IMDGSegregationClass.COMPATIBLE:
            distance = 0.0
            statutory = "Compatible: Co-loading in same container permitted."
        elif rule == IMDGSegregationClass.AWAY_FROM:
            distance = 3.0
            statutory = "Segregation 1 (Away from): Minimum 3 meters separation required."
        elif rule == IMDGSegregationClass.SEPARATED_FROM:
            distance = 6.0
            statutory = "Segregation 2 (Separated from): Minimum 6 meters or steel bulkhead required."
        elif rule == IMDGSegregationClass.COMPARTMENT:
            distance = 12.0
            statutory = "Segregation 3: Complete compartment or hold separation required."
        elif rule == IMDGSegregationClass.LONGITUDINAL:
            distance = 24.0
            statutory = "Segregation 4: Longitudinal separation by intervening hold required."
        else:
            distance = 999.0
            statutory = "FORBIDDEN: Incompatible substances. Co-loading strictly prohibited."

        return DGSegregationResult(
            un_a=un_a,
            dg_class_a=dg_class_a,
            un_b=un_b,
            dg_class_b=dg_class_b,
            segregation_requirement=rule,
            is_coloading_permitted=is_permitted,
            min_distance_meters=distance,
            statutory_rule=statutory,
        )


# =====================================================================
# PHASE 177: SPECIALIZED FOOD SAFETY & QUARANTINE INSPECTION
# =====================================================================

class FoodInspectionMethod(str, Enum):
    REDUCED = "REDUCED"        # Kiểm tra giảm (<= 5% random documentary audit)
    NORMAL = "NORMAL"          # Kiểm tra thông thường (100% dossier review, no sampling)
    TIGHTENED = "TIGHTENED"    # Kiểm tra chặt (100% dossier + 100% sample lab testing)


class QuarantineType(str, Enum):
    ANIMAL_LIVE = "ANIMAL_LIVE"          # 15 days validity
    ANIMAL_CONSUMPTION = "ANIMAL_FOOD"   # 30 days validity
    ANIMAL_PROCESSED = "ANIMAL_PROC"     # 60 days validity
    PLANT_PHYTOSANITARY = "PLANT_PHYTO"  # 30 days validity


@dataclass(frozen=True)
class FoodSafetyConsignmentRecord:
    consignor_id: str
    product_hs: str
    current_method: FoodInspectionMethod
    consecutive_passes: int
    has_iso22000_or_haccp: bool
    cert_valid_days: int
    failed_last_batch: bool
    official_warning_issued: bool = False


@dataclass(frozen=True)
class FoodSafetyInspectionDecision:
    consignor_id: str
    assigned_method: FoodInspectionMethod
    sample_inspection_rate_pct: float
    requires_lab_testing: bool
    transition_reason: str
    next_milestone: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consignor_id": self.consignor_id,
            "assigned_method": self.assigned_method.value,
            "sample_inspection_rate_pct": self.sample_inspection_rate_pct,
            "requires_lab_testing": self.requires_lab_testing,
            "transition_reason": self.transition_reason,
            "next_milestone": self.next_milestone,
        }


@dataclass(frozen=True)
class QuarantineCertificateCheck:
    certificate_id: str
    quarantine_type: QuarantineType
    issue_date: str
    inspection_date: str
    max_validity_days: int
    elapsed_days: int
    is_valid: bool
    remaining_days: int
    action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "quarantine_type": self.quarantine_type.value,
            "issue_date": self.issue_date,
            "inspection_date": self.inspection_date,
            "max_validity_days": self.max_validity_days,
            "elapsed_days": self.elapsed_days,
            "is_valid": self.is_valid,
            "remaining_days": self.remaining_days,
            "action": self.action,
        }


class SpecializedInspectionEngine:
    """Core domain engine for Specialized Food Safety & Quarantine Inspection (Phase 177).

    Governed by:
    - Decree 15/2018/NĐ-CP (Articles 16, 17, 18, 19: State inspection of imported food)
    - Law on Animal Health 2015 & Circular 25/2016/TT-BNNPTNT
    - Law on Plant Protection 2013 & Circular 33/2014/TT-BNNPTNT
    """

    @classmethod
    def evaluate_food_inspection_tier(
        cls, record: FoodSafetyConsignmentRecord
    ) -> FoodSafetyInspectionDecision:
        # Rule 1: Immediate escalation to TIGHTENED upon failure or official warning
        if record.failed_last_batch or record.official_warning_issued:
            return FoodSafetyInspectionDecision(
                consignor_id=record.consignor_id,
                assigned_method=FoodInspectionMethod.TIGHTENED,
                sample_inspection_rate_pct=100.0,
                requires_lab_testing=True,
                transition_reason="ESCALATION: Triggered by non-conforming batch or official food safety warning (Art 17.1).",
                next_milestone="Requires exactly 3 consecutive conforming consignments to revert to Normal (Art 17.3).",
            )

        # Rule 2: De-escalation from TIGHTENED to NORMAL
        if record.current_method == FoodInspectionMethod.TIGHTENED:
            if record.consecutive_passes >= 3:
                return FoodSafetyInspectionDecision(
                    consignor_id=record.consignor_id,
                    assigned_method=FoodInspectionMethod.NORMAL,
                    sample_inspection_rate_pct=0.0,
                    requires_lab_testing=False,
                    transition_reason="DE-ESCALATION: 3 consecutive conforming batches achieved. Reverted to Normal (Art 17.3).",
                    next_milestone="Requires 3 conforming batches + valid HACCP/ISO22000 to advance to Reduced.",
                )
            else:
                remaining = 3 - record.consecutive_passes
                return FoodSafetyInspectionDecision(
                    consignor_id=record.consignor_id,
                    assigned_method=FoodInspectionMethod.TIGHTENED,
                    sample_inspection_rate_pct=100.0,
                    requires_lab_testing=True,
                    transition_reason=f"MAINTAINED: Tightened inspection active ({record.consecutive_passes}/3 passes).",
                    next_milestone=f"Need {remaining} more consecutive conforming batches to de-escalate to Normal.",
                )

        # Rule 3: Advancement from NORMAL to REDUCED
        if record.current_method == FoodInspectionMethod.NORMAL:
            if (
                record.consecutive_passes >= 3
                and record.has_iso22000_or_haccp
                and record.cert_valid_days > 0
            ):
                return FoodSafetyInspectionDecision(
                    consignor_id=record.consignor_id,
                    assigned_method=FoodInspectionMethod.REDUCED,
                    sample_inspection_rate_pct=5.0,
                    requires_lab_testing=False,
                    transition_reason="UPGRADE: 3 consecutive passes + valid GMP/HACCP/ISO 22000 certificate (Art 16.1b).",
                    next_milestone="Maintained in Reduced method unless non-conformity occurs.",
                )
            else:
                reasons: List[str] = []
                if record.consecutive_passes < 3:
                    reasons.append(f"{record.consecutive_passes}/3 passes achieved")
                if not record.has_iso22000_or_haccp:
                    reasons.append("lacks certified GMP/HACCP/ISO 22000")
                if record.cert_valid_days <= 0:
                    reasons.append("certificate expired")
                return FoodSafetyInspectionDecision(
                    consignor_id=record.consignor_id,
                    assigned_method=FoodInspectionMethod.NORMAL,
                    sample_inspection_rate_pct=0.0,
                    requires_lab_testing=False,
                    transition_reason=f"MAINTAINED: Normal dossier review ({', '.join(reasons)}).",
                    next_milestone="Achieve 3 passes + valid food safety accreditation for Reduced method.",
                )

        # Rule 4: Already REDUCED
        return FoodSafetyInspectionDecision(
            consignor_id=record.consignor_id,
            assigned_method=FoodInspectionMethod.REDUCED,
            sample_inspection_rate_pct=5.0,
            requires_lab_testing=False,
            transition_reason="MAINTAINED: Reduced inspection method active (random <= 5% dossier check).",
            next_milestone="Any single batch non-conformity will trigger immediate Tightened inspection.",
        )

    @classmethod
    def verify_quarantine_validity(
        cls,
        certificate_id: str,
        quarantine_type: QuarantineType,
        issue_date_str: str,
        inspection_date_str: str,
    ) -> QuarantineCertificateCheck:
        d_issue = datetime.strptime(issue_date_str, "%Y-%m-%d").date()
        d_inspect = datetime.strptime(inspection_date_str, "%Y-%m-%d").date()

        elapsed = (d_inspect - d_issue).days

        if quarantine_type == QuarantineType.ANIMAL_LIVE:
            max_days = 15
        elif quarantine_type == QuarantineType.ANIMAL_CONSUMPTION:
            max_days = 30
        elif quarantine_type == QuarantineType.ANIMAL_PROCESSED:
            max_days = 60
        else:  # PLANT_PHYTOSANITARY
            max_days = 30

        is_valid = 0 <= elapsed <= max_days
        remaining = max_days - elapsed

        if not is_valid:
            if elapsed < 0:
                action = "REJECT: Inspection date cannot precede certificate issuance date."
            else:
                action = f"EXPIRED: Certificate expired by {abs(remaining)} days. Quarantine renewal required."
        else:
            action = f"VALID: Certificate active with {remaining} days remaining until expiration."

        return QuarantineCertificateCheck(
            certificate_id=certificate_id,
            quarantine_type=quarantine_type,
            issue_date=issue_date_str,
            inspection_date=inspection_date_str,
            max_validity_days=max_days,
            elapsed_days=elapsed,
            is_valid=is_valid,
            remaining_days=remaining,
            action=action,
        )


# =====================================================================
# PHASE 178: EU CBAM & EUDR GREEN SUPPLY CHAIN EXPORT COMPLIANCE
# =====================================================================

class CBAMSector(str, Enum):
    IRON_AND_STEEL = "IRON_STEEL"    # HS 72, 73
    ALUMINIUM = "ALUMINIUM"          # HS 76
    CEMENT = "CEMENT"                # HS 2523
    FERTILIZERS = "FERTILIZERS"      # HS 31
    HYDROGEN = "HYDROGEN"            # HS 2804 10


@dataclass(frozen=True)
class CBAMEmissionsInput:
    sector: CBAMSector
    export_volume_tonnes: float
    total_production_volume_tonnes: float
    direct_emissions_scope1_tco2e: float
    electricity_consumed_mwh: float
    grid_emission_factor_tco2_mwh: float = 0.722  # Vietnam national grid factor average
    eu_ets_allowance_price_eur: float = 75.0
    vn_carbon_effective_price_eur: float = 0.0


@dataclass(frozen=True)
class CBAMAssessmentResult:
    sector: CBAMSector
    export_volume_tonnes: float
    direct_emissions_tco2e: float
    indirect_emissions_tco2e: float
    total_embedded_emissions_tco2e: float
    specific_embedded_emissions_per_tonne: float
    net_carbon_price_spread_eur: float
    total_cbam_liability_eur: float
    reporting_regime: str
    compliance_notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sector": self.sector.value,
            "export_volume_tonnes": self.export_volume_tonnes,
            "direct_emissions_tco2e": self.direct_emissions_tco2e,
            "indirect_emissions_tco2e": self.indirect_emissions_tco2e,
            "total_embedded_emissions_tco2e": self.total_embedded_emissions_tco2e,
            "specific_embedded_emissions_per_tonne": self.specific_embedded_emissions_per_tonne,
            "net_carbon_price_spread_eur": self.net_carbon_price_spread_eur,
            "total_cbam_liability_eur": self.total_cbam_liability_eur,
            "reporting_regime": self.reporting_regime,
            "compliance_notes": self.compliance_notes,
        }


@dataclass(frozen=True)
class EUDRParcelVerification:
    plot_id: str
    commodity_hs: str
    area_hectares: float
    coordinates: List[Tuple[float, float]]  # [(lat, lon)]
    deforestation_free_post_2020: bool
    legal_land_title_certified: bool
    is_compliant: bool
    validation_status: str
    rejection_reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plot_id": self.plot_id,
            "commodity_hs": self.commodity_hs,
            "area_hectares": self.area_hectares,
            "coordinates": self.coordinates,
            "deforestation_free_post_2020": self.deforestation_free_post_2020,
            "legal_land_title_certified": self.legal_land_title_certified,
            "is_compliant": self.is_compliant,
            "validation_status": self.validation_status,
            "rejection_reasons": self.rejection_reasons,
        }


class CBAMEUDRComplianceEngine:
    """Core domain engine for EU CBAM & EUDR Green Supply Chain Export Compliance (Phase 178).

    Governed by:
    - EU Regulation 2023/956 & Implementing Regulation 2023/1773 (CBAM)
    - EU Regulation 2023/1115 (EUDR: Deforestation-free supply chains)
    """

    @classmethod
    def calculate_cbam_liability(cls, inp: CBAMEmissionsInput) -> CBAMAssessmentResult:
        if inp.export_volume_tonnes <= 0:
            raise EcomComplianceError("Export volume must be strictly positive.")
        if inp.total_production_volume_tonnes <= 0:
            raise EcomComplianceError("Total production volume must be strictly positive.")

        # 1. Indirect emissions (Scope 2) = MWh * Grid EF
        indirect_emissions = max(0.0, inp.electricity_consumed_mwh * inp.grid_emission_factor_tco2_mwh)
        direct_emissions = max(0.0, inp.direct_emissions_scope1_tco2e)
        total_facility_emissions = direct_emissions + indirect_emissions

        # 2. Specific Embedded Emissions (SE) in tCO2e per tonne of product
        se = total_facility_emissions / inp.total_production_volume_tonnes
        total_export_embedded = se * inp.export_volume_tonnes

        # 3. Net carbon price spread
        price_spread = max(0.0, inp.eu_ets_allowance_price_eur - inp.vn_carbon_effective_price_eur)

        # 4. Total CBAM financial liability
        total_liability_eur = total_export_embedded * price_spread

        notes = [
            f"Specific embedded intensity: {se:.4f} tCO2e/tonne.",
            f"Direct Scope 1: {direct_emissions:,.2f} tCO2e | Indirect Scope 2: {indirect_emissions:,.2f} tCO2e.",
        ]
        if inp.vn_carbon_effective_price_eur > 0:
            notes.append(
                f"Deducted Vietnam domestic effective carbon price: €{inp.vn_carbon_effective_price_eur:.2f}/tCO2e."
            )

        return CBAMAssessmentResult(
            sector=inp.sector,
            export_volume_tonnes=inp.export_volume_tonnes,
            direct_emissions_tco2e=round(direct_emissions, 2),
            indirect_emissions_tco2e=round(indirect_emissions, 2),
            total_embedded_emissions_tco2e=round(total_export_embedded, 2),
            specific_embedded_emissions_per_tonne=round(se, 4),
            net_carbon_price_spread_eur=round(price_spread, 2),
            total_cbam_liability_eur=round(total_liability_eur, 2),
            reporting_regime="DEFINITIVE_FINANCIAL_SURRENDER (2026+)",
            compliance_notes=notes,
        )

    @classmethod
    def verify_eudr_compliance(
        cls,
        plot_id: str,
        commodity_hs: str,
        area_hectares: float,
        coordinates: List[Tuple[float, float]],
        deforestation_free_post_2020: bool,
        legal_land_title_certified: bool,
    ) -> EUDRParcelVerification:
        rejections: List[str] = []

        # Gate 1: Deforestation after Dec 31, 2020
        if not deforestation_free_post_2020:
            rejections.append("Failed Gate 1: Deforestation detected on parcel after cut-off date Dec 31, 2020.")

        # Gate 2: Legal land tenure
        if not legal_land_title_certified:
            rejections.append("Failed Gate 2: Land title not legally registered or certified under Vietnamese Land Law.")

        # Gate 3: Geolocation requirements
        # Parcels >= 4.0 hectares require polygon (>= 4 points and closed: first == last)
        if area_hectares >= 4.0:
            if len(coordinates) < 4:
                rejections.append(
                    f"Failed Gate 3: Parcels >= 4 ha require polygon with >= 4 vertices (received {len(coordinates)})."
                )
            else:
                first, last = coordinates[0], coordinates[-1]
                if abs(first[0] - last[0]) > 1e-5 or abs(first[1] - last[1]) > 1e-5:
                    rejections.append("Failed Gate 3: Polygon perimeter is not closed (first point != last point).")
        else:
            # Parcels < 4.0 ha require at least 1 valid coordinate
            if not coordinates:
                rejections.append("Failed Gate 3: Single point coordinate required for parcel < 4 ha.")

        is_compliant = len(rejections) == 0

        status = "EUDR_COMPLIANT_CLEARED" if is_compliant else "EUDR_REJECTED_NON_CONFORMING"

        return EUDRParcelVerification(
            plot_id=plot_id,
            commodity_hs=commodity_hs,
            area_hectares=area_hectares,
            coordinates=coordinates,
            deforestation_free_post_2020=deforestation_free_post_2020,
            legal_land_title_certified=legal_land_title_certified,
            is_compliant=is_compliant,
            validation_status=status,
            rejection_reasons=rejections,
        )
