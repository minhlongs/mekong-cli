"""
Tests for Vietnamese Legal Profession, Bar Association & Law Practice Suite (Phase 136).
Compliant with:
- Law on Lawyers 2006 (Law No. 65/2006/QH11) as amended by Law No. 20/2012/QH13
- Decree No. 123/2013/NĐ-CP & Decree No. 137/2018/NĐ-CP on Law Practice Regulations
- Code of Professional Ethics and Conduct of Vietnamese Lawyers (Decision No. 201/QĐ-HĐLSTQ)
- Criminal Procedure Code 2015 (Law No. 101/2015/QH13)
"""

import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.core.lawyer_engine import (
    LawyerEngine,
    PracticeForm,
    LegalSpecialization,
    ServiceScope,
    ProceduralRole,
    EthicalVerdict,
)
from src.cli.commands.lawyer_command import lawyer_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as scripts_mcp


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["MEKONG_LAWYER_DB"] = path
    yield path
    os.environ.pop("MEKONG_LAWYER_DB", None)
    for p in (path, f"{path}-wal", f"{path}-shm"):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


@pytest.fixture
def engine(temp_db):
    return LawyerEngine(db_path=temp_db)


@pytest.fixture
def runner():
    return CliRunner()


class TestLawyerEngine:
    def test_register_lawyer_valid(self, engine):
        res = engine.register_lawyer(
            card_number="LS-HN-001",
            license_number="CC-BTP-101",
            full_name="Nguyễn Văn Luật",
            bar_association="Đoàn Luật sư TP. Hà Nội",
            organization_name="Công ty Luật TNHH Ánh Sáng",
            practice_form="CONG_TY_LUAT_TNHH_2TV",
            specialization="TRANH_TUNG_DAN_SU",
            issue_date="2024-05-15",
            status="ACTIVE",
        )
        assert res["success"] is True
        assert res["lawyer"]["card_number"] == "LS-HN-001"
        assert res["lawyer"]["practice_form"] == PracticeForm.CONG_TY_LUAT_TNHH_2TV.value
        assert "Law on Lawyers" in res["statutory_reference"]

    def test_register_lawyer_missing_fields(self, engine):
        res = engine.register_lawyer(
            card_number="",
            license_number="CC-101",
            full_name="Trần Văn B",
            bar_association="Đoàn Luật sư TP.HCM",
            organization_name="VPLS B",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_register_lawyer_invalid_form(self, engine):
        res = engine.register_lawyer(
            card_number="LS-002",
            license_number="CC-102",
            full_name="Lê Thị C",
            bar_association="Đoàn Luật sư Đà Nẵng",
            organization_name="VPLS C",
            practice_form="INVALID_FORM",
        )
        assert res["success"] is False
        assert "Invalid practice form" in res["error"]

    def test_register_lawyer_invalid_spec(self, engine):
        res = engine.register_lawyer(
            card_number="LS-003",
            license_number="CC-103",
            full_name="Phạm Văn D",
            bar_association="Đoàn Luật sư Hải Phòng",
            organization_name="VPLS D",
            specialization="INVALID_SPEC",
        )
        assert res["success"] is False
        assert "Invalid specialization" in res["error"]

    def test_register_lawyer_update_existing(self, engine):
        engine.register_lawyer(
            card_number="LS-004",
            license_number="CC-104",
            full_name="Vũ Văn E",
            bar_association="Đoàn Luật sư Cần Thơ",
            organization_name="Công ty Luật E1",
        )
        res_update = engine.register_lawyer(
            card_number="LS-004",
            license_number="CC-104",
            full_name="Vũ Văn E",
            bar_association="Đoàn Luật sư Cần Thơ",
            organization_name="Công ty Luật E2",
        )
        assert res_update["success"] is True
        assert res_update["lawyer"]["organization_name"] == "Công ty Luật E2"

    def test_register_firm_valid(self, engine):
        res = engine.register_firm(
            registration_number="DK-HN-2024-01",
            firm_name="Công ty Luật TNHH Minh Long & Cộng sự",
            form="CONG_TY_LUAT_TNHH_2TV",
            managing_partner="Nguyễn Văn Luật",
            justice_dept="Sở Tư pháp TP. Hà Nội",
            address="123 Phố Huế, Hai Bà Trưng, Hà Nội",
            charter_capital=5_000_000_000.0,
            operating_status="ACTIVE",
        )
        assert res["success"] is True
        assert res["law_firm"]["registration_number"] == "DK-HN-2024-01"
        assert res["law_firm"]["charter_capital"] == 5_000_000_000.0

    def test_register_firm_missing_fields(self, engine):
        res = engine.register_firm(
            registration_number="",
            firm_name="VPLS Test",
            form="VAN_PHONG_LUAT_SU",
            managing_partner="",
            justice_dept="",
            address="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_register_firm_invalid_capital(self, engine):
        res = engine.register_firm(
            registration_number="DK-02",
            firm_name="VPLS Test 2",
            form="VAN_PHONG_LUAT_SU",
            managing_partner="Partner A",
            justice_dept="Sở Tư pháp",
            address="Hà Nội",
            charter_capital=-100.0,
        )
        assert res["success"] is False
        assert "non-negative" in res["error"]

    def test_register_firm_update_existing(self, engine):
        engine.register_firm(
            registration_number="DK-03",
            firm_name="VPLS 3",
            form="VAN_PHONG_LUAT_SU",
            managing_partner="Partner 1",
            justice_dept="Sở Tư pháp",
            address="Hà Nội",
        )
        res = engine.register_firm(
            registration_number="DK-03",
            firm_name="VPLS 3 New",
            form="VAN_PHONG_LUAT_SU",
            managing_partner="Partner 2",
            justice_dept="Sở Tư pháp",
            address="Hà Nội",
        )
        assert res["success"] is True
        assert res["law_firm"]["firm_name"] == "VPLS 3 New"

    def test_execute_contract_valid(self, engine):
        res = engine.execute_legal_contract(
            contract_number="HD-2025-001",
            client_name="Tập đoàn Hoa Sen",
            client_id_tax="0301234567",
            service_scope="TU_VAN_PHAP_LUAT",
            case_or_matter_title="Tư vấn M&A dự án năng lượng",
            assigned_lawyer_card="LS-HN-005",
            remuneration_vnd=250_000_000.0,
            signing_date="2025-02-10",
            status="ACTIVE",
        )
        assert res["success"] is True
        assert res["legal_contract"]["contract_number"] == "HD-2025-001"
        assert res["legal_contract"]["remuneration_vnd"] == 250_000_000.0
        assert "Articles 54-56" in res["statutory_reference"]

    def test_execute_contract_missing_fields(self, engine):
        res = engine.execute_legal_contract(
            contract_number="",
            client_name="",
            client_id_tax="",
            service_scope="TU_VAN_PHAP_LUAT",
            case_or_matter_title="",
            assigned_lawyer_card="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_execute_contract_invalid_scope(self, engine):
        res = engine.execute_legal_contract(
            contract_number="HD-2025-003",
            client_name="Client Y",
            client_id_tax="010888888",
            service_scope="INVALID_SCOPE",
            case_or_matter_title="Title Y",
            assigned_lawyer_card="LS-HN-006",
        )
        assert res["success"] is False
        assert "Invalid service scope" in res["error"]

    def test_execute_contract_negative_fee(self, engine):
        res = engine.execute_legal_contract(
            contract_number="HD-2025-004",
            client_name="Client Z",
            client_id_tax="010777777",
            service_scope="TU_VAN_PHAP_LUAT",
            case_or_matter_title="Title Z",
            assigned_lawyer_card="LS-HN-007",
            remuneration_vnd=-500.0,
        )
        assert res["success"] is False
        assert "non-negative" in res["error"]

    def test_record_defense_valid(self, engine):
        res = engine.record_litigation_defense(
            participation_code="TGTT-2025-001",
            case_number="HSST-2025/12",
            proceeding_agency="Tòa án nhân dân TP. Hà Nội",
            lawyer_card="LS-HN-008",
            procedural_role="NGUOI_BAO_CHUA",
            registration_date="2025-03-01",
            registration_status="ACCEPTED",
            notes="Bào chữa cho bị cáo trong vụ án hình sự",
        )
        assert res["success"] is True
        assert res["litigation_participation"]["participation_code"] == "TGTT-2025-001"
        assert res["litigation_participation"]["procedural_role"] == ProceduralRole.NGUOI_BAO_CHUA.value
        assert "Article 27 Law on Lawyers" in res["statutory_reference"]

    def test_record_defense_missing_fields(self, engine):
        res = engine.record_litigation_defense(
            participation_code="",
            case_number="",
            proceeding_agency="",
            lawyer_card="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_record_defense_invalid_role(self, engine):
        res = engine.record_litigation_defense(
            participation_code="TGTT-003",
            case_number="DS-01",
            proceeding_agency="Tòa án ND",
            lawyer_card="LS-HN-009",
            procedural_role="INVALID_ROLE",
        )
        assert res["success"] is False
        assert "Invalid procedural role" in res["error"]

    def test_audit_ethics_valid(self, engine):
        res = engine.audit_ethical_compliance(
            review_code="ETH-2025-001",
            lawyer_card="LS-HN-010",
            conflict_of_interest_checked=True,
            client_confidentiality_certified=True,
            legal_aid_pro_bono_hours=12.5,
            compliance_verdict="EXEMPLARY",
            reviewer_notes="Hoàn thành xuất sắc nghĩa vụ trợ giúp pháp lý và quy tắc đạo đức",
        )
        assert res["success"] is True
        assert res["ethical_review"]["review_code"] == "ETH-2025-001"
        assert res["ethical_review"]["compliance_verdict"] == EthicalVerdict.EXEMPLARY.value
        assert "Decision 201/QĐ-HĐLSTQ" in res["statutory_reference"]

    def test_audit_ethics_missing_fields(self, engine):
        res = engine.audit_ethical_compliance(
            review_code="",
            lawyer_card="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_audit_ethics_invalid_verdict(self, engine):
        res = engine.audit_ethical_compliance(
            review_code="ETH-003",
            lawyer_card="LS-HN-011",
            compliance_verdict="INVALID_VERDICT",
        )
        assert res["success"] is False
        assert "Invalid compliance verdict" in res["error"]

    def test_audit_ethics_negative_pro_bono(self, engine):
        res = engine.audit_ethical_compliance(
            review_code="ETH-004",
            lawyer_card="LS-HN-012",
            legal_aid_pro_bono_hours=-5.0,
        )
        assert res["success"] is False
        assert "non-negative" in res["error"]

    def test_list_records_all_categories(self, engine):
        engine.register_lawyer(
            card_number="LS-01",
            license_number="CC-01",
            full_name="Lawyer 1",
            bar_association="Bar 1",
            organization_name="Org 1",
        )
        engine.register_firm(
            registration_number="FIRM-01",
            firm_name="Firm 1",
            form="CONG_TY_LUAT_TNHH_2TV",
            managing_partner="Lawyer 1",
            justice_dept="Dept 1",
            address="Addr 1",
        )
        engine.execute_legal_contract(
            contract_number="CTR-01",
            client_name="Client 1",
            client_id_tax="Tax 1",
            service_scope="TU_VAN_PHAP_LUAT",
            case_or_matter_title="Title 1",
            assigned_lawyer_card="LS-01",
        )
        engine.record_litigation_defense(
            participation_code="TG-01",
            case_number="Case 1",
            proceeding_agency="Agency 1",
            lawyer_card="LS-01",
        )
        engine.audit_ethical_compliance(
            review_code="ETH-01",
            lawyer_card="LS-01",
        )

        for cat in ("lawyers", "firms", "contracts", "litigation", "ethics"):
            res = engine.list_records(category=cat, limit=10)
            assert res["success"] is True
            assert len(res["records"]) == 1

    def test_list_records_invalid_category(self, engine):
        res = engine.list_records(category="invalid_category")
        assert res["success"] is False
        assert "Invalid category" in res["error"]

    def test_telemetry_status(self, engine):
        status = engine.get_telemetry_status()
        assert status["success"] is True
        assert "telemetry" in status
        telemetry = status["telemetry"]
        assert "lawyers" in telemetry
        assert "law_firms" in telemetry
        assert "legal_contracts" in telemetry
        assert "litigation" in telemetry
        assert "ethics_and_pro_bono" in telemetry


class TestLawyerCli:
    def test_cli_status(self, runner, temp_db):
        res = runner.invoke(lawyer_app, ["status"])
        assert res.exit_code == 0
        assert "VIETNAM BAR FEDERATION" in res.output

    def test_cli_status_json(self, runner, temp_db):
        res = runner.invoke(lawyer_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert "telemetry" in data

    def test_cli_main_callback_json(self, runner, temp_db):
        res = runner.invoke(lawyer_app, ["--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True

    def test_cli_attorney_cmd(self, runner, temp_db):
        res = runner.invoke(lawyer_app, [
            "attorney",
            "--card", "LS-CLI-01",
            "--license", "CC-CLI-01",
            "--name", "Lê Văn Luật",
            "--bar", "Đoàn Luật sư TP. Hà Nội",
            "--org", "VPLS Đồng Đội",
            "--form", "VAN_PHONG_LUAT_SU",
            "--spec", "TRANH_TUNG_HINH_SU",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["lawyer"]["card_number"] == "LS-CLI-01"

    def test_cli_attorney_missing_options(self, runner, temp_db):
        res = runner.invoke(lawyer_app, ["attorney"])
        assert res.exit_code != 0

    def test_cli_firm_cmd(self, runner, temp_db):
        res = runner.invoke(lawyer_app, [
            "firm",
            "--reg-num", "DK-CLI-01",
            "--name", "Công ty Luật Trí Việt",
            "--partner", "Lê Văn Luật",
            "--dept", "Sở Tư pháp TP. Hà Nội",
            "--address", "Số 1 Cầu Giấy, Hà Nội",
            "--capital", "2000000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["law_firm"]["registration_number"] == "DK-CLI-01"

    def test_cli_contract_cmd(self, runner, temp_db):
        res = runner.invoke(lawyer_app, [
            "contract",
            "--contract-num", "HD-CLI-01",
            "--client", "Vinamilk",
            "--tax-id", "0300588569",
            "--scope", "TU_VAN_PHAP_LUAT",
            "--title", "Tư vấn sở hữu trí tuệ",
            "--lawyer", "LS-CLI-02",
            "--fee", "150000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["legal_contract"]["contract_number"] == "HD-CLI-01"

    def test_cli_defense_cmd(self, runner, temp_db):
        res = runner.invoke(lawyer_app, [
            "defense",
            "--code", "TGTT-CLI-01",
            "--case", "HS-2025/99",
            "--agency", "Tòa án TP.HCM",
            "--lawyer", "LS-CLI-03",
            "--role", "NGUOI_BAO_CHUA",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["litigation_participation"]["participation_code"] == "TGTT-CLI-01"

    def test_cli_ethics_cmd(self, runner, temp_db):
        res = runner.invoke(lawyer_app, [
            "ethics",
            "--code", "ETH-CLI-01",
            "--lawyer", "LS-CLI-04",
            "--pro-bono", "8.0",
            "--verdict", "COMPLIANT",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["ethical_review"]["review_code"] == "ETH-CLI-01"

    def test_cli_list_cmd(self, runner, temp_db):
        runner.invoke(lawyer_app, [
            "attorney",
            "--card", "LS-CLI-05",
            "--license", "CC-CLI-05",
            "--name", "Võ Tấn",
            "--bar", "Đoàn Luật sư Cần Thơ",
            "--org", "Công ty Luật Tấn",
            "--json",
        ])
        res = runner.invoke(lawyer_app, ["list", "lawyers", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert len(data["records"]) >= 1


class TestLawyerCoreMcp:
    def test_core_mcp_handlers(self, temp_db):
        server = MekongMcpServer()
        # Register lawyer
        res_lawyer = json.loads(server._handle_lawyer_attorney(
            card="LS-MCP-01",
            license_num="CC-MCP-01",
            name="Vũ Đức",
            bar="Đoàn Luật sư Hà Nội",
            org="Công ty Luật Đức",
        ))
        assert res_lawyer["success"] is True

        # Register firm
        res_firm = json.loads(server._handle_lawyer_firm(
            reg_num="DK-MCP-01",
            name="Công ty Luật Đức",
            partner="Vũ Đức",
            dept="Sở Tư pháp Hà Nội",
            address="Hà Nội",
            capital=1_000_000_000.0,
        ))
        assert res_firm["success"] is True

        # Execute contract
        res_contract = json.loads(server._handle_lawyer_contract(
            contract_num="HD-MCP-01",
            client="Client MCP",
            tax_id="010111222",
            title="Tư vấn thuế",
            lawyer="LS-MCP-01",
            fee=50_000_000.0,
        ))
        assert res_contract["success"] is True

        # Record defense
        res_defense = json.loads(server._handle_lawyer_defense(
            code="TG-MCP-01",
            case="Case-MCP",
            agency="TAND Cấp cao",
            lawyer="LS-MCP-01",
        ))
        assert res_defense["success"] is True

        # Audit ethics
        res_ethics = json.loads(server._handle_lawyer_ethics(
            code="ETH-MCP-01",
            lawyer="LS-MCP-01",
            pro_bono=10.0,
        ))
        assert res_ethics["success"] is True

        # List
        res_list = json.loads(server._handle_lawyer_list(category="lawyers"))
        assert res_list["success"] is True
        assert len(res_list["records"]) >= 1

        # Status
        res_status = json.loads(server._handle_lawyer_status())
        assert res_status["success"] is True

    def test_core_mcp_aliases(self, temp_db):
        server = MekongMcpServer()
        assert server._handle_mekong_lawyer_attorney == server._handle_lawyer_attorney
        assert server._handle_mekong_lawyer_firm == server._handle_lawyer_firm
        assert server._handle_mekong_lawyer_contract == server._handle_lawyer_contract
        assert server._handle_mekong_lawyer_defense == server._handle_lawyer_defense
        assert server._handle_mekong_lawyer_ethics == server._handle_lawyer_ethics
        assert server._handle_mekong_lawyer_list == server._handle_lawyer_list
        assert server._handle_mekong_lawyer_status == server._handle_lawyer_status


class TestLawyerScriptsMcp:
    def test_scripts_mcp_handlers(self, temp_db):
        # Register lawyer
        res_lawyer = json.loads(scripts_mcp.handle_lawyer_attorney({
            "card": "LS-SCR-01",
            "license_num": "CC-SCR-01",
            "name": "Bùi Tiến",
            "bar": "Đoàn Luật sư Hà Nội",
            "org": "Công ty Luật Tiến",
        }))
        assert res_lawyer["success"] is True

        # Register firm
        res_firm = json.loads(scripts_mcp.handle_lawyer_firm({
            "reg_num": "DK-SCR-01",
            "name": "Công ty Luật Tiến",
            "partner": "Bùi Tiến",
            "dept": "Sở Tư pháp Hà Nội",
            "address": "Hà Nội",
            "capital": 500_000_000.0,
        }))
        assert res_firm["success"] is True

        # Execute contract
        res_contract = json.loads(scripts_mcp.handle_lawyer_contract({
            "contract_num": "HD-SCR-01",
            "client": "Client SCR",
            "tax_id": "010333444",
            "title": "Tư vấn doanh nghiệp",
            "lawyer": "LS-SCR-01",
            "fee": 30_000_000.0,
        }))
        assert res_contract["success"] is True

        # Record defense
        res_defense = json.loads(scripts_mcp.handle_lawyer_defense({
            "code": "TG-SCR-01",
            "case": "Case-SCR",
            "agency": "TAND Hà Nội",
            "lawyer": "LS-SCR-01",
        }))
        assert res_defense["success"] is True

        # Audit ethics
        res_ethics = json.loads(scripts_mcp.handle_lawyer_ethics({
            "code": "ETH-SCR-01",
            "lawyer": "LS-SCR-01",
            "pro_bono": 5.0,
        }))
        assert res_ethics["success"] is True

        # List
        res_list = json.loads(scripts_mcp.handle_lawyer_list({"category": "lawyers"}))
        assert res_list["success"] is True

        # Status
        res_status = json.loads(scripts_mcp.handle_lawyer_status({}))
        assert res_status["success"] is True

    def test_scripts_mcp_core_handlers_map(self):
        for name in (
            "mekong_lawyer_attorney",
            "mekong_lawyer_firm",
            "mekong_lawyer_contract",
            "mekong_lawyer_defense",
            "mekong_lawyer_ethics",
            "mekong_lawyer_list",
            "mekong_lawyer_status",
            "lawyer_attorney",
            "lawyer_firm",
            "lawyer_contract",
            "lawyer_defense",
            "lawyer_ethics",
            "lawyer_list",
            "lawyer_status",
        ):
            assert name in scripts_mcp.CORE_HANDLERS
            assert callable(scripts_mcp.CORE_HANDLERS[name])

    def test_scripts_mcp_tools_spec(self):
        names = {t["name"] for t in scripts_mcp.CORE_TOOLS_SPEC}
        for expected in (
            "mekong_lawyer_attorney",
            "mekong_lawyer_firm",
            "mekong_lawyer_contract",
            "mekong_lawyer_defense",
            "mekong_lawyer_ethics",
            "mekong_lawyer_list",
            "mekong_lawyer_status",
        ):
            assert expected in names
