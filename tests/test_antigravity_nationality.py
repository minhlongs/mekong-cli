"""
Unit & Integration Tests for Vietnamese Nationality, Naturalization, Renunciation & Dual Citizenship Suite.
Compliant with:
- Law on Vietnamese Nationality 2008 (Luật Quốc tịch Việt Nam - Law No. 24/2008/QH12)
- Law Amending and Supplementing Law on Vietnamese Nationality 2014 (Law No. 56/2014/QH13)
- Decree No. 16/2020/ND-CP detailing the implementation of the Law on Vietnamese Nationality
- Circular No. 02/2020/TT-BTP guiding Decree No. 16/2020/ND-CP
- tests/test_core_boundary.py (Strict zero vendor-sdk / AST boundary compliance)
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.nationality_engine import (
    NationalityEngine,
    NaturalizationExemption,
    DualNationalityPermission,
    RenunciationBar,
    NationalityStatus,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as script_mcp

runner = CliRunner()


@pytest.fixture
def engine(tmp_path):
    db_file = tmp_path / "test_nationality.db"
    return NationalityEngine(db_path=str(db_file))


class TestNationalityEngine:
    def test_process_naturalization_standard_success(self, engine):
        res = engine.process_naturalization(
            applicant_name="Alexandre De Rhodes",
            vietnamese_chosen_name="Đắc Lộ",
            birth_date="1980-03-15",
            current_nationality="France",
            residence_years=7.5,
            vietnamese_proficiency=True,
            livelihood_assured=True,
            exemption=NaturalizationExemption.NONE.value,
            dual_nationality_permit=DualNationalityPermission.RENUNCIATION_REQUIRED.value,
            status=NationalityStatus.DOSSIER_SUBMITTED.value,
            notes="Applicant speaks fluent Vietnamese and has lived in Hanoi for 7 years.",
        )
        assert res["dossier_id"].startswith("NAT-")
        assert res["applicant_name"] == "Alexandre De Rhodes"
        assert res["vietnamese_chosen_name"] == "Đắc Lộ"
        assert res["residence_years"] == 7.5
        assert res["vietnamese_proficiency"] == 1
        assert res["livelihood_assured"] == 1
        assert res["exemption_category"] == NaturalizationExemption.NONE.value
        assert res["dual_nationality_permit"] == DualNationalityPermission.RENUNCIATION_REQUIRED.value
        assert res["status"] == NationalityStatus.DOSSIER_SUBMITTED.value

    def test_process_naturalization_statutory_issues_rejection(self, engine):
        # Deficient residence years (< 5), no proficiency, no livelihood -> auto-rejected if not SUBMITTED/REJECTED
        res = engine.process_naturalization(
            applicant_name="John Smith",
            vietnamese_chosen_name="Nguyễn Văn John",
            birth_date="1995-10-10",
            current_nationality="USA",
            residence_years=2.0,
            vietnamese_proficiency=False,
            livelihood_assured=False,
            exemption=NaturalizationExemption.NONE.value,
            status=NationalityStatus.JUSTICE_VERIFIED.value,
        )
        assert res["status"] == NationalityStatus.REJECTED.value
        assert "REJECTION: Residence in Vietnam must be at least 5 years" in res["notes"]
        assert "REJECTION: Knowing Vietnamese sufficiently is required" in res["notes"]
        assert "REJECTION: Capable of ensuring livelihood in Vietnam is required" in res["notes"]

    def test_process_naturalization_exemptions(self, engine):
        # Exemption SPOUSE_PARENT_CHILD waives 5-year residency and other standard bars
        res = engine.process_naturalization(
            applicant_name="Maria Tanaka",
            vietnamese_chosen_name="Nguyễn Thị Mai",
            birth_date="1992-06-20",
            current_nationality="Japan",
            residence_years=1.5,
            vietnamese_proficiency=False,
            livelihood_assured=True,
            exemption=NaturalizationExemption.SPOUSE_PARENT_CHILD.value,
            status=NationalityStatus.JUSTICE_VERIFIED.value,
        )
        assert res["status"] == NationalityStatus.JUSTICE_VERIFIED.value
        assert res["exemption_category"] == NaturalizationExemption.SPOUSE_PARENT_CHILD.value

    def test_process_naturalization_dual_permit(self, engine):
        res = engine.process_naturalization(
            applicant_name="David Park",
            vietnamese_chosen_name="Park Văn Đạt",
            birth_date="1988-12-05",
            current_nationality="South Korea",
            residence_years=5.0,
            vietnamese_proficiency=True,
            livelihood_assured=True,
            exemption=NaturalizationExemption.BENEFICIAL_TO_STATE.value,
            dual_nationality_permit=DualNationalityPermission.SPECIAL_PRESIDENTIAL_PERMIT.value,
            presidential_decision_no="456/2026/QĐ-CTN",
            decision_date="2026-09-15",
            status=NationalityStatus.PRESIDENT_DECREED.value,
        )
        assert res["status"] == NationalityStatus.PRESIDENT_DECREED.value
        assert res["dual_nationality_permit"] == DualNationalityPermission.SPECIAL_PRESIDENTIAL_PERMIT.value
        assert res["presidential_decision_no"] == "456/2026/QĐ-CTN"

    def test_process_naturalization_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Applicant name cannot be empty"):
            engine.process_naturalization(
                applicant_name="",
                vietnamese_chosen_name="Nguyen Van A",
                birth_date="1990-01-01",
                current_nationality="Laos",
            )

        with pytest.raises(ValueError, match="Chosen Vietnamese name cannot be empty"):
            engine.process_naturalization(
                applicant_name="Somxay",
                vietnamese_chosen_name="  ",
                birth_date="1990-01-01",
                current_nationality="Laos",
            )

        with pytest.raises(ValueError, match="Birth date cannot be empty"):
            engine.process_naturalization(
                applicant_name="Somxay",
                vietnamese_chosen_name="Nguyen Van Som",
                birth_date="",
                current_nationality="Laos",
            )

        with pytest.raises(ValueError, match="Current nationality cannot be empty"):
            engine.process_naturalization(
                applicant_name="Somxay",
                vietnamese_chosen_name="Nguyen Van Som",
                birth_date="1990-01-01",
                current_nationality="",
            )

        with pytest.raises(ValueError, match="Invalid exemption category"):
            engine.process_naturalization(
                applicant_name="Somxay",
                vietnamese_chosen_name="Nguyen Van Som",
                birth_date="1990-01-01",
                current_nationality="Laos",
                exemption="INVALID_EXEMPTION",
            )

        with pytest.raises(ValueError, match="Invalid dual nationality permission"):
            engine.process_naturalization(
                applicant_name="Somxay",
                vietnamese_chosen_name="Nguyen Van Som",
                birth_date="1990-01-01",
                current_nationality="Laos",
                dual_nationality_permit="INVALID_PERMIT",
            )

        with pytest.raises(ValueError, match="Invalid nationality status"):
            engine.process_naturalization(
                applicant_name="Somxay",
                vietnamese_chosen_name="Nguyen Van Som",
                birth_date="1990-01-01",
                current_nationality="Laos",
                status="INVALID_STATUS",
            )

    def test_process_naturalization_upsert(self, engine):
        res1 = engine.process_naturalization(
            applicant_name="Elena Petrova",
            vietnamese_chosen_name="Lê Thị Lan",
            birth_date="1987-04-11",
            current_nationality="Russia",
            residence_years=6.0,
            dossier_id="NAT-CUSTOM-001",
            status=NationalityStatus.DOSSIER_SUBMITTED.value,
        )
        assert res1["dossier_id"] == "NAT-CUSTOM-001"
        assert res1["status"] == NationalityStatus.DOSSIER_SUBMITTED.value

        # Update status
        res2 = engine.process_naturalization(
            applicant_name="Elena Petrova",
            vietnamese_chosen_name="Lê Thị Lan",
            birth_date="1987-04-11",
            current_nationality="Russia",
            residence_years=6.0,
            dossier_id="NAT-CUSTOM-001",
            status=NationalityStatus.PRESIDENT_DECREED.value,
            presidential_decision_no="789/2026/QĐ-CTN",
        )
        assert res2["dossier_id"] == "NAT-CUSTOM-001"
        assert res2["status"] == NationalityStatus.PRESIDENT_DECREED.value
        assert res2["presidential_decision_no"] == "789/2026/QĐ-CTN"

    def test_process_renunciation_success(self, engine):
        res = engine.process_renunciation(
            applicant_name="Trần Văn Minh",
            birth_date="1984-11-22",
            target_foreign_country="Germany",
            tax_debt_cleared=True,
            criminal_prosecution_pending=False,
            judgment_execution_pending=False,
            national_security_clearance=True,
            status=NationalityStatus.MINISTER_PROPOSED.value,
            notes="Ready for submission to Prime Minister",
        )
        assert res["dossier_id"].startswith("REN-")
        assert res["applicant_name"] == "Trần Văn Minh"
        assert res["target_foreign_country"] == "Germany"
        assert res["renunciation_bar"] == RenunciationBar.NONE.value
        assert res["status"] == NationalityStatus.MINISTER_PROPOSED.value

    def test_process_renunciation_statutory_bars(self, engine):
        # 1. National Security
        r1 = engine.process_renunciation(
            applicant_name="Nguyễn Văn X",
            birth_date="1980-01-01",
            target_foreign_country="State A",
            national_security_clearance=False,
            status=NationalityStatus.JUSTICE_VERIFIED.value,
        )
        assert r1["renunciation_bar"] == RenunciationBar.NATIONAL_SECURITY_PREJUDICE.value
        assert r1["status"] == NationalityStatus.REJECTED.value

        # 2. Tax Debt
        r2 = engine.process_renunciation(
            applicant_name="Lê Văn Y",
            birth_date="1981-02-02",
            target_foreign_country="State B",
            tax_debt_cleared=False,
            status=NationalityStatus.JUSTICE_VERIFIED.value,
        )
        assert r2["renunciation_bar"] == RenunciationBar.TAX_DEBT.value
        assert r2["status"] == NationalityStatus.REJECTED.value

        # 3. Criminal Prosecution
        r3 = engine.process_renunciation(
            applicant_name="Phạm Văn Z",
            birth_date="1982-03-03",
            target_foreign_country="State C",
            criminal_prosecution_pending=True,
            status=NationalityStatus.JUSTICE_VERIFIED.value,
        )
        assert r3["renunciation_bar"] == RenunciationBar.CRIMINAL_PROSECUTION.value
        assert r3["status"] == NationalityStatus.REJECTED.value

        # 4. Judgment Execution Pending
        r4 = engine.process_renunciation(
            applicant_name="Võ Văn T",
            birth_date="1983-04-04",
            target_foreign_country="State D",
            judgment_execution_pending=True,
            status=NationalityStatus.JUSTICE_VERIFIED.value,
        )
        assert r4["renunciation_bar"] == RenunciationBar.JUDGMENT_EXECUTION.value
        assert r4["status"] == NationalityStatus.REJECTED.value

    def test_process_renunciation_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Applicant name cannot be empty"):
            engine.process_renunciation(
                applicant_name="",
                birth_date="1980-01-01",
                target_foreign_country="Germany",
            )
        with pytest.raises(ValueError, match="Birth date cannot be empty"):
            engine.process_renunciation(
                applicant_name="Tran A",
                birth_date="",
                target_foreign_country="Germany",
            )
        with pytest.raises(ValueError, match="Target foreign country cannot be empty"):
            engine.process_renunciation(
                applicant_name="Tran A",
                birth_date="1980-01-01",
                target_foreign_country="  ",
            )
        with pytest.raises(ValueError, match="Invalid nationality status"):
            engine.process_renunciation(
                applicant_name="Tran A",
                birth_date="1980-01-01",
                target_foreign_country="Germany",
                status="INVALID_STATUS",
            )

    def test_process_restoration_success(self, engine):
        res = engine.process_restoration(
            applicant_name="Hoàng Thị Thu",
            birth_date="1976-08-14",
            former_vietnamese_status="Original Birth Certificate Hanoi 1976",
            restoration_ground="Repatriation & Care for elderly parents (Art 23 k1b)",
            current_nationality="Canada",
            status=NationalityStatus.PRESIDENT_DECREED.value,
            presidential_decision_no="312/2026/QĐ-CTN",
            decision_date="2026-08-30",
        )
        assert res["dossier_id"].startswith("RES-")
        assert res["applicant_name"] == "Hoàng Thị Thu"
        assert res["former_vietnamese_status"] == "Original Birth Certificate Hanoi 1976"
        assert res["current_nationality"] == "Canada"
        assert res["status"] == NationalityStatus.PRESIDENT_DECREED.value
        assert res["presidential_decision_no"] == "312/2026/QĐ-CTN"

    def test_process_restoration_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Applicant name cannot be empty"):
            engine.process_restoration(
                applicant_name="",
                birth_date="1980-01-01",
                former_vietnamese_status="Old Passport",
                restoration_ground="Repatriation",
                current_nationality="Canada",
            )
        with pytest.raises(ValueError, match="Birth date cannot be empty"):
            engine.process_restoration(
                applicant_name="Hoang A",
                birth_date="",
                former_vietnamese_status="Old Passport",
                restoration_ground="Repatriation",
                current_nationality="Canada",
            )
        with pytest.raises(ValueError, match="Former Vietnamese status proof cannot be empty"):
            engine.process_restoration(
                applicant_name="Hoang A",
                birth_date="1980-01-01",
                former_vietnamese_status="  ",
                restoration_ground="Repatriation",
                current_nationality="Canada",
            )
        with pytest.raises(ValueError, match="Restoration ground description cannot be empty"):
            engine.process_restoration(
                applicant_name="Hoang A",
                birth_date="1980-01-01",
                former_vietnamese_status="Old Passport",
                restoration_ground=" ",
                current_nationality="Canada",
            )
        with pytest.raises(ValueError, match="Current nationality cannot be empty"):
            engine.process_restoration(
                applicant_name="Hoang A",
                birth_date="1980-01-01",
                former_vietnamese_status="Old Passport",
                restoration_ground="Repatriation",
                current_nationality="",
            )
        with pytest.raises(ValueError, match="Invalid nationality status"):
            engine.process_restoration(
                applicant_name="Hoang A",
                birth_date="1980-01-01",
                former_vietnamese_status="Old Passport",
                restoration_ground="Repatriation",
                current_nationality="Canada",
                status="INVALID_STATUS",
            )

    def test_issue_nationality_certificate_success(self, engine):
        res = engine.issue_nationality_certificate(
            applicant_name="Đặng Thái Sơn",
            identity_type="PASSPORT",
            identity_number="C9876543",
            residence_status="OVERSEAS_VIETNAMESE",
            issuing_authority="Sở Tư pháp TP Hồ Chí Minh",
            certificate_number="55/2026/GXN-QT",
            issue_date="2026-09-28",
            status="VALID",
            notes="Certificate for civil and property registry",
        )
        assert res["cert_id"].startswith("CERT-")
        assert res["applicant_name"] == "Đặng Thái Sơn"
        assert res["identity_number"] == "C9876543"
        assert res["issuing_authority"] == "Sở Tư pháp TP Hồ Chí Minh"
        assert res["certificate_number"] == "55/2026/GXN-QT"
        assert res["status"] == "VALID"

    def test_issue_nationality_certificate_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Applicant name cannot be empty"):
            engine.issue_nationality_certificate(
                applicant_name="",
                identity_type="PASSPORT",
                identity_number="123",
                residence_status="DOMESTIC",
                issuing_authority="STP",
                certificate_number="1/2026",
                issue_date="2026-01-01",
            )
        with pytest.raises(ValueError, match="Identity document type cannot be empty"):
            engine.issue_nationality_certificate(
                applicant_name="Dang A",
                identity_type="  ",
                identity_number="123",
                residence_status="DOMESTIC",
                issuing_authority="STP",
                certificate_number="1/2026",
                issue_date="2026-01-01",
            )
        with pytest.raises(ValueError, match="Identity document number cannot be empty"):
            engine.issue_nationality_certificate(
                applicant_name="Dang A",
                identity_type="PASSPORT",
                identity_number="",
                residence_status="DOMESTIC",
                issuing_authority="STP",
                certificate_number="1/2026",
                issue_date="2026-01-01",
            )
        with pytest.raises(ValueError, match="Issuing authority .* cannot be empty"):
            engine.issue_nationality_certificate(
                applicant_name="Dang A",
                identity_type="PASSPORT",
                identity_number="123",
                residence_status="DOMESTIC",
                issuing_authority="",
                certificate_number="1/2026",
                issue_date="2026-01-01",
            )
        with pytest.raises(ValueError, match="Certificate number cannot be empty"):
            engine.issue_nationality_certificate(
                applicant_name="Dang A",
                identity_type="PASSPORT",
                identity_number="123",
                residence_status="DOMESTIC",
                issuing_authority="STP",
                certificate_number="  ",
                issue_date="2026-01-01",
            )
        with pytest.raises(ValueError, match="Issue date cannot be empty"):
            engine.issue_nationality_certificate(
                applicant_name="Dang A",
                identity_type="PASSPORT",
                identity_number="123",
                residence_status="DOMESTIC",
                issuing_authority="STP",
                certificate_number="1/2026",
                issue_date="",
            )

    def test_get_record_and_list_records(self, engine):
        nat = engine.process_naturalization(
            applicant_name="Test Applicant",
            vietnamese_chosen_name="Nguyễn Văn Test",
            birth_date="1990-01-01",
            current_nationality="UK",
        )
        rec = engine.get_record("naturalization", nat["dossier_id"])
        assert rec["dossier_id"] == nat["dossier_id"]

        with pytest.raises(ValueError, match="Unknown category"):
            engine.get_record("unknown_cat", "123")

        with pytest.raises(KeyError, match="Record 'NONEXISTENT' not found"):
            engine.get_record("naturalization", "NONEXISTENT")

        records = engine.list_records("naturalization")
        assert len(records) >= 1
        assert any(r["dossier_id"] == nat["dossier_id"] for r in records)

        audits = engine.list_records("audit")
        assert len(audits) >= 1

        with pytest.raises(ValueError, match="Unknown category"):
            engine.list_records("unknown_cat")

    def test_get_telemetry_status(self, engine):
        engine.process_naturalization(
            applicant_name="Applicant 1",
            vietnamese_chosen_name="Ten VN 1",
            birth_date="1980-01-01",
            current_nationality="France",
            status=NationalityStatus.PRESIDENT_DECREED.value,
        )
        engine.process_renunciation(
            applicant_name="Applicant 2",
            birth_date="1985-02-02",
            target_foreign_country="USA",
            tax_debt_cleared=False,
            status=NationalityStatus.JUSTICE_VERIFIED.value,
        )
        engine.process_restoration(
            applicant_name="Applicant 3",
            birth_date="1970-03-03",
            former_vietnamese_status="Birth Cert",
            restoration_ground="Repatriation",
            current_nationality="Australia",
            status=NationalityStatus.PRESIDENT_DECREED.value,
        )
        engine.issue_nationality_certificate(
            applicant_name="Applicant 4",
            identity_type="CCCD",
            identity_number="001234567890",
            residence_status="DOMESTIC",
            issuing_authority="STP Hà Nội",
            certificate_number="01/2026/GXN",
            issue_date="2026-09-30",
        )
        status = engine.get_telemetry_status()
        assert status["total_naturalization_dossiers"] >= 1
        assert status["decreed_naturalizations"] >= 1
        assert status["total_renunciation_dossiers"] >= 1
        assert status["barred_renunciations"] >= 1
        assert status["total_restoration_dossiers"] >= 1
        assert status["decreed_restorations"] >= 1
        assert status["valid_nationality_certificates"] >= 1
        assert status["audit_logs_count"] >= 4
        assert status["system_status"] == "ONLINE_HEALTHY"


class TestNationalityCLI:
    @pytest.fixture(autouse=True)
    def setup_app(self, tmp_path, monkeypatch):
        db_file = tmp_path / "cli_nationality.db"
        monkeypatch.setenv("MEKONG_NATIONALITY_DB", str(db_file))
        self.app = build_app()

    def test_cli_help(self):
        result = runner.invoke(self.app, ["nationality", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Nationality" in result.output
        assert "naturalize" in result.output
        assert "renounce" in result.output
        assert "restore" in result.output
        assert "certificate" in result.output

        # Alias check
        result_alias = runner.invoke(self.app, ["citizenship", "--help"])
        assert result_alias.exit_code == 0
        assert "naturalize" in result_alias.output

    def test_cli_dashboard_and_json(self):
        # Visual dashboard
        res_dash = runner.invoke(self.app, ["nationality"])
        assert res_dash.exit_code == 0
        assert "QUẢN LÝ QUỐC TỊCH & NHẬP TỊCH" in res_dash.output

        # JSON dashboard
        res_json = runner.invoke(self.app, ["nationality", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_naturalization_dossiers" in data
        assert data["system_status"] == "ONLINE_HEALTHY"

        # status subcommand
        res_status = runner.invoke(self.app, ["nationality", "status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.output)
        assert data_status["statutory_framework"] == "Law on Vietnamese Nationality 2008/2014 & Decree 16/2020/ND-CP"

    def test_cli_naturalize(self):
        # Standard naturalize
        res = runner.invoke(self.app, [
            "nationality", "naturalize",
            "--applicant", "Alex Smith",
            "--chosen-name", "Nguyễn Văn Alex",
            "--birth-date", "1991-05-15",
            "--nationality", "USA",
            "--residence-years", "6.5",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["dossier_id"].startswith("NAT-")
        assert data["applicant_name"] == "Alex Smith"
        assert data["vietnamese_chosen_name"] == "Nguyễn Văn Alex"

        # Visual mode
        res_v = runner.invoke(self.app, [
            "nationality", "naturalize",
            "--applicant", "Maria Gomez",
            "--chosen-name", "Trần Thị Mai",
            "--birth-date", "1993-08-20",
            "--nationality", "Spain",
            "--residence-years", "5.0",
        ])
        assert res_v.exit_code == 0
        assert "Naturalization Dossier Evaluated" in res_v.output

    def test_cli_renounce(self):
        # Renunciation success
        res = runner.invoke(self.app, [
            "nationality", "renounce",
            "--applicant", "Nguyễn Văn Bình",
            "--birth-date", "1980-02-14",
            "--target-country", "Germany",
            "--tax-cleared",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["dossier_id"].startswith("REN-")
        assert data["renunciation_bar"] == RenunciationBar.NONE.value

        # Renunciation barred
        res_bar = runner.invoke(self.app, [
            "nationality", "renounce",
            "--applicant", "Trần Văn Cường",
            "--birth-date", "1985-07-21",
            "--target-country", "Canada",
            "--tax-pending",
            "--json"
        ])
        assert res_bar.exit_code == 0
        data_bar = json.loads(res_bar.output)
        assert data_bar["renunciation_bar"] == RenunciationBar.TAX_DEBT.value
        assert data_bar["status"] == NationalityStatus.REJECTED.value

    def test_cli_restore(self):
        res = runner.invoke(self.app, [
            "nationality", "restore",
            "--applicant", "Vũ Hoàng Lan",
            "--birth-date", "1972-11-09",
            "--former-status", "Giấy khai sinh gốc năm 1972",
            "--ground", "Hồi hương chăm sóc cha mẹ",
            "--nationality", "France",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["dossier_id"].startswith("RES-")
        assert data["applicant_name"] == "Vũ Hoàng Lan"
        assert data["current_nationality"] == "France"

    def test_cli_certificate(self):
        res = runner.invoke(self.app, [
            "nationality", "certificate",
            "--applicant", "Lê Văn Hùng",
            "--id-type", "PASSPORT",
            "--id-number", "VN998877",
            "--residence", "OVERSEAS_VIETNAMESE",
            "--authority", "ĐSQ Việt Nam tại Pháp",
            "--cert-no", "99/2026/GXN-QT",
            "--issue-date", "2026-09-30",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["cert_id"].startswith("CERT-")
        assert data["applicant_name"] == "Lê Văn Hùng"
        assert data["certificate_number"] == "99/2026/GXN-QT"

    def test_cli_list(self):
        # Create one naturalization record
        runner.invoke(self.app, [
            "nationality", "naturalize",
            "--applicant", "Johnathan",
            "--chosen-name", "Đoàn John",
            "--birth-date", "1988-01-01",
            "--nationality", "USA",
        ])

        # List records JSON
        res_json = runner.invoke(self.app, [
            "nationality", "list",
            "--category", "naturalization",
            "--json"
        ])
        assert res_json.exit_code == 0
        items = json.loads(res_json.output)
        assert isinstance(items, list)
        assert len(items) >= 1

        # List records Visual
        res_v = runner.invoke(self.app, [
            "nationality", "list",
            "--category", "naturalization",
        ])
        assert res_v.exit_code == 0
        assert "Nationality Records" in res_v.output

        # Invalid category
        res_err = runner.invoke(self.app, [
            "nationality", "list",
            "--category", "nonexistent_category",
        ])
        assert res_err.exit_code == 1


class TestNationalityMCP:
    @pytest.fixture(autouse=True)
    def setup_mcp_db(self, tmp_path, monkeypatch):
        db_file = tmp_path / "mcp_nationality.db"
        monkeypatch.setenv("MEKONG_NATIONALITY_DB", str(db_file))
        self.server = MekongMcpServer()

    def test_core_mcp_server_handlers(self):
        # 1. Naturalize
        nat_raw = self.server._handle_nationality_naturalize(
            applicant_name="Sarah Connor",
            vietnamese_chosen_name="Nguyễn Sa Ra",
            birth_date="1984-05-12",
            current_nationality="USA",
            residence_years=5.5,
            vietnamese_proficiency=True,
            livelihood_assured=True,
        )
        nat_data = json.loads(nat_raw)
        assert nat_data["dossier_id"].startswith("NAT-")
        assert nat_data["vietnamese_chosen_name"] == "Nguyễn Sa Ra"

        # 2. Renounce
        ren_raw = self.server._handle_nationality_renounce(
            applicant_name="Lê Văn Long",
            birth_date="1987-03-25",
            target_foreign_country="Australia",
            tax_debt_cleared=True,
        )
        ren_data = json.loads(ren_raw)
        assert ren_data["dossier_id"].startswith("REN-")
        assert ren_data["renunciation_bar"] == RenunciationBar.NONE.value

        # 3. Restore
        res_raw = self.server._handle_nationality_restore(
            applicant_name="Phạm Thị Bích",
            birth_date="1975-12-10",
            former_vietnamese_status="Giấy khai sinh gốc",
            restoration_ground="Hồi hương",
            current_nationality="France",
        )
        res_data = json.loads(res_raw)
        assert res_data["dossier_id"].startswith("RES-")

        # 4. Certificate
        cert_raw = self.server._handle_nationality_certificate(
            applicant_name="Nguyễn Văn An",
            identity_type="PASSPORT",
            identity_number="B1234567",
            residence_status="DOMESTIC",
            issuing_authority="Sở Tư pháp Hà Nội",
            certificate_number="12/2026/GXN-QT",
            issue_date="2026-09-30",
        )
        cert_data = json.loads(cert_raw)
        assert cert_data["cert_id"].startswith("CERT-")

        # 5. List
        list_raw = self.server._handle_nationality_list(category="naturalization", limit=10)
        list_data = json.loads(list_raw)
        assert isinstance(list_data, list)
        assert len(list_data) >= 1

        # 6. Status
        status_raw = self.server._handle_nationality_status()
        status_data = json.loads(status_raw)
        assert status_data["total_naturalization_dossiers"] >= 1
        assert status_data["system_status"] == "ONLINE_HEALTHY"

        # Aliases test
        status_alias_raw = self.server._handle_mekong_nationality_status()
        assert json.loads(status_alias_raw)["total_naturalization_dossiers"] >= 1

    def test_scripts_mcp_server_handlers_and_spec(self):
        # Test scripts/mcp_server.py dispatch
        # Status
        status_raw = script_mcp.CORE_HANDLERS["mekong_nationality_status"]({})
        status_data = json.loads(status_raw)
        assert "total_naturalization_dossiers" in status_data

        # Alias in CORE_HANDLERS
        status_alias_raw = script_mcp.CORE_HANDLERS["nationality_status"]({})
        assert "total_naturalization_dossiers" in json.loads(status_alias_raw)

        # Naturalize
        nat_raw = script_mcp.CORE_HANDLERS["mekong_nationality_naturalize"]({
            "applicant_name": "Michael Jordan",
            "vietnamese_chosen_name": "Mai Cơn",
            "birth_date": "1963-02-17",
            "current_nationality": "USA",
        })
        nat_data = json.loads(nat_raw)
        assert nat_data["dossier_id"].startswith("NAT-")

        # Renounce
        ren_raw = script_mcp.CORE_HANDLERS["mekong_nationality_renounce"]({
            "applicant_name": "Trần Văn Nam",
            "birth_date": "1990-09-09",
            "target_foreign_country": "Japan",
        })
        assert json.loads(ren_raw)["dossier_id"].startswith("REN-")

        # Restore
        res_raw = script_mcp.CORE_HANDLERS["mekong_nationality_restore"]({
            "applicant_name": "Lý Thị Hà",
            "birth_date": "1983-04-18",
            "former_vietnamese_status": "Hộ chiếu cũ",
            "restoration_ground": "Đầu tư kinh doanh",
            "current_nationality": "Singapore",
        })
        assert json.loads(res_raw)["dossier_id"].startswith("RES-")

        # Certificate
        cert_raw = script_mcp.CORE_HANDLERS["mekong_nationality_certificate"]({
            "applicant_name": "Võ Văn Hậu",
            "identity_type": "CCCD",
            "identity_number": "001099887766",
            "residence_status": "DOMESTIC",
            "issuing_authority": "Sở Tư pháp Đà Nẵng",
            "certificate_number": "34/2026/GXN-QT",
            "issue_date": "2026-09-30",
        })
        assert json.loads(cert_raw)["cert_id"].startswith("CERT-")

        # List
        list_raw = script_mcp.CORE_HANDLERS["mekong_nationality_list"]({"category": "certificate"})
        assert len(json.loads(list_raw)) >= 1

        # Direct function calls
        res_direct = json.loads(script_mcp.handle_nationality_status({}))
        assert res_direct["system_status"] == "ONLINE_HEALTHY"

        # Check tool specs exist in CORE_TOOLS_SPEC
        tool_names = [t["name"] for t in script_mcp.CORE_TOOLS_SPEC]
        assert "mekong_nationality_naturalize" in tool_names
        assert "mekong_nationality_renounce" in tool_names
        assert "mekong_nationality_restore" in tool_names
        assert "mekong_nationality_certificate" in tool_names
        assert "mekong_nationality_list" in tool_names
        assert "mekong_nationality_status" in tool_names
