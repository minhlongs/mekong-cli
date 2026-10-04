# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Guardianship, Custodianship & Ward Protection Suite (Phase 148)."""

from __future__ import annotations

import ast
import json
import os
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.guardianship_engine import (
    AssetCategory,
    GuardianRelationship,
    GuardianshipEngine,
    GuardianshipStatus,
    GuardianshipType,
    TerminationGrounds,
    TransactionType,
    WardCategory,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestGuardianshipCoreBoundary:
    """Ensure GuardianshipEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/guardianship_engine.py")
        assert source_path.exists(), "guardianship_engine.py must exist"

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


class TestGuardianshipEngine:
    """Unit tests for GuardianshipEngine under Civil Code 2015 & Law on Civil Status 2014."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> GuardianshipEngine:
        db_path = str(tmp_path / "test_guardianship.db")
        return GuardianshipEngine(db_path=db_path)

    def test_register_guardianship_success(self, engine: GuardianshipEngine) -> None:
        reg = engine.register_guardianship(
            ward_name="Lê Hoàng Nam",
            ward_dob="2012-04-15",
            ward_id_number="079212009988",
            ward_address="12 Hai Bà Trưng, Quận 1, TP.HCM",
            ward_category=WardCategory.MINOR_NO_PARENTS,
            guardian_name="Lê Tuấn Hùng",
            guardian_dob="1998-02-20",
            guardian_id_number="079098001122",
            guardian_address="12 Hai Bà Trưng, Quận 1, TP.HCM",
            guardian_phone="0901234567",
            guardian_relationship=GuardianRelationship.ELDER_SIBLING,
            guardianship_type=GuardianshipType.NATURAL,
            commune_ubnd="UBND Phường Bến Nghé",
            registration_date="2026-03-01",
            registration_id="GH-TEST-001",
        )
        assert reg["registration_id"] == "GH-TEST-001"
        assert reg["ward_name"] == "Lê Hoàng Nam"
        assert reg["guardian_name"] == "Lê Tuấn Hùng"
        assert reg["status"] == "ACTIVE"
        assert "CERT-GH-" in reg["certificate_code"]
        assert reg["ward_category"] == WardCategory.MINOR_NO_PARENTS.value

    def test_underage_guardian_rejected(self, engine: GuardianshipEngine) -> None:
        with pytest.raises(ValueError, match="at least 18 years of age"):
            engine.register_guardianship(
                ward_name="Bé Mai",
                ward_dob="2015-01-01",
                ward_id_number="079215001111",
                ward_address="Quận 1",
                ward_category=WardCategory.MINOR_NO_PARENTS,
                guardian_name="Anh Nam",
                guardian_dob="2010-01-01",  # 16 years old
                guardian_id_number="079210002222",
                guardian_address="Quận 1",
                guardian_phone="0901111222",
                guardian_relationship=GuardianRelationship.ELDER_SIBLING,
                registration_date="2026-03-01",
            )

    def test_incapacitated_guardian_rejected(self, engine: GuardianshipEngine) -> None:
        with pytest.raises(ValueError, match="lacks full civil act capacity"):
            engine.register_guardianship(
                ward_name="Bé Mai",
                ward_dob="2015-01-01",
                ward_id_number="079215001111",
                ward_address="Quận 1",
                ward_category=WardCategory.MINOR_NO_PARENTS,
                guardian_name="Bác Bình",
                guardian_dob="1980-01-01",
                guardian_id_number="079080003333",
                guardian_address="Quận 1",
                guardian_phone="0901111222",
                guardian_relationship=GuardianRelationship.UNCLE_AUNT,
                has_full_capacity=False,
                registration_date="2026-03-01",
            )

    def test_criminal_conviction_disqualification(self, engine: GuardianshipEngine) -> None:
        with pytest.raises(ValueError, match="intentional crimes against life, health, dignity, or property"):
            engine.register_guardianship(
                ward_name="Bé Mai",
                ward_dob="2015-01-01",
                ward_id_number="079215001111",
                ward_address="Quận 1",
                ward_category=WardCategory.MINOR_NO_PARENTS,
                guardian_name="Chú Cường",
                guardian_dob="1985-05-10",
                guardian_id_number="079085004444",
                guardian_address="Quận 1",
                guardian_phone="0901111222",
                guardian_relationship=GuardianRelationship.UNCLE_AUNT,
                has_conviction_against_life_property=True,
                registration_date="2026-03-01",
            )

    def test_restricted_parental_rights_disqualification(self, engine: GuardianshipEngine) -> None:
        with pytest.raises(ValueError, match="parental rights restricted"):
            engine.register_guardianship(
                ward_name="Bé Mai",
                ward_dob="2015-01-01",
                ward_id_number="079215001111",
                ward_address="Quận 1",
                ward_category=WardCategory.MINOR_NO_PARENTS,
                guardian_name="Mẹ Kế Loan",
                guardian_dob="1988-06-12",
                guardian_id_number="079088005555",
                guardian_address="Quận 1",
                guardian_phone="0901111222",
                guardian_relationship=GuardianRelationship.OTHER,
                parental_rights_restricted=True,
                registration_date="2026-03-01",
            )

    def test_natural_guardian_ranking(self, engine: GuardianshipEngine) -> None:
        candidates_minor = [
            {"name": "Bác Tuấn", "relationship": GuardianRelationship.UNCLE_AUNT.value, "age": 50},
            {"name": "Chị Lan", "relationship": GuardianRelationship.ELDER_SIBLING.value, "age": 24},
            {"name": "Ông Nội Hùng", "relationship": GuardianRelationship.GRANDPARENT.value, "age": 72},
        ]
        ranked_minor = engine.resolve_natural_guardian_ranking(WardCategory.MINOR_NO_PARENTS, candidates_minor)
        assert ranked_minor[0]["name"] == "Chị Lan"  # Rank 1: Sibling
        assert ranked_minor[1]["name"] == "Ông Nội Hùng"  # Rank 2: Grandparent
        assert ranked_minor[2]["name"] == "Bác Tuấn"  # Rank 3: Uncle/Aunt

        candidates_adult = [
            {"name": "Con Cả Nam", "relationship": GuardianRelationship.ADULT_CHILD.value, "age": 28},
            {"name": "Vợ Hoa", "relationship": GuardianRelationship.SPOUSE.value, "age": 52},
            {"name": "Cha Minh", "relationship": GuardianRelationship.PARENT.value, "age": 78},
        ]
        ranked_adult = engine.resolve_natural_guardian_ranking(WardCategory.INCAPACITATED_ADULT, candidates_adult)
        assert ranked_adult[0]["name"] == "Vợ Hoa"  # Rank 1: Spouse
        assert ranked_adult[1]["name"] == "Cha Minh"  # Rank 2: Parent
        assert ranked_adult[2]["name"] == "Con Cả Nam"  # Rank 3: Adult child

    def test_supervisor_registration(self, engine: GuardianshipEngine) -> None:
        engine.register_guardianship(
            ward_name="Trần Văn Nam",
            ward_dob="2014-06-10",
            ward_id_number="079214001122",
            ward_address="Quận 1",
            ward_category=WardCategory.MINOR_NO_PARENTS,
            guardian_name="Trần Văn Minh",
            guardian_dob="1995-03-12",
            guardian_id_number="079095002233",
            guardian_address="Quận 1",
            guardian_phone="0909998877",
            guardian_relationship=GuardianRelationship.ELDER_SIBLING,
            registration_id="GH-SUP-TEST",
        )

        sup = engine.register_supervisor(
            registration_id="GH-SUP-TEST",
            supervisor_name="Trần Văn Trí",
            supervisor_dob="1970-08-15",
            supervisor_id_number="079070001234",
            supervisor_address="Quận 1",
            supervisor_relationship="UNCLE",
            appointing_authority="UBND Phường Bến Nghé",
            supervisor_id="SUP-001",
        )
        assert sup["ok"] is True
        assert sup["supervisor_name"] == "Trần Văn Trí"
        assert sup["status"] == "ACTIVE"

        rec = engine.get_guardianship("GH-SUP-TEST")
        assert rec["supervisor"] is not None
        assert rec["supervisor"]["supervisor_name"] == "Trần Văn Trí"

    def test_asset_inventory_within_10_days(self, engine: GuardianshipEngine) -> None:
        engine.register_guardianship(
            ward_name="Nguyễn Thị Kim",
            ward_dob="2016-09-01",
            ward_id_number="079216005544",
            ward_address="Quận 3",
            ward_category=WardCategory.MINOR_NO_PARENTS,
            guardian_name="Nguyễn Văn Bảo",
            guardian_dob="1996-01-10",
            guardian_id_number="079096006655",
            guardian_address="Quận 3",
            guardian_phone="0912345678",
            guardian_relationship=GuardianRelationship.ELDER_SIBLING,
            registration_date="2026-03-01",
            registration_id="GH-INV-TEST",
        )

        # Inventory on 5th day
        inv = engine.record_asset_inventory(
            registration_id="GH-INV-TEST",
            asset_name="Nhà phố 100m2",
            asset_category=AssetCategory.REAL_ESTATE,
            estimated_value_vnd=15_000_000_000.0,
            identifier="GCN-Q3-2026-001",
            inventory_date="2026-03-06",
            asset_id="AST-001",
        )
        assert inv["ok"] is True
        assert inv["days_from_registration"] == 5
        assert "Compliant" in inv["compliance_note"]

    def test_prohibition_on_gifting_ward_assets(self, engine: GuardianshipEngine) -> None:
        engine.register_guardianship(
            ward_name="Hoàng Gia Bảo",
            ward_dob="2017-02-14",
            ward_id_number="079217008899",
            ward_address="Quận 7",
            ward_category=WardCategory.MINOR_NO_PARENTS,
            guardian_name="Hoàng Quốc Việt",
            guardian_dob="1992-05-20",
            guardian_id_number="079092007788",
            guardian_address="Quận 7",
            guardian_phone="0988776655",
            guardian_relationship=GuardianRelationship.ELDER_SIBLING,
            registration_id="GH-GIFT-TEST",
        )

        with pytest.raises(ValueError, match="strictly prohibits donating or gifting"):
            engine.record_asset_transaction(
                registration_id="GH-GIFT-TEST",
                transaction_type=TransactionType.GIFT,
                amount_vnd=10_000_000.0,
                purpose="Tặng xe máy cho người khác",
            )

    def test_major_transaction_requires_supervisor_consent(self, engine: GuardianshipEngine) -> None:
        engine.register_guardianship(
            ward_name="Đặng Thùy Trang",
            ward_dob="2013-11-20",
            ward_id_number="079213003322",
            ward_address="Quận 10",
            ward_category=WardCategory.MINOR_NO_PARENTS,
            guardian_name="Đặng Tuấn Anh",
            guardian_dob="1994-07-15",
            guardian_id_number="079094002211",
            guardian_address="Quận 10",
            guardian_phone="0977665544",
            guardian_relationship=GuardianRelationship.ELDER_SIBLING,
            registration_id="GH-TX-TEST",
        )

        # Major transaction (e.g. 100M VND) without supervisor consent must fail
        with pytest.raises(ValueError, match="requires supervisor consent"):
            engine.record_asset_transaction(
                registration_id="GH-TX-TEST",
                transaction_type=TransactionType.INVESTMENT,
                amount_vnd=100_000_000.0,
                purpose="Đầu tư tiết kiệm",
                supervisor_consent=False,
            )

        # With supervisor consent, it succeeds
        tx = engine.record_asset_transaction(
            registration_id="GH-TX-TEST",
            transaction_type=TransactionType.INVESTMENT,
            amount_vnd=100_000_000.0,
            purpose="Đầu tư tiết kiệm",
            supervisor_consent=True,
        )
        assert tx["ok"] is True
        assert tx["status"] == "APPROVED"
        assert tx["is_major_transaction"] is True

    def test_guardianship_termination_and_3month_handover(self, engine: GuardianshipEngine) -> None:
        engine.register_guardianship(
            ward_name="Phạm Thanh Phong",
            ward_dob="2008-03-10",
            ward_id_number="079208001122",
            ward_address="Bình Thạnh",
            ward_category=WardCategory.MINOR_NO_PARENTS,
            guardian_name="Phạm Minh Tâm",
            guardian_dob="1990-04-12",
            guardian_id_number="079090003344",
            guardian_address="Bình Thạnh",
            guardian_phone="0966554433",
            guardian_relationship=GuardianRelationship.ELDER_SIBLING,
            registration_id="GH-TERM-TEST",
        )

        term = engine.terminate_guardianship(
            registration_id="GH-TERM-TEST",
            grounds=TerminationGrounds.WARD_ATTAINED_MAJORITY,
            effective_date="2026-03-10",
            handover_notes="Người được giám hộ đã tròn 18 tuổi",
        )
        assert term["ok"] is True
        assert term["status"] == "TERMINATED"
        assert term["handover_deadline"] == "2026-06-08"  # 90 days / 3 months statutory limit
        assert "3 tháng" in term["statutory_timeline"]

        rec = engine.get_guardianship("GH-TERM-TEST")
        assert rec["status"] == "TERMINATED"

    def test_telemetry_status(self, engine: GuardianshipEngine) -> None:
        status = engine.get_telemetry_status()
        assert "total_guardianship_cases" in status
        assert "active_cases" in status
        assert "total_managed_assets_vnd" in status
        assert "supervisor_coverage_pct" in status


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestGuardianshipCLI:
    """CLI integration tests for mekong guardianship, giamho, and guardian."""

    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_file = str(tmp_path / "cli_guardianship.db")
        monkeypatch.setenv("MEKONG_GUARDIANSHIP_DB", db_file)

    def test_cli_status(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["guardianship", "status"])
        assert result.exit_code == 0
        assert "HỆ THỐNG GIÁM HỘ" in result.output or "Chỉ số Vận hành" in result.output

    def test_cli_status_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["guardianship", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "telemetry" in data
        assert "active_cases" in data["telemetry"]

    def test_cli_register_and_list(self) -> None:
        app = build_app()
        result = runner.invoke(app, [
            "guardianship", "register",
            "Trần Gia Hưng", "2015-05-20", "079215009988",
            "Trần Gia Huy", "1997-08-14", "079097001122",
            "--category", "MINOR_NO_PARENTS",
            "--relationship", "ELDER_SIBLING",
            "--json",
        ])
        assert result.exit_code == 0
        res = json.loads(result.output)
        assert res["ward_name"] == "Trần Gia Hưng"
        reg_id = res["registration_id"]

        # List command
        list_res = runner.invoke(app, ["guardianship", "list", "--json"])
        assert list_res.exit_code == 0
        items = json.loads(list_res.output)
        assert len(items) >= 1
        assert any(item["registration_id"] == reg_id for item in items)

    def test_cli_supervisor_and_inventory(self) -> None:
        app = build_app()
        # Register first
        reg_out = runner.invoke(app, [
            "guardianship", "register",
            "Vũ Minh Khang", "2013-09-12", "079213007766",
            "Vũ Minh Đức", "1995-10-10", "079095008877",
            "--json",
        ])
        reg_id = json.loads(reg_out.output)["registration_id"]

        # Register supervisor
        sup_out = runner.invoke(app, [
            "guardianship", "supervisor",
            reg_id, "Vũ Văn Tài", "079065001122",
            "--authority", "UBND Phường Đa Kao",
            "--json",
        ])
        assert sup_out.exit_code == 0
        assert json.loads(sup_out.output)["ok"] is True

        # Inventory asset
        inv_out = runner.invoke(app, [
            "guardianship", "inventory",
            reg_id, "Sổ tiết kiệm Vietcombank", "BANK_DEPOSIT", "500000000",
            "--json",
        ])
        assert inv_out.exit_code == 0
        assert json.loads(inv_out.output)["ok"] is True

    def test_cli_transact_and_terminate(self) -> None:
        app = build_app()
        reg_out = runner.invoke(app, [
            "guardianship", "register",
            "Lý Hoàng Yến", "2016-04-18", "079216003344",
            "Lý Hoàng Sơn", "1994-11-25", "079094005566",
            "--json",
        ])
        reg_id = json.loads(reg_out.output)["registration_id"]

        # Transact care expense (15M)
        tx_out = runner.invoke(app, [
            "guardianship", "transact",
            reg_id, "EXPENSE_CARE", "15000000", "Chi phí sinh hoạt và dinh dưỡng",
            "--json",
        ])
        assert tx_out.exit_code == 0
        assert json.loads(tx_out.output)["ok"] is True

        # Terminate
        term_out = runner.invoke(app, [
            "guardianship", "terminate",
            reg_id, "WARD_ADOPTED",
            "--handover-notes", "Được gia đình nhận làm con nuôi hợp pháp",
            "--json",
        ])
        assert term_out.exit_code == 0
        assert json.loads(term_out.output)["status"] == "TERMINATED"

    def test_cli_aliases_giamho_and_guardian(self) -> None:
        app = build_app()
        res_gh = runner.invoke(app, ["giamho", "status", "--json"])
        assert res_gh.exit_code == 0
        assert "telemetry" in json.loads(res_gh.output)

        res_g = runner.invoke(app, ["guardian", "status", "--json"])
        assert res_g.exit_code == 0
        assert "telemetry" in json.loads(res_g.output)


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestGuardianshipMCPParity:
    """Test 100% parity across FastMCP and JSON-RPC fallback implementations."""

    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_file = str(tmp_path / "mcp_guardianship.db")
        monkeypatch.setenv("MEKONG_GUARDIANSHIP_DB", db_file)

    def test_fastmcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        reg_json = server._handle_guardianship_register(
            ward_name="Bùi Tấn Tài",
            ward_dob="2014-07-22",
            ward_id_number="079214008811",
            guardian_name="Bùi Tấn Phát",
            guardian_dob="1996-03-15",
            guardian_id_number="079096009922",
        )
        reg_res = json.loads(reg_json)
        assert reg_res["ward_name"] == "Bùi Tấn Tài"
        reg_id = reg_res["registration_id"]

        sup_json = server._handle_guardianship_supervisor(
            registration_id=reg_id,
            supervisor_name="Bùi Văn Long",
            supervisor_id_number="079068001133",
        )
        assert json.loads(sup_json)["ok"] is True

        inv_json = server._handle_guardianship_inventory(
            registration_id=reg_id,
            asset_name="Xe máy Honda SH",
            asset_category="VEHICLE",
            estimated_value_vnd=90_000_000.0,
        )
        assert json.loads(inv_json)["ok"] is True

        tx_json = server._handle_guardianship_transact(
            registration_id=reg_id,
            transaction_type="TREATMENT",
            amount_vnd=25_000_000.0,
            purpose="Chi phí điều trị y tế",
        )
        assert json.loads(tx_json)["ok"] is True

        term_json = server._handle_guardianship_terminate(
            registration_id=reg_id,
            grounds="PARENTS_RESUMED_RIGHTS",
        )
        assert json.loads(term_json)["status"] == "TERMINATED"

        search_json = server._handle_guardianship_search(query="Bùi Tấn")
        assert len(json.loads(search_json)) >= 1

        status_json = server._handle_guardianship_status()
        assert json.loads(status_json)["total_guardianship_cases"] >= 1

    def test_stdio_jsonrpc_handlers_and_spec(self) -> None:
        import scripts.mcp_server as mcp_script

        # Verify handlers exist in CORE_HANDLERS
        for tool in [
            "mekong_guardianship_register",
            "mekong_guardianship_supervisor",
            "mekong_guardianship_inventory",
            "mekong_guardianship_transact",
            "mekong_guardianship_terminate",
            "mekong_guardianship_search",
            "mekong_guardianship_status",
            "guardianship_register",
            "guardianship_supervisor",
            "guardianship_inventory",
            "guardianship_transact",
            "guardianship_terminate",
            "guardianship_search",
            "guardianship_status",
        ]:
            assert tool in mcp_script.CORE_HANDLERS, f"Missing {tool} in CORE_HANDLERS"

        # Verify tool spec in CORE_TOOLS_SPEC
        spec_names = {t["name"] for t in mcp_script.CORE_TOOLS_SPEC}
        assert "mekong_guardianship_register" in spec_names
        assert "mekong_guardianship_supervisor" in spec_names
        assert "mekong_guardianship_inventory" in spec_names
        assert "mekong_guardianship_transact" in spec_names
        assert "mekong_guardianship_terminate" in spec_names
        assert "mekong_guardianship_search" in spec_names
        assert "mekong_guardianship_status" in spec_names

        # Execute handler directly
        reg_json = mcp_script.handle_guardianship_register({
            "ward_name": "Lương Gia Hân",
            "ward_dob": "2015-09-30",
            "ward_id_number": "079215003311",
            "guardian_name": "Lương Gia Bảo",
            "guardian_dob": "1995-12-10",
            "guardian_id_number": "079095004422",
        })
        reg = json.loads(reg_json)
        assert reg["ward_name"] == "Lương Gia Hân"

        stat_json = mcp_script.handle_guardianship_status({})
        assert json.loads(stat_json)["total_guardianship_cases"] >= 1
