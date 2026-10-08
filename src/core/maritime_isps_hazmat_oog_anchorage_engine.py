"""Maritime ISPS Security, Hazmat Waste, OOG Stevedoring, and Anchorage Booking Suite.

Phases 299-302 Simplest Viable Maritime Operational Suite.
- Phase 299: ISPS Code Security Levels & Declaration of Security (DoS) tracking
- Phase 300: Hazmat Waste Manifest & Port Clearance Blocker (Disposal Receipt)
- Phase 301: OOG (Out of Gauge) Stevedoring Tariffs with Overtime Multipliers
- Phase 302: Anchorage Booking Capacity by Total GRT Budget Allocation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional


# ==============================================================================
# Phase 299: ISPS Code Port Security Engine
# ==============================================================================

class SecurityLevel(str, Enum):
    LEVEL_1 = "LEVEL_1"  # Normal
    LEVEL_2 = "LEVEL_2"  # Heightened
    LEVEL_3 = "LEVEL_3"  # Exceptional


@dataclass
class DeclarationOfSecurity:
    """DoS agreement between Ship and Port Facility."""
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
        """Check time validity and level alignment."""
        if self.port_security_level != self.vessel_security_level:
            return False
        return self.valid_from <= check_time <= self.valid_until


@dataclass
class IspsClearanceResult:
    is_cleared: bool
    current_level: SecurityLevel
    remarks: str
    security_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_cleared": self.is_cleared,
            "current_level": self.current_level.value,
            "remarks": self.remarks,
            "security_hash": self.security_hash,
        }


class MaritimeIspsEngine:
    """Security tracker for ISPS Code DoS."""

    @classmethod
    def evaluate_dos_clearance(cls, dos: DeclarationOfSecurity, current_time: str) -> IspsClearanceResult:
        is_cleared = dos.is_valid_and_aligned(current_time)

        if is_cleared:
            remarks = f"An ninh Cảng & Tàu đồng bộ ({dos.port_security_level.value}). Cấp phép ISPS Clearance."
        elif dos.valid_from > current_time or dos.valid_until < current_time:
            remarks = "Giấy chứng nhận DoS đã hết hạn hoặc chưa có hiệu lực."
        else:
            remarks = (f"Xung đột cấp độ an ninh: Cảng {dos.port_security_level.value} "
                       f"vs Tàu {dos.vessel_security_level.value}. Yêu cầu cập nhật DoS.")

        raw = f"{dos.dos_id}|{is_cleared}|{dos.port_security_level.value}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return IspsClearanceResult(
            is_cleared=is_cleared,
            current_level=dos.port_security_level,
            remarks=remarks,
            security_hash=token,
        )


# ==============================================================================
# Phase 300: Hazmat / Medical Waste Engine
# ==============================================================================

class WasteType(str, Enum):
    MARPOL_I_OIL = "MARPOL_I_OIL"
    MARPOL_V_GARBAGE = "MARPOL_V_GARBAGE"
    MEDICAL_BIOHAZARD = "MEDICAL_BIOHAZARD"
    IMDG_CHEMICAL = "IMDG_CHEMICAL"


@dataclass
class HazmatWasteManifest:
    """Manifest for tracking hazardous/medical waste offloading."""
    manifest_id: str
    vessel_name: str
    waste_type: WasteType
    quantity_cubic_meters: float
    un_code: Optional[str] = None
    offload_date: str = ""
    disposal_vendor: str = ""
    disposal_receipt_id: Optional[str] = None  # Crucial field for port clearance


@dataclass
class HazmatClearanceResult:
    manifest_id: str
    vessel_name: str
    is_cleared_for_departure: bool
    missing_receipts: bool
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "vessel_name": self.vessel_name,
            "is_cleared_for_departure": self.is_cleared_for_departure,
            "missing_receipts": self.missing_receipts,
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class HazmatWasteEngine:
    """Port Clearance Blocker based on Hazmat Waste."""

    @classmethod
    def evaluate_port_clearance(cls, manifests: List[HazmatWasteManifest], vessel_name: str) -> HazmatClearanceResult:
        uncleared = [m for m in manifests if not m.disposal_receipt_id]

        is_cleared = len(uncleared) == 0
        missing_receipts = len(uncleared) > 0

        if is_cleared:
            remarks = "Toàn bộ rác thải / hóa chất chất nguy hại đã được Vendor tiếp nhận và cấp chứng chỉ Disposal Receipt. Cấp phép rời cảng (Clearance)."
        else:
            remarks = f"Tàu {vessel_name} còn {len(uncleared)} bản khai (Manifest) chưa có chứng chỉ Disposal Receipt. KHÔNG được rời cảng."

        raw = f"{vessel_name}|{is_cleared}|{len(uncleared)}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return HazmatClearanceResult(
            manifest_id=manifests[0].manifest_id if manifests else "N/A",
            vessel_name=vessel_name,
            is_cleared_for_departure=is_cleared,
            missing_receipts=missing_receipts,
            remarks=remarks,
            audit_hash=token,
        )


# ==============================================================================
# Phase 301: Out-of-Gauge (OOG) Stevedoring Tariffs
# ==============================================================================

@dataclass
class OogCargoDimensions:
    """Dimensions of a flat-rack or break-bulk OOG cargo."""
    container_size_teu: int = 1  # 1 for 20ft, 2 for 40ft
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
        return {
            "base_rate_usd": round(self.base_rate_usd, 2),
            "oog_multiplier": self.oog_multiplier,
            "overtime_multiplier": self.overtime_multiplier,
            "final_charge_usd": round(self.final_charge_usd, 2),
            "remarks": self.remarks,
            "invoice_hash": self.invoice_hash,
        }


class OogStevedoringEngine:
    """Stevedoring Tariffs with OOG Multipliers."""

    BASE_RATE_PER_TEU_USD = 100.0

    @classmethod
    def calculate_tariff(cls, dimensions: OogCargoDimensions, is_overtime: bool) -> OogTariffResult:
        base_rate = dimensions.container_size_teu * cls.BASE_RATE_PER_TEU_USD

        # OOG Rule:
        # - Over in 1 dimension = x1.5
        # - Over in 2 or 3 dimensions = x2.0
        # - Extreme Weight (>40 MT per TEU) = extra x1.25 multiplier

        over_dims = 0
        if dimensions.over_width_cm > 0: over_dims += 1
        if dimensions.over_height_cm > 0: over_dims += 1
        if dimensions.over_length_cm > 0: over_dims += 1

        oog_multiplier = 1.0
        if over_dims == 1:
            oog_multiplier = 1.5
        elif over_dims >= 2:
            oog_multiplier = 2.0

        weight_ratio = dimensions.gross_weight_mt / max(dimensions.container_size_teu, 1)
        if weight_ratio > 40.0:
            oog_multiplier *= 1.25  # Super-heavy penalty

        overtime_multiplier = 1.3 if is_overtime else 1.0

        final_charge = base_rate * oog_multiplier * overtime_multiplier

        remarks = f"Kích thước lố khổ {over_dims} chiều. Multiplier OOG: x{oog_multiplier:.2f} | Ngoài giờ: x{overtime_multiplier:.2f}"

        raw = f"{dimensions.container_size_teu}|{base_rate:.2f}|{oog_multiplier:.2f}|{final_charge:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return OogTariffResult(
            base_rate_usd=base_rate,
            oog_multiplier=oog_multiplier,
            overtime_multiplier=overtime_multiplier,
            final_charge_usd=final_charge,
            remarks=remarks,
            invoice_hash=token,
        )


# ==============================================================================
# Phase 302: Anchorage Capacity Booking
# ==============================================================================

@dataclass
class AnchorageBooking:
    booking_id: str
    vessel_name: str
    vessel_grt: float
    arrival_time_str: str  # YYYY-MM-DD HH:MM
    departure_time_str: str  # YYYY-MM-DD HH:MM


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
        return {
            "booking_id": self.booking_id,
            "requested_zone": self.requested_zone,
            "is_accepted": self.is_accepted,
            "peak_grt_in_window": round(self.peak_grt_in_window, 2),
            "max_grt_capacity": round(self.max_grt_capacity, 2),
            "remarks": self.remarks,
            "booking_hash": self.booking_hash,
        }


class AnchorageBookingEngine:
    """Linear GRT capacity bucket model for Anchorage zones."""

    @classmethod
    def evaluate_booking(
        cls,
        zone_name: str,
        max_grt_capacity: float,
        existing_bookings: List[AnchorageBooking],
        new_booking: AnchorageBooking
    ) -> AnchorageCheckResult:

        req_start = new_booking.arrival_time_str
        req_end = new_booking.departure_time_str

        # Check overlapping bookings in time window
        overlapping = []
        for b in existing_bookings:
            # Overlaps if (b.start < new.end) AND (b.end > new.start)
            if b.arrival_time_str < req_end and b.departure_time_str > req_start:
                overlapping.append(b)

        # Total GRT in that window (Simplest possible check for peak, assumes all overlapping are concurrent)
        current_peak_grt = sum(b.vessel_grt for b in overlapping)
        new_total_grt = current_peak_grt + new_booking.vessel_grt

        is_accepted = new_total_grt <= max_grt_capacity

        if is_accepted:
            remarks = f"Phê duyệt. Tổng GRT tại {zone_name} (chứa tàu mới): {new_total_grt:,.0f} / {max_grt_capacity:,.0f} GRT."
        else:
            remarks = f"Từ chối. Vượt giới hạn an toàn khu neo {zone_name}: {new_total_grt:,.0f} > {max_grt_capacity:,.0f} GRT."

        raw = f"{new_booking.booking_id}|{zone_name}|{is_accepted}|{new_total_grt}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return AnchorageCheckResult(
            booking_id=new_booking.booking_id,
            requested_zone=zone_name,
            is_accepted=is_accepted,
            peak_grt_in_window=new_total_grt,
            max_grt_capacity=max_grt_capacity,
            remarks=remarks,
            booking_hash=token,
        )
