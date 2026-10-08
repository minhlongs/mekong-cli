import pytest

from src.core.maritime_isps_hazmat_oog_anchorage_engine import (
    SecurityLevel,
    DeclarationOfSecurity,
    MaritimeIspsEngine,
    WasteType,
    HazmatWasteManifest,
    HazmatWasteEngine,
    OogCargoDimensions,
    OogStevedoringEngine,
    AnchorageBooking,
    AnchorageBookingEngine,
)

# ------------------------------------------------------------------------------
# Phase 299: ISPS Security Tests
# ------------------------------------------------------------------------------

def test_isps_clearance_valid():
    dos = DeclarationOfSecurity(
        dos_id="DOS-2026-001",
        vessel_name="MV MEKONG SECURE",
        port_facility="Cat Lai Terminal",
        ship_security_officer="Capt. H",
        port_facility_security_officer="Mr. T",
        port_security_level=SecurityLevel.LEVEL_1,
        vessel_security_level=SecurityLevel.LEVEL_1,
        valid_from="2026-10-01",
        valid_until="2026-10-15"
    )
    res = MaritimeIspsEngine.evaluate_dos_clearance(dos, current_time="2026-10-08")
    assert res.is_cleared is True
    assert "đồng bộ" in res.remarks

def test_isps_clearance_conflict():
    dos = DeclarationOfSecurity(
        dos_id="DOS-2026-002",
        vessel_name="MV MEKONG ALERT",
        port_facility="Cat Lai Terminal",
        ship_security_officer="Capt. H",
        port_facility_security_officer="Mr. T",
        port_security_level=SecurityLevel.LEVEL_2,  # Port is elevated
        vessel_security_level=SecurityLevel.LEVEL_1,
        valid_from="2026-10-01",
        valid_until="2026-10-15"
    )
    res = MaritimeIspsEngine.evaluate_dos_clearance(dos, current_time="2026-10-08")
    assert res.is_cleared is False
    assert "Xung đột" in res.remarks


# ------------------------------------------------------------------------------
# Phase 300: Hazmat Port Clearance Tests
# ------------------------------------------------------------------------------

def test_hazmat_port_clearance_blocked():
    manifests = [
        HazmatWasteManifest(
            manifest_id="HW-001",
            vessel_name="MV CHEMICAL",
            waste_type=WasteType.IMDG_CHEMICAL,
            quantity_cubic_meters=5.0,
            un_code="UN 1230",
            disposal_receipt_id="REC-X1"  # Cleared
        ),
        HazmatWasteManifest(
            manifest_id="HW-002",
            vessel_name="MV CHEMICAL",
            waste_type=WasteType.MEDICAL_BIOHAZARD,
            quantity_cubic_meters=1.0,
            disposal_receipt_id=None  # MISSING RECEIPT
        )
    ]
    res = HazmatWasteEngine.evaluate_port_clearance(manifests, "MV CHEMICAL")
    assert res.missing_receipts is True
    assert res.is_cleared_for_departure is False
    assert "1 bản khai" in res.remarks

def test_hazmat_port_clearance_cleared():
    manifests = [
        HazmatWasteManifest(
            manifest_id="HW-003",
            vessel_name="MV CLEAN",
            waste_type=WasteType.MARPOL_V_GARBAGE,
            quantity_cubic_meters=10.0,
            disposal_receipt_id="REC-OK1"
        )
    ]
    res = HazmatWasteEngine.evaluate_port_clearance(manifests, "MV CLEAN")
    assert res.is_cleared_for_departure is True


# ------------------------------------------------------------------------------
# Phase 301: OOG Stevedoring Tests
# ------------------------------------------------------------------------------

def test_oog_tariff_multiplier():
    # Regular 20ft (1 TEU)
    regular = OogCargoDimensions(container_size_teu=1)
    res_reg = OogStevedoringEngine.calculate_tariff(regular, is_overtime=False)
    assert res_reg.base_rate_usd == 100.0
    assert res_reg.oog_multiplier == 1.0
    assert res_reg.final_charge_usd == 100.0

    # Over-width only (1 dimension) -> x1.5
    over_w = OogCargoDimensions(container_size_teu=1, over_width_cm=50)
    res_w = OogStevedoringEngine.calculate_tariff(over_w, is_overtime=False)
    assert res_w.oog_multiplier == 1.5
    assert res_w.final_charge_usd == 150.0

    # Over-width and over-height (2 dims) -> x2.0
    over_wh = OogCargoDimensions(container_size_teu=2, over_width_cm=50, over_height_cm=40)
    res_wh = OogStevedoringEngine.calculate_tariff(over_wh, is_overtime=True)
    assert res_wh.base_rate_usd == 200.0  # 2 TEU
    assert res_wh.oog_multiplier == 2.0
    assert res_wh.overtime_multiplier == 1.3
    # 200 * 2.0 * 1.3 = 520
    assert res_wh.final_charge_usd == 520.0


# ------------------------------------------------------------------------------
# Phase 302: Anchorage Booking Tests
# ------------------------------------------------------------------------------

def test_anchorage_capacity_logic():
    existing = [
        AnchorageBooking("B1", "SHIP A", 50000, "2026-10-08 10:00", "2026-10-08 18:00"),
        AnchorageBooking("B2", "SHIP B", 30000, "2026-10-08 14:00", "2026-10-08 22:00")
    ]
    max_cap = 100000.0

    # New ship comes at 16:00, overlaps with BOTH A (until 18) and B.
    # Current peak = 80000. We add 25000 -> 105000 > 100000 (rejected)
    new1 = AnchorageBooking("B3", "SHIP C", 25000, "2026-10-08 16:00", "2026-10-08 20:00")
    res1 = AnchorageBookingEngine.evaluate_booking("Vung Tau OPL", max_cap, existing, new1)
    assert res1.is_accepted is False
    assert res1.peak_grt_in_window == 105000.0

    # New ship comes at 19:00, only overlaps with B (A left at 18).
    # Current peak = 30000. We add 25000 -> 55000 < 100000 (accepted)
    new2 = AnchorageBooking("B4", "SHIP D", 25000, "2026-10-08 19:00", "2026-10-08 23:00")
    res2 = AnchorageBookingEngine.evaluate_booking("Vung Tau OPL", max_cap, existing, new2)
    assert res2.is_accepted is True
    assert res2.peak_grt_in_window == 55000.0
