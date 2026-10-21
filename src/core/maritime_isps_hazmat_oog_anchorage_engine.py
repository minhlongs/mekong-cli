"""Maritime ISPS Security, Hazmat Waste, OOG Stevedoring, and Anchorage Booking Suite (Phases 299-302)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional

class SecurityLevel(str, Enum):
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"
    LEVEL_3 = "LEVEL_3"

@dataclass
class DeclarationOfSecurity:
    dos_id: str
    vessel_name: str
    port_facility: str
    ship_security_officer: str
    port_facility_security_officer: str
    port_security_level: SecurityLevel
    vessel_security_level: SecurityLevel
    valid_from: str
    valid_until: str

    def is_valid_and_aligned(self, check_time: str) -> bool:
        return self.port_security_level == self.vessel_security_level and (self.valid_from <= check_time <= self.valid_until)

@dataclass
class IspsClearanceResult:
    is_cleared: bool
    current_level: SecurityLevel
    remarks: str
    security_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {"is_cleared": self.is_cleared, "current_level": self.current_level.value, "remarks": self.remarks, "security_hash": self.security_hash}

class MaritimeIspsEngine:
    @classmethod
    def evaluate_dos_clearance(cls, dos: DeclarationOfSecurity, current_time: str) -> IspsClearanceResult:
        is_cleared = dos.is_valid_and_aligned(current_time)
        if is_cleared:
            remarks = f"An ninh Cảng & Tàu đồng bộ ({dos.port_security_level.value}). Cấp phép ISPS Clearance."
        elif dos.valid_from > current_time or dos.valid_until < current_time:
            remarks = "Giấy chứng nhận DoS đã hết hạn hoặc chưa có hiệu lực."
        else:
            remarks = f"Xung đột cấp độ an ninh: Cảng {dos.port_security_level.value} vs Tàu {dos.vessel_security_level.value}. Yêu cầu cập nhật DoS."
        token = hashlib.sha256(f"{dos.dos_id}|{is_cleared}|{dos.port_security_level.value}".encode("utf-8")).hexdigest()
        return IspsClearanceResult(is_cleared, dos.port_security_level, remarks, token)

class WasteType(str, Enum):
    MARPOL_I_OIL = "MARPOL_I_OIL"
    MARPOL_V_GARBAGE = "MARPOL_V_GARBAGE"
    MEDICAL_BIOHAZARD = "MEDICAL_BIOHAZARD"
    IMDG_CHEMICAL = "IMDG_CHEMICAL"

@dataclass
class HazmatWasteManifest:
    manifest_id: str
    vessel_name: str
    waste_type: WasteType
    quantity_cubic_meters: float
    un_code: Optional[str] = None
    offload_date: str = ""
    disposal_vendor: str = ""
    disposal_receipt_id: Optional[str] = None

@dataclass
class HazmatClearanceResult:
    manifest_id: str
    vessel_name: str
    is_cleared_for_departure: bool
    missing_receipts: bool
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {"manifest_id": self.manifest_id, "vessel_name": self.vessel_name, "is_cleared_for_departure": self.is_cleared_for_departure, "missing_receipts": self.missing_receipts, "remarks": self.remarks, "audit_hash": self.audit_hash}

class HazmatWasteEngine:
    @classmethod
    def evaluate_port_clearance(cls, manifests: List[HazmatWasteManifest], vessel_name: str) -> HazmatClearanceResult:
        uncleared = [m for m in manifests if not m.disposal_receipt_id]
        is_cleared = len(uncleared) == 0
        remarks = "Toàn bộ rác thải / hóa chất chất nguy hại đã được Vendor tiếp nhận và cấp chứng chỉ Disposal Receipt. Cấp phép rời cảng (Clearance)." if is_cleared else f"Tàu {vessel_name} còn {len(uncleared)} bản khai (Manifest) chưa có chứng chỉ Disposal Receipt. KHÔNG được rời cảng."
        token = hashlib.sha256(f"{vessel_name}|{is_cleared}|{len(uncleared)}".encode("utf-8")).hexdigest()
        return HazmatClearanceResult(manifests[0].manifest_id if manifests else "N/A", vessel_name, is_cleared, not is_cleared, remarks, token)

@dataclass
class OogCargoDimensions:
    container_size_teu: int = 1
    over_width_cm: int = 0
    over_height_cm: int = 0
    over_length_cm: int = 0
    gross_weight_mt: float = 0.0

@dataclass
class OogTariffResult:
    base_rate_usd: float
    oog_multiplier: float
    overtime_multiplier: float
    final_charge_usd: float
    remarks: str
    invoice_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {"base_rate_usd": round(self.base_rate_usd, 2), "oog_multiplier": self.oog_multiplier, "overtime_multiplier": self.overtime_multiplier, "final_charge_usd": round(self.final_charge_usd, 2), "remarks": self.remarks, "invoice_hash": self.invoice_hash}

class OogStevedoringEngine:
    BASE_RATE_PER_TEU_USD = 100.0

    @classmethod
    def calculate_tariff(cls, dimensions: OogCargoDimensions, is_overtime: bool) -> OogTariffResult:
        base_rate = dimensions.container_size_teu * cls.BASE_RATE_PER_TEU_USD
        over_dims = sum(x > 0 for x in (dimensions.over_width_cm, dimensions.over_height_cm, dimensions.over_length_cm))
        oog_multiplier = 1.5 if over_dims == 1 else (2.0 if over_dims >= 2 else 1.0)
        if (dimensions.gross_weight_mt / max(dimensions.container_size_teu, 1)) > 40.0:
            oog_multiplier *= 1.25
        overtime_multiplier = 1.3 if is_overtime else 1.0
        final_charge = base_rate * oog_multiplier * overtime_multiplier
        remarks = f"Kích thước lố khổ {over_dims} chiều. Multiplier OOG: x{oog_multiplier:.2f} | Ngoài giờ: x{overtime_multiplier:.2f}"
        token = hashlib.sha256(f"{dimensions.container_size_teu}|{base_rate:.2f}|{oog_multiplier:.2f}|{final_charge:.2f}".encode("utf-8")).hexdigest()
        return OogTariffResult(base_rate, oog_multiplier, overtime_multiplier, final_charge, remarks, token)

@dataclass
class AnchorageBooking:
    booking_id: str
    vessel_name: str
    vessel_grt: float
    arrival_time_str: str
    departure_time_str: str

@dataclass
class AnchorageCheckResult:
    booking_id: str
    requested_zone: str
    is_accepted: bool
    peak_grt_in_window: float
    max_grt_capacity: float
    remarks: str
    booking_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {"booking_id": self.booking_id, "requested_zone": self.requested_zone, "is_accepted": self.is_accepted, "peak_grt_in_window": round(self.peak_grt_in_window, 2), "max_grt_capacity": round(self.max_grt_capacity, 2), "remarks": self.remarks, "booking_hash": self.booking_hash}

class AnchorageBookingEngine:
    @classmethod
    def evaluate_booking(cls, zone_name: str, max_grt_capacity: float, existing_bookings: List[AnchorageBooking], new_booking: AnchorageBooking) -> AnchorageCheckResult:
        req_start, req_end = new_booking.arrival_time_str, new_booking.departure_time_str
        overlapping = [b for b in existing_bookings if b.arrival_time_str < req_end and b.departure_time_str > req_start]
        new_total_grt = sum(b.vessel_grt for b in overlapping) + new_booking.vessel_grt
        is_accepted = new_total_grt <= max_grt_capacity
        remarks = f"Phê duyệt. Tổng GRT tại {zone_name} (chứa tàu mới): {new_total_grt:,.0f} / {max_grt_capacity:,.0f} GRT." if is_accepted else f"Từ chối. Vượt giới hạn an toàn khu neo {zone_name}: {new_total_grt:,.0f} > {max_grt_capacity:,.0f} GRT."
        token = hashlib.sha256(f"{new_booking.booking_id}|{zone_name}|{is_accepted}|{new_total_grt}".encode("utf-8")).hexdigest()
        return AnchorageCheckResult(new_booking.booking_id, zone_name, is_accepted, new_total_grt, max_grt_capacity, remarks, token)
