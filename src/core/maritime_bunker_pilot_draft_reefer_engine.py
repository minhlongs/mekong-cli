"""Maritime Bunkering MFM Dispute, Tidal Pilotage, Draft Survey, and Reefer Claim Suite.

Phases 311-314 Simplest Viable Maritime Operational Engine.
- Phase 311: Bunkering Mass Flow Meter (MFM) Discrepancy & Dispute Resolver (SS 600 / SS 648)
- Phase 312: Seaport Pilotage Booking & Tidal Window Clearance (TT 39/2023/TT-BGTVT)
- Phase 313: Draft Survey Cargo Displacement & Constant Calculator (UN ECE Code)
- Phase 314: Reefer Container Temperature Excursion & Cargo Claim Analyzer
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional


# ==============================================================================
# Phase 311: Bunkering MFM Discrepancy & Dispute Resolver
# ==============================================================================

@dataclass
class BunkerDisputeInput:
    bunker_delivery_note_no: str
    vessel_name: str
    barge_name: str
    fuel_grade: str                     # e.g., VLSFO 0.5%, MGO 0.1%
    mfm_delivered_mt: float             # Metric tons delivered as measured by Barge MFM
    vessel_received_mt: float           # Metric tons measured by ship sounding
    bdn_density_kg_m3: float            # Density at 15°C from BDN (e.g., 985.0 kg/m3)
    ship_measured_density_kg_m3: float  # Density tested on ship hydrometer/sample


@dataclass
class BunkerDisputeResult:
    bdn_no: str
    vessel_name: str
    mfm_delivered_mt: float
    vessel_received_mt: float
    discrepancy_mt: float
    discrepancy_pct: float
    is_disputed: bool
    cappuccino_suspected: bool
    dispute_level: str                  # NORMAL | WARNING | FORMAL_PROTEST
    notice_of_protest_required: bool
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bdn_no": self.bdn_no,
            "vessel_name": self.vessel_name,
            "mfm_delivered_mt": self.mfm_delivered_mt,
            "vessel_received_mt": self.vessel_received_mt,
            "discrepancy_mt": round(self.discrepancy_mt, 3),
            "discrepancy_pct": round(self.discrepancy_pct, 2),
            "is_disputed": self.is_disputed,
            "cappuccino_suspected": self.cappuccino_suspected,
            "dispute_level": self.dispute_level,
            "notice_of_protest_required": self.notice_of_protest_required,
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class BunkerMfmDisputeEngine:
    """SS 600 / SS 648 MFM Discrepancy & Cappuccino Bunker Detector."""

    TOLERANCE_PCT = 0.5  # International maritime standard tolerance: 0.5%
    DENSITY_DIFF_THRESHOLD_KG_M3 = 3.0  # Suspect aeration if measured density < BDN density by > 3 kg/m3

    @classmethod
    def evaluate_discrepancy(cls, data: BunkerDisputeInput) -> BunkerDisputeResult:
        # Discrepancy = MFM - Ship
        diff_mt = data.mfm_delivered_mt - data.vessel_received_mt
        diff_pct = (abs(diff_mt) / max(data.mfm_delivered_mt, 0.001)) * 100.0

        # Check for Cappuccino Bunker (aerated fuel creating false volume/density drop)
        density_drop = data.bdn_density_kg_m3 - data.ship_measured_density_kg_m3
        cappuccino_suspected = (density_drop >= cls.DENSITY_DIFF_THRESHOLD_KG_M3) and (diff_mt > 0)

        if diff_pct <= cls.TOLERANCE_PCT:
            is_disputed = False
            dispute_level = "NORMAL"
            nop_required = False
            remarks = (f"Chênh lệch số liệu cấp dầu {diff_pct:.2f}% nằm trong ngưỡng dung sai quốc tế cho phép (<= {cls.TOLERANCE_PCT}%). "
                       f"Chấp nhận số liệu MFM để ký nhận BDN.")
        elif diff_pct <= 1.0:
            is_disputed = True
            dispute_level = "WARNING"
            nop_required = True
            remarks = (f"CẢNH BÁO: Chênh lệch {diff_pct:.2f}% ({diff_mt:.2f} MT) vượt dung sai 0.5%. "
                       f"Khuyến nghị lập Biên bản ghi nhận chênh lệch (Letter of Discrepancy) kèm chữ ký hai bên.")
        else:
            is_disputed = True
            dispute_level = "FORMAL_PROTEST"
            nop_required = True
            remarks = (f"TRANH CHẤP NGHIÊM TRỌNG: Chênh lệch thiếu hụt {diff_pct:.2f}% ({diff_mt:.2f} MT). "
                       f"Bắt buộc thuyền trưởng phát hành Thư kháng nghị chính thức (Notice of Protest - NoP) "
                       f"và niêm phong mẫu dầu đại diện (Bunker Manifold Sample).")

        if cappuccino_suspected:
            remarks += f" [CẢNH BÁO BỌT KHÍ]: Tỷ trọng thực tế giảm {density_drop:.1f} kg/m³ so với BDN. Nghi vấn hiện tượng sục khí (Cappuccino Bunkers)!"

        raw = f"{data.bunker_delivery_note_no}|{data.vessel_name}|{diff_mt:.3f}|{cappuccino_suspected}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return BunkerDisputeResult(
            bdn_no=data.bunker_delivery_note_no,
            vessel_name=data.vessel_name,
            mfm_delivered_mt=data.mfm_delivered_mt,
            vessel_received_mt=data.vessel_received_mt,
            discrepancy_mt=diff_mt,
            discrepancy_pct=diff_pct,
            is_disputed=is_disputed,
            cappuccino_suspected=cappuccino_suspected,
            dispute_level=dispute_level,
            notice_of_protest_required=nop_required,
            remarks=remarks,
            audit_hash=token,
        )


# ==============================================================================
# Phase 312: Seaport Pilotage Booking & Tidal Window Clearance
# ==============================================================================

@dataclass
class HourlyTide:
    hour: int          # 0 to 23
    tide_height_m: float


@dataclass
class PilotageWindowInput:
    vessel_name: str
    grt: float
    static_draft_m: float
    channel_depth_datum_m: float     # Độ sâu luồng chuẩn tắc (hải đồ)
    speed_knots: float = 10.0
    transit_duration_hours: int = 2  # Thời gian hành hải trong luồng
    channel_distance_nm: float = 20.0 # Chiều dài đoạn luồng (hải lý)
    hourly_tides: List[HourlyTide] = field(default_factory=list)


@dataclass
class PilotageClearanceResult:
    vessel_name: str
    static_draft_m: float
    squat_allowance_m: float
    required_ukc_m: float
    min_water_depth_needed_m: float
    eligible_transit_hours: List[int] # Danh sách các khung giờ bắt đầu hợp lệ
    is_clearance_granted: bool
    estimated_pilot_dues_vnd: float
    remarks: str
    clearance_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "static_draft_m": self.static_draft_m,
            "squat_allowance_m": round(self.squat_allowance_m, 2),
            "required_ukc_m": round(self.required_ukc_m, 2),
            "min_water_depth_needed_m": round(self.min_water_depth_needed_m, 2),
            "eligible_transit_hours": self.eligible_transit_hours,
            "is_clearance_granted": self.is_clearance_granted,
            "estimated_pilot_dues_vnd": round(self.estimated_pilot_dues_vnd, 0),
            "remarks": self.remarks,
            "clearance_hash": self.clearance_hash,
        }


class PilotageTidalWindowEngine:
    """Tidal Window Under Keel Clearance (UKC) & TT 39/2023 Pilot Dues."""

    @classmethod
    def evaluate_clearance_and_booking(cls, req: PilotageWindowInput) -> PilotageClearanceResult:
        # Standard squat calculation approximation: Squat (m) = (Speed_knots / 10)^2 * 0.5 (for open/semi-confined channel)
        squat_allowance = ((req.speed_knots / 10.0) ** 2) * 0.5
        # Under Keel Clearance standard: 10% of static draft, minimum 1.0 meter
        min_ukc = max(req.static_draft_m * 0.10, 1.0)
        min_depth_needed = req.static_draft_m + squat_allowance + min_ukc

        # Evaluate tidal window
        tide_map = {t.hour: t.tide_height_m for t in req.hourly_tides}
        eligible_hours: List[int] = []

        for start_h in range(24):
            can_transit = True
            for transit_h in range(start_h, start_h + req.transit_duration_hours):
                current_h = transit_h % 24
                tide_h = tide_map.get(current_h, 0.0)
                available_depth = req.channel_depth_datum_m + tide_h
                if available_depth < min_depth_needed:
                    can_transit = False
                    break
            if can_transit:
                eligible_hours.append(start_h)

        is_cleared = len(eligible_hours) > 0

        # Pilotage dues calculation under Circular 39/2023/TT-BGTVT
        # Base formula: GRT * Distance (NM) * Rate (VND/GRT-NM) + Minimum base fee
        # Simplified rate: 65 VND / GRT-NM (standard seaport channel rate) with min cap 3,000,000 VND
        calculated_dues = max(req.grt * req.channel_distance_nm * 65.0, 3_000_000.0)

        if is_cleared:
            time_slots_str = ", ".join([f"{h:02d}:00" for h in eligible_hours[:6]])
            if len(eligible_hours) > 6:
                time_slots_str += "..."
            remarks = (f"ĐỦ ĐIỀU KIỆN QUA LUỒNG: Độ sâu tối thiểu cần {min_depth_needed:.2f}m (Mớn {req.static_draft_m}m + Squat {squat_allowance:.2f}m + UKC {min_ukc:.2f}m). "
                       f"Cửa sổ triều khả dụng: {len(eligible_hours)} giờ (Khung giờ bắt đầu: {time_slots_str}).")
        else:
            remarks = (f"TỪ CHỐI QUA LUỒNG: Mớn nước an toàn yêu cầu {min_depth_needed:.2f}m vượt quá độ sâu luồng kết hợp thủy triều. "
                       f"Tàu cần giảm tải (lightering) hoặc chờ chu kỳ triều cường.")

        raw = f"{req.vessel_name}|{req.static_draft_m}|{is_cleared}|{len(eligible_hours)}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return PilotageClearanceResult(
            vessel_name=req.vessel_name,
            static_draft_m=req.static_draft_m,
            squat_allowance_m=squat_allowance,
            required_ukc_m=min_ukc,
            min_water_depth_needed_m=min_depth_needed,
            eligible_transit_hours=eligible_hours,
            is_clearance_granted=is_cleared,
            estimated_pilot_dues_vnd=calculated_dues,
            remarks=remarks,
            clearance_hash=token,
        )


# ==============================================================================
# Phase 313: Draft Survey Cargo Displacement & Constant Calculator
# ==============================================================================

@dataclass
class DraftMarks:
    fwd_port: float
    fwd_stbd: float
    mid_port: float
    mid_stbd: float
    aft_port: float
    aft_stbd: float


@dataclass
class DraftSurveyInput:
    survey_id: str
    vessel_name: str
    draft_marks: DraftMarks
    table_displacement_mt: float     # Lượng dãn nước tra bảng thủy tĩnh tại Quarter Mean Draft
    tpc: float                       # Tấn trên 1 cm mớn nước (Tonnes per Centimetre)
    lcf_m: float                     # Khoảng cách từ trọng tâm diện tích mặt đường thủy đến giữa tàu (LCF)
    lbp_m: float                     # Chiều dài giữa 2 đường thẳng vuông góc (Length Between Perpendiculars)
    measured_water_density: float    # Tỷ trọng nước đo thực tế (ví dụ 1.018 t/m³)
    deductible_weights_mt: float     # Tổng trọng lượng ballast, nhiên liệu, nước ngọt đo được


@dataclass
class DraftSurveyResult:
    survey_id: str
    vessel_name: str
    quarter_mean_draft_m: float
    apparent_trim_m: float
    first_trim_correction_mt: float
    density_corrected_disp_mt: float
    net_displacement_mt: float
    remarks: str
    survey_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "survey_id": self.survey_id,
            "vessel_name": self.vessel_name,
            "quarter_mean_draft_m": round(self.quarter_mean_draft_m, 3),
            "apparent_trim_m": round(self.apparent_trim_m, 3),
            "first_trim_correction_mt": round(self.first_trim_correction_mt, 2),
            "density_corrected_disp_mt": round(self.density_corrected_disp_mt, 2),
            "net_displacement_mt": round(self.net_displacement_mt, 2),
            "remarks": self.remarks,
            "survey_hash": self.survey_hash,
        }


class DraftSurveyEngine:
    """UN ECE Code of Uniform Standards for Draft Survey."""

    STANDARD_SEA_DENSITY = 1.025  # Standard salt water density in t/m³

    @classmethod
    def calculate_draft_survey(cls, inp: DraftSurveyInput) -> DraftSurveyResult:
        dm = inp.draft_marks
        # Calculate mean drafts
        fwd_mean = (dm.fwd_port + dm.fwd_stbd) / 2.0
        mid_mean = (dm.mid_port + dm.mid_stbd) / 2.0
        aft_mean = (dm.aft_port + dm.aft_stbd) / 2.0

        # Mean of Means (Quarter Mean Draft - D_QM) according to UN ECE Code
        # D_QM = (Fwd_Mean + 6 * Mid_Mean + Aft_Mean) / 8
        quarter_mean = (fwd_mean + 6.0 * mid_mean + aft_mean) / 8.0

        # Apparent Trim (Trim = Aft - Fwd)
        apparent_trim = aft_mean - fwd_mean

        # First Trim Correction (tấn) = (Trim * LCF * TPC * 100) / LBP
        first_trim_corr = (apparent_trim * inp.lcf_m * inp.tpc * 100.0) / max(inp.lbp_m, 1.0)

        # Displacement corrected for trim
        trim_corr_disp = inp.table_displacement_mt + first_trim_corr

        # Density Correction: Disp_corr = Disp_trim * (Density_measured / 1.025)
        density_corr_disp = trim_corr_disp * (inp.measured_water_density / cls.STANDARD_SEA_DENSITY)

        # Net Displacement after deducting non-cargo weights (Ballast, Fuel, Fresh water)
        net_disp = density_corr_disp - inp.deductible_weights_mt

        remarks = (f"Giám định mớn nước: Mớn trung bình D_QM = {quarter_mean:.3f}m, Trim = {apparent_trim:+.3f}m. "
                   f"Hiệu chỉnh Trim 1st: {first_trim_corr:+.2f} MT, Tỷ trọng nước ({inp.measured_water_density:.3f} t/m³). "
                   f"Lượng dãn nước thực: {density_corr_disp:,.2f} MT -> Trừ dằn/dầu: Khối lượng tịnh = {net_disp:,.2f} MT.")

        raw = f"{inp.survey_id}|{inp.vessel_name}|{quarter_mean:.3f}|{net_disp:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return DraftSurveyResult(
            survey_id=inp.survey_id,
            vessel_name=inp.vessel_name,
            quarter_mean_draft_m=quarter_mean,
            apparent_trim_m=apparent_trim,
            first_trim_correction_mt=first_trim_corr,
            density_corrected_disp_mt=density_corr_disp,
            net_displacement_mt=net_disp,
            remarks=remarks,
            survey_hash=token,
        )


# ==============================================================================
# Phase 314: Reefer Container Temperature Excursion & Cargo Claim Analyzer
# ==============================================================================

class ReeferCargoType(str, Enum):
    FROZEN_SEAFOOD = "FROZEN_SEAFOOD"  # Set-point: -20°C (Tolerance: +2.0°C)
    FROZEN_MEAT = "FROZEN_MEAT"        # Set-point: -18°C (Tolerance: +2.0°C)
    FRESH_FRUIT = "FRESH_FRUIT"        # Set-point: +4°C (Tolerance: +/-1.5°C)
    PHARMACEUTICALS = "PHARMA"         # Set-point: +5°C (Tolerance: +/-1.0°C)


@dataclass
class ReeferTempLog:
    timestamp_hour: int
    actual_temp_c: float
    stage: str                         # GATE_IN | YARD_STACK | VESSEL_VOYAGE | DISCHARGE


@dataclass
class ReeferClaimInput:
    container_no: str
    cargo_type: ReeferCargoType
    set_point_c: float
    tolerance_c: float
    temp_logs: List[ReeferTempLog]
    cargo_invoice_value_usd: float


@dataclass
class ReeferClaimResult:
    container_no: str
    cargo_type: str
    set_point_c: float
    max_recorded_temp_c: float
    excursion_hours: int
    accumulated_degree_hours: float
    is_claim_valid: bool
    liable_party: str                  # TERMINAL | CARRIER | SHIPPER | NONE
    recommended_compensation_usd: float
    remarks: str
    claim_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "container_no": self.container_no,
            "cargo_type": self.cargo_type,
            "set_point_c": self.set_point_c,
            "max_recorded_temp_c": round(self.max_recorded_temp_c, 1),
            "excursion_hours": self.excursion_hours,
            "accumulated_degree_hours": round(self.accumulated_degree_hours, 2),
            "is_claim_valid": self.is_claim_valid,
            "liable_party": self.liable_party,
            "recommended_compensation_usd": round(self.recommended_compensation_usd, 2),
            "remarks": self.remarks,
            "claim_hash": self.claim_hash,
        }


class ReeferClaimEngine:
    """Reefer Temperature Excursion & Cold Chain Liability Adjudicator."""

    @classmethod
    def analyze_claim(cls, req: ReeferClaimInput) -> ReeferClaimResult:
        upper_limit = req.set_point_c + req.tolerance_c
        max_temp = -999.0
        excursion_hours = 0
        degree_hours = 0.0
        stage_violations: Dict[str, int] = {}

        for log in req.temp_logs:
            if log.actual_temp_c > max_temp:
                max_temp = log.actual_temp_c

            if log.actual_temp_c > upper_limit:
                excursion_hours += 1
                excess = log.actual_temp_c - upper_limit
                degree_hours += excess
                stage_violations[log.stage] = stage_violations.get(log.stage, 0) + 1

        # Check if cargo initially warm at gate-in
        is_warm_stuffing = False
        if req.temp_logs and req.temp_logs[0].stage == "GATE_IN":
            if req.temp_logs[0].actual_temp_c > upper_limit + 2.0:
                is_warm_stuffing = True

        is_claim_valid = excursion_hours >= 3 or degree_hours >= 10.0
        liable_party = "NONE"
        compensation_usd = 0.0

        if is_claim_valid:
            if is_warm_stuffing:
                liable_party = "SHIPPER"
                remarks = (f"TỪ CHỐI BỒI THƯỜNG HÃNG TÀU/CẢNG: Hàng hóa đã bị quá nhiệt trước khi đóng bãi ({req.temp_logs[0].actual_temp_c}°C ngay tại Gate-in). "
                           f"Lỗi thuộc về Shipper (Warm Stuffing/Không tiền kiểm lạnh).")
            else:
                yard_viols = stage_violations.get("YARD_STACK", 0)
                vessel_viols = stage_violations.get("VESSEL_VOYAGE", 0)

                if yard_viols >= vessel_viols and yard_viols > 0:
                    liable_party = "TERMINAL"
                    # Compensation formula: based on damage ratio (proportional to degree hours)
                    damage_ratio = min(degree_hours / 50.0, 1.0)
                    compensation_usd = req.cargo_invoice_value_usd * damage_ratio
                    remarks = (f"KHIẾU NẠI HỢP LỆ: Vi phạm nhiệt độ tại bãi cảng {yard_viols}h (chậm cắm điện/mất nguồn). "
                               f"Trách nhiệm thuộc về Cảng khai thác (Terminal Operator). Mức bồi thường đề xuất: ${compensation_usd:,.2f} USD.")
                else:
                    liable_party = "CARRIER"
                    damage_ratio = min(degree_hours / 50.0, 1.0)
                    compensation_usd = req.cargo_invoice_value_usd * damage_ratio
                    remarks = (f"KHIẾU NẠI HỢP LỆ: Sự cố máy lạnh trong quá trình hành hải ({vessel_viols}h vi phạm). "
                               f"Trách nhiệm thuộc về Hãng tàu (Ocean Carrier). Mức bồi thường đề xuất: ${compensation_usd:,.2f} USD.")
        else:
            remarks = (f"NHIỆT ĐỘ TRONG NGƯỠNG AN TOÀN: Dao động nhiệt độ không vượt quá dung sai cho phép hoặc dưới 3 giờ liên tục. "
                       f"Không phát sinh tổn thất hàng hóa có thể bồi thường.")

        raw = f"{req.container_no}|{excursion_hours}|{degree_hours:.2f}|{liable_party}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return ReeferClaimResult(
            container_no=req.container_no,
            cargo_type=req.cargo_type.value,
            set_point_c=req.set_point_c,
            max_recorded_temp_c=max_temp if max_temp != -999.0 else req.set_point_c,
            excursion_hours=excursion_hours,
            accumulated_degree_hours=degree_hours,
            is_claim_valid=is_claim_valid,
            liable_party=liable_party,
            recommended_compensation_usd=compensation_usd,
            remarks=remarks,
            claim_hash=token,
        )
