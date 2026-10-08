"""Test Suite for Phases 291-294: Maritime Sewage, Medical, Stevedoring, Bonded."""
import json
from datetime import datetime
from src.core.maritime_sewage_medical_stevedoring_bonded_engine import (
    SewageTreatmentType,
    SewageDischargeVerdict,
    SewageDischargeInput,
    SewageDischargeEngine,
    DepartmentRole,
    MedicalVerdict,
    MedicalAssessmentInput,
    SeafarerMedicalEngine,
    PortZone,
    ContainerSize,
    CargoStatus,
    HandlingOperation,
    CargoHazardCategory,
    StevedoringTariffInput,
    StevedoringTariffEngine,
    BondedWarehouseStatus,
    BondedWarehouseInput,
    BondedWarehouseEngine,
)

def test_sewage_engine_approved_stp_pass():
    sample = SewageDischargeInput(
        vessel_name="MV TEST 1",
        imo_number="1111111",
        distance_to_shore_nm=0.0,
        vessel_speed_knots=0.0,
        treatment_type=SewageTreatmentType.APPROVED_STP,
        is_in_port_waters=False,
    )
    result = SewageDischargeEngine.evaluate(sample)
    assert "PERMITTED" in result.verdict.name
    assert result.is_discharge_permitted is True

def test_medical_engine_deck_pass():
    sample = MedicalAssessmentInput(
        seafarer_name="NGUYEN VAN A",
        passport_or_sid="SID123",
        age=30,
        department=DepartmentRole.DECK_WATCHKEEPING,
        visual_acuity_right=1.0,
        visual_acuity_left=1.0,
        visual_acuity_both_eyes=1.0,
        is_color_vision_passed=True,
        hearing_whisper_m=4.0,
        hearing_normal_m=6.0,
    )
    res = SeafarerMedicalEngine.evaluate(sample)
    assert "FIT" in res.verdict.name
    assert res.certificate_validity_months == 24

def test_medical_engine_deck_fail_color():
    sample = MedicalAssessmentInput(
        seafarer_name="NGUYEN VAN B",
        passport_or_sid="SID123",
        age=30,
        department=DepartmentRole.DECK_WATCHKEEPING,
        visual_acuity_right=1.0,
        visual_acuity_left=1.0,
        visual_acuity_both_eyes=1.0,
        is_color_vision_passed=False,
        hearing_whisper_m=4.0,
        hearing_normal_m=6.0,
    )
    res = SeafarerMedicalEngine.evaluate(sample)
    assert "UNFIT" in res.verdict.name

def test_bonded_engine_normal():
    # 365 days limit. Check at 100 days
    req = BondedWarehouseInput(
        declaration_number="C11-1234",
        entry_date_str="2025-01-01",
        check_date_str="2025-04-11", # 100 days
        is_extension_granted=False,
        warehouse_name="WH1"
    )
    res = BondedWarehouseEngine.supervise(req)
    assert res.status == BondedWarehouseStatus.NORMAL_STORAGE
    assert res.days_in_storage == 100
    assert res.allowed_max_days == 365

