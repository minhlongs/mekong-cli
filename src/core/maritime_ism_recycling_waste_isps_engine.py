"""Maritime ISM Safety Management, Green Ship Recycling (HKC/IHM),

Port Reception Facilities (PRF Waste) & ISPS Port Security Engine (Phases 243-246).

Statutory & Regulatory Frameworks:
- Phase 243: SOLAS 1974 Ch. IX, IMO Res. A.741(18) (ISM Code), Vietnam Maritime Code 2015 Arts. 65-72,
  Decree 58/2017/NĐ-CP Arts. 11-15 (DOC/SMC Validation, DPA Audits, Major NC Downgrade, Drill Readiness).
- Phase 244: Hong Kong Convention 2009 (HKC), EU SRR No 1257/2013, Law on Environmental Protection 2020 Art. 75,
  Decree 08/2022/NĐ-CP & Decree 82/2019/NĐ-CP (IHM Table A/B Thresholds, LDT Scrap Steel Recovery, Net Salvage).
- Phase 245: MARPOL 73/78 Annexes I/IV/V/VI, Circular 39/2023/TT-BGTVT, Circular 41/2020/TT-BGTVT &
  Directive (EU) 2019/883 (No-Special-Fee Cost Recovery, AWN 24h Advance Filing, Mandatory PRF Discharge).
- Phase 246: ISPS Code Parts A & B (SOLAS Ch. XI-2), Vietnam Maritime Code 2015 Arts. 102-105,
  Decree 58/2017/NĐ-CP Arts. 82-94 & Decision 22/2017/QĐ-TTg (Security Levels 1-3, DoS Mandate, TVC Threat Index).

AST Invariant:
- Zero external library dependencies (relies solely on Python standard library).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
import hashlib
import json
import math
from typing import Any, Dict, List, Optional, Tuple


# ==============================================================================
# PHASE 243: ISM CODE SMS & DPA SAFETY MANAGEMENT
# ==============================================================================

class IsmCertificateType(str, Enum):
    """Types of statutory ISM certificates."""
    DOC = "document_of_compliance"  # Company Document of Compliance
    SMC = "safety_management_certificate"  # Shipboard Safety Management Certificate
    INTERIM_DOC = "interim_doc"  # Max 12 months validity
    INTERIM_SMC = "interim_smc"  # Max 6 months validity (extendable by 6m)


class NonConformitySeverity(str, Enum):
    """ISM audit finding severity classification."""
    OBSERVATION = "observation"  # Statement of fact made during an audit
    MINOR_NC = "minor_nc"  # Non-conformity without immediate danger
    MAJOR_NC = "major_nc"  # Serious threat to safety/environment or systemic breakdown


class AuditType(str, Enum):
    """Statutory ISM audit types."""
    INITIAL = "initial"
    ANNUAL = "annual"  # Mandatory for DOC within +/- 3 months of anniversary
    INTERMEDIATE = "intermediate"  # Mandatory for SMC between 2nd and 3rd year
    RENEWAL = "renewal"  # Every 5 years
    ADDITIONAL = "additional"  # Following detention, major NC or significant modification


@dataclass(frozen=True)
class IsmCertificateStatus:
    """Evaluation of ISM Certificate validity and audit scheduling."""
    cert_type: IsmCertificateType
    cert_number: str
    issue_date: str
    expiry_date: str
    is_valid: bool
    days_to_expiry: int
    audit_due: bool
    audit_window_start: str
    audit_window_end: str
    remarks: str


@dataclass(frozen=True)
class IsmAuditEvaluation:
    """Result of ISM Non-Conformity and DPA compliance evaluation."""
    ship_name: str
    imo_number: str
    total_findings: int
    major_nc_count: int
    minor_nc_count: int
    observation_count: int
    smc_suspended: bool
    detention_risk: bool
    downgrade_permitted: bool
    cap_deadline_days: int
    drill_readiness_pct: float
    audit_summary: str
    findings_detail: List[Dict[str, Any]] = field(default_factory=list)


class IsmSafetyManagementEngine:
    """Core domain engine for ISM Code Safety Management System compliance (Phase 243)."""

    # SOLAS IX & ISM Code Article 13 & 14 statutory validity limits (days)
    FULL_TERM_VALIDITY_DAYS = 1825  # 5 years
    INTERIM_DOC_MAX_DAYS = 365  # 12 months
    INTERIM_SMC_MAX_DAYS = 180  # 6 months
    AUDIT_WINDOW_DAYS = 90  # +/- 3 months = 90 days

    @classmethod
    def evaluate_certificate_validity(
        cls,
        cert_type: IsmCertificateType,
        cert_number: str,
        issue_date_str: str,
        expiry_date_str: str,
        current_date_str: Optional[str] = None,
        last_audit_date_str: Optional[str] = None,
    ) -> IsmCertificateStatus:
        """Evaluates certificate validity and audit window compliance under ISM Code Section 13-14."""
        cur_dt = (
            datetime.strptime(current_date_str, "%Y-%m-%d").date()
            if current_date_str
            else date.today()
        )
        iss_dt = datetime.strptime(issue_date_str, "%Y-%m-%d").date()
        exp_dt = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        days_to_expiry = (exp_dt - cur_dt).days
        is_expired = days_to_expiry < 0

        # Maximum validity bounds validation
        max_duration = (
            cls.INTERIM_DOC_MAX_DAYS
            if cert_type == IsmCertificateType.INTERIM_DOC
            else (
                cls.INTERIM_SMC_MAX_DAYS
                if cert_type == IsmCertificateType.INTERIM_SMC
                else cls.FULL_TERM_VALIDITY_DAYS + 30  # leeway
            )
        )
        total_duration = (exp_dt - iss_dt).days
        invalid_duration = total_duration > max_duration

        # Compute next audit window based on certificate type
        audit_due = False
        if cert_type == IsmCertificateType.DOC:
            # Annual audit within +/- 3 months of each anniversary date
            anniversary_this_year = date(cur_dt.year, iss_dt.month, iss_dt.day)
            window_start = anniversary_this_year - timedelta(days=cls.AUDIT_WINDOW_DAYS)
            window_end = anniversary_this_year + timedelta(days=cls.AUDIT_WINDOW_DAYS)
            if window_start <= cur_dt <= window_end:
                audit_due = True
        elif cert_type == IsmCertificateType.SMC:
            # Intermediate audit between 2nd and 3rd anniversary dates
            two_year_dt = date(iss_dt.year + 2, iss_dt.month, iss_dt.day)
            three_year_dt = date(iss_dt.year + 3, iss_dt.month, iss_dt.day)
            window_start = two_year_dt
            window_end = three_year_dt
            if two_year_dt <= cur_dt <= three_year_dt:
                audit_due = True
        else:
            # Interim certificates do not have periodic intermediate audits
            window_start = iss_dt
            window_end = exp_dt

        is_valid = (not is_expired) and (not invalid_duration)

        remarks_list = []
        if is_expired:
            remarks_list.append("Chứng chỉ đã hết hiệu lực theo luật định")
        elif days_to_expiry <= 30:
            remarks_list.append(f"Chứng chỉ sắp hết hạn trong {days_to_expiry} ngày")

        if audit_due:
            remarks_list.append("Đang trong cửa sổ thời hạn kiểm tra định kỳ bắt buộc")

        return IsmCertificateStatus(
            cert_type=cert_type,
            cert_number=cert_number,
            issue_date=iss_dt.isoformat(),
            expiry_date=exp_dt.isoformat(),
            is_valid=is_valid,
            days_to_expiry=days_to_expiry,
            audit_due=audit_due,
            audit_window_start=window_start.isoformat(),
            audit_window_end=window_end.isoformat(),
            remarks="; ".join(remarks_list) if remarks_list else "Chứng chỉ hợp lệ, đầy đủ điều kiện hoạt động",
        )

    @classmethod
    def evaluate_audit_findings(
        cls,
        ship_name: str,
        imo_number: str,
        findings: List[Dict[str, Any]],
        drills_conducted: int = 12,
        drills_required: int = 12,
    ) -> IsmAuditEvaluation:
        """Evaluates non-conformities, suspension triggers, and CAP limits under IMO Res. A.741(18)."""
        major_nc = 0
        minor_nc = 0
        obs = 0

        evaluated_findings = []
        for f in findings:
            sev = f.get("severity", "").lower()
            desc = f.get("description", "")
            clause = f.get("clause", "ISM Code")
            is_downgraded = bool(f.get("downgraded_to_minor", False))

            if ("major" in sev or sev == NonConformitySeverity.MAJOR_NC.value) and not is_downgraded:
                major_nc += 1
                ev_sev = NonConformitySeverity.MAJOR_NC.value
            elif ("minor" in sev or sev == NonConformitySeverity.MINOR_NC.value) or is_downgraded:
                minor_nc += 1
                ev_sev = NonConformitySeverity.MINOR_NC.value
            else:
                obs += 1
                ev_sev = NonConformitySeverity.OBSERVATION.value

            evaluated_findings.append({
                "clause": clause,
                "description": desc,
                "severity": ev_sev,
                "cap_deadline_days": 0 if ev_sev == NonConformitySeverity.MAJOR_NC.value else 90,
            })

        # SOLAS / ISM Rule: Major NC leads to suspension of SMC unless immediately downgraded
        smc_suspended = major_nc > 0
        detention_risk = major_nc > 0
        downgrade_permitted = major_nc > 0  # Requires approved immediate temporary mitigation
        cap_deadline_days = 90 if not smc_suspended else 0

        # Emergency drill readiness percentage
        drill_pct = round(min(100.0, (drills_conducted / max(1, drills_required)) * 100.0), 1)
        if drill_pct < 80.0 and major_nc == 0:
            # Inadequate drill frequency can trigger a minor NC
            minor_nc += 1

        summary = (
            f"Tàu {ship_name} (IMO: {imo_number}): "
            + (
                f"ĐÌNH CHỈ SMC / NGUY CƠ LƯU GIỮ do có {major_nc} lỗi không phù hợp lớn (Major NC). "
                f"Cần áp dụng biện pháp khắc phục tạm thời ngay lập tức để hạ cấp xuống Minor NC."
                if smc_suspended
                else f"Hệ thống SMS đạt chuẩn; ghi nhận {minor_nc} Minor NC (thời hạn CAP 90 ngày) và {obs} khuyến nghị."
            )
        )

        return IsmAuditEvaluation(
            ship_name=ship_name,
            imo_number=imo_number,
            total_findings=len(findings),
            major_nc_count=major_nc,
            minor_nc_count=minor_nc,
            observation_count=obs,
            smc_suspended=smc_suspended,
            detention_risk=detention_risk,
            downgrade_permitted=downgrade_permitted,
            cap_deadline_days=cap_deadline_days,
            drill_readiness_pct=drill_pct,
            audit_summary=summary,
            findings_detail=evaluated_findings,
        )


# ==============================================================================
# PHASE 244: GREEN SHIP RECYCLING & INVENTORY OF HAZARDOUS MATERIALS (IHM)
# ==============================================================================

class IhmMaterialCategory(str, Enum):
    """IHM Table A and Table B hazardous materials under Hong Kong Convention 2009."""
    ASBESTOS = "asbestos"  # Table A: Prohibited, threshold 0.1% (1000 mg/kg)
    ODS = "ozone_depleting_substances"  # Table A: Prohibited, zero release
    PCB = "polychlorinated_biphenyls"  # Table A: Prohibited, threshold 50 mg/kg
    ANTI_FOULING_CYBUTRYNE = "anti_fouling_cybutryne"  # Table A: Prohibited, 1000 mg/kg
    CADMIUM = "cadmium"  # Table B: Declarable, threshold 100 mg/kg
    HEXAVALENT_CHROMIUM = "hexavalent_chromium"  # Table B: Declarable, threshold 1000 mg/kg
    LEAD = "lead"  # Table B: Declarable, threshold 1000 mg/kg
    MERCURY = "mercury"  # Table B: Declarable, threshold 1000 mg/kg
    PBB_PBDE = "polybrominated_biphenyls"  # Table B: Declarable, threshold 1000 mg/kg
    RADIOACTIVE = "radioactive_substances"  # Table B: Declarable, any detectable


@dataclass(frozen=True)
class IhmMaterialFinding:
    """Individual hazardous material assessment record."""
    material: IhmMaterialCategory
    location: str
    measured_concentration_mg_kg: float
    statutory_threshold_mg_kg: float
    is_table_a_prohibited: bool
    is_exceeded: bool
    estimated_mass_kg: float


@dataclass(frozen=True)
class ShipRecyclingValuation:
    """Valuation of scrap yield, hazardous disposal, and net salvage value under HKC/LEP 2020."""
    ldt_tonnes: float
    recovered_steel_tonnes: float
    recovered_nonferrous_tonnes: float
    total_hazardous_waste_tonnes: float
    gross_scrap_revenue_usd: float
    hazardous_disposal_cost_usd: float
    labor_demolition_cost_usd: float
    net_salvage_value_usd: float
    net_salvage_value_vnd: float
    ihm_compliant: bool
    irrc_ready: bool
    compliance_notes: str


class GreenShipRecyclingIhmEngine:
    """Core domain engine for Hong Kong Convention 2009 & IHM Ship Recycling (Phase 244)."""

    # Statutory concentration threshold limits (mg/kg or ppm) under HKC MEPC.269(68)
    THRESHOLDS_MG_KG = {
        IhmMaterialCategory.ASBESTOS: 1000.0,  # 0.1% by weight
        IhmMaterialCategory.ODS: 0.0,  # Zero allowance
        IhmMaterialCategory.PCB: 50.0,
        IhmMaterialCategory.ANTI_FOULING_CYBUTRYNE: 1000.0,
        IhmMaterialCategory.CADMIUM: 100.0,
        IhmMaterialCategory.HEXAVALENT_CHROMIUM: 1000.0,
        IhmMaterialCategory.LEAD: 1000.0,
        IhmMaterialCategory.MERCURY: 1000.0,
        IhmMaterialCategory.PBB_PBDE: 1000.0,
        IhmMaterialCategory.RADIOACTIVE: 0.0,
    }

    TABLE_A_MATERIALS = {
        IhmMaterialCategory.ASBESTOS,
        IhmMaterialCategory.ODS,
        IhmMaterialCategory.PCB,
        IhmMaterialCategory.ANTI_FOULING_CYBUTRYNE,
    }

    @classmethod
    def audit_ihm_materials(
        cls,
        samples: List[Dict[str, Any]],
    ) -> Tuple[bool, List[IhmMaterialFinding]]:
        """Audits sampled ship components against HKC Table A & B threshold limits."""
        findings: List[IhmMaterialFinding] = []
        has_table_a_violation = False

        category_aliases = {
            "ods": IhmMaterialCategory.ODS,
            "pcb": IhmMaterialCategory.PCB,
            "pcbs": IhmMaterialCategory.PCB,
            "asbestos": IhmMaterialCategory.ASBESTOS,
            "cybutryne": IhmMaterialCategory.ANTI_FOULING_CYBUTRYNE,
            "cadmium": IhmMaterialCategory.CADMIUM,
            "lead": IhmMaterialCategory.LEAD,
            "mercury": IhmMaterialCategory.MERCURY,
        }

        for s in samples:
            mat_raw = str(s.get("material", s.get("category", ""))).lower().strip()
            if mat_raw in category_aliases:
                mat = category_aliases[mat_raw]
            else:
                try:
                    mat = IhmMaterialCategory(mat_raw)
                except ValueError:
                    mat = IhmMaterialCategory.LEAD

            loc = s.get("location", "Hull/Machinery")
            conc = float(s.get("measured_mg_kg", s.get("concentration_mg_kg", 0.0)))
            mass_kg = float(s.get("estimated_mass_kg", s.get("estimated_quantity_tonnes", 0.0) * 1000.0 if "estimated_quantity_tonnes" in s else 0.0))
            threshold = cls.THRESHOLDS_MG_KG.get(mat, 1000.0)

            is_table_a = mat in cls.TABLE_A_MATERIALS
            is_exceeded = conc > threshold

            if is_table_a and is_exceeded:
                has_table_a_violation = True

            findings.append(
                IhmMaterialFinding(
                    material=mat,
                    location=loc,
                    measured_concentration_mg_kg=conc,
                    statutory_threshold_mg_kg=threshold,
                    is_table_a_prohibited=is_table_a,
                    is_exceeded=is_exceeded,
                    estimated_mass_kg=mass_kg,
                )
            )

        ihm_compliant = not has_table_a_violation
        return ihm_compliant, findings

    @classmethod
    def calculate_recycling_valuation(
        cls,
        ldt_tonnes: float,
        ihm_findings: List[IhmMaterialFinding],
        steel_scrap_price_usd_tonne: float = 480.0,
        nonferrous_price_usd_tonne: float = 1800.0,
        hazardous_treatment_tariff_usd_tonne: float = 650.0,
        demolition_labor_usd_ldt: float = 95.0,
        usd_vnd_exchange_rate: float = 25400.0,
    ) -> ShipRecyclingValuation:
        """Calculates recovery yield, decontamination cost, and net scrap valuation."""
        # Engineering scrap recovery coefficients
        steel_recovery_ratio = 0.88  # 88% structural scrap steel
        nonferrous_recovery_ratio = 0.035  # 3.5% non-ferrous metals (copper, bronze, aluminium)

        steel_tonnes = round(ldt_tonnes * steel_recovery_ratio, 2)
        nonferrous_tonnes = round(ldt_tonnes * nonferrous_recovery_ratio, 2)

        # Total hazardous material mass from IHM findings in tonnes
        haz_waste_kg = sum(f.estimated_mass_kg for f in ihm_findings if f.is_exceeded)
        # Default safety baseline hazardous allowance if no findings given: 1.2% of LDT
        if haz_waste_kg <= 0.0:
            haz_waste_kg = ldt_tonnes * 1000.0 * 0.012

        haz_waste_tonnes = round(haz_waste_kg / 1000.0, 3)

        # Revenue and cost elements
        gross_rev = (steel_tonnes * steel_scrap_price_usd_tonne) + (
            nonferrous_tonnes * nonferrous_price_usd_tonne
        )
        haz_cost = haz_waste_tonnes * hazardous_treatment_tariff_usd_tonne
        labor_cost = ldt_tonnes * demolition_labor_usd_ldt

        net_val_usd = round(gross_rev - haz_cost - labor_cost, 2)
        net_val_vnd = round(net_val_usd * usd_vnd_exchange_rate, 0)

        # HKC Compliance: Table A materials must be fully surveyed and have an approved Ship Recycling Plan (SRP)
        table_a_exceeded = any(f.is_table_a_prohibited and f.is_exceeded for f in ihm_findings)
        ihm_compliant = not table_a_exceeded
        irrc_ready = ihm_compliant and (net_val_usd > 0.0)

        notes = (
            "Đủ điều kiện cấp Chứng chỉ Sẵn sàng Tái chế Tàu biển Quốc tế (IRRC) theo Công ước Hồng Kông 2009"
            if irrc_ready
            else "Chưa đủ điều kiện IRRC: Cần hoàn thiện Kế hoạch Tái chế Tàu biển (SRP) và xử lý dỡ bỏ vật liệu Nguy hại Bảng A."
        )

        return ShipRecyclingValuation(
            ldt_tonnes=ldt_tonnes,
            recovered_steel_tonnes=steel_tonnes,
            recovered_nonferrous_tonnes=nonferrous_tonnes,
            total_hazardous_waste_tonnes=haz_waste_tonnes,
            gross_scrap_revenue_usd=round(gross_rev, 2),
            hazardous_disposal_cost_usd=round(haz_cost, 2),
            labor_demolition_cost_usd=round(labor_cost, 2),
            net_salvage_value_usd=net_val_usd,
            net_salvage_value_vnd=net_val_vnd,
            ihm_compliant=ihm_compliant,
            irrc_ready=irrc_ready,
            compliance_notes=notes,
        )


# ==============================================================================
# PHASE 245: PORT RECEPTION FACILITIES (PRF WASTE DELIVERY & CIRCULAR 39)
# ==============================================================================

class MarpolWasteType(str, Enum):
    """MARPOL 73/78 waste categories received at port reception facilities."""
    ANNEX_I_OILY_BILGE = "annex_i_oily_bilge"  # Nước la-ghành, dầu cặn
    ANNEX_I_SLUDGE = "annex_i_sludge"  # Dầu bùn tách lọc máy chính/phụ
    ANNEX_IV_SEWAGE = "annex_iv_sewage"  # Nước thải sinh hoạt
    ANNEX_V_DOMESTIC_GARBAGE = "annex_v_domestic_garbage"  # Rác thải sinh hoạt thông thường
    ANNEX_V_PLASTIC = "annex_v_plastic"  # Rác nhựa (cấm xả tuyệt đối ra biển)
    ANNEX_V_CARGO_RESIDUES = "annex_v_cargo_residues"  # Dư lượng hàng hóa
    ANNEX_VI_SCRUBBER_RESIDUES = "annex_vi_scrubber_sludge"  # Cặn bùn từ hệ thống khử lưu huỳnh EGCS


@dataclass(frozen=True)
class AdvanceWasteNotificationStatus:
    """Status of Advance Waste Notification (AWN) under Circular 41/2020 & Directive 2019/883."""
    hours_before_arrival: float
    is_filed_on_time: bool  # >= 24h before arrival
    remaining_storage_m3: float
    predicted_generation_next_leg_m3: float
    safety_buffer_ratio: float
    mandatory_discharge_required: bool
    notification_summary: str


@dataclass(frozen=True)
class PortWasteFeeReceipt:
    """Statutory port reception facility fee under Circular 39/2023/TT-BGTVT."""
    gross_tonnage: float
    days_at_berth: float
    indirect_waste_fee_vnd: float
    included_garbage_allowance_m3: float
    delivered_garbage_m3: float
    excess_garbage_m3: float
    excess_garbage_fee_vnd: float
    hazardous_waste_fee_vnd: float
    total_waste_fee_vnd: float
    statutory_tariff_ref: str


class PortReceptionWasteEngine:
    """Core domain engine for Port Reception Facilities & Circular 39 No-Special-Fee system (Phase 245)."""

    # Statutory baseline tariffs under Circular 39/2023/TT-BGTVT (VND/m3 or VND/GT/call)
    ANNEX_V_INDIRECT_RATE_PER_GT = 120.0  # VND/GT/call for domestic garbage indirect fee
    MIN_INDIRECT_FEE_VND = 1500000.0  # Sàn phí gián tiếp tối thiểu 1.5M VND
    MAX_INDIRECT_FEE_VND = 18000000.0  # Trần phí gián tiếp tối đa 18M VND

    ANNEX_V_EXCESS_TARIFF_M3 = 350000.0  # 350,000 VND/m3 rác sinh hoạt vượt định ngạch
    ANNEX_I_BILGE_TARIFF_M3 = 650000.0  # 650,000 VND/m3 nước lẫn dầu
    ANNEX_I_SLUDGE_TARIFF_M3 = 950000.0  # 950,000 VND/m3 dầu cặn sludge đặc
    ANNEX_IV_SEWAGE_TARIFF_M3 = 250000.0  # 250,000 VND/m3 nước thải sinh hoạt
    ANNEX_VI_SCRUBBER_TARIFF_M3 = 1200000.0  # 1,200,000 VND/m3 cặn EGCS scrubber

    @classmethod
    def evaluate_awn_delivery_mandate(
        cls,
        hours_before_arrival: float,
        remaining_storage_m3: float,
        total_tank_capacity_m3: float,
        predicted_generation_next_leg_m3: float,
    ) -> AdvanceWasteNotificationStatus:
        """Verifies 24h AWN timeline and checks mandatory discharge trigger under MARPOL/Circular 41."""
        is_filed_on_time = hours_before_arrival >= 24.0

        # Safety buffer under IMO MEPC: Remaining storage must accommodate next leg + 25% safety buffer
        required_next_leg_with_buffer = predicted_generation_next_leg_m3 * 1.25
        tank_fullness_ratio = (
            (total_tank_capacity_m3 - remaining_storage_m3) / max(0.1, total_tank_capacity_m3)
        )

        # Trigger mandatory discharge if:
        # 1. Remaining capacity is less than required for next leg with buffer, OR
        # 2. Existing tank fullness is >= 75%
        mandatory_discharge = (
            remaining_storage_m3 < required_next_leg_with_buffer
        ) or (tank_fullness_ratio >= 0.75)

        summary_parts = []
        if not is_filed_on_time:
            summary_parts.append(
                f"CẢNH BÁO: Nộp AWN muộn ({hours_before_arrival:.1f}h < 24.0h theo quy định)"
            )
        else:
            summary_parts.append("Hồ sơ AWN nộp đúng thời hạn 24 giờ trước khi cập cảng")

        if mandatory_discharge:
            summary_parts.append(
                "BẮT BUỘC BƠM XẢ CHẤT THẢI LÊN CẢNG: Dung tích chứa còn lại không đủ an toàn cho hành trình tiếp theo"
            )
        else:
            summary_parts.append("Được phép giữ lại chất thải trên tàu theo hành trình đã đăng ký")

        return AdvanceWasteNotificationStatus(
            hours_before_arrival=hours_before_arrival,
            is_filed_on_time=is_filed_on_time,
            remaining_storage_m3=remaining_storage_m3,
            predicted_generation_next_leg_m3=predicted_generation_next_leg_m3,
            safety_buffer_ratio=1.25,
            mandatory_discharge_required=mandatory_discharge,
            notification_summary="; ".join(summary_parts),
        )

    @classmethod
    def calculate_port_waste_tariffs(
        cls,
        gross_tonnage: float,
        days_at_berth: float,
        delivered_garbage_m3: float,
        annex_i_sludge_m3: float = 0.0,
        annex_i_bilge_m3: float = 0.0,
        annex_iv_sewage_m3: float = 0.0,
        annex_vi_scrubber_m3: float = 0.0,
    ) -> PortWasteFeeReceipt:
        """Calculates Circular 39 indirect garbage fee (No-Special-Fee) and direct special waste fees."""
        # 1. Indirect Fee (Thu gián tiếp qua tàu):
        base_indirect = gross_tonnage * cls.ANNEX_V_INDIRECT_RATE_PER_GT
        indirect_fee = max(cls.MIN_INDIRECT_FEE_VND, min(cls.MAX_INDIRECT_FEE_VND, base_indirect))

        # Included garbage allowance under Circular 39: 0.00015 m3 per GT per day (min 2.0 m3)
        included_allowance = max(2.0, round(gross_tonnage * 0.00015 * max(1.0, days_at_berth), 2))

        # Excess garbage fee
        excess_garbage = max(0.0, delivered_garbage_m3 - included_allowance)
        excess_garbage_fee = excess_garbage * cls.ANNEX_V_EXCESS_TARIFF_M3

        # 2. Direct special hazardous waste fees
        haz_fee = (
            (annex_i_sludge_m3 * cls.ANNEX_I_SLUDGE_TARIFF_M3)
            + (annex_i_bilge_m3 * cls.ANNEX_I_BILGE_TARIFF_M3)
            + (annex_iv_sewage_m3 * cls.ANNEX_IV_SEWAGE_TARIFF_M3)
            + (annex_vi_scrubber_m3 * cls.ANNEX_VI_SCRUBBER_TARIFF_M3)
        )

        total_fee = indirect_fee + excess_garbage_fee + haz_fee

        return PortWasteFeeReceipt(
            gross_tonnage=gross_tonnage,
            days_at_berth=days_at_berth,
            indirect_waste_fee_vnd=round(indirect_fee, 0),
            included_garbage_allowance_m3=included_allowance,
            delivered_garbage_m3=delivered_garbage_m3,
            excess_garbage_m3=round(excess_garbage, 2),
            excess_garbage_fee_vnd=round(excess_garbage_fee, 0),
            hazardous_waste_fee_vnd=round(haz_fee, 0),
            total_waste_fee_vnd=round(total_fee, 0),
            statutory_tariff_ref="Biểu mức thu giá dịch vụ thu gom chất thải cảng biển - Thông tư 39/2023/TT-BGTVT",
        )


# ==============================================================================
# PHASE 246: SEAPORT ISPS CODE SECURITY LEVELS & DECLARATION OF SECURITY (DOS)
# ==============================================================================

class MaritimeSecurityLevel(int, Enum):
    """Statutory maritime security levels under ISPS Code Part A Section 2.1."""
    LEVEL_1 = 1  # Normal: Minimum appropriate protective security measures
    LEVEL_2 = 2  # Heightened: Additional protective measures for heightened risk
    LEVEL_3 = 3  # Exceptional: Specific protective measures for probable/imminent incident


class SecurityRiskTier(str, Enum):
    """Threat risk tiers derived from TVC Matrix (Threat x Vulnerability x Consequence)."""
    LOW = "low"  # Score <= 20
    MEDIUM = "medium"  # Score 21 - 50
    HIGH = "high"  # Score 51 - 80
    CRITICAL = "critical"  # Score > 80


@dataclass(frozen=True)
class DeclarationOfSecurityResult:
    """Assessment of Declaration of Security (DoS) statutory requirement under ISPS Code A/5."""
    ship_security_level: MaritimeSecurityLevel
    port_security_level: MaritimeSecurityLevel
    dos_mandatory: bool
    governing_trigger: str
    access_screening_pct: float
    max_patrol_interval_mins: int
    guard_deployment_time_mins: int
    security_hash: str


@dataclass(frozen=True)
class ThreatVulnerabilityAssessment:
    """Security risk score based on Threat, Vulnerability, and Consequence (TVC) matrix."""
    facility_name: str
    threat_likelihood: int  # 1 (Rare) to 5 (Almost Certain)
    vulnerability_level: int  # 1 (Robust) to 5 (Vulnerable)
    consequence_severity: int  # 1 (Negligible) to 5 (Catastrophic)
    risk_score: int  # T * V * C (1 to 125)
    risk_tier: SecurityRiskTier
    recommended_level: MaritimeSecurityLevel
    mitigation_measures: List[str]


class IspsPortSecurityEngine:
    """Core domain engine for ISPS Code Maritime Security & DoS Evaluation (Phase 246)."""

    @classmethod
    def evaluate_dos_requirement(
        cls,
        ship_level: int,
        port_level: int,
        has_dangerous_cargo: bool = False,
        is_sts_operation: bool = False,
        port_directive_active: bool = False,
    ) -> DeclarationOfSecurityResult:
        """Evaluates whether a formal Declaration of Security (DoS) must be executed under ISPS Code A/5."""
        s_lvl = MaritimeSecurityLevel(min(3, max(1, ship_level)))
        p_lvl = MaritimeSecurityLevel(min(3, max(1, port_level)))

        dos_mandatory = False
        triggers = []

        # 1. Level discrepancy: Ship operates at higher security level than port facility
        if s_lvl.value > p_lvl.value:
            dos_mandatory = True
            triggers.append(f"Cấp độ an ninh tàu ({s_lvl.value}) cao hơn cấp độ cảng ({p_lvl.value})")

        # 2. Exceptional condition: Either entity is at Security Level 3
        if s_lvl == MaritimeSecurityLevel.LEVEL_3 or p_lvl == MaritimeSecurityLevel.LEVEL_3:
            dos_mandatory = True
            triggers.append("Đang áp dụng Cấp độ an ninh 3 (Nguy cơ an ninh đặc biệt/khẩn cấp)")

        # 3. Operations involving dangerous cargo or STS transfer at heightened levels
        if has_dangerous_cargo and (s_lvl.value >= 2 or p_lvl.value >= 2):
            dos_mandatory = True
            triggers.append("Xếp dỡ hàng nguy hiểm tại Cấp độ an ninh tăng cường")

        if is_sts_operation:
            dos_mandatory = True
            triggers.append("Hoạt động chuyển tải từ tàu sang tàu (Ship-to-Ship Transfer)")

        if port_directive_active:
            dos_mandatory = True
            triggers.append("Yêu cầu chỉ đạo trực tiếp của Cảng vụ hàng hải địa phương")

        # Operative security parameters based on governing highest level
        max_level = max(s_lvl.value, p_lvl.value)
        if max_level == 3:
            screening_pct = 100.0
            patrol_interval = 15  # Patrol every 15 minutes
            guard_deploy_time = 0  # Continuous armed / static guard
        elif max_level == 2:
            screening_pct = 50.0  # 50% random bag/cargo screening
            patrol_interval = 60  # Patrol every 60 minutes
            guard_deploy_time = 5  # Deploy within 5 minutes
        else:
            screening_pct = 10.0  # 10% random sample screening
            patrol_interval = 180  # Patrol every 3 hours
            guard_deploy_time = 15  # Deploy within 15 minutes

        trigger_str = "; ".join(triggers) if triggers else "Không bắt buộc ký DoS (Cả hai bên cùng Cấp độ 1 tiêu chuẩn)"

        # Generate cryptographic audit hash
        audit_payload = f"{s_lvl.value}:{p_lvl.value}:{dos_mandatory}:{has_dangerous_cargo}:{is_sts_operation}"
        sec_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()[:16].upper()

        return DeclarationOfSecurityResult(
            ship_security_level=s_lvl,
            port_security_level=p_lvl,
            dos_mandatory=dos_mandatory,
            governing_trigger=trigger_str,
            access_screening_pct=screening_pct,
            max_patrol_interval_mins=patrol_interval,
            guard_deployment_time_mins=guard_deploy_time,
            security_hash=f"ISPS-DOS-{sec_hash}",
        )

    @classmethod
    def calculate_tvc_risk_score(
        cls,
        facility_name: str,
        threat: int,
        vulnerability: int,
        consequence: int,
    ) -> ThreatVulnerabilityAssessment:
        """Calculates security threat score using Threat x Vulnerability x Consequence (TVC) matrix."""
        t = min(5, max(1, threat))
        v = min(5, max(1, vulnerability))
        c = min(5, max(1, consequence))

        score = t * v * c  # Range: 1 to 125

        if score <= 20:
            tier = SecurityRiskTier.LOW
            rec_level = MaritimeSecurityLevel.LEVEL_1
            measures = [
                "Duy trì kiểm soát cổng ra vào cảng 24/7 theo quy trình Cấp độ 1",
                "Kiểm tra thẻ an ninh nhận dạng của 100% nhân sự vào cầu cảng",
                "Tuần tra chu vi định kỳ 3 giờ/lần",
            ]
        elif score <= 50:
            tier = SecurityRiskTier.MEDIUM
            rec_level = MaritimeSecurityLevel.LEVEL_1
            measures = [
                "Tăng cường kiểm tra ngẫu nhiên phương tiện lên 25%",
                "Rà soát hệ thống chiếu sáng khu vực hạn chế và bãi chứa hàng",
                "Giảm khoảng cách tuần tra bảo vệ xuống 90 phút/lần",
            ]
        elif score <= 80:
            tier = SecurityRiskTier.HIGH
            rec_level = MaritimeSecurityLevel.LEVEL_2
            measures = [
                "Thiết lập Cấp độ an ninh 2 (Tăng cường)",
                "Kiểm tra soi chiếu tối thiểu 50% hàng hóa và hành lý",
                "Tăng cường gấp đôi lực lượng bảo vệ tại các chốt kiểm soát",
                "Giới hạn số lượng cổng ra vào khu vực cầu tàu",
            ]
        else:
            tier = SecurityRiskTier.CRITICAL
            rec_level = MaritimeSecurityLevel.LEVEL_3
            measures = [
                "BAN HÀNH CẤP ĐỘ AN NINH 3 (KHẨN CẤP / ĐẶC BIỆT)",
                "Đình chỉ ngay lập tức các hoạt động làm hàng không thiết yếu",
                "Soi chiếu an ninh 100% người, phương tiện và hàng hóa",
                "Phối hợp Bộ đội Biên phòng và Cảnh sát giao thông đường thủy phong tỏa luồng",
                "Bố trí lực lượng có vũ trang bảo vệ khu vực trọng yếu",
            ]

        return ThreatVulnerabilityAssessment(
            facility_name=facility_name,
            threat_likelihood=t,
            vulnerability_level=v,
            consequence_severity=c,
            risk_score=score,
            risk_tier=tier,
            recommended_level=rec_level,
            mitigation_measures=measures,
        )
