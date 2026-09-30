"""
Unit & Integration Tests for Vietnamese Immigration, Entry, Exit, Transit, Residence & Visa Management Suite.
Compliant with:
- Law on Entry, Exit, Transit, and Residence of Foreigners in Vietnam 2014 (Law No. 47/2014/QH13)
- Law Amending and Supplementing Law on Entry/Exit of Vietnamese Citizens and Law on Entry/Exit/Residence of Foreigners 2023 (Law No. 23/2023/QH15)
- Law on Exit and Entry of Vietnamese Citizens 2019 (Law No. 49/2019/QH14)
- Decree No. 75/2020/ND-CP & Decree No. 127/2024/ND-CP (Electronic Visas, Border Controls, Autogates)
- tests/test_core_boundary.py (Strict zero vendor-sdk / AST boundary compliance)
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.immigration_engine import (
    ImmigrationEngine,
    VisaType,
    ResidenceCardType,
    MovementDirection,
    BorderGateType,
    RestrictionType,
    PassportType,
    ImmigrationStatus,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as script_mcp

runner = CliRunner()


@pytest.fixture
def engine(tmp_path):
    db_file = tmp_path / "test_immigration.db"
    return ImmigrationEngine(db_path=str(db_file))


class TestImmigrationEngine:
    def test_apply_visa_success(self, engine):
        res = engine.apply_visa(
            applicant_name="Arthur Dent",
            nationality="UK",
            passport_number="GB12345678",
            passport_expiry="2032-12-31",
            visa_type="EV",
            duration_days=90,
            entries_allowed="MULTIPLE",
            inviting_organization="Travel Co Vietnam",
            port_of_entry="Noi Bai International Airport",
            valid_from="2026-10-01",
            status="GRANTED",
            notes="Electronic visa 90 days multiple entries under Law 23/2023",
        )
        assert res["visa_id"].startswith("VISA-")
        assert res["applicant_name"] == "Arthur Dent"
        assert res["nationality"] == "UK"
        assert res["duration_days"] == 90
        assert res["entries_allowed"] == "MULTIPLE"
        assert res["valid_from"] == "2026-10-01"
        assert res["valid_until"] == "2026-12-30"
        assert res["status"] == "GRANTED"

    def test_apply_visa_passport_expiry_invalid(self, engine):
        # Visa ends in 90 days, but passport expires before visa ends
        with pytest.raises(ValueError, match="Passport expiry .* must exceed visa validity .* by at least 30 days"):
            engine.apply_visa(
                applicant_name="Ford Prefect",
                nationality="Betelgeuse",
                passport_number="BP999888",
                passport_expiry="2026-10-15",
                valid_from="2026-10-01",
                duration_days=90,
            )

    def test_apply_visa_active_restriction_suspension(self, engine):
        # Register active entry suspension order first
        engine.register_restriction(
            subject_name="Tricia McMillan",
            nationality="USA",
            passport_number="US998877",
            restriction_type="ENTRY_SUSPENSION",
            legal_basis="Art 21 k1d Law 47/2014",
            issuing_body="Immigration Department",
        )
        # Apply for visa -> status auto-rejected
        res = engine.apply_visa(
            applicant_name="Tricia McMillan",
            nationality="USA",
            passport_number="US998877",
            passport_expiry="2030-01-01",
            visa_type="DL",
            duration_days=30,
            status="SUBMITTED",
        )
        assert res["status"] == "REJECTED"
        assert "SUSPENSION: Active entry suspension order" in res["notes"]

    def test_apply_visa_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Applicant name cannot be empty"):
            engine.apply_visa(
                applicant_name="",
                nationality="USA",
                passport_number="123",
                passport_expiry="2030-01-01",
            )
        with pytest.raises(ValueError, match="Nationality cannot be empty"):
            engine.apply_visa(
                applicant_name="John",
                nationality="",
                passport_number="123",
                passport_expiry="2030-01-01",
            )
        with pytest.raises(ValueError, match="Passport number cannot be empty"):
            engine.apply_visa(
                applicant_name="John",
                nationality="USA",
                passport_number="",
                passport_expiry="2030-01-01",
            )
        with pytest.raises(ValueError, match="Passport expiry date cannot be empty"):
            engine.apply_visa(
                applicant_name="John",
                nationality="USA",
                passport_number="123",
                passport_expiry="",
            )
        with pytest.raises(ValueError, match="Invalid visa type"):
            engine.apply_visa(
                applicant_name="John",
                nationality="USA",
                passport_number="123",
                passport_expiry="2030-01-01",
                visa_type="INVALID_TYPE",
            )
        with pytest.raises(ValueError, match="Entries allowed must be 'SINGLE' or 'MULTIPLE'"):
            engine.apply_visa(
                applicant_name="John",
                nationality="USA",
                passport_number="123",
                passport_expiry="2030-01-01",
                entries_allowed="TRIPLE",
            )

    def test_issue_residence_card_trc_and_prc(self, engine):
        # TRC
        trc = engine.issue_residence_card(
            holder_name="Zaphod Beeblebrox",
            nationality="Sweden",
            passport_number="SE554433",
            card_type="TRC",
            card_symbol="DT1",
            duration_months=36,
            sponsor_entity="Galaxy Investments LLC",
            residential_address="District 1, Ho Chi Minh City",
            issue_date="2026-10-01",
        )
        assert trc["card_id"].startswith("TRC-")
        assert trc["card_type"] == "TRC"
        assert trc["card_symbol"] == "DT1"
        assert trc["duration_months"] == 36
        assert trc["expiry_date"] > "2029-01-01"

        # PRC
        prc = engine.issue_residence_card(
            holder_name="Marvin Android",
            nationality="Germany",
            passport_number="DE112233",
            card_type="PRC",
            card_symbol="PRC",
            duration_months=120,
            sponsor_entity="Ministry of Science and Technology",
            residential_address="Cau Giay, Hanoi",
            issue_date="2026-10-01",
        )
        assert prc["card_id"].startswith("PRC-")
        assert prc["card_type"] == "PRC"

    def test_issue_residence_card_duration_cap(self, engine):
        # TRC duration capped at 120 months (10 years) under Art 38
        with pytest.raises(ValueError, match="TRC duration cannot exceed 120 months"):
            engine.issue_residence_card(
                holder_name="Slartibartfast",
                nationality="Norway",
                passport_number="NO990011",
                card_type="TRC",
                card_symbol="DT1",
                duration_months=140,
                sponsor_entity="Coastlines Corp",
                residential_address="Ha Long, Quang Ninh",
            )

    def test_issue_residence_card_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Holder name cannot be empty"):
            engine.issue_residence_card(
                holder_name="",
                nationality="France",
                passport_number="123",
                card_type="TRC",
                card_symbol="DT1",
                duration_months=12,
                sponsor_entity="Sponsor",
                residential_address="Hanoi",
            )
        with pytest.raises(ValueError, match="Card symbol .* cannot be empty"):
            engine.issue_residence_card(
                holder_name="Jean",
                nationality="France",
                passport_number="123",
                card_type="TRC",
                card_symbol="",
                duration_months=12,
                sponsor_entity="Sponsor",
                residential_address="Hanoi",
            )
        with pytest.raises(ValueError, match="Duration months must be positive"):
            engine.issue_residence_card(
                holder_name="Jean",
                nationality="France",
                passport_number="123",
                card_type="TRC",
                card_symbol="DT1",
                duration_months=0,
                sponsor_entity="Sponsor",
                residential_address="Hanoi",
            )

    def test_log_border_movement_cleared(self, engine):
        mov = engine.log_border_movement(
            person_name="Gillian Anderson",
            nationality="USA",
            passport_number="US887766",
            direction="ENTRY",
            border_gate="Tan Son Nhat International Airport",
            gate_type="INTERNATIONAL_AIRPORT",
            transport_code="VN30",
            autogate_used=True,
            notes="Tourist entry",
        )
        assert mov["movement_id"].startswith("MOV-")
        assert mov["direction"] == "ENTRY"
        assert mov["border_gate"] == "Tan Son Nhat International Airport"
        assert mov["autogate_used"] == 1
        assert mov["clearance_status"] == "CLEARED"

    def test_log_border_movement_intercepted(self, engine):
        # Register EXIT_POSTPONEMENT order
        engine.register_restriction(
            subject_name="David Duchovny",
            nationality="USA",
            passport_number="US665544",
            restriction_type="EXIT_POSTPONEMENT",
            legal_basis="Art 28 k1a Law 47/2014",
            issuing_body="HCMC People's Court",
        )
        # Attempt EXIT
        mov = engine.log_border_movement(
            person_name="David Duchovny",
            nationality="USA",
            passport_number="US665544",
            direction="EXIT",
            border_gate="Noi Bai International Airport",
        )
        assert mov["clearance_status"] == "INTERCEPTED"
        assert "BLOCKED: EXIT_POSTPONEMENT order" in mov["notes"]

    def test_log_border_movement_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Person name cannot be empty"):
            engine.log_border_movement(
                person_name="",
                nationality="USA",
                passport_number="123",
                direction="ENTRY",
                border_gate="Noi Bai",
            )
        with pytest.raises(ValueError, match="Invalid direction"):
            engine.log_border_movement(
                person_name="Mulder",
                nationality="USA",
                passport_number="123",
                direction="INVALID_DIR",
                border_gate="Noi Bai",
            )
        with pytest.raises(ValueError, match="Invalid gate type"):
            engine.log_border_movement(
                person_name="Mulder",
                nationality="USA",
                passport_number="123",
                direction="ENTRY",
                border_gate="Noi Bai",
                gate_type="SPACE_PORT",
            )

    def test_register_restriction_success(self, engine):
        res = engine.register_restriction(
            subject_name="Walter Skinner",
            nationality="USA",
            passport_number="US112244",
            restriction_type="ENTRY_SUSPENSION",
            legal_basis="Art 21 Law 47/2014",
            issuing_body="Ministry of Public Security",
            effective_from="2026-10-01",
            effective_until="2029-10-01",
            status="ACTIVE",
        )
        assert res["order_id"].startswith("ORD-")
        assert res["restriction_type"] == "ENTRY_SUSPENSION"
        assert res["legal_basis"] == "Art 21 Law 47/2014"
        assert res["status"] == "ACTIVE"

    def test_register_restriction_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Subject name cannot be empty"):
            engine.register_restriction(
                subject_name="",
                nationality="USA",
                passport_number="123",
                restriction_type="ENTRY_SUSPENSION",
                legal_basis="Art 21",
                issuing_body="MPS",
            )
        with pytest.raises(ValueError, match="Legal basis .* cannot be empty"):
            engine.register_restriction(
                subject_name="Agent Doggett",
                nationality="USA",
                passport_number="123",
                restriction_type="ENTRY_SUSPENSION",
                legal_basis="",
                issuing_body="MPS",
            )
        with pytest.raises(ValueError, match="Invalid restriction type"):
            engine.register_restriction(
                subject_name="Agent Doggett",
                nationality="USA",
                passport_number="123",
                restriction_type="INVALID_TYPE",
                legal_basis="Art 21",
                issuing_body="MPS",
            )

    def test_issue_citizen_passport_success(self, engine):
        pass_res = engine.issue_citizen_passport(
            citizen_name="Nguyễn Văn An",
            citizen_id="001095123456",
            birth_date="1995-08-20",
            passport_type="ELECTRONIC_CHIP",
            passport_number="P0123456",
            has_electronic_chip=True,
            autogate_enrolled=True,
            issue_date="2026-10-01",
        )
        assert pass_res["passport_id"].startswith("PASS-")
        assert pass_res["citizen_name"] == "Nguyễn Văn An"
        assert pass_res["passport_number"] == "P0123456"
        assert pass_res["has_electronic_chip"] == 1
        assert pass_res["autogate_enrolled"] == 1
        assert pass_res["expiry_date"] == "2036-10-01"

    def test_issue_citizen_passport_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Citizen name cannot be empty"):
            engine.issue_citizen_passport(
                citizen_name="",
                citizen_id="001095123456",
                birth_date="1995-08-20",
            )
        with pytest.raises(ValueError, match="Citizen ID .* cannot be empty"):
            engine.issue_citizen_passport(
                citizen_name="Nguyen Van A",
                citizen_id="",
                birth_date="1995-08-20",
            )
        with pytest.raises(ValueError, match="Birth date cannot be empty"):
            engine.issue_citizen_passport(
                citizen_name="Nguyen Van A",
                citizen_id="001095123456",
                birth_date="",
            )
        with pytest.raises(ValueError, match="Invalid passport type"):
            engine.issue_citizen_passport(
                citizen_name="Nguyen Van A",
                citizen_id="001095123456",
                birth_date="1995-08-20",
                passport_type="INVALID_PASS_TYPE",
            )

    def test_get_record_and_list_records(self, engine):
        visa = engine.apply_visa(
            applicant_name="Dana Scully",
            nationality="USA",
            passport_number="US556677",
            passport_expiry="2032-01-01",
            visa_type="EV",
        )
        rec = engine.get_record("visa", visa["visa_id"])
        assert rec["visa_id"] == visa["visa_id"]

        with pytest.raises(ValueError, match="Unknown category"):
            engine.get_record("unknown_cat", "123")

        with pytest.raises(KeyError, match="Record 'NONEXISTENT' not found"):
            engine.get_record("visa", "NONEXISTENT")

        records = engine.list_records("visa")
        assert len(records) >= 1

        audits = engine.list_records("audit")
        assert len(audits) >= 1

        with pytest.raises(ValueError, match="Unknown category"):
            engine.list_records("unknown_cat")

    def test_get_telemetry_status(self, engine):
        engine.apply_visa(
            applicant_name="Traveler 1",
            nationality="Canada",
            passport_number="CA112233",
            passport_expiry="2030-01-01",
            status="GRANTED",
        )
        engine.issue_residence_card(
            holder_name="Investor 1",
            nationality="Japan",
            passport_number="JP998877",
            card_type="TRC",
            card_symbol="DT1",
            duration_months=36,
            sponsor_entity="Tokyo Corp",
            residential_address="Hanoi",
        )
        engine.log_border_movement(
            person_name="Citizen 1",
            nationality="Vietnam",
            passport_number="VN123456",
            direction="ENTRY",
            border_gate="Noi Bai",
            autogate_used=True,
        )
        engine.register_restriction(
            subject_name="Suspect 1",
            nationality="State X",
            passport_number="SX9999",
            restriction_type="ENTRY_SUSPENSION",
            legal_basis="Art 21",
            issuing_body="BCA",
        )
        engine.issue_citizen_passport(
            citizen_name="Citizen 2",
            citizen_id="001099112233",
            birth_date="1990-01-01",
            has_electronic_chip=True,
            autogate_enrolled=True,
        )
        status = engine.get_telemetry_status()
        assert status["total_visa_applications"] >= 1
        assert status["active_granted_visas"] >= 1
        assert status["active_residence_cards"] >= 1
        assert status["active_trc_cards"] >= 1
        assert status["total_border_movements"] >= 1
        assert status["autogate_movements"] >= 1
        assert status["active_restriction_orders"] >= 1
        assert status["active_citizen_passports"] >= 1
        assert status["electronic_chip_passports"] >= 1
        assert status["system_status"] == "ONLINE_HEALTHY"


class TestImmigrationCLI:
    @pytest.fixture(autouse=True)
    def setup_app(self, tmp_path, monkeypatch):
        db_file = tmp_path / "cli_immigration.db"
        monkeypatch.setenv("MEKONG_IMMIGRATION_DB", str(db_file))
        self.app = build_app()

    def test_cli_help(self):
        result = runner.invoke(self.app, ["immigration", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Immigration" in result.output
        assert "visa" in result.output
        assert "residence" in result.output
        assert "border" in result.output
        assert "restriction" in result.output
        assert "passport" in result.output

        # Alias check
        result_alias = runner.invoke(self.app, ["entryexit", "--help"])
        assert result_alias.exit_code == 0
        assert "visa" in result_alias.output

    def test_cli_dashboard_and_json(self):
        # Visual dashboard
        res_dash = runner.invoke(self.app, ["immigration"])
        assert res_dash.exit_code == 0
        assert "QUẢN LÝ XUẤT NHẬP CẢNH & CƯ TRÚ" in res_dash.output

        # JSON dashboard
        res_json = runner.invoke(self.app, ["immigration", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_visa_applications" in data
        assert data["system_status"] == "ONLINE_HEALTHY"

        # status subcommand
        res_status = runner.invoke(self.app, ["immigration", "status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.output)
        assert "Law No. 47/2014/QH13" in data_status["statutory_framework"]

    def test_cli_visa(self):
        res = runner.invoke(self.app, [
            "immigration", "visa",
            "--applicant", "Alexandre Yersin",
            "--nationality", "Switzerland",
            "--passport-number", "CH998877",
            "--passport-expiry", "2035-05-15",
            "--visa-type", "EV",
            "--duration-days", "90",
            "--entries", "MULTIPLE",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["visa_id"].startswith("VISA-")
        assert data["applicant_name"] == "Alexandre Yersin"
        assert data["duration_days"] == 90
        assert data["entries_allowed"] == "MULTIPLE"

        # Visual mode
        res_v = runner.invoke(self.app, [
            "immigration", "visa",
            "--applicant", "Louis Pasteur",
            "--nationality", "France",
            "--passport-number", "FR123456",
            "--passport-expiry", "2032-11-20",
            "--visa-type", "DL",
            "--duration-days", "30",
        ])
        assert res_v.exit_code == 0
        assert "Visa Application Processed" in res_v.output

    def test_cli_residence(self):
        res = runner.invoke(self.app, [
            "immigration", "residence",
            "--holder", "Tim Cook",
            "--nationality", "USA",
            "--passport-number", "US001122",
            "--card-type", "TRC",
            "--symbol", "DT1",
            "--duration-months", "36",
            "--sponsor", "Apple Vietnam",
            "--address", "District 1, HCMC",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["card_id"].startswith("TRC-")
        assert data["holder_name"] == "Tim Cook"
        assert data["card_symbol"] == "DT1"

    def test_cli_border(self):
        res = runner.invoke(self.app, [
            "immigration", "border",
            "--person", "Sundar Pichai",
            "--nationality", "USA",
            "--passport-number", "US776611",
            "--direction", "ENTRY",
            "--gate", "Noi Bai International Airport",
            "--autogate",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["movement_id"].startswith("MOV-")
        assert data["clearance_status"] == "CLEARED"
        assert data["autogate_used"] == 1

    def test_cli_restriction(self):
        res = runner.invoke(self.app, [
            "immigration", "restriction",
            "--subject", "Criminal Suspect A",
            "--nationality", "Foreign",
            "--passport-number", "X998811",
            "--type", "EXIT_POSTPONEMENT",
            "--basis", "Tax debt Art 28 Law 47/2014",
            "--authority", "Da Nang Tax Office",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["order_id"].startswith("ORD-")
        assert data["restriction_type"] == "EXIT_POSTPONEMENT"

    def test_cli_passport(self):
        res = runner.invoke(self.app, [
            "immigration", "passport",
            "--name", "Phan Bội Châu",
            "--citizen-id", "001090998877",
            "--birth-date", "1990-12-26",
            "--type", "ELECTRONIC_CHIP",
            "--chip",
            "--autogate",
            "--json"
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["passport_id"].startswith("PASS-")
        assert data["citizen_name"] == "Phan Bội Châu"
        assert data["has_electronic_chip"] == 1
        assert data["autogate_enrolled"] == 1

    def test_cli_list(self):
        # Register a visa first
        runner.invoke(self.app, [
            "immigration", "visa",
            "--applicant", "Marie Curie",
            "--nationality", "France",
            "--passport-number", "FR998800",
            "--passport-expiry", "2035-01-01",
        ])

        # List records JSON
        res_json = runner.invoke(self.app, [
            "immigration", "list",
            "--category", "visa",
            "--json"
        ])
        assert res_json.exit_code == 0
        items = json.loads(res_json.output)
        assert isinstance(items, list)
        assert len(items) >= 1

        # List records Visual
        res_v = runner.invoke(self.app, [
            "immigration", "list",
            "--category", "visa",
        ])
        assert res_v.exit_code == 0
        assert "Immigration Records" in res_v.output

        # Invalid category
        res_err = runner.invoke(self.app, [
            "immigration", "list",
            "--category", "invalid_category",
        ])
        assert res_err.exit_code == 1


class TestImmigrationMCP:
    @pytest.fixture(autouse=True)
    def setup_mcp_db(self, tmp_path, monkeypatch):
        db_file = tmp_path / "mcp_immigration.db"
        monkeypatch.setenv("MEKONG_IMMIGRATION_DB", str(db_file))
        self.server = MekongMcpServer()

    def test_core_mcp_server_handlers(self):
        # 1. Visa
        v_raw = self.server._handle_immigration_visa(
            applicant_name="Nikola Tesla",
            nationality="USA",
            passport_number="US119933",
            passport_expiry="2034-07-10",
            visa_type="DN1",
            duration_days=90,
        )
        v_data = json.loads(v_raw)
        assert v_data["visa_id"].startswith("VISA-")
        assert v_data["visa_type"] == "DN1"

        # 2. Residence
        res_raw = self.server._handle_immigration_residence(
            holder_name="Albert Einstein",
            nationality="Switzerland",
            passport_number="CH556677",
            card_type="TRC",
            card_symbol="DT1",
            duration_months=36,
            sponsor_entity="Physics Institute",
            residential_address="Hanoi",
        )
        res_data = json.loads(res_raw)
        assert res_data["card_id"].startswith("TRC-")

        # 3. Border
        b_raw = self.server._handle_immigration_border(
            person_name="Richard Feynman",
            nationality="USA",
            passport_number="US443322",
            direction="ENTRY",
            border_gate="Da Nang International Airport",
            autogate_used=True,
        )
        b_data = json.loads(b_raw)
        assert b_data["movement_id"].startswith("MOV-")

        # 4. Restriction
        rest_raw = self.server._handle_immigration_restriction(
            subject_name="Restricted Person",
            nationality="Country Z",
            passport_number="Z001",
            restriction_type="ENTRY_SUSPENSION",
            legal_basis="Art 21",
            issuing_body="MPS",
        )
        rest_data = json.loads(rest_raw)
        assert rest_data["order_id"].startswith("ORD-")

        # 5. Passport
        pass_raw = self.server._handle_immigration_passport(
            citizen_name="Lê Quý Đôn",
            citizen_id="001090778899",
            birth_date="1992-03-15",
            passport_type="ELECTRONIC_CHIP",
        )
        pass_data = json.loads(pass_raw)
        assert pass_data["passport_id"].startswith("PASS-")

        # 6. List
        list_raw = self.server._handle_immigration_list(category="visa", limit=10)
        list_data = json.loads(list_raw)
        assert isinstance(list_data, list)
        assert len(list_data) >= 1

        # 7. Status
        status_raw = self.server._handle_immigration_status()
        status_data = json.loads(status_raw)
        assert status_data["total_visa_applications"] >= 1
        assert status_data["system_status"] == "ONLINE_HEALTHY"

        # Aliases test
        status_alias_raw = self.server._handle_mekong_immigration_status()
        assert json.loads(status_alias_raw)["total_visa_applications"] >= 1

    def test_scripts_mcp_server_handlers_and_spec(self):
        # 1. Status
        status_raw = script_mcp.CORE_HANDLERS["mekong_immigration_status"]({})
        status_data = json.loads(status_raw)
        assert "total_visa_applications" in status_data

        # Alias in CORE_HANDLERS
        status_alias_raw = script_mcp.CORE_HANDLERS["immigration_status"]({})
        assert "total_visa_applications" in json.loads(status_alias_raw)

        # 2. Visa
        v_raw = script_mcp.CORE_HANDLERS["mekong_immigration_visa"]({
            "applicant_name": "Galileo Galilei",
            "nationality": "Italy",
            "passport_number": "IT123456",
            "passport_expiry": "2035-02-15",
            "visa_type": "EV",
            "duration_days": 90,
        })
        v_data = json.loads(v_raw)
        assert v_data["visa_id"].startswith("VISA-")

        # 3. Residence
        res_raw = script_mcp.CORE_HANDLERS["mekong_immigration_residence"]({
            "holder_name": "Isaac Newton",
            "nationality": "UK",
            "passport_number": "GB998877",
            "card_type": "TRC",
            "card_symbol": "DT1",
            "duration_months": 24,
            "sponsor_entity": "Cambridge Vietnam",
            "residential_address": "District 3, HCMC",
        })
        assert json.loads(res_raw)["card_id"].startswith("TRC-")

        # 4. Border
        b_raw = script_mcp.CORE_HANDLERS["mekong_immigration_border"]({
            "person_name": "Johannes Kepler",
            "nationality": "Germany",
            "passport_number": "DE998877",
            "direction": "ENTRY",
            "border_gate": "Noi Bai International Airport",
        })
        assert json.loads(b_raw)["movement_id"].startswith("MOV-")

        # 5. Restriction
        rest_raw = script_mcp.CORE_HANDLERS["mekong_immigration_restriction"]({
            "subject_name": "Prohibited Entry X",
            "nationality": "State Y",
            "passport_number": "SY9900",
            "restriction_type": "ENTRY_SUSPENSION",
            "legal_basis": "Art 21 Law 47/2014",
            "issuing_body": "MPS",
        })
        assert json.loads(rest_raw)["order_id"].startswith("ORD-")

        # 6. Passport
        pass_raw = script_mcp.CORE_HANDLERS["mekong_immigration_passport"]({
            "citizen_name": "Trần Hưng Đạo",
            "citizen_id": "001090112233",
            "birth_date": "1991-01-01",
        })
        assert json.loads(pass_raw)["passport_id"].startswith("PASS-")

        # 7. List
        list_raw = script_mcp.CORE_HANDLERS["mekong_immigration_list"]({"category": "passport"})
        assert len(json.loads(list_raw)) >= 1

        # Direct function calls
        res_direct = json.loads(script_mcp.handle_immigration_status({}))
        assert res_direct["system_status"] == "ONLINE_HEALTHY"

        # Check tool specs exist in CORE_TOOLS_SPEC
        tool_names = [t["name"] for t in script_mcp.CORE_TOOLS_SPEC]
        assert "mekong_immigration_visa" in tool_names
        assert "mekong_immigration_residence" in tool_names
        assert "mekong_immigration_border" in tool_names
        assert "mekong_immigration_restriction" in tool_names
        assert "mekong_immigration_passport" in tool_names
        assert "mekong_immigration_list" in tool_names
        assert "mekong_immigration_status" in tool_names
