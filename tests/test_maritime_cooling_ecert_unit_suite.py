"""Unit tests for Maritime Phases 353-354 Micro-Engines.

Tests:
- CentralCoolingEngine (CCWS LMTD, scoop energy savings, MGPS Cu biofouling)
- MarineEcertEngine (IMO FAL.5/Circ.39, SHA-256 digital signature, lifecycle status)
Strictly zero-mock and kept under 200 lines.
"""

import hashlib
from src.core.maritime_loading_hns_cool_ecert_engine import (
    CentralCoolingEngine,
    CentralCoolingInput,
    MarineEcertEngine,
    MarineEcertInput,
)


def test_central_cooling_optimal_and_scoop_savings():
    inp = CentralCoolingInput(
        vessel_id="CONTAINER-01",
        heat_duty_kw=4500.0,
        freshwater_in_temp_c=48.0,
        freshwater_out_temp_c=36.0,
        seawater_in_temp_c=28.0,
        vessel_speed_knots=15.0,
        seawater_flow_m3_h=850.0,
        is_scoop_system_fitted=True,
        mgps_copper_current_amps=2.5,
    )
    res = CentralCoolingEngine.evaluate(inp)
    assert res.seawater_out_temp_c > 28.0
    assert res.lmtd_celsius > 0.0
    assert res.is_scoop_active is True
    assert res.pump_power_saved_kw > 40.0
    assert 2.0 <= res.cu_ion_concentration_ug_l <= 10.0
    assert res.is_mgps_effective is True
    assert res.status == "OPTIMAL"


def test_central_cooling_suboptimal_and_mgps_deficient():
    inp = CentralCoolingInput(
        vessel_id="CONTAINER-02",
        heat_duty_kw=9000.0,
        freshwater_in_temp_c=55.0,
        freshwater_out_temp_c=40.0,
        seawater_in_temp_c=32.0,
        vessel_speed_knots=8.0,
        seawater_flow_m3_h=200.0,
        is_scoop_system_fitted=True,
        mgps_copper_current_amps=0.2,
    )
    res = CentralCoolingEngine.evaluate(inp)
    assert res.is_scoop_active is False
    assert res.pump_power_saved_kw == 0.0
    assert res.cu_ion_concentration_ug_l < 2.0
    assert res.is_mgps_effective is False
    assert res.status == "SUB_OPTIMAL"
    assert any("MGPS DOSING DEFICIENT" in adv for adv in res.advisories)


def test_marine_ecert_verification_valid():
    cert_id = "UTN-DNV-2025-001"
    imo = "IMO9876543"
    c_type = "CLASS"
    ro = "DNV"
    iss = "2025-01-15"
    exp = "2030-01-14"
    raw = f"{cert_id}|{imo}|{c_type}|{ro}|{iss}|{exp}"
    valid_sig = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    inp = MarineEcertInput(
        certificate_id=cert_id,
        certificate_type=c_type,
        vessel_imo=imo,
        vessel_name="MEKONG VOYAGER",
        issuing_ro=ro,
        issue_date_iso=iss,
        expiry_date_iso=exp,
        verification_url="https://verify.dnv.com/ecert",
        digital_signature_hex=valid_sig,
        current_date_iso="2026-10-09",
    )
    res = MarineEcertEngine.evaluate(inp)
    assert res.is_signature_valid is True
    assert res.is_period_valid is True
    assert res.lifecycle_status == "VALID"
    assert res.is_port_clearance_acceptable is True


def test_marine_ecert_tampered_and_revoked():
    cert_id = "UTN-VR-2025-999"
    imo = "IMO9123456"
    c_type = "LOAD_LINE"
    ro = "VR"
    iss = "2024-01-01"
    exp = "2029-01-01"

    # Signature tampering
    inp_tampered = MarineEcertInput(
        certificate_id=cert_id,
        certificate_type=c_type,
        vessel_imo=imo,
        vessel_name="VN SHIP",
        issuing_ro=ro,
        issue_date_iso=iss,
        expiry_date_iso=exp,
        verification_url="https://vr.org.vn",
        digital_signature_hex="bad_digest_hex_code",
    )
    res_tampered = MarineEcertEngine.evaluate(inp_tampered)
    assert res_tampered.is_signature_valid is False
    assert res_tampered.lifecycle_status == "SIGNATURE_MISMATCH"
    assert res_tampered.is_port_clearance_acceptable is False

    # Revoked certificate
    raw = f"{cert_id}|{imo}|{c_type}|{ro}|{iss}|{exp}"
    valid_sig = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    inp_revoked = MarineEcertInput(
        certificate_id=cert_id,
        certificate_type=c_type,
        vessel_imo=imo,
        vessel_name="VN SHIP",
        issuing_ro=ro,
        issue_date_iso=iss,
        expiry_date_iso=exp,
        verification_url="https://vr.org.vn",
        digital_signature_hex=valid_sig,
        is_revoked=True,
    )
    res_revoked = MarineEcertEngine.evaluate(inp_revoked)
    assert res_revoked.is_signature_valid is True
    assert res_revoked.lifecycle_status == "REVOKED"
    assert res_revoked.is_port_clearance_acceptable is False
