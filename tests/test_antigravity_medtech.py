# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials (Phase 70)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.medtech_engine import (
    DEVICE_RISK_CLASSES,
    FACILITY_TYPES,
    REFERENCE_FOREIGN_AUTHORITIES,
    MedtechEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestMedtechCoreBoundary:
    """Ensure MedtechEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/medtech_engine.py")
        assert source_path.exists(), "medtech_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestMedtechEngine:
    """Test MedtechEngine risk classification, market authorization, price caps, facilities, and trials."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> MedtechEngine:
        db_file = tmp_path / "test_medtech.db"
        return MedtechEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Check risk classes under Decree 98/2021
        assert "CLASS_A" in DEVICE_RISK_CLASSES
        assert "CLASS_B" in DEVICE_RISK_CLASSES
        assert "CLASS_C" in DEVICE_RISK_CLASSES
        assert "CLASS_D" in DEVICE_RISK_CLASSES
        assert DEVICE_RISK_CLASSES["CLASS_A"]["requires_clinical_trial"] is False
        assert DEVICE_RISK_CLASSES["CLASS_B"]["requires_clinical_trial"] is False
        assert DEVICE_RISK_CLASSES["CLASS_C"]["requires_clinical_trial"] is True
        assert DEVICE_RISK_CLASSES["CLASS_D"]["requires_clinical_trial"] is True

        # Check reference foreign authorities
        assert "FDA" in REFERENCE_FOREIGN_AUTHORITIES
        assert "CE" in REFERENCE_FOREIGN_AUTHORITIES
        assert "PMDA" in REFERENCE_FOREIGN_AUTHORITIES
        assert "TGA" in REFERENCE_FOREIGN_AUTHORITIES
        assert "HEALTH_CANADA" in REFERENCE_FOREIGN_AUTHORITIES

        # Check facility standards under Law 15/2023/QH15
        assert FACILITY_TYPES["GENERAL_HOSPITAL"]["min_beds"] == 30
        assert FACILITY_TYPES["GENERAL_HOSPITAL"]["min_floor_m2_per_bed"] == 50.0
        assert FACILITY_TYPES["GENERAL_HOSPITAL"]["min_doctor_practice_months"] == 54
        assert FACILITY_TYPES["POLYCLINIC"]["min_doctor_practice_months"] == 36

    def test_register_medical_device_class_a(self, engine: MedtechEngine) -> None:
        res = engine.register_medical_device(
            device_name="Găng tay khám bệnh tiệt trùng",
            risk_class="CLASS_A",
            manufacturer="VRG Medical Gloves JSC",
            country_of_origin="Vietnam",
            importer_name="Công ty CP Y Tế Quốc Tế",
            intended_use="Bảo hộ và khám bệnh thông thường",
        )
        assert res["ok"] is True
        assert res["device_id"].startswith("DEV-")
        prof = res["device_profile"]
        assert prof["risk_class"] == "CLASS_A"
        assert prof["is_clinical_trial_exempt"] is True
        assert "CBTT/SYT" in prof["market_auth_number"]
        assert prof["validity_period"] == "VÔ THỜI HẠN"
        assert "Sở Y tế" in prof["licensing_authority"]

        devices = engine.list_medical_devices()
        assert len(devices) == 1
        assert devices[0]["device_name"] == "Găng tay khám bệnh tiệt trùng"

    def test_register_medical_device_class_b(self, engine: MedtechEngine) -> None:
        res = engine.register_medical_device(
            device_name="Máy đo huyết áp điện tử bắp tay",
            risk_class="CLASS_B",
            manufacturer="Omron Healthcare",
            country_of_origin="Japan",
            importer_name="Công ty TNHH Omron Việt Nam",
            intended_use="Đo huyết áp và nhịp tim không xâm lấn",
        )
        assert res["ok"] is True
        prof = res["device_profile"]
        assert prof["risk_class"] == "CLASS_B"
        assert prof["is_clinical_trial_exempt"] is True
        assert "CBTB/SYT" in prof["market_auth_number"]

    def test_register_medical_device_class_c_with_cfs_fast_track(self, engine: MedtechEngine) -> None:
        res = engine.register_medical_device(
            device_name="Hệ thống máy thở hồi sức cấp cứu",
            risk_class="CLASS_C",
            manufacturer="Drägerwerk AG & Co. KGaA",
            country_of_origin="Germany",
            importer_name="Công ty CP Trang Thiết Bị Y Tế Trung Ương",
            intended_use="Thông khí nhân tạo và hỗ trợ hô hấp ICU",
            reference_cfs="CE",
        )
        assert res["ok"] is True
        prof = res["device_profile"]
        assert prof["risk_class"] == "CLASS_C"
        assert prof["reference_cfs_agency"] == "CE"
        assert prof["is_clinical_trial_exempt"] is True
        assert "ĐKLH/BYT-TB" in prof["market_auth_number"]
        assert prof["validity_period"] == "5 năm"
        assert "Bộ Y tế" in prof["licensing_authority"]

    def test_register_medical_device_class_d_without_cfs(self, engine: MedtechEngine) -> None:
        res = engine.register_medical_device(
            device_name="Stent nong mạch vành phủ thuốc sinh học",
            risk_class="CLASS_D",
            manufacturer="VietStent Innovation Co.",
            country_of_origin="Vietnam",
            importer_name="Công ty TNHH Thiết Bị Can Thiệp Mạch",
            intended_use="Tái thông lòng mạch vành bị hẹp hoặc tắc nghẽn",
            reference_cfs=None,
        )
        assert res["ok"] is True
        prof = res["device_profile"]
        assert prof["risk_class"] == "CLASS_D"
        assert prof["reference_cfs_agency"] == "NONE"
        assert prof["is_clinical_trial_exempt"] is False
        assert "Bắt buộc" in prof["exemption_reason"]

    def test_declare_device_price_compliant(self, engine: MedtechEngine) -> None:
        # CIF = 10,000,000 VND
        # Wholesale = 13,000,000 VND -> Markup = (13M - 10M)/10M = 30.0% <= 35%
        res = engine.declare_device_price(
            device_id="DEV-TEST-001",
            device_name="Máy siêu âm cầm tay",
            cif_cost_vnd=10000000.0,
            wholesale_price_vnd=13000000.0,
            retail_price_vnd=15000000.0,
        )
        assert res["ok"] is True
        assert res["declaration_id"].startswith("PRC-")
        p = res["price_declaration"]
        assert p["markup_percentage"] == 30.0
        assert p["is_markup_compliant"] is True
        assert "HỢP LỆ" in p["compliance_verdict"]

        decls = engine.list_price_declarations()
        assert len(decls) == 1
        assert decls[0]["device_name"] == "Máy siêu âm cầm tay"

    def test_declare_device_price_non_compliant(self, engine: MedtechEngine) -> None:
        # CIF = 20,000,000 VND
        # Wholesale = 30,000,000 VND -> Markup = (30M - 20M)/20M = 50.0% > 35%
        res = engine.declare_device_price(
            device_id="DEV-TEST-002",
            device_name="Thiết bị nội soi cao cấp",
            cif_cost_vnd=20000000.0,
            wholesale_price_vnd=30000000.0,
            retail_price_vnd=35000000.0,
        )
        assert res["ok"] is True
        p = res["price_declaration"]
        assert p["markup_percentage"] == 50.0
        assert p["is_markup_compliant"] is False
        assert "VƯỢT NGƯỠNG" in p["compliance_verdict"]

    def test_evaluate_facility_license_general_hospital_approved(self, engine: MedtechEngine) -> None:
        res = engine.evaluate_facility_license(
            facility_name="Bệnh viện Đa khoa Quốc tế Phúc An",
            facility_type="GENERAL_HOSPITAL",
            province="TP. Hồ Chí Minh",
            bed_capacity=150,
            total_floor_area_m2=9000.0,  # 60 m2/bed >= 50
            chief_medical_officer="PGS.TS. Lê Đình Triều",
            cmo_practice_months=72,  # >= 54
        )
        assert res["ok"] is True
        assert res["facility_id"].startswith("FAC-")
        f = res["facility_evaluation"]
        assert f["is_license_approved"] is True
        assert f["operating_license_no"].startswith("GP-KCB/")
        assert f["floor_m2_per_bed"] == 60.0
        assert f["cmo_qualification_compliant"] is True

        facs = engine.list_healthcare_facilities()
        assert len(facs) == 1
        assert facs[0]["facility_name"] == "Bệnh viện Đa khoa Quốc tế Phúc An"

    def test_evaluate_facility_license_general_hospital_rejected(self, engine: MedtechEngine) -> None:
        # Lacking beds (< 30) and insufficient CMO practice months (< 54)
        res = engine.evaluate_facility_license(
            facility_name="Bệnh viện Mini",
            facility_type="GENERAL_HOSPITAL",
            province="Bình Dương",
            bed_capacity=15,  # < 30
            total_floor_area_m2=600.0,
            chief_medical_officer="BS. Nguyễn Văn E",
            cmo_practice_months=30,  # < 54
        )
        assert res["ok"] is True
        f = res["facility_evaluation"]
        assert f["is_license_approved"] is False
        assert f["bed_capacity_compliant"] is False
        assert f["cmo_qualification_compliant"] is False
        assert f["operating_license_no"] == "REJECTED_DEFICIENT"

    def test_evaluate_facility_license_polyclinic(self, engine: MedtechEngine) -> None:
        res = engine.evaluate_facility_license(
            facility_name="Phòng khám Đa khoa Sài Gòn Medic",
            facility_type="POLYCLINIC",
            province="TP. Hồ Chí Minh",
            bed_capacity=0,
            total_floor_area_m2=250.0,  # >= 40 m2
            chief_medical_officer="BS.CKII. Đỗ Hoàng Yến",
            cmo_practice_months=48,  # >= 36
        )
        assert res["ok"] is True
        f = res["facility_evaluation"]
        assert f["is_license_approved"] is True
        assert f["facility_type"] == "POLYCLINIC"

    def test_submit_clinical_trial_protocol(self, engine: MedtechEngine) -> None:
        res = engine.submit_clinical_trial_protocol(
            device_id="DEV-STENT-001",
            trial_title="Đánh giá hiệu quả lâm sàng của Stent phủ thuốc phân hủy sinh học",
            trial_phase=2,
            principal_investigator="GS.TS. Võ Thành Nhân",
            study_site="Bệnh viện Chợ Rẫy",
            target_subjects=120,
            irb_approved=True,
        )
        assert res["ok"] is True
        assert res["trial_id"].startswith("TRL-")
        t = res["trial_profile"]
        assert t["trial_phase"] == 2
        assert t["is_irb_approved"] is True
        assert t["irb_approval_code"].startswith("IRB-VN-")
        assert t["status"] == "ACTIVE_ENROLLING"

        trials = engine.list_clinical_trials()
        assert len(trials) == 1
        assert trials[0]["principal_investigator"] == "GS.TS. Võ Thành Nhân"

    def test_list_and_get_status_aggregation(self, engine: MedtechEngine) -> None:
        # Register device
        engine.register_medical_device("Máy SpO2", "CLASS_B")
        # Declare price
        engine.declare_device_price("DEV-01", "Máy SpO2", 500000.0, 650000.0, 750000.0)
        # Facility
        engine.evaluate_facility_license("PK Đa Khoa A", "POLYCLINIC", "Hà Nội", 0, 100.0, "BS A", 40)
        # Clinical trial
        engine.submit_clinical_trial_protocol("DEV-01", "Thử nghiệm SpO2", 1)

        # Check listings
        assert len(engine.list_medical_devices()) == 1
        assert len(engine.list_price_declarations()) == 1
        assert len(engine.list_healthcare_facilities()) == 1
        assert len(engine.list_clinical_trials()) == 1

        # Check status
        st = engine.get_status()
        assert st["ok"] is True
        m = st["metrics"]
        assert m["registered_medical_devices"] == 1
        assert m["clinical_trial_exempt_devices"] == 1
        assert m["price_declarations_filed"] == 1
        assert m["compliant_price_declarations"] == 1
        assert m["healthcare_facilities_evaluated"] == 1
        assert m["licensed_healthcare_facilities"] == 1
        assert m["clinical_trials_initiated"] == 1
        assert m["active_enrolling_trials"] == 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestMedtechCLI:
    """Test Typer CLI surface for mekong medtech."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_main_status(self, app) -> None:
        result = runner.invoke(app, ["medtech", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_cli_device(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "medtech",
                "device",
                "Máy chụp cắt lớp CT Scanner 128 dãy",
                "--class",
                "CLASS_C",
                "--maker",
                "GE Healthcare",
                "--origin",
                "USA",
                "--importer",
                "Công ty TNHH Thiết Bị Y Tế Thủ Đô",
                "--use",
                "Chẩn đoán hình ảnh sọ não và lồng ngực",
                "--cfs",
                "FDA",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["device_profile"]["risk_class"] == "CLASS_C"
        assert data["device_profile"]["is_clinical_trial_exempt"] is True

    def test_cli_price(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "medtech",
                "price",
                "DEV-TEST-CLI",
                "Máy siêu âm Doppler tim mạch",
                "--cif",
                "500000000",
                "--wholesale",
                "650000000",
                "--retail",
                "750000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["price_declaration"]["markup_percentage"] == 30.0
        assert data["price_declaration"]["is_markup_compliant"] is True

    def test_cli_facility(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "medtech",
                "facility",
                "Bệnh viện Quốc tế Nam Sài Gòn",
                "--type",
                "GENERAL_HOSPITAL",
                "--province",
                "TP. Hồ Chí Minh",
                "--beds",
                "200",
                "--area",
                "12000",
                "--cmo",
                "PGS.TS. Đặng Quốc Hưng",
                "--months",
                "72",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["facility_evaluation"]["is_license_approved"] is True

    def test_cli_trial(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "medtech",
                "trial",
                "DEV-TEST-CLI",
                "Thử nghiệm lâm sàng Stent can thiệp mạch",
                "--phase",
                "3",
                "--pi",
                "GS.TS. Nguyễn Hữu Dũng",
                "--site",
                "Bệnh viện Bạch Mai",
                "--subjects",
                "180",
                "--irb",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["trial_profile"]["trial_phase"] == 3
        assert data["trial_profile"]["is_irb_approved"] is True

    def test_cli_list(self, app) -> None:
        result = runner.invoke(app, ["medtech", "list", "devices", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "medical_devices" in data

    def test_cli_status(self, app) -> None:
        result = runner.invoke(app, ["medtech", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Integration Tests
# ---------------------------------------------------------------------------


class TestMedtechMCP:
    """Test MCP server tool handlers and FastMCP parity for medtech."""

    def test_pure_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            handle_medtech_device,
            handle_medtech_price,
            handle_medtech_facility,
            handle_medtech_trial,
            handle_medtech_list,
            handle_medtech_status,
        )

        # Device
        res_d = json.loads(handle_medtech_device({"name": "Thiết Bị MCP", "class": "CLASS_B"}))
        assert res_d["ok"] is True

        # Price
        res_p = json.loads(handle_medtech_price({"device_id": "DEV-MCP", "name": "Thiết Bị MCP", "cif": 10000000, "wholesale": 13000000, "retail": 15000000}))
        assert res_p["ok"] is True

        # Facility
        res_f = json.loads(handle_medtech_facility({"name": "Bệnh Viện MCP", "type": "GENERAL_HOSPITAL", "beds": 100, "area": 6000, "months": 60}))
        assert res_f["ok"] is True

        # Trial
        res_t = json.loads(handle_medtech_trial({"device_id": "DEV-MCP", "title": "Đề Cương MCP", "phase": 2}))
        assert res_t["ok"] is True

        # List & Status
        res_l = json.loads(handle_medtech_list({"category": "devices"}))
        assert isinstance(res_l, list)

        res_s = json.loads(handle_medtech_status({}))
        assert res_s["ok"] is True

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Device
        res_d = json.loads(server._handle_medtech_device(device_name="Thiết Bị Core MCP", risk_class="CLASS_A"))
        assert res_d["ok"] is True

        # Price
        res_p = json.loads(server._handle_medtech_price(device_id="DEV-CORE", device_name="Thiết Bị Core", cif_cost_vnd=10000000, wholesale_price_vnd=12500000, retail_price_vnd=14000000))
        assert res_p["ok"] is True

        # Facility
        res_f = json.loads(server._handle_medtech_facility(facility_name="Bệnh Viện Core", facility_type="GENERAL_HOSPITAL", bed_capacity=120, total_floor_area_m2=7500, cmo_practice_months=60))
        assert res_f["ok"] is True

        # Trial
        res_t = json.loads(server._handle_medtech_trial(device_id="DEV-CORE", trial_title="Thử Nghiệm Core", trial_phase=2))
        assert res_t["ok"] is True

        # List & Status
        res_l = json.loads(server._handle_medtech_list(category="devices"))
        assert isinstance(res_l, list)

        res_s = json.loads(server._handle_medtech_status())
        assert res_s["ok"] is True
