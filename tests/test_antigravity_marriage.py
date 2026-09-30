# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Marriage, Matrimonial Property Regimes & Family Law Suite (Phase 147)."""

from __future__ import annotations

import ast
import json
import os
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.marriage_engine import (
    AssetCategory,
    DivorceStatus,
    DivorceType,
    MarriageEngine,
    MarriageStatus,
    OwnershipType,
    PropertyRegimeType,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestMarriageCoreBoundary:
    """Ensure MarriageEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/marriage_engine.py")
        assert source_path.exists(), "marriage_engine.py must exist"

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


class TestMarriageEngine:
    """Unit tests for MarriageEngine under Law on Marriage and Family 2014."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> MarriageEngine:
        db_path = str(tmp_path / "test_marriage.db")
        return MarriageEngine(db_path=db_path)

    def test_register_marriage_success(self, engine: MarriageEngine) -> None:
        reg = engine.register_marriage(
            husband_name="Nguyễn Văn An",
            wife_name="Trần Thị Bình",
            husband_dob="1995-05-15",
            wife_dob="1998-08-20",
            husband_id="001095000123",
            wife_id="001098000456",
            husband_address="Quận 1, TP. Hồ Chí Minh",
            wife_address="Quận 3, TP. Hồ Chí Minh",
            registration_date="2024-02-14",
            registration_office="UBND Phường Bến Nghé, Quận 1",
            marriage_id="MARR-TEST-001",
        )
        assert reg["marriage_id"] == "MARR-TEST-001"
        assert reg["husband_name"] == "Nguyễn Văn An"
        assert reg["wife_name"] == "Trần Thị Bình"
        assert reg["status"] == "ACTIVE"
        assert reg["property_regime"] == "STATUTORY"
        assert "CERT-KH-" in reg["certificate_number"]

    def test_register_marriage_underage_rejected(self, engine: MarriageEngine) -> None:
        # Male under 20
        with pytest.raises(ValueError, match="Husband must be at least 20 years old"):
            engine.register_marriage(
                husband_name="Trẻ Nam",
                wife_name="Cô Nữ",
                husband_dob="2010-01-01",
                wife_dob="2000-01-01",
                husband_id="001210000001",
                wife_id="001200000002",
                registration_date="2026-01-01",
            )

        # Female under 18
        with pytest.raises(ValueError, match="Wife must be at least 18 years old"):
            engine.register_marriage(
                husband_name="Anh Nam",
                wife_name="Bé Gái",
                husband_dob="2000-01-01",
                wife_dob="2012-01-01",
                husband_id="001200000003",
                wife_id="001212000004",
                registration_date="2026-01-01",
            )

    def test_register_marriage_monogamy_violation(self, engine: MarriageEngine) -> None:
        # Register first marriage
        engine.register_marriage(
            husband_name="Lê Văn Chung",
            wife_name="Phạm Thị Dung",
            husband_dob="1992-03-10",
            wife_dob="1994-04-12",
            husband_id="001092000789",
            wife_id="001094000321",
            registration_date="2020-01-10",
        )

        # Husband attempts second marriage while first is active
        with pytest.raises(ValueError, match="active legal marriage"):
            engine.register_marriage(
                husband_name="Lê Văn Chung",
                wife_name="Hoàng Thị Hoa",
                husband_dob="1992-03-10",
                wife_dob="1996-06-15",
                husband_id="001092000789",
                wife_id="001096000999",
                registration_date="2025-01-01",
            )

    def test_prenuptial_agreement_success(self, engine: MarriageEngine) -> None:
        reg = engine.register_marriage(
            husband_name="Phan Văn Đạt",
            wife_name="Đặng Thị Em",
            husband_dob="1990-10-10",
            wife_dob="1993-11-11",
            husband_id="001090000111",
            wife_id="001093000222",
            registration_date="2024-05-20",
            property_regime="AGREED",
            marriage_id="MARR-AGREED-01",
        )
        assert reg["property_regime"] == "AGREED"

        prenup = engine.register_prenuptial_agreement(
            marriage_id="MARR-AGREED-01",
            agreement_date="2024-05-15",
            notary_office="Phòng Công chứng số 1 TP. Hà Nội",
            notary_certificate_number="CC-PRENUP-2024/99",
            terms_summary="Toàn bộ tài sản hình thành trước và trong hôn nhân thuộc sở hữu riêng của mỗi bên",
        )
        assert prenup["marriage_id"] == "MARR-AGREED-01"
        assert prenup["notary_office"] == "Phòng Công chứng số 1 TP. Hà Nội"
        assert prenup["regime_type"] == "AGREED_PRENUPTIAL"

    def test_prenuptial_agreement_invalid_date(self, engine: MarriageEngine) -> None:
        engine.register_marriage(
            husband_name="Vũ Văn Giàu",
            wife_name="Bùi Thị Hoa",
            husband_dob="1988-01-01",
            wife_dob="1991-02-02",
            husband_id="001088000333",
            wife_id="001091000444",
            registration_date="2023-01-01",
            marriage_id="MARR-LATE-01",
        )
        # Agreement date after marriage registration date is invalid per Article 47
        with pytest.raises(ValueError, match="must be prior to or on the marriage registration date"):
            engine.register_prenuptial_agreement(
                marriage_id="MARR-LATE-01",
                agreement_date="2023-06-01",
                notary_office="Văn phòng Công chứng Hà Thành",
            )

    def test_matrimonial_asset_classification(self, engine: MarriageEngine) -> None:
        reg = engine.register_marriage(
            husband_name="Trịnh Quốc Hưng",
            wife_name="Ngô Thanh Mai",
            husband_dob="1985-07-07",
            wife_dob="1989-08-08",
            husband_id="001085000555",
            wife_id="001089000666",
            registration_date="2018-10-10",
            marriage_id="MARR-ASSETS-01",
        )
        # Common asset
        asset1 = engine.record_matrimonial_asset(
            marriage_id="MARR-ASSETS-01",
            asset_name="Căn hộ chung cư Vinhomes Central Park",
            asset_category="REAL_ESTATE",
            estimated_value=6_500_000_000.0,
            ownership_type="COMMON",
            acquisition_date="2020-03-15",
            identifier_number="SH-VCP-2020-01",
        )
        assert asset1["ownership_type"] == "COMMON"
        assert asset1["estimated_value"] == 6_500_000_000.0

        # Separate asset
        asset2 = engine.record_matrimonial_asset(
            marriage_id="MARR-ASSETS-01",
            asset_name="Cổ phần thừa kế riêng Công ty Dược",
            asset_category="FINANCIAL",
            estimated_value=2_000_000_000.0,
            ownership_type="SEPARATE",
            acquisition_date="2015-01-01",
            notes="Tài sản thừa kế riêng của người vợ theo Di chúc",
        )
        assert asset2["ownership_type"] == "SEPARATE"

        assets = engine.list_matrimonial_assets(marriage_id="MARR-ASSETS-01")
        assert len(assets) == 2

    def test_divorce_petition_consensual(self, engine: MarriageEngine) -> None:
        engine.register_marriage(
            husband_name="Dương Tuấn Kiệt",
            wife_name="Đỗ Kim Lan",
            husband_dob="1987-04-04",
            wife_dob="1990-05-05",
            husband_id="001087000777",
            wife_id="001090000888",
            registration_date="2016-09-09",
            marriage_id="MARR-DIV-01",
        )
        petition = engine.file_divorce_petition(
            marriage_id="MARR-DIV-01",
            divorce_type="CONSENSUAL",
            petitioner="BOTH",
            grounds="Thuận tình ly hôn do mục đích hôn nhân không đạt được",
            court_name="TAND Quận Ba Đình, TP. Hà Nội",
            petition_id="PET-DIV-001",
        )
        assert petition["divorce_type"] == "CONSENSUAL"
        assert petition["petitioner"] == "BOTH"
        assert petition["status"] == "PENDING_RECONCILIATION"

    def test_divorce_petition_unilateral_husband_statutory_bar(self, engine: MarriageEngine) -> None:
        engine.register_marriage(
            husband_name="Hoàng Minh Long",
            wife_name="Võ Ngọc Như",
            husband_dob="1993-02-02",
            wife_dob="1996-03-03",
            husband_id="001093000999",
            wife_id="001096000111",
            registration_date="2022-04-04",
            marriage_id="MARR-BAR-01",
        )
        # Husband filing while wife is pregnant is strictly prohibited under Article 51(3)
        with pytest.raises(ValueError, match="Husband has NO right to request divorce while wife is pregnant"):
            engine.file_divorce_petition(
                marriage_id="MARR-BAR-01",
                divorce_type="UNILATERAL",
                petitioner="HUSBAND",
                grounds="Bất đồng quan điểm",
                wife_is_pregnant=True,
            )

        # Husband filing while nursing child under 12 months is prohibited under Article 51(3)
        with pytest.raises(ValueError, match="nursing a child under 12 months"):
            engine.file_divorce_petition(
                marriage_id="MARR-BAR-01",
                divorce_type="UNILATERAL",
                petitioner="HUSBAND",
                grounds="Mâu thuẫn gia đình",
                nursing_child_under_12m=True,
            )

    def test_divorce_petition_unilateral_wife_allowed(self, engine: MarriageEngine) -> None:
        engine.register_marriage(
            husband_name="Lâm Văn Oanh",
            wife_name="Cao Thị Phúc",
            husband_dob="1991-06-06",
            wife_dob="1994-07-07",
            husband_id="001091000222",
            wife_id="001094000333",
            registration_date="2021-08-08",
            marriage_id="MARR-WIFE-01",
        )
        # Wife filing while pregnant is legally permitted under Article 51(3)
        petition = engine.file_divorce_petition(
            marriage_id="MARR-WIFE-01",
            divorce_type="UNILATERAL",
            petitioner="WIFE",
            grounds="Chồng có hành vi bạo lực gia đình nghiêm trọng",
            has_domestic_violence=True,
            wife_is_pregnant=True,
        )
        assert petition["petitioner"] == "WIFE"
        assert bool(petition["has_domestic_violence"]) is True

    def test_child_custody_and_support_rules(self, engine: MarriageEngine) -> None:
        engine.register_marriage(
            husband_name="Tô Đình Quang",
            wife_name="Hà Thị Sen",
            husband_dob="1986-12-12",
            wife_dob="1989-11-11",
            husband_id="001086000444",
            wife_id="001089000555",
            registration_date="2015-05-05",
            marriage_id="MARR-KIDS-01",
        )
        pet = engine.file_divorce_petition(
            marriage_id="MARR-KIDS-01",
            divorce_type="CONSENSUAL",
            petitioner="BOTH",
            petition_id="PET-KIDS-001",
        )

        # Child under 36 months: defaults to MOTHER per Article 81(3)
        infant = engine.process_child_custody_support(
            petition_id="PET-KIDS-001",
            child_name="Tô Bé Xinh",
            child_dob="2025-06-01",
            effective_date="2026-01-01",
            custodial_parent="MOTHER",
            monthly_support_vnd=8_000_000.0,
        )
        assert infant["custodial_parent"] == "MOTHER"
        assert "Điều 81(3)" in infant["notes"]
        assert infant["monthly_support_vnd"] == 8_000_000.0

        # Child 7 years or older: must consult child's wishes per Article 81(2)
        older_child = engine.process_child_custody_support(
            petition_id="PET-KIDS-001",
            child_name="Tô Đình Lớn",
            child_dob="2017-02-10",
            effective_date="2026-01-01",
            custodial_parent="FATHER",
            monthly_support_vnd=7_000_000.0,
        )
        assert "Điều 81(2)" in older_child["notes"]

    def test_settle_property_division(self, engine: MarriageEngine) -> None:
        engine.register_marriage(
            husband_name="Lưu Văn Tùng",
            wife_name="Vũ Thị Uyên",
            husband_dob="1984-01-15",
            wife_dob="1988-02-20",
            husband_id="001084000666",
            wife_id="001088000777",
            registration_date="2017-03-15",
            marriage_id="MARR-SETTLE-01",
        )
        engine.record_matrimonial_asset(
            marriage_id="MARR-SETTLE-01",
            asset_name="Nhà phố Quận 7",
            asset_category="REAL_ESTATE",
            estimated_value=10_000_000_000.0,
            ownership_type="COMMON",
        )
        engine.record_matrimonial_asset(
            marriage_id="MARR-SETTLE-01",
            asset_name="Ô tô Mercedes C200",
            asset_category="VEHICLE",
            estimated_value=1_200_000_000.0,
            ownership_type="COMMON",
        )
        engine.record_matrimonial_asset(
            marriage_id="MARR-SETTLE-01",
            asset_name="Nhẫn kim cương quà tặng riêng",
            asset_category="OTHER",
            estimated_value=300_000_000.0,
            ownership_type="SEPARATE",
        )

        settlement = engine.settle_matrimonial_property(
            marriage_id="MARR-SETTLE-01",
            husband_ratio=0.5,
            wife_ratio=0.5,
            settlement_agreement="Thỏa thuận chia đôi tài sản chung 50/50 theo Điều 59",
        )
        assert settlement["common_property_total_vnd"] == 11_200_000_000.0
        assert settlement["husband_share_vnd"] == 5_600_000_000.0
        assert settlement["wife_share_vnd"] == 5_600_000_000.0
        assert settlement["separate_property_total_vnd"] == 300_000_000.0

    def test_search_and_telemetry(self, engine: MarriageEngine) -> None:
        engine.register_marriage(
            husband_name="Trần Hùng Dũng",
            wife_name="Lê Thu Trang",
            husband_dob="1992-09-09",
            wife_dob="1995-10-10",
            husband_id="001092000888",
            wife_id="001095000999",
            marriage_id="MARR-SEARCH-01",
        )

        srch = engine.search_marriage_records("Trần Hùng Dũng")
        assert len(srch) >= 1
        assert srch[0]["husband_name"] == "Trần Hùng Dũng"

        status = engine.get_telemetry_status()
        assert status["system_status"] == "ONLINE_HEALTHY"
        assert status["total_marriages"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestMarriageCLI:
    """CLI tests for mekong marriage and its aliases mekong honnhan, giadinh."""

    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.db_path = str(tmp_path / "cli_marriage.db")
        monkeypatch.setenv("MEKONG_MARRIAGE_DB", self.db_path)
        self.app = build_app()

    def test_cli_status(self) -> None:
        result = runner.invoke(self.app, ["marriage", "status"])
        assert result.exit_code == 0
        assert "QUẢN LÝ HÔN NHÂN & GIA ĐÌNH" in result.output

        res_json = runner.invoke(self.app, ["marriage", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["system_status"] == "ONLINE_HEALTHY"

    def test_cli_register_and_list(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "marriage",
                "register",
                "Phạm Văn Hải",
                "Đào Thị Yến",
                "1994-03-20",
                "1997-07-25",
                "001094111222",
                "001097333444",
                "--marriage-id", "MARR-CLI-01",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["marriage_id"] == "MARR-CLI-01"
        assert data["husband_name"] == "Phạm Văn Hải"

        # List
        res_list = runner.invoke(self.app, ["marriage", "list", "--category", "marriage", "--json"])
        assert res_list.exit_code == 0
        items = json.loads(res_list.output)
        assert len(items) >= 1

    def test_cli_prenuptial(self) -> None:
        # First register
        runner.invoke(
            self.app,
            [
                "marriage",
                "register",
                "Ngô Bá Khá",
                "Trần Thị Lan",
                "1993-01-01",
                "1995-02-02",
                "001093555666",
                "001095777888",
                "--reg-date", "2024-06-01",
                "--marriage-id", "MARR-CLI-PRENUP",
            ],
        )

        res_pn = runner.invoke(
            self.app,
            [
                "marriage",
                "prenuptial",
                "MARR-CLI-PRENUP",
                "2024-05-30",
                "Văn phòng Công chứng Hoàn Kiếm",
                "--notary-cert", "NOTARY-2024-88",
                "--json",
            ],
        )
        assert res_pn.exit_code == 0
        data = json.loads(res_pn.output)
        assert data["marriage_id"] == "MARR-CLI-PRENUP"
        assert data["regime_type"] == "AGREED_PRENUPTIAL"

    def test_cli_asset_and_settle(self) -> None:
        # Register
        runner.invoke(
            self.app,
            [
                "marriage",
                "register",
                "Vương Đình Huệ",
                "Lê Thị Thảo",
                "1980-05-05",
                "1983-06-06",
                "001080123456",
                "001083654321",
                "--marriage-id", "MARR-CLI-SETTLE",
            ],
        )

        # Asset
        res_asset = runner.invoke(
            self.app,
            [
                "marriage",
                "asset",
                "MARR-CLI-SETTLE",
                "Khu đất Thảo Điền",
                "REAL_ESTATE",
                "25000000000",
                "--ownership", "COMMON",
                "--json",
            ],
        )
        assert res_asset.exit_code == 0
        asset_data = json.loads(res_asset.output)
        assert asset_data["estimated_value"] == 25_000_000_000.0

        # File divorce petition first
        res_div = runner.invoke(
            self.app,
            [
                "marriage",
                "divorce",
                "MARR-CLI-SETTLE",
                "CONSENSUAL",
                "BOTH",
                "Hai bên không còn hòa hợp",
                "--court", "TAND TP.HCM",
                "--json",
            ],
        )
        div_data = json.loads(res_div.output)

        # Settle
        res_settle = runner.invoke(
            self.app,
            [
                "marriage",
                "settle",
                div_data["petition_id"],
                "QD-ST-2026/01",
                "--husband-percent", "50",
                "--json",
            ],
        )
        assert res_settle.exit_code == 0
        settle_data = json.loads(res_settle.output)
        assert settle_data["husband_total_allocation_vnd"] == 12_500_000_000.0

    def test_cli_divorce_and_custody(self) -> None:
        # Register
        runner.invoke(
            self.app,
            [
                "marriage",
                "register",
                "Phan Gia Khiêm",
                "Trương Mỹ Dung",
                "1985-09-09",
                "1988-10-10",
                "001085987654",
                "001088456789",
                "--marriage-id", "MARR-CLI-DIVORCE",
            ],
        )

        # Divorce
        res_div = runner.invoke(
            self.app,
            [
                "marriage",
                "divorce",
                "MARR-CLI-DIVORCE",
                "CONSENSUAL",
                "BOTH",
                "Hai bên không còn tình cảm gắn bó",
                "--json",
            ],
        )
        assert res_div.exit_code == 0
        div_data = json.loads(res_div.output)
        assert "petition_id" in div_data

        # Custody
        res_cust = runner.invoke(
            self.app,
            [
                "marriage",
                "custody",
                div_data["petition_id"],
                "Phan Gia Phúc",
                "2024-11-01",
                "MOTHER",
                "6000000",
                "--json",
            ],
        )
        assert res_cust.exit_code == 0
        cust_data = json.loads(res_cust.output)
        assert cust_data["custodial_parent"] == "MOTHER"
        assert cust_data["monthly_support_vnd"] == 6_000_000.0

    def test_cli_search(self) -> None:
        runner.invoke(
            self.app,
            [
                "marriage",
                "register",
                "Tạ Quang Bửu",
                "Vũ Thị Nguyệt",
                "1990-12-12",
                "1992-11-11",
                "001090654321",
                "001092123456",
            ],
        )
        res = runner.invoke(self.app, ["marriage", "search", "Tạ Quang Bửu", "--json"])
        assert res.exit_code == 0
        items = json.loads(res.output)
        assert len(items) >= 1

    def test_cli_aliases_honnhan_giadinh(self) -> None:
        # Test honnhan alias
        res_hn = runner.invoke(self.app, ["honnhan", "status", "--json"])
        assert res_hn.exit_code == 0
        assert json.loads(res_hn.output)["system_status"] == "ONLINE_HEALTHY"

        # Test giadinh alias
        res_gd = runner.invoke(self.app, ["giadinh", "status", "--json"])
        assert res_gd.exit_code == 0
        assert json.loads(res_gd.output)["system_status"] == "ONLINE_HEALTHY"


# ---------------------------------------------------------------------------
# MCP Dual Parity Tests
# ---------------------------------------------------------------------------


class TestMarriageMCP:
    """Test FastMCP and fallback JSON-RPC 2.0 stdio server handlers for Marriage."""

    def test_core_mcp_marriage_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_path = str(tmp_path / "test_mcp_core_marriage.db")
        monkeypatch.setenv("MEKONG_MARRIAGE_DB", db_path)
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-marriage-server")

        # 1. Register
        res_reg = json.loads(server._handle_marriage_register(
            husband_name="Lý Thái Tổ",
            wife_name="Lê Thị Phất Ngân",
            husband_dob="1980-01-01",
            wife_dob="1985-02-02",
            husband_id="001080000001",
            wife_id="001085000002",
            marriage_id="MARR-MCP-01",
        ))
        assert res_reg["marriage_id"] == "MARR-MCP-01"

        # 2. Prenuptial
        res_pn = json.loads(server._handle_marriage_prenuptial(
            marriage_id="MARR-MCP-01",
            agreement_date="2024-01-01",
            notary_office="Công chứng Thăng Long",
        ))
        assert res_pn["regime_type"] == "AGREED_PRENUPTIAL"

        # 3. Asset
        res_asset = json.loads(server._handle_marriage_asset(
            marriage_id="MARR-MCP-01",
            asset_name="Trống đồng cổ truyền",
            asset_category="OTHER",
            estimated_value=500_000_000.0,
            ownership_type="COMMON",
            asset_id="ASSET-MCP-01",
        ))
        assert res_asset["asset_id"] == "ASSET-MCP-01"

        # 4. Divorce
        res_div = json.loads(server._handle_marriage_divorce(
            marriage_id="MARR-MCP-01",
            divorce_type="CONSENSUAL",
            petitioner="BOTH",
            petition_id="PET-MCP-01",
        ))
        assert res_div["petition_id"] == "PET-MCP-01"

        # 5. Custody
        res_cust = json.loads(server._handle_marriage_custody(
            petition_id="PET-MCP-01",
            child_name="Lý Phật Mã",
            child_dob="2024-10-01",
            custodial_parent="MOTHER",
            monthly_support_vnd=10_000_000.0,
        ))
        assert res_cust["custodial_parent"] == "MOTHER"

        # 6. Search
        res_srch = json.loads(server._handle_marriage_search(query="Lý Thái Tổ"))
        assert len(res_srch) >= 1

        # 7. Status
        res_stat = json.loads(server._handle_marriage_status())
        assert res_stat["system_status"] == "ONLINE_HEALTHY"

    def test_scripts_mcp_marriage_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_path = str(tmp_path / "test_mcp_scripts_marriage.db")
        monkeypatch.setenv("MEKONG_MARRIAGE_DB", db_path)
        from scripts.mcp_server import (
            handle_marriage_asset,
            handle_marriage_custody,
            handle_marriage_divorce,
            handle_marriage_prenuptial,
            handle_marriage_register,
            handle_marriage_search,
            handle_marriage_status,
        )

        # 1. Register
        res_reg = json.loads(handle_marriage_register({
            "husband_name": "Trần Nhân Tông",
            "wife_name": "Bảo Thánh Hoàng hậu",
            "husband_dob": "1982-03-03",
            "wife_dob": "1986-04-04",
            "husband_id": "001082000003",
            "wife_id": "001086000004",
            "marriage_id": "MARR-SCRIPT-01",
        }))
        assert res_reg["marriage_id"] == "MARR-SCRIPT-01"

        # 2. Prenuptial
        res_pn = json.loads(handle_marriage_prenuptial({
            "marriage_id": "MARR-SCRIPT-01",
            "agreement_date": "2024-02-01",
            "notary_office": "Công chứng Yên Tử",
        }))
        assert res_pn["regime_type"] == "AGREED_PRENUPTIAL"

        # 3. Asset
        res_asset = json.loads(handle_marriage_asset({
            "marriage_id": "MARR-SCRIPT-01",
            "asset_name": "Vườn thuốc thảo dược",
            "asset_category": "REAL_ESTATE",
            "estimated_value": 3_000_000_000.0,
            "ownership_type": "COMMON",
            "asset_id": "ASSET-SCRIPT-01",
        }))
        assert res_asset["asset_id"] == "ASSET-SCRIPT-01"

        # 4. Divorce
        res_div = json.loads(handle_marriage_divorce({
            "marriage_id": "MARR-SCRIPT-01",
            "divorce_type": "CONSENSUAL",
            "petitioner": "BOTH",
            "petition_id": "PET-SCRIPT-01",
        }))
        assert res_div["petition_id"] == "PET-SCRIPT-01"

        # 5. Custody
        res_cust = json.loads(handle_marriage_custody({
            "petition_id": "PET-SCRIPT-01",
            "child_name": "Trần Anh Tông",
            "child_dob": "2024-12-01",
            "custodial_parent": "MOTHER",
            "monthly_support_vnd": 12_000_000.0,
        }))
        assert res_cust["custodial_parent"] == "MOTHER"

        # 6. Search
        res_srch = json.loads(handle_marriage_search({"query": "Trần Nhân Tông"}))
        assert len(res_srch) >= 1

        # 7. Status
        res_stat = json.loads(handle_marriage_status({}))
        assert res_stat["system_status"] == "ONLINE_HEALTHY"

    def test_scripts_mcp_core_tools_spec_and_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        expected_tools = [
            "mekong_marriage_register",
            "mekong_marriage_prenuptial",
            "mekong_marriage_asset",
            "mekong_marriage_divorce",
            "mekong_marriage_custody",
            "mekong_marriage_search",
            "mekong_marriage_status",
        ]

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for tool in expected_tools:
            assert tool in spec_names, f"Tool {tool} missing from CORE_TOOLS_SPEC"
            assert tool in CORE_HANDLERS, f"Tool {tool} missing from CORE_HANDLERS"
            bare_name = tool.replace("mekong_", "")
            assert bare_name in CORE_HANDLERS, f"Alias {bare_name} missing from CORE_HANDLERS"
