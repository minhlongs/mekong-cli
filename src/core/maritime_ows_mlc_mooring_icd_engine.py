"""Mekong Maritime OWS 15 ppm, MLC Seafarer Wages, Mooring Tariffs & ICD Transit Engine.

Phases 283-286 of Mekong Maritime Operations, Secured Finance & Customs Logistics Suite:
- Phase 283: Oil Water Separator (OWS) 15 ppm, 3-Way Fail-Safe Recirculation & ORB Part I Engine (MARPOL Annex I Reg. 14/15, MEPC.107(49)).
- Phase 284: Seafarers Employment Agreement (SEA), MLC 2006 Wages & Repatriation Escrow Engine (MLC 2006 Title 2, VMC 2015 Arts. 58-64).
- Phase 285: Port Mooring & Unmooring Tariffs, Night Surcharges & MEG4 Mooring Safety Engine (Circular 39/2023/TT-BGTVT, OCIMF MEG4).
- Phase 286: Inland Clearance Depot (ICD) Transit, OLA Declaration & Customs Feeder Corridor Engine (Law on Customs 2014, Decree 08/2015/NĐ-CP).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import math


# ==============================================================================
# Phase 283: OWS 15 ppm & Oil Record Book Engine
# ==============================================================================

class OwsComplianceStatus(str, Enum):
    COMPLIANT_DISCHARGE = "COMPLIANT_DISCHARGE"
    VALVE_AUTO_RECIRCULATE = "VALVE_AUTO_RECIRCULATE"
    PROHIBITED_LOCATION = "PROHIBITED_LOCATION"
    VESSEL_NOT_EN_ROUTE = "VESSEL_NOT_EN_ROUTE"
    EQUIPMENT_FAULT = "EQUIPMENT_FAULT"


@dataclass
class OwsDischargeInput:
    vessel_name: str
    imo_number: str
    oil_content_ppm: float
    vessel_speed_knots: float
    distance_from_land_nm: float
    is_special_area: bool = False
    flow_rate_m3_h: float = 2.5
    discharge_duration_minutes: float = 60.0
    fail_safe_valve_operational: bool = True


@dataclass
class OwsDischargeResult:
    vessel_name: str
    imo_number: str
    oil_content_ppm: float
    compliance_status: OwsComplianceStatus
    valve_position: str  # "OVERBOARD" or "RECIRCULATE_TO_HOLDING_TANK"
    total_discharged_m3: float
    orb_code: str
    orb_entry: str
    action_required: str
    verification_token: str

    def to_dict(self) -> dict:
        return {
            "vessel_name": self.vessel_name,
            "imo_number": self.imo_number,
            "oil_content_ppm": self.oil_content_ppm,
            "compliance_status": self.compliance_status.value,
            "valve_position": self.valve_position,
            "total_discharged_m3": self.total_discharged_m3,
            "orb_code": self.orb_code,
            "orb_entry": self.orb_entry,
            "action_required": self.action_required,
            "verification_token": self.verification_token,
        }


class OwsDischargeEngine:
    MAX_ALLOWABLE_OIL_PPM: float = 15.0
    MIN_DISTANCE_LAND_NM: float = 12.0
    MIN_VESSEL_SPEED_KNOTS: float = 0.5

    @classmethod
    def evaluate_discharge(cls, sample: OwsDischargeInput) -> OwsDischargeResult:
        if not sample.fail_safe_valve_operational:
            status = OwsComplianceStatus.EQUIPMENT_FAULT
            valve = "RECIRCULATE_TO_HOLDING_TANK"
            action = "Lỗi hệ thống van an toàn 3 ngả hoặc cảm biến 15 ppm. Dừng xả, cô lập thiết bị."
            discharged = 0.0
        elif sample.oil_content_ppm >= cls.MAX_ALLOWABLE_OIL_PPM:
            status = OwsComplianceStatus.VALVE_AUTO_RECIRCULATE
            valve = "RECIRCULATE_TO_HOLDING_TANK"
            action = f"Nồng độ dầu {sample.oil_content_ppm:.1f} ppm >= 15.0 ppm. Van 3 ngả tự động ngắt xả qua mạn, hồi lưu về két la-gông."
            discharged = 0.0
        elif sample.distance_from_land_nm < cls.MIN_DISTANCE_LAND_NM or sample.is_special_area:
            status = OwsComplianceStatus.PROHIBITED_LOCATION
            valve = "RECIRCULATE_TO_HOLDING_TANK"
            action = "Khu vực cấm xả: Cự ly bờ < 12 NM hoặc nằm trong vùng biển đặc biệt (MARPOL Special Area)."
            discharged = 0.0
        elif sample.vessel_speed_knots < cls.MIN_VESSEL_SPEED_KNOTS:
            status = OwsComplianceStatus.VESSEL_NOT_EN_ROUTE
            valve = "RECIRCULATE_TO_HOLDING_TANK"
            action = "Tàu không đang hành trình (vận tốc < 0.5 knots). Không được phép xả nước la-gông qua mạn."
            discharged = 0.0
        else:
            status = OwsComplianceStatus.COMPLIANT_DISCHARGE
            valve = "OVERBOARD"
            action = "Đạt chuẩn MARPOL Annex I Reg. 15. Xả qua mạn an toàn dưới sự giám sát của thiết bị báo động 15 ppm."
            discharged = round((sample.flow_rate_m3_h * sample.discharge_duration_minutes) / 60.0, 3)

        orb_code = "Code D (Item 15.2)"
        orb_entry = (
            f"Tàu {sample.vessel_name} (IMO {sample.imo_number}): Xử lý nước la-gông qua OWS MEPC.107(49). "
            f"Nồng độ dầu: {sample.oil_content_ppm:.1f} ppm. Vận tốc: {sample.vessel_speed_knots} kts. "
            f"Vị trí van: {valve}. Khối lượng xả qua mạn: {discharged} m3."
        )

        token_raw = f"{sample.vessel_name}:{sample.imo_number}:{sample.oil_content_ppm}:{status}:{valve}:{discharged}"
        token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        return OwsDischargeResult(
            vessel_name=sample.vessel_name,
            imo_number=sample.imo_number,
            oil_content_ppm=sample.oil_content_ppm,
            compliance_status=status,
            valve_position=valve,
            total_discharged_m3=discharged,
            orb_code=orb_code,
            orb_entry=orb_entry,
            action_required=action,
            verification_token=token,
        )


# ==============================================================================
# Phase 284: MLC 2006 Seafarer Wages & Repatriation Escrow Engine
# ==============================================================================

@dataclass
class SeafarerContractInput:
    seafarer_name: str
    rank: str
    nationality: str = "Vietnam"
    basic_monthly_wage_usd: float = 750.0
    contract_months: int = 9
    actual_monthly_overtime_hours: float = 60.0
    guaranteed_overtime_hours: float = 48.0
    responsibility_allowance_usd: float = 100.0
    subsistence_allowance_usd: float = 50.0
    pni_repatriation_bond_amount_usd: float = 12000.0


@dataclass
class MlcWagesStatement:
    seafarer_name: str
    rank: str
    basic_monthly_wage_usd: float
    hourly_basic_rate_usd: float
    overtime_hourly_rate_usd: float
    payable_overtime_hours: float
    overtime_pay_usd: float
    paid_annual_leave_pay_usd: float
    allowances_total_usd: float
    gross_monthly_wage_usd: float
    gross_monthly_wage_vnd: float
    abandonment_reserve_4m_usd: float
    repatriation_bond_adequate: bool
    mlc_wage_compliant: bool
    sea_auth_token: str

    def to_dict(self) -> dict:
        return {
            "seafarer_name": self.seafarer_name,
            "rank": self.rank,
            "basic_monthly_wage_usd": self.basic_monthly_wage_usd,
            "hourly_basic_rate_usd": self.hourly_basic_rate_usd,
            "overtime_hourly_rate_usd": self.overtime_hourly_rate_usd,
            "payable_overtime_hours": self.payable_overtime_hours,
            "overtime_pay_usd": self.overtime_pay_usd,
            "paid_annual_leave_pay_usd": self.paid_annual_leave_pay_usd,
            "allowances_total_usd": self.allowances_total_usd,
            "gross_monthly_wage_usd": self.gross_monthly_wage_usd,
            "gross_monthly_wage_vnd": self.gross_monthly_wage_vnd,
            "abandonment_reserve_4m_usd": self.abandonment_reserve_4m_usd,
            "repatriation_bond_adequate": self.repatriation_bond_adequate,
            "mlc_wage_compliant": self.mlc_wage_compliant,
            "sea_auth_token": self.sea_auth_token,
        }


class MlcSeafarerWagesEngine:
    STANDARD_MONTHLY_HOURS: float = 208.0
    MIN_OVERTIME_MULTIPLIER: float = 1.25
    MIN_LEAVE_DAYS_PER_MONTH: float = 2.5
    USD_TO_VND_RATE: float = 25000.0
    MIN_AB_BASIC_WAGE_ILO: float = 658.0  # ILO / ITF reference minimum for AB

    @classmethod
    def calculate_wages_and_escrow(cls, contract: SeafarerContractInput) -> MlcWagesStatement:
        hourly_basic = round(contract.basic_monthly_wage_usd / cls.STANDARD_MONTHLY_HOURS, 2)
        ot_rate = round(hourly_basic * cls.MIN_OVERTIME_MULTIPLIER, 2)
        payable_ot_hours = max(contract.actual_monthly_overtime_hours, contract.guaranteed_overtime_hours)
        overtime_pay = round(payable_ot_hours * ot_rate, 2)

        # Paid annual leave accrual: 2.5 days per month of service
        daily_basic_wage = contract.basic_monthly_wage_usd / 30.0
        paid_leave_pay = round(daily_basic_wage * cls.MIN_LEAVE_DAYS_PER_MONTH, 2)

        allowances = round(contract.responsibility_allowance_usd + contract.subsistence_allowance_usd, 2)
        gross_usd = round(contract.basic_monthly_wage_usd + overtime_pay + paid_leave_pay + allowances, 2)
        gross_vnd = round(gross_usd * cls.USD_TO_VND_RATE, 0)

        # Standard A2.5.2 abandonment reserve: 4 months of outstanding wages + repatriation
        abandonment_reserve_usd = round(4.0 * contract.basic_monthly_wage_usd, 2)
        estimated_flight_and_subsistence = 3000.0
        total_escrow_needed = abandonment_reserve_usd + estimated_flight_and_subsistence
        repatriation_adequate = contract.pni_repatriation_bond_amount_usd >= total_escrow_needed

        # Compliance check
        wage_compliant = contract.basic_monthly_wage_usd >= cls.MIN_AB_BASIC_WAGE_ILO

        token_raw = f"{contract.seafarer_name}:{contract.rank}:{gross_usd}:{repatriation_adequate}:{wage_compliant}"
        token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        return MlcWagesStatement(
            seafarer_name=contract.seafarer_name,
            rank=contract.rank,
            basic_monthly_wage_usd=contract.basic_monthly_wage_usd,
            hourly_basic_rate_usd=hourly_basic,
            overtime_hourly_rate_usd=ot_rate,
            payable_overtime_hours=payable_ot_hours,
            overtime_pay_usd=overtime_pay,
            paid_annual_leave_pay_usd=paid_leave_pay,
            allowances_total_usd=allowances,
            gross_monthly_wage_usd=gross_usd,
            gross_monthly_wage_vnd=gross_vnd,
            abandonment_reserve_4m_usd=abandonment_reserve_usd,
            repatriation_bond_adequate=repatriation_adequate,
            mlc_wage_compliant=wage_compliant,
            sea_auth_token=token,
        )


# ==============================================================================
# Phase 285: Port Mooring & Unmooring Tariffs & MEG4 Engine
# ==============================================================================

class MooringOperationType(str, Enum):
    MOORING = "MOORING"          # Buộc dây
    UNMOORING = "UNMOORING"      # Cởi dây
    SHIFTING = "SHIFTING"        # Đảo cầu bến (buộc + cởi)


@dataclass
class MooringTariffInput:
    vessel_name: str
    gross_tonnage: float
    operation_type: MooringOperationType = MooringOperationType.MOORING
    is_night_operation: bool = False
    is_holiday: bool = False
    standby_hours: float = 0.0
    mooring_line_swl_tons: float = 50.0
    mooring_line_mbl_tons: float = 90.0


@dataclass
class MooringTariffResult:
    vessel_name: str
    gross_tonnage: float
    operation_type: MooringOperationType
    base_charge_usd: float
    night_surcharge_usd: float
    holiday_surcharge_usd: float
    standby_charge_usd: float
    total_charge_usd: float
    total_charge_vnd: float
    meg4_line_tension_ratio: float
    meg4_safe: bool
    meg4_notes: str
    receipt_code: str

    def to_dict(self) -> dict:
        return {
            "vessel_name": self.vessel_name,
            "gross_tonnage": self.gross_tonnage,
            "operation_type": self.operation_type.value,
            "base_charge_usd": self.base_charge_usd,
            "night_surcharge_usd": self.night_surcharge_usd,
            "holiday_surcharge_usd": self.holiday_surcharge_usd,
            "standby_charge_usd": self.standby_charge_usd,
            "total_charge_usd": self.total_charge_usd,
            "total_charge_vnd": self.total_charge_vnd,
            "meg4_line_tension_ratio": self.meg4_line_tension_ratio,
            "meg4_safe": self.meg4_safe,
            "meg4_notes": self.meg4_notes,
            "receipt_code": self.receipt_code,
        }


class PortMooringTariffEngine:
    USD_TO_VND_RATE: float = 25000.0
    NIGHT_SURCHARGE_PCT: float = 0.40      # +40% (18:00 - 06:00)
    HOLIDAY_SURCHARGE_PCT: float = 0.50    # +50% for public holidays
    STANDBY_RATE_PER_HOUR: float = 25.0    # 25 USD / hour beyond 30 min free
    MAX_MEG4_WORKING_RATIO: float = 0.60   # SWL / MBL <= 60%

    @classmethod
    def calculate_mooring_dues(cls, input_data: MooringTariffInput) -> MooringTariffResult:
        gt = input_data.gross_tonnage

        # Tiered base pricing per Circular 39/2023/TT-BGTVT
        if gt < 2000.0:
            tier_base = 25.0
        elif gt < 5000.0:
            tier_base = 45.0
        elif gt < 10000.0:
            tier_base = 75.0
        elif gt < 20000.0:
            tier_base = 120.0
        elif gt < 50000.0:
            tier_base = 200.0
        else:
            excess_steps = math.ceil((gt - 50000.0) / 10000.0)
            tier_base = 200.0 + (excess_steps * 20.0)

        # Operation multiplier
        if input_data.operation_type == MooringOperationType.MOORING:
            op_mult = 1.0
        elif input_data.operation_type == MooringOperationType.UNMOORING:
            op_mult = 0.85
        else:  # SHIFTING
            op_mult = 1.25

        base_charge = round(tier_base * op_mult, 2)
        night_surcharge = round(base_charge * cls.NIGHT_SURCHARGE_PCT, 2) if input_data.is_night_operation else 0.0
        holiday_surcharge = round(base_charge * cls.HOLIDAY_SURCHARGE_PCT, 2) if input_data.is_holiday else 0.0

        billable_standby_hours = max(0.0, input_data.standby_hours - 0.5)
        standby_charge = round(billable_standby_hours * cls.STANDBY_RATE_PER_HOUR, 2)

        total_usd = round(base_charge + night_surcharge + holiday_surcharge + standby_charge, 2)
        total_vnd = round(total_usd * cls.USD_TO_VND_RATE, 0)

        # OCIMF MEG4 Mooring Line Safety
        if input_data.mooring_line_mbl_tons > 0.0:
            ratio = round(input_data.mooring_line_swl_tons / input_data.mooring_line_mbl_tons, 3)
        else:
            ratio = 1.0

        meg4_safe = ratio <= cls.MAX_MEG4_WORKING_RATIO
        if meg4_safe:
            notes = f"Tỷ lệ tải SWL/MBL đạt {ratio*100:.1f}% <= 60%. Đảm bảo an toàn chống đứt dây theo OCIMF MEG4."
        else:
            notes = f"CẢNH BÁO: Tỷ lệ tải SWL/MBL đạt {ratio*100:.1f}% > 60%. Nguy cơ đứt bật ngược (snap-back). Giảm tải ngay."

        token_raw = f"{input_data.vessel_name}:{gt}:{input_data.operation_type}:{total_usd}:{meg4_safe}"
        token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        return MooringTariffResult(
            vessel_name=input_data.vessel_name,
            gross_tonnage=gt,
            operation_type=input_data.operation_type,
            base_charge_usd=base_charge,
            night_surcharge_usd=night_surcharge,
            holiday_surcharge_usd=holiday_surcharge,
            standby_charge_usd=standby_charge,
            total_charge_usd=total_usd,
            total_charge_vnd=total_vnd,
            meg4_line_tension_ratio=ratio,
            meg4_safe=meg4_safe,
            meg4_notes=notes,
            receipt_code=f"MOOR-{token[:8]}",
        )


# ==============================================================================
# Phase 286: ICD Bonded Transit & OLA Declaration Engine
# ==============================================================================

class IcdTransitStatus(str, Enum):
    ON_TIME_SECURE = "ON_TIME_SECURE"
    TRANSIT_DELAY_WARNING = "TRANSIT_DELAY_WARNING"
    TRANSIT_OVERDUE_CRITICAL = "TRANSIT_OVERDUE_CRITICAL"
    SEAL_TAMPERED = "SEAL_TAMPERED"
    DUTY_GUARANTEE_DEFICIT = "DUTY_GUARANTEE_DEFICIT"


@dataclass
class IcdTransitInput:
    declaration_no: str
    container_no: str
    origin_seaport_code: str
    dest_icd_code: str
    distance_km: float
    max_transit_hours: float
    departure_time_iso: str
    arrival_time_iso: str
    customs_seal_intact: bool = True
    bank_guarantee_amount_vnd: float = 500_000_000.0
    declared_tax_liability_vnd: float = 450_000_000.0


@dataclass
class IcdTransitResult:
    declaration_no: str
    container_no: str
    actual_transit_hours: float
    max_transit_hours: float
    transit_status: IcdTransitStatus
    customs_clearance_granted: bool
    duty_coverage_ratio: float
    action_directive: str
    tracking_token: str

    def to_dict(self) -> dict:
        return {
            "declaration_no": self.declaration_no,
            "container_no": self.container_no,
            "actual_transit_hours": self.actual_transit_hours,
            "max_transit_hours": self.max_transit_hours,
            "transit_status": self.transit_status.value,
            "customs_clearance_granted": self.customs_clearance_granted,
            "duty_coverage_ratio": self.duty_coverage_ratio,
            "action_directive": self.action_directive,
            "tracking_token": self.tracking_token,
        }


class IcdBondedTransitEngine:
    CRITICAL_DELAY_THRESHOLD_HOURS: float = 6.0

    @classmethod
    def supervise_icd_transit(cls, data: IcdTransitInput) -> IcdTransitResult:
        try:
            dep = datetime.fromisoformat(data.departure_time_iso)
            arr = datetime.fromisoformat(data.arrival_time_iso)
            duration_hours = round(max(0.0, (arr - dep).total_seconds() / 3600.0), 2)
        except Exception:
            duration_hours = 0.0

        coverage_ratio = round(data.bank_guarantee_amount_vnd / max(1.0, data.declared_tax_liability_vnd), 3)

        if not data.customs_seal_intact:
            status = IcdTransitStatus.SEAL_TAMPERED
            clearance = False
            action = "CẢNH BÁO NIÊM PHONG: Seal hải quan bị rách hoặc đứt. Niêm phong lại và chuyển sang luồng Đỏ kiểm tra 100%."
        elif coverage_ratio < 1.0:
            status = IcdTransitStatus.DUTY_GUARANTEE_DEFICIT
            clearance = False
            action = f"THIẾU HỤT BẢO LÃNH: Mức bảo lãnh chỉ đạt {coverage_ratio*100:.1f}% số thuế phải nộp. Yêu cầu nộp bổ sung bảo lãnh ngân hàng."
        elif duration_hours > (data.max_transit_hours + cls.CRITICAL_DELAY_THRESHOLD_HOURS):
            status = IcdTransitStatus.TRANSIT_OVERDUE_CRITICAL
            clearance = False
            action = f"QUÁ HẠN NGHIÊM TRỌNG: Quá thời gian quy định > {cls.CRITICAL_DELAY_THRESHOLD_HOURS}h. Nghi vấn tẩu tán hàng, chuyển cơ quan điều tra."
        elif duration_hours > data.max_transit_hours:
            status = IcdTransitStatus.TRANSIT_DELAY_WARNING
            clearance = True  # Conditional clearance pending explanation
            action = "CHẬM HÀNH TRÌNH: Yêu cầu doanh nghiệp giải trình lý do ùn tắc đường bộ trước khi cấp phép giải phóng hàng."
        else:
            status = IcdTransitStatus.ON_TIME_SECURE
            clearance = True
            action = "ĐỦ ĐIỀU KIỆN THÔNG QUAN: Hàng vận chuyển đúng lộ trình, seal nguyên vẹn, bảo lãnh thuế đầy đủ. Xác nhận đến đích OLA."

        token_raw = f"{data.declaration_no}:{data.container_no}:{duration_hours}:{status}:{clearance}"
        token = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:24].upper()

        return IcdTransitResult(
            declaration_no=data.declaration_no,
            container_no=data.container_no,
            actual_transit_hours=duration_hours,
            max_transit_hours=data.max_transit_hours,
            transit_status=status,
            customs_clearance_granted=clearance,
            duty_coverage_ratio=coverage_ratio,
            action_directive=action,
            tracking_token=token,
        )
