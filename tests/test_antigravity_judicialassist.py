"""
Unit & Integration Tests for Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Suite.
Compliant with:
- Law on Mutual Legal Assistance 2007 (Luật Tương trợ tư pháp - Law No. 08/2007/QH12)
- Criminal Procedure Code 2015 (Part Eight: International Cooperation)
- Civil Procedure Code 2015 (Part Eight: Foreign-Element Procedures)
- tests/test_core_boundary.py (Strict zero vendor-sdk / AST boundary compliance)
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.judicialassist_engine import (
    JudicialAssistEngine,
    CivilRequestType,
    CriminalRequestType,
    ExtraditionGround,
    RefusalGround,
    RequestDirection,
    CooperationBasis,
    WorkflowStatus,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as script_mcp

runner = CliRunner()


@pytest.fixture
def engine(tmp_path):
    db_file = tmp_path / "test_judicialassist.db"
    return JudicialAssistEngine(db_path=str(db_file))


class TestJudicialAssistEngine:
    def test_civil_request_valid(self, engine):
        res = engine.create_civil_request(
            case_code="12/2026/TLST-DS",
            direction="OUTGOING",
            request_type="SERVICE_OF_DOCUMENTS",
            requesting_body="TAND TP Hà Nội",
            foreign_country="France",
            target_person_org="Jean Dupont",
            service_address="15 Rue de Rivoli, Paris",
            cooperation_basis="BILATERAL_TREATY",
            costs_usd=450.0,
            status="SUBMITTED",
            notes="Service of summons and petition",
        )
        assert res["request_id"].startswith("CIVIL-")
        assert res["case_code"] == "12/2026/TLST-DS"
        assert res["foreign_country"] == "France"
        assert res["costs_usd"] == 450.0
        assert res["status"] == "SUBMITTED"

    def test_civil_request_missing_fields(self, engine):
        with pytest.raises(ValueError, match="Case code cannot be empty"):
            engine.create_civil_request(
                case_code="",
                direction="OUTGOING",
                request_type="SERVICE_OF_DOCUMENTS",
                requesting_body="TAND TP Hà Nội",
                foreign_country="France",
                target_person_org="Jean Dupont",
                service_address="Paris",
            )

        with pytest.raises(ValueError, match="Invalid direction"):
            engine.create_civil_request(
                case_code="12/2026/TLST-DS",
                direction="INVALID_DIR",
                request_type="SERVICE_OF_DOCUMENTS",
                requesting_body="TAND TP Hà Nội",
                foreign_country="France",
                target_person_org="Jean Dupont",
                service_address="Paris",
            )

        with pytest.raises(ValueError, match="Invalid civil request type"):
            engine.create_civil_request(
                case_code="12/2026/TLST-DS",
                direction="OUTGOING",
                request_type="INVALID_TYPE",
                requesting_body="TAND TP Hà Nội",
                foreign_country="France",
                target_person_org="Jean Dupont",
                service_address="Paris",
            )

    def test_civil_request_conflict_update(self, engine):
        res1 = engine.create_civil_request(
            case_code="12/2026/TLST-DS",
            direction="OUTGOING",
            request_type="SERVICE_OF_DOCUMENTS",
            requesting_body="TAND TP Hà Nội",
            foreign_country="France",
            target_person_org="Jean Dupont",
            service_address="Paris",
            request_id="CIVIL-FIXED-01",
        )
        assert res1["request_id"] == "CIVIL-FIXED-01"

        res2 = engine.create_civil_request(
            case_code="12/2026/TLST-DS",
            direction="OUTGOING",
            request_type="SERVICE_OF_DOCUMENTS",
            requesting_body="TAND TP Hà Nội",
            foreign_country="France",
            target_person_org="Jean Dupont",
            service_address="Paris, France",
            status="COMPLETED",
            request_id="CIVIL-FIXED-01",
        )
        assert res2["service_address"] == "Paris, France"
        assert res2["status"] == "COMPLETED"

    def test_criminal_request_valid(self, engine):
        res = engine.create_criminal_request(
            case_code="08/2026/HSST",
            direction="OUTGOING",
            request_type="TESTIMONY_EXTRACTION",
            requesting_agency="Cơ quan CSĐT Bộ Công an",
            foreign_country="Singapore",
            alleged_offense="Fraudulent appropriation of assets via transnational telecommunications",
            dual_criminality=True,
            cooperation_basis="BILATERAL_TREATY",
            asset_value_vnd=5000000000.0,
            status="SUBMITTED",
        )
        assert res["request_id"].startswith("CRIM-")
        assert res["foreign_country"] == "Singapore"
        assert res["dual_criminality"] == 1
        assert res["asset_value_vnd"] == 5000000000.0
        assert res["status"] == "SUBMITTED"

    def test_criminal_request_coercive_requires_dual_criminality(self, engine):
        # Under Art 20, coercive search/freeze without dual criminality triggers statutory refusal
        res = engine.create_criminal_request(
            case_code="09/2026/HSST",
            direction="INCOMING",
            request_type="SEARCH_AND_SEIZURE",
            requesting_agency="Foreign Police Agency",
            foreign_country="Germany",
            alleged_offense="Tax offense not recognized in Vietnam",
            dual_criminality=False,
            status="SUBMITTED",
        )
        assert res["status"] == "REFUSED"
        assert "STATUTORY_REFUSAL" in res["notes"]

    def test_criminal_request_conflict_update(self, engine):
        res1 = engine.create_criminal_request(
            case_code="10/2026/HSST",
            direction="OUTGOING",
            request_type="CRIMINAL_RECORD_CHECK",
            requesting_agency="VKSND Tối cao",
            foreign_country="Japan",
            alleged_offense="Theft",
            request_id="CRIM-FIXED-01",
        )
        assert res1["request_id"] == "CRIM-FIXED-01"

        res2 = engine.create_criminal_request(
            case_code="10/2026/HSST",
            direction="OUTGOING",
            request_type="CRIMINAL_RECORD_CHECK",
            requesting_agency="VKSND Tối cao",
            foreign_country="Japan",
            alleged_offense="Theft and Embezzlement",
            status="COMPLETED",
            request_id="CRIM-FIXED-01",
        )
        assert res2["alleged_offense"] == "Theft and Embezzlement"
        assert res2["status"] == "COMPLETED"

    def test_extradition_valid(self, engine):
        res = engine.evaluate_extradition(
            subject_name="Alex Smith",
            nationality="Australia",
            direction="INCOMING",
            requesting_country="Australia",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Aggravated Armed Robbery",
            penalty_framework_months=60,
            dual_criminality=True,
            provisional_arrest=True,
            arrest_date="2026-09-01",
        )
        assert res["dossier_id"].startswith("EXTRA-")
        assert res["refusal_ground"] == "NONE"
        assert res["provisional_arrest"] == 1
        assert res["status"] == "SUBMITTED"

    def test_extradition_penalty_thresholds(self, engine):
        # Under Art 33 k1, prosecution requires >= 12 months
        with pytest.raises(ValueError, match="at least 12 months"):
            engine.evaluate_extradition(
                subject_name="John Doe",
                nationality="USA",
                direction="INCOMING",
                requesting_country="USA",
                extradition_ground="PROSECUTION_INVESTIGATION",
                offense_name="Minor Trespassing",
                penalty_framework_months=6,
            )

        # Under Art 33 k2, sentence execution requires remaining >= 6 months
        with pytest.raises(ValueError, match="at least 6 months"):
            engine.evaluate_extradition(
                subject_name="John Doe",
                nationality="USA",
                direction="INCOMING",
                requesting_country="USA",
                extradition_ground="SENTENCE_EXECUTION",
                offense_name="Theft",
                penalty_framework_months=24,
                remaining_sentence_months=3,
            )

    def test_extradition_vietnamese_citizen_mandatory_refusal(self, engine):
        # Art 35 k1a: Mandatory refusal to extradite Vietnamese citizens
        res = engine.evaluate_extradition(
            subject_name="Nguyen Van A",
            nationality="Vietnam",
            direction="INCOMING",
            requesting_country="South Korea",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Financial Fraud",
            penalty_framework_months=36,
            is_vietnamese_citizen=True,
        )
        assert res["refusal_ground"] == "VIETNAMESE_CITIZEN"
        assert res["status"] == "REFUSED"
        assert "MANDATORY_REFUSAL: Art 35 k1a" in res["notes"]

    def test_extradition_statute_of_limitations_refusal(self, engine):
        # Art 35 k1b: Statute of limitations expired
        res = engine.evaluate_extradition(
            subject_name="Robert Taylor",
            nationality="Canada",
            direction="INCOMING",
            requesting_country="Canada",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Embezzlement from 1995",
            penalty_framework_months=36,
            statute_of_limitations_expired=True,
        )
        assert res["refusal_ground"] == "STATUTE_OF_LIMITATIONS_EXPIRED"
        assert res["status"] == "REFUSED"

    def test_extradition_ne_bis_in_idem_refusal(self, engine):
        # Art 35 k1c: Final judgment rendered
        res = engine.evaluate_extradition(
            subject_name="Michael Brown",
            nationality="UK",
            direction="INCOMING",
            requesting_country="UK",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Smuggling",
            penalty_framework_months=48,
            ne_bis_in_idem=True,
        )
        assert res["refusal_ground"] == "NE_BIS_IN_IDEM"
        assert res["status"] == "REFUSED"

    def test_extradition_torture_persecution_refusal(self, engine):
        # Art 35 k1d: Risk of torture or persecution
        res = engine.evaluate_extradition(
            subject_name="Carlos Gomez",
            nationality="State X",
            direction="INCOMING",
            requesting_country="State X",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Public Dissent",
            penalty_framework_months=36,
            torture_persecution_risk=True,
        )
        assert res["refusal_ground"] == "TORTURE_PERSECUTION_RISK"
        assert res["status"] == "REFUSED"

    def test_extradition_political_military_refusal(self, engine):
        # Art 35 k1đ: Political or pure military offense
        res = engine.evaluate_extradition(
            subject_name="David Lee",
            nationality="State Y",
            direction="INCOMING",
            requesting_country="State Y",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Desertion during peacetime",
            penalty_framework_months=24,
            political_military_offense=True,
        )
        assert res["refusal_ground"] == "POLITICAL_MILITARY_OFFENSE"
        assert res["status"] == "REFUSED"

    def test_extradition_death_penalty_discretionary_refusal(self, engine):
        # Art 35 k2a: Death penalty without assurance
        res = engine.evaluate_extradition(
            subject_name="Frank Miller",
            nationality="State Z",
            direction="INCOMING",
            requesting_country="State Z",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Aggravated Murder",
            penalty_framework_months=120,
            death_penalty_without_assurance=True,
        )
        assert res["refusal_ground"] == "DEATH_PENALTY_NO_ASSURANCE"
        assert res["status"] == "REFUSED"

    def test_sentence_transfer_valid(self, engine):
        res = engine.process_sentence_transfer(
            prisoner_name="Hans Gruber",
            prisoner_nationality="Germany",
            direction="OUTGOING",
            from_country="Vietnam",
            to_country="Germany",
            original_sentence_months=60,
            served_sentence_months=24,
            remaining_sentence_months=36,
            prisoner_written_consent=True,
            dual_criminality=True,
            civil_compensation_cleared=True,
            court_decision="QD-05/2026/QD-CA-TRANSFER",
        )
        assert res["transfer_id"].startswith("TRANS-")
        assert res["prisoner_name"] == "Hans Gruber"
        assert res["remaining_sentence_months"] == 36
        assert res["status"] == "SUBMITTED"

    def test_sentence_transfer_statutory_refusals(self, engine):
        # Remaining sentence < 12 months (Art 50 k1c)
        res1 = engine.process_sentence_transfer(
            prisoner_name="Mark Smith",
            prisoner_nationality="UK",
            direction="OUTGOING",
            from_country="Vietnam",
            to_country="UK",
            original_sentence_months=36,
            served_sentence_months=30,
            remaining_sentence_months=6,
        )
        assert res1["status"] == "REFUSED"
        assert "less than 12 months" in res1["notes"]

        # No written consent (Art 50 k1b)
        res2 = engine.process_sentence_transfer(
            prisoner_name="Paul White",
            prisoner_nationality="UK",
            direction="OUTGOING",
            from_country="Vietnam",
            to_country="UK",
            original_sentence_months=48,
            served_sentence_months=12,
            remaining_sentence_months=36,
            prisoner_written_consent=False,
        )
        assert res2["status"] == "REFUSED"
        assert "Voluntary written consent" in res2["notes"]

        # Outstanding civil compensation (Art 51 k1c)
        res3 = engine.process_sentence_transfer(
            prisoner_name="George Green",
            prisoner_nationality="USA",
            direction="OUTGOING",
            from_country="Vietnam",
            to_country="USA",
            original_sentence_months=48,
            served_sentence_months=12,
            remaining_sentence_months=36,
            civil_compensation_cleared=False,
        )
        assert res3["status"] == "REFUSED"
        assert "Outstanding civil obligations" in res3["notes"]

    def test_treaty_registration_and_update(self, engine):
        res1 = engine.register_bilateral_treaty(
            country_name="Poland",
            treaty_title="Treaty on Mutual Legal Assistance in Civil and Criminal Matters",
            signing_date="2003-03-22",
            effective_date="2005-01-19",
            covered_domains=["CIVIL", "CRIMINAL", "EXTRADITION"],
            is_active=True,
            treaty_id="TREATY-POL-01",
        )
        assert res1["treaty_id"] == "TREATY-POL-01"
        assert res1["country_name"] == "Poland"
        assert "CIVIL" in res1["covered_domains"]

        res2 = engine.register_bilateral_treaty(
            country_name="Poland",
            treaty_title="Treaty on Mutual Legal Assistance in Civil and Criminal Matters (Amended)",
            signing_date="2003-03-22",
            effective_date="2005-01-19",
            covered_domains=["CIVIL", "CRIMINAL", "EXTRADITION", "SENTENCE_TRANSFER"],
            is_active=True,
            treaty_id="TREATY-POL-01",
        )
        assert "SENTENCE_TRANSFER" in res2["covered_domains"]

    def test_list_records_all_categories(self, engine):
        engine.create_civil_request(
            case_code="01/2026/TLST",
            direction="OUTGOING",
            request_type="SERVICE_OF_DOCUMENTS",
            requesting_body="Court A",
            foreign_country="Laos",
            target_person_org="Person A",
            service_address="Vientiane",
        )
        engine.create_criminal_request(
            case_code="01/2026/HS",
            direction="OUTGOING",
            request_type="TESTIMONY_EXTRACTION",
            requesting_agency="Police B",
            foreign_country="Cambodia",
            alleged_offense="Smuggling",
        )
        engine.evaluate_extradition(
            subject_name="Target C",
            nationality="Cambodia",
            direction="INCOMING",
            requesting_country="Cambodia",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="Theft",
            penalty_framework_months=36,
        )
        engine.process_sentence_transfer(
            prisoner_name="Prisoner D",
            prisoner_nationality="Laos",
            direction="OUTGOING",
            from_country="Vietnam",
            to_country="Laos",
            original_sentence_months=48,
            served_sentence_months=12,
            remaining_sentence_months=36,
        )
        engine.register_bilateral_treaty(
            country_name="Laos",
            treaty_title="Mutual Legal Assistance Treaty",
            signing_date="2010-05-15",
            effective_date="2011-01-01",
            covered_domains=["CIVIL", "CRIMINAL"],
        )

        assert len(engine.list_records("civil")) >= 1
        assert len(engine.list_records("criminal")) >= 1
        assert len(engine.list_records("extradition")) >= 1
        assert len(engine.list_records("transfer")) >= 1
        assert len(engine.list_records("treaty")) >= 1
        assert len(engine.list_records("audit")) >= 5

        with pytest.raises(ValueError, match="Unknown category"):
            engine.list_records("unknown_cat")

    def test_telemetry_status(self, engine):
        status = engine.get_telemetry_status()
        assert status["system_status"] == "ONLINE_HEALTHY"
        assert status["total_civil_requests"] == 0
        assert status["refused_extraditions"] == 0
        assert status["completed_sentence_transfers"] == 0


class TestJudicialAssistCLI:
    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "cli_test_judicialassist.db")
        monkeypatch.setenv("MEKONG_JUDICIALASSIST_DB", db_path)

    def test_cli_help(self):
        app = build_app()
        result = runner.invoke(app, ["judicialassist", "--help"])
        assert result.exit_code == 0
        assert "Luật Tương trợ tư pháp 2007" in result.output

        # Test extradition alias
        res_alias = runner.invoke(app, ["extradition", "--help"])
        assert res_alias.exit_code == 0
        assert "Luật Tương trợ tư pháp 2007" in res_alias.output

    def test_cli_status_dashboard(self):
        app = build_app()
        result = runner.invoke(app, ["judicialassist", "status"])
        assert result.exit_code == 0
        assert "HỆ THỐNG TƯƠNG TRỢ TƯ PHÁP QUỐC TẾ" in result.output
        assert "Civil MLA" in result.output

    def test_cli_status_json(self):
        app = build_app()
        result = runner.invoke(app, ["judicialassist", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["system_status"] == "ONLINE_HEALTHY"
        assert "central_authorities" in data

    def test_cli_civil_success_and_json(self):
        app = build_app()
        result = runner.invoke(app, [
            "judicialassist", "civil",
            "--case-code", "44/2026/TLST-DS",
            "--requesting-body", "TAND TP HCM",
            "--foreign-country", "Japan",
            "--target", "Tanaka Ken",
            "--address", "Tokyo, Japan",
            "--costs-usd", "300",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["request_id"].startswith("CIVIL-")
        assert data["target_person_org"] == "Tanaka Ken"

    def test_cli_civil_validation_error(self):
        app = build_app()
        result = runner.invoke(app, [
            "judicialassist", "civil",
            "--case-code", "44/2026/TLST-DS",
            "--requesting-body", "TAND TP HCM",
            "--foreign-country", "Japan",
            "--target", "Tanaka Ken",
            "--address", "Tokyo, Japan",
            "--direction", "INVALID_DIR",
        ])
        assert result.exit_code != 0
        assert "Error registering civil request" in result.output

    def test_cli_criminal_success_and_json(self):
        app = build_app()
        result = runner.invoke(app, [
            "judicialassist", "criminal",
            "--case-code", "19/2026/HSST",
            "--agency", "VKSND TP Đà Nẵng",
            "--foreign-country", "South Korea",
            "--offense", "Cross-border telecom scam",
            "--asset-vnd", "1000000000",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["request_id"].startswith("CRIM-")
        assert data["asset_value_vnd"] == 1000000000.0

    def test_cli_extradition_success_and_json(self):
        app = build_app()
        result = runner.invoke(app, [
            "judicialassist", "extradition",
            "--subject", "James Wilson",
            "--nationality", "Canada",
            "--country", "Canada",
            "--offense", "Extortion",
            "--penalty-months", "36",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dossier_id"].startswith("EXTRA-")
        assert data["refusal_ground"] == "NONE"

    def test_cli_extradition_mandatory_refusal_flag(self):
        app = build_app()
        result = runner.invoke(app, [
            "judicialassist", "extradition",
            "--subject", "Le Van B",
            "--nationality", "Vietnam",
            "--country", "USA",
            "--offense", "Cybercrime",
            "--penalty-months", "48",
            "--vietnamese-citizen",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["refusal_ground"] == "VIETNAMESE_CITIZEN"
        assert data["status"] == "REFUSED"

    def test_cli_transfer_success_and_json(self):
        app = build_app()
        result = runner.invoke(app, [
            "judicialassist", "transfer",
            "--prisoner", "Jean Valjean",
            "--nationality", "France",
            "--from-country", "Vietnam",
            "--to-country", "France",
            "--original-months", "60",
            "--served-months", "20",
            "--remaining-months", "40",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["transfer_id"].startswith("TRANS-")
        assert data["status"] == "SUBMITTED"

    def test_cli_treaty_success_and_json(self):
        app = build_app()
        result = runner.invoke(app, [
            "judicialassist", "treaty",
            "--country", "Czech Republic",
            "--title", "Agreement on Extradition and Mutual Legal Assistance",
            "--signing-date", "2007-09-12",
            "--effective-date", "2008-05-01",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["treaty_id"].startswith("TREATY-")
        assert data["country_name"] == "Czech Republic"

    def test_cli_list_records(self):
        app = build_app()
        result = runner.invoke(app, ["judicialassist", "list", "--category", "civil", "--json"])
        assert result.exit_code == 0
        records = json.loads(result.output)
        assert isinstance(records, list)


class TestJudicialAssistMCP:
    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path, monkeypatch):
        db_path = str(tmp_path / "mcp_test_judicialassist.db")
        monkeypatch.setenv("MEKONG_JUDICIALASSIST_DB", db_path)

    def test_core_mcp_server_handlers(self):
        server = MekongMcpServer(name="test-server")

        res_civil = json.loads(server._handle_judicialassist_civil(
            case_code="33/2026/TLST",
            direction="OUTGOING",
            request_type="SERVICE_OF_DOCUMENTS",
            requesting_body="Court HCMC",
            foreign_country="Australia",
            target_person_org="Company ABC",
            service_address="Sydney",
        ))
        assert res_civil["request_id"].startswith("CIVIL-")

        res_crim = json.loads(server._handle_judicialassist_criminal(
            case_code="22/2026/HS",
            direction="OUTGOING",
            request_type="TESTIMONY_EXTRACTION",
            requesting_agency="Ministry of Public Security",
            foreign_country="Thailand",
            alleged_offense="Illegal drug trafficking",
        ))
        assert res_crim["request_id"].startswith("CRIM-")

        res_extra = json.loads(server._handle_judicialassist_extradition(
            subject_name="Arthur Dent",
            nationality="UK",
            direction="INCOMING",
            requesting_country="UK",
            extradition_ground="PROSECUTION_INVESTIGATION",
            offense_name="High Fraud",
            penalty_framework_months=36,
        ))
        assert res_extra["dossier_id"].startswith("EXTRA-")

        res_trans = json.loads(server._handle_judicialassist_transfer(
            prisoner_name="Ford Prefect",
            prisoner_nationality="UK",
            direction="OUTGOING",
            from_country="Vietnam",
            to_country="UK",
            original_sentence_months=48,
            served_sentence_months=12,
            remaining_sentence_months=36,
        ))
        assert res_trans["transfer_id"].startswith("TRANS-")

        res_treaty = json.loads(server._handle_judicialassist_treaty(
            country_name="Russia",
            treaty_title="Treaty on Legal Assistance and Legal Relations in Civil and Criminal Matters",
            signing_date="1998-08-25",
            effective_date="1999-09-11",
        ))
        assert res_treaty["treaty_id"].startswith("TREATY-")

        res_list = json.loads(server._handle_judicialassist_list(category="civil"))
        assert len(res_list) >= 1

        res_status = json.loads(server._handle_judicialassist_status())
        assert res_status["system_status"] == "ONLINE_HEALTHY"

    def test_scripts_mcp_server_handlers_and_aliases(self):
        res_civil = json.loads(script_mcp.handle_judicialassist_civil({
            "case_code": "55/2026/TLST",
            "direction": "OUTGOING",
            "request_type": "SERVICE_OF_DOCUMENTS",
            "requesting_body": "Court Hanoi",
            "foreign_country": "Korea",
            "target_person_org": "Park Jin",
            "service_address": "Seoul",
        }))
        assert res_civil["request_id"].startswith("CIVIL-")

        res_crim = json.loads(script_mcp.handle_judicialassist_criminal({
            "case_code": "55/2026/HS",
            "direction": "OUTGOING",
            "request_type": "TESTIMONY_EXTRACTION",
            "requesting_agency": "VKSND",
            "foreign_country": "China",
            "alleged_offense": "Smuggling",
        }))
        assert res_crim["request_id"].startswith("CRIM-")

        res_extra = json.loads(script_mcp.handle_judicialassist_extradition({
            "subject_name": "Wang Wei",
            "nationality": "China",
            "direction": "INCOMING",
            "requesting_country": "China",
            "extradition_ground": "PROSECUTION_INVESTIGATION",
            "offense_name": "Corruption",
            "penalty_framework_months": 72,
        }))
        assert res_extra["dossier_id"].startswith("EXTRA-")

        res_trans = json.loads(script_mcp.handle_judicialassist_transfer({
            "prisoner_name": "Chen Li",
            "prisoner_nationality": "China",
            "direction": "OUTGOING",
            "from_country": "Vietnam",
            "to_country": "China",
            "original_sentence_months": 60,
            "served_sentence_months": 24,
            "remaining_sentence_months": 36,
        }))
        assert res_trans["transfer_id"].startswith("TRANS-")

        res_treaty = json.loads(script_mcp.handle_judicialassist_treaty({
            "country_name": "China",
            "treaty_title": "Treaty on Extradition",
            "signing_date": "2015-04-07",
            "effective_date": "2016-08-01",
        }))
        assert res_treaty["treaty_id"].startswith("TREATY-")

        res_list = json.loads(script_mcp.handle_judicialassist_list({"category": "civil"}))
        assert len(res_list) >= 1

        res_status = json.loads(script_mcp.handle_judicialassist_status({}))
        assert res_status["system_status"] == "ONLINE_HEALTHY"

        # Verify aliases in CORE_HANDLERS
        assert "mekong_judicialassist_civil" in script_mcp.CORE_HANDLERS
        assert "judicialassist_civil" in script_mcp.CORE_HANDLERS
        assert "mekong_judicialassist_extradition" in script_mcp.CORE_HANDLERS
        assert "judicialassist_extradition" in script_mcp.CORE_HANDLERS
        assert "mekong_judicialassist_status" in script_mcp.CORE_HANDLERS
