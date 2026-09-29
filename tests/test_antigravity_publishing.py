"""
Test Suite for Vietnamese Publishing, Printing, Distribution & Legal Depository Suite (Phase 86).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- PublishingEngine domain logic (publisher licensing Art. 22, ISBN-13 checksum prefix 978-604, legal deposit Art. 28, 10-day embargo audit, printing facility licensing).
- CLI commands with Rich tables and headless --json mode.
- Dual MCP server handlers (FastMCP and fallback JSON-RPC 2.0).
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.publishing_engine import PublishingEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestPublishingBoundary:
    """Verifies that publishing_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "publishing_engine.py")
        with open(engine_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=engine_path)

        forbidden_prefixes = ("requests", "httpx", "aiohttp", "boto3", "openai", "anthropic", "google")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(forbidden_prefixes), f"Forbidden from-import: {node.module}"


class TestPublishingEngine:
    """Tests core business logic of PublishingEngine."""

    def test_register_publisher_approved(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.register_publisher(
            publisher_name="Nhà xuất bản Tri Thức Mới",
            director_name="Nguyễn Văn An",
            charter_capital_vnd=6_000_000_000.0,
            office_area_sqm=250.0,
            headquarters_location="Hà Nội",
            has_qualified_editor_in_chief=True,
        )
        assert res["status"] == "LICENSED_APPROVED"
        assert res["license_granted"] is True
        assert res["charter_capital_vnd"] == 6_000_000_000.0
        assert len(res["deficiencies"]) == 0

    def test_register_publisher_deficient_capital_and_area(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.register_publisher(
            publisher_name="Nhà xuất bản Thử Nghiệm",
            director_name="Trần Văn Bình",
            charter_capital_vnd=3_000_000_000.0,  # Below 5B VND min
            office_area_sqm=120.0,  # Below 200 sqm min
            headquarters_location="Đà Nẵng",
            has_qualified_editor_in_chief=False,
        )
        assert res["status"] == "DEFICIENT_CONDITIONS"
        assert res["license_granted"] is False
        assert len(res["deficiencies"]) >= 3

    def test_allocate_isbn(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.allocate_isbn(
            book_title="Kỷ Nguyên Trí Tuệ Nhân Tạo",
            publisher_name="Nhà xuất bản Tri Thức Mới",
            author_name="Lê Minh Tuấn",
            genre="science",
            publication_year=2026,
        )
        assert res["status"] == "ALLOCATED"
        assert res["isbn"].startswith("978-604-")
        # EAN-13 should have length with hyphens or 13 digits stripped
        digits = res["isbn"].replace("-", "")
        assert len(digits) == 13

    def test_record_legal_depository_compliant(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.record_legal_depository(
            publisher_id="PUB-NXBTTM-001",
            isbn="978-604-0-12345-6",
            state_copies=3,
            national_library_copies=2,
            is_digital=False,
        )
        assert res["status"] == "DEPOSITED_COMPLIANT"
        assert res["embargo_period_days"] == 10
        assert res["is_compliant"] is True

    def test_record_legal_depository_deficient_copies(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.record_legal_depository(
            publisher_id="PUB-NXBTTM-001",
            isbn="978-604-0-12345-6",
            state_copies=2,  # < 3
            national_library_copies=1,  # < 2
            is_digital=False,
        )
        assert res["status"] == "DEFICIENT_COPIES_REJECTED"
        assert res["is_compliant"] is False
        assert len(res["deficiencies"]) >= 2

    def test_audit_release_decision_authorized(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        # First deposit
        engine.record_legal_depository(
            publisher_id="PUB-NXBTTM-001",
            isbn="978-604-0-12345-6",
            state_copies=3,
            national_library_copies=2,
        )
        # Audit after 12 days
        res = engine.audit_release_decision(
            publisher_id="PUB-NXBTTM-001",
            isbn="978-604-0-12345-6",
            print_run=5000,
            retail_price_vnd=150_000.0,
            days_since_deposit=12,
        )
        assert res["status"] == "AUTHORIZED_FOR_RELEASE"
        assert res["is_cleared"] is True
        assert res["estimated_fine_vnd"] == 0

    def test_audit_release_decision_under_embargo(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        engine.record_legal_depository(
            publisher_id="PUB-NXBTTM-001",
            isbn="978-604-0-12345-6",
            state_copies=3,
            national_library_copies=2,
        )
        # Premature distribution after 4 days (< 10 days)
        res = engine.audit_release_decision(
            publisher_id="PUB-NXBTTM-001",
            isbn="978-604-0-12345-6",
            print_run=5000,
            retail_price_vnd=150_000.0,
            days_since_deposit=4,
        )
        assert res["status"] == "UNDER_10_DAY_EMBARGO"
        assert res["is_cleared"] is False
        assert res["estimated_fine_vnd"] == 15_000_000.0

    def test_audit_release_decision_no_deposit(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.audit_release_decision(
            publisher_id="PUB-UNKNOWN",
            isbn="978-604-9-99999-9",
            print_run=2000,
            retail_price_vnd=90_000.0,
            days_since_deposit=0,
        )
        assert res["status"] == "ILLEGAL_NO_LEGAL_DEPOSIT"
        assert res["is_cleared"] is False
        assert res["estimated_fine_vnd"] == 20_000_000.0

    def test_review_printing_facility_compliant(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.review_printing_facility(
            facility_name="Xí nghiệp In Quân Đội 1",
            press_types="offset,digital",
            has_security_clearance=True,
            has_certified_print_manager=True,
        )
        assert res["status"] == "COMPLIANT_LICENSED"
        assert res["is_licensed"] is True

    def test_review_printing_facility_non_compliant(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        res = engine.review_printing_facility(
            facility_name="Cơ sở In Tư nhân Lậu",
            press_types="offset",
            has_security_clearance=False,
            has_certified_print_manager=False,
        )
        assert res["status"] == "NON_COMPLIANT_REJECTED"
        assert res["is_licensed"] is False

    def test_list_records_and_dashboard(self, temp_db):
        engine = PublishingEngine(db_path=temp_db)
        engine.register_publisher("NXB Kim Đồng Mới", charter_capital_vnd=8e9, office_area_sqm=300)
        engine.allocate_isbn("Doremon tập 1")
        engine.record_legal_depository("PUB-NXB-01", "978-604-0-00001-1")
        engine.review_printing_facility("Nhà in Ba Đình")

        publishers = engine.list_records("publishers")
        assert len(publishers) >= 1
        isbns = engine.list_records("isbns")
        assert len(isbns) >= 1
        deposits = engine.list_records("deposits")
        assert len(deposits) >= 1

        dash = engine.get_publishing_dashboard()
        assert dash["total_publishers"] >= 1
        assert dash["total_isbns_allocated"] >= 1
        assert dash["total_legal_deposits"] >= 1


class TestPublishingCLI:
    """Tests CLI command execution for mekong publishing."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_help(self, runner, app):
        result = runner.invoke(app, ["publishing", "--help"])
        assert result.exit_code == 0
        assert "publishing" in result.stdout.lower()

    def test_cli_status_json(self, runner, app):
        result = runner.invoke(app, ["publishing", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_publishers" in data

    def test_cli_publisher_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "publishing",
                "publisher",
                "NXB Khoa Học Kỹ Thuật Số",
                "--director",
                "Vũ Hồng Hà",
                "--capital",
                "7000000000",
                "--area",
                "280",
                "--agency",
                "Bộ Khoa học và Công nghệ",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] in ("LICENSED", "LICENSED_APPROVED")

    def test_cli_isbn_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "publishing",
                "isbn",
                "Lập trình AI với Python",
                "--publisher",
                "GP-NXB-2026-MK01",
                "--author",
                "Nguyễn Nam",
                "--category",
                "science",
                "--copies",
                "1500",
                "--price",
                "150000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] in ("APPROVED", "ALLOCATED")
        assert "isbn" in data

    def test_cli_deposit_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "publishing",
                "deposit",
                "978-604-0-12345-6",
                "--copies",
                "3",
                "--library-copies",
                "2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] in ("DEPOSITED", "DEPOSITED_COMPLIANT")
        assert "deposit_code" in data

    def test_cli_release_json(self, runner, app):
        # First create a deposit
        dep_res = runner.invoke(
            app,
            [
                "publishing",
                "deposit",
                "978-604-0-54321-0",
                "--copies",
                "3",
                "--library-copies",
                "2",
                "--date",
                "2026-01-01",
                "--json",
            ],
        )
        dep_data = json.loads(dep_res.stdout)
        dep_code = dep_data["deposit_code"]

        result = runner.invoke(
            app,
            [
                "publishing",
                "release",
                dep_code,
                "--date",
                "2026-01-20",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["can_release"] is True

    def test_cli_printing_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "publishing",
                "printing",
                "Nhà in Thăng Long",
                "--address",
                "Hà Nội",
                "--security",
                "--presses",
                "3",
                "--qualified",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] in ("COMPLIANT", "COMPLIANT_LICENSED")

    def test_cli_list_json(self, runner, app):
        result = runner.invoke(app, ["publishing", "list", "publishers", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestPublishingMCP:
    """Tests dual FastMCP and fallback JSON-RPC handlers."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_raw = server._handle_publishing_license(
            publisher_name="NXB Công Nghệ Mới",
            charter_capital_vnd=6_000_000_000.0,
            office_area_sqm=220.0,
        )
        data = json.loads(res_raw)
        assert data["status"] == "LICENSED_APPROVED"

        res_isbn = server._handle_publishing_isbn(book_title="Blockchain Architecture")
        data_isbn = json.loads(res_isbn)
        assert data_isbn["status"] == "ALLOCATED"

        res_deposit = server._handle_publishing_deposit(
            publisher_id="PUB-MCP-01",
            isbn=data_isbn["isbn"],
            state_copies=3,
            national_library_copies=2,
        )
        data_dep = json.loads(res_deposit)
        assert data_dep["status"] == "DEPOSITED_COMPLIANT"

        res_status = server._handle_publishing_status()
        data_status = json.loads(res_status)
        assert "total_publishers" in data_status

    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_publishing_license,
            handle_publishing_isbn,
            handle_publishing_deposit,
            handle_publishing_release,
            handle_publishing_printing,
            handle_publishing_list,
            handle_publishing_status,
        )

        res_raw = handle_publishing_license({
            "publisher_name": "NXB Khoa Học Scripts",
            "charter_capital_vnd": 5_500_000_000.0,
            "office_area_sqm": 210.0,
        })
        data = json.loads(res_raw)
        assert data["status"] == "LICENSED_APPROVED"

        res_isbn = handle_publishing_isbn({"book_title": "Quantum Computing 101"})
        data_isbn = json.loads(res_isbn)
        assert data_isbn["status"] == "ALLOCATED"

        res_print = handle_publishing_printing({
            "facility_name": "Xưởng In Báo Nhân Dân",
            "has_security_clearance": True,
            "has_certified_print_manager": True,
        })
        data_print = json.loads(res_print)
        assert data_print["status"] == "COMPLIANT_LICENSED"

        res_status = handle_publishing_status({})
        data_status = json.loads(res_status)
        assert "total_publishers" in data_status
