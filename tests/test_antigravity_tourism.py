# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating Suite (Phase 76)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.tourism_engine import (
    ACCOMMODATION_STAR_STANDARDS,
    ADVENTURE_TOURISM_TYPES,
    TOUR_GUIDE_CARD_TYPES,
    TRAVEL_LICENSE_TYPES,
    TourismEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestTourismCoreBoundary:
    """Ensure TourismEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/tourism_engine.py")
        assert source_path.exists(), "tourism_engine.py must exist"

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


class TestTourismEngine:
    """Test TourismEngine licensing, hotel star ratings, tour guides, adventure safety, and bookings."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> TourismEngine:
        db_file = tmp_path / "test_tourism.db"
        return TourismEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Travel License Configs under Law on Tourism 2017 & Decree 168/2017/NĐ-CP
        assert "DOMESTIC_TRAVEL" in TRAVEL_LICENSE_TYPES
        assert TRAVEL_LICENSE_TYPES["DOMESTIC_TRAVEL"]["min_escrow_vnd"] == 100_000_000.0
        assert "INTERNATIONAL_INBOUND" in TRAVEL_LICENSE_TYPES
        assert TRAVEL_LICENSE_TYPES["INTERNATIONAL_INBOUND"]["min_escrow_vnd"] == 250_000_000.0
        assert "INTERNATIONAL_OUTBOUND" in TRAVEL_LICENSE_TYPES
        assert TRAVEL_LICENSE_TYPES["INTERNATIONAL_OUTBOUND"]["min_escrow_vnd"] == 500_000_000.0
        assert "INTERNATIONAL_FULL" in TRAVEL_LICENSE_TYPES
        assert TRAVEL_LICENSE_TYPES["INTERNATIONAL_FULL"]["min_escrow_vnd"] == 500_000_000.0

        # Accommodation Star Standards under TCVN 4391:2015
        assert "1_STAR" in ACCOMMODATION_STAR_STANDARDS
        assert ACCOMMODATION_STAR_STANDARDS["1_STAR"]["min_rooms"] == 10
        assert "2_STAR" in ACCOMMODATION_STAR_STANDARDS
        assert ACCOMMODATION_STAR_STANDARDS["2_STAR"]["min_rooms"] == 20
        assert "3_STAR" in ACCOMMODATION_STAR_STANDARDS
        assert ACCOMMODATION_STAR_STANDARDS["3_STAR"]["min_rooms"] == 50
        assert "4_STAR" in ACCOMMODATION_STAR_STANDARDS
        assert ACCOMMODATION_STAR_STANDARDS["4_STAR"]["min_rooms"] == 80
        assert "5_STAR" in ACCOMMODATION_STAR_STANDARDS
        assert ACCOMMODATION_STAR_STANDARDS["5_STAR"]["min_rooms"] == 100

        # Tour Guide Cards under Law on Tourism 2017 & Circular 06/2017/TT-BVHTTDL
        assert "DOMESTIC" in TOUR_GUIDE_CARD_TYPES
        assert "INTERNATIONAL" in TOUR_GUIDE_CARD_TYPES
        assert "ON_SITE" in TOUR_GUIDE_CARD_TYPES

        # Adventure Tourism Types under Decree 168/2017/NĐ-CP
        assert "CAVING_EXPEDITION" in ADVENTURE_TOURISM_TYPES
        assert "SCUBA_DIVING" in ADVENTURE_TOURISM_TYPES
        assert "PARAGLIDING" in ADVENTURE_TOURISM_TYPES
        assert "WHITE_WATER_RAFTING" in ADVENTURE_TOURISM_TYPES
        assert "ROCK_CLIMBING" in ADVENTURE_TOURISM_TYPES
        assert "ZIPLINE_CANOPY" in ADVENTURE_TOURISM_TYPES

    def test_issue_travel_license_domestic_success(self, engine: TourismEngine) -> None:
        res = engine.issue_travel_license(
            enterprise_name="Công ty TNHH Du lịch Đồng Bằng",
            tax_id="0315889901",
            license_type="DOMESTIC_TRAVEL",
            escrow_amount_vnd=120_000_000.0,
            escrow_bank="Vietcombank",
            responsible_person="Lê Văn An",
            qualification="Cử nhân Lữ hành",
        )
        assert res["status"] == "success"
        prof = res["license_profile"]
        assert prof["enterprise_name"] == "Công ty TNHH Du lịch Đồng Bằng"
        assert prof["license_type"] == "DOMESTIC_TRAVEL"
        assert prof["escrow_amount_vnd"] == 120_000_000.0
        assert prof["min_required_escrow_vnd"] == 100_000_000.0
        assert prof["status"] == "ACTIVE"
        assert prof["license_number"].startswith("GPLH-")

    def test_issue_travel_license_international_full_success(self, engine: TourismEngine) -> None:
        res = engine.issue_travel_license(
            enterprise_name="Công ty Cổ phần Saigontourist Global",
            tax_id="0300123456",
            license_type="INTERNATIONAL_FULL",
            escrow_amount_vnd=500_000_000.0,
            escrow_bank="BIDV",
            responsible_person="Trần Thu Hà",
            qualification="Thạc sĩ Quản trị Lữ hành",
        )
        assert res["status"] == "success"
        prof = res["license_profile"]
        assert prof["license_type"] == "INTERNATIONAL_FULL"
        assert prof["min_required_escrow_vnd"] == 500_000_000.0
        assert prof["licensing_authority"] == "Cục Du lịch Quốc gia Việt Nam"

    def test_issue_travel_license_insufficient_escrow(self, engine: TourismEngine) -> None:
        with pytest.raises(ValueError, match="Tiền ký quỹ không đủ điều kiện"):
            # International full requires 500M, providing only 200M
            engine.issue_travel_license(
                enterprise_name="Công ty Thiếu Tiền Ký Quỹ",
                tax_id="0109999888",
                license_type="INTERNATIONAL_FULL",
                escrow_amount_vnd=200_000_000.0,
            )

    def test_issue_travel_license_invalid_type(self, engine: TourismEngine) -> None:
        with pytest.raises(ValueError, match="Loại giấy phép lữ hành không hợp lệ"):
            engine.issue_travel_license(
                enterprise_name="Công ty Không Hợp Lệ",
                tax_id="0109999888",
                license_type="SPACE_TOURISM_GALAXY",
                escrow_amount_vnd=1_000_000_000.0,
            )

    def test_rate_accommodation_compliant_5_star(self, engine: TourismEngine) -> None:
        res = engine.rate_accommodation(
            establishment_name="Vinpearl Landmark Luxury Resort",
            accommodation_type="RESORT",
            room_count=150,
            province="Kiên Giang",
            star_rating="5_STAR",
            has_swimming_pool=True,
            has_restaurant=True,
            has_conference_room=True,
        )
        assert res["status"] == "success"
        prof = res["rating_profile"]
        assert prof["star_count"] == 5
        assert prof["is_rating_compliant"] is True
        assert prof["status"] == "CERTIFIED"
        assert prof["eval_authority"] == "Cục Du lịch Quốc gia Việt Nam"

    def test_rate_accommodation_non_compliant(self, engine: TourismEngine) -> None:
        # 5 star requires 100 rooms and pool; provide only 40 rooms and no pool
        res = engine.rate_accommodation(
            establishment_name="Khách sạn Nhỏ Muốn 5 Sao",
            accommodation_type="HOTEL",
            room_count=40,
            province="Hà Nội",
            star_rating="5_STAR",
            has_swimming_pool=False,
            has_restaurant=True,
            has_conference_room=False,
        )
        assert res["status"] == "success"
        prof = res["rating_profile"]
        assert prof["is_rating_compliant"] is False
        assert prof["status"] == "NON_COMPLIANT"
        assert len(prof["deficiencies"]) >= 2

    def test_rate_accommodation_invalid_star(self, engine: TourismEngine) -> None:
        with pytest.raises(ValueError, match="Hạng sao không hợp lệ"):
            engine.rate_accommodation(
                establishment_name="Khách sạn 7 sao",
                accommodation_type="HOTEL",
                room_count=200,
                star_rating="7_STAR_ULTRA",
            )

    def test_issue_tour_guide_card_success(self, engine: TourismEngine) -> None:
        res = engine.issue_tour_guide_card(
            full_name="Đặng Thùy Dương",
            card_type="INTERNATIONAL",
            language="Tiếng Anh (IELTS 8.0) & Tiếng Pháp",
            qualification="Cử nhân Ngôn ngữ & Hướng dẫn Du lịch",
        )
        assert res["status"] == "success"
        prof = res["guide_profile"]
        assert prof["full_name"] == "Đặng Thùy Dương"
        assert prof["card_type"] == "INTERNATIONAL"
        assert prof["card_number"].startswith("HDV-INT-")
        assert prof["is_valid"] is True

    def test_issue_tour_guide_card_invalid_type(self, engine: TourismEngine) -> None:
        with pytest.raises(ValueError, match="Loại thẻ hướng dẫn viên không hợp lệ"):
            engine.issue_tour_guide_card(
                full_name="Nguyễn Văn A",
                card_type="SUPER_GUIDE",
                language="Tiếng Việt",
                qualification="Tốt nghiệp phổ thông",
            )

    def test_audit_adventure_safety_cleared(self, engine: TourismEngine) -> None:
        res = engine.audit_adventure_safety(
            tour_name="Thám hiểm Hang Én & Sơn Đoòng",
            adventure_type="CAVING_EXPEDITION",
            location="Quảng Bình",
            has_certified_instructor=True,
            has_safety_gear=True,
            has_rescue_plan=True,
            insurance_coverage_vnd=150_000_000.0,
        )
        assert res["status"] == "success"
        prof = res["safety_profile"]
        assert prof["is_safety_cleared"] is True
        assert "ĐỦ ĐIỀU KIỆN" in prof["action_verdict"]

    def test_audit_adventure_safety_suspended(self, engine: TourismEngine) -> None:
        # Missing rescue plan and low insurance
        res = engine.audit_adventure_safety(
            tour_name="Dù lượn Đèo Mã Pí Lèng mạo hiểm",
            adventure_type="PARAGLIDING",
            location="Hà Giang",
            has_certified_instructor=True,
            has_safety_gear=True,
            has_rescue_plan=False,
            insurance_coverage_vnd=50_000_000.0,
        )
        assert res["status"] == "success"
        prof = res["safety_profile"]
        assert prof["is_safety_cleared"] is False
        assert "ĐÌNH CHỈ" in prof["action_verdict"]

    def test_create_tour_booking_success(self, engine: TourismEngine) -> None:
        res = engine.create_tour_booking(
            tourist_name="Đoàn Du Khách Nhật Bản",
            nationality="Japan",
            tour_type="INBOUND",
            passengers_count=12,
            price_per_pax_vnd=15_000_000.0,
            start_date="2026-11-01",
            duration_days=7,
        )
        assert res["status"] == "success"
        prof = res["booking_profile"]
        assert prof["tourist_name"] == "Đoàn Du Khách Nhật Bản"
        assert prof["passengers_count"] == 12
        assert prof["price_per_pax_vnd"] == 15_000_000.0
        assert prof["total_revenue_vnd"] == 180_000_000.0
        assert prof["status"] == "CONFIRMED"

    def test_create_tour_booking_invalid_pax_or_price(self, engine: TourismEngine) -> None:
        with pytest.raises(ValueError, match="Số lượng khách du lịch phải ít nhất là 1"):
            engine.create_tour_booking(
                tourist_name="Khách Vô Danh",
                passengers_count=0,
                price_per_pax_vnd=1_000_000.0,
            )

        with pytest.raises(ValueError, match="Giá tour phải lớn hơn 0"):
            engine.create_tour_booking(
                tourist_name="Khách Miễn Phí",
                passengers_count=2,
                price_per_pax_vnd=-500.0,
            )

    def test_listing_apis(self, engine: TourismEngine) -> None:
        # Populate records
        engine.issue_travel_license("Công ty Lữ hành List 1", "0101112223", "DOMESTIC_TRAVEL", 100_000_000.0)
        engine.rate_accommodation("Khách sạn List 1", "HOTEL", 30, "Đà Nẵng", "2_STAR")
        engine.issue_tour_guide_card("HDV List 1", "DOMESTIC", "Tiếng Việt", "Trung cấp Lữ hành")
        engine.audit_adventure_safety("Tour Zipline List 1", "ZIPLINE_CANOPY", "Huế")
        engine.create_tour_booking("Booking List 1", "Vietnam", "DOMESTIC", 4, 5_000_000.0)

        # Test listing
        licenses = engine.list_licenses(limit=10)
        assert len(licenses) >= 1
        assert len(licenses.data) >= 1

        accommodations = engine.list_accommodations(limit=10)
        assert len(accommodations) >= 1

        guides = engine.list_tour_guides(limit=10)
        assert len(guides) >= 1

        audits = engine.list_adventure_audits(limit=10)
        assert len(audits) >= 1

        bookings = engine.list_bookings(limit=10)
        assert len(bookings) >= 1

    def test_get_status_metrics(self, engine: TourismEngine) -> None:
        engine.issue_travel_license("Công ty Status Demo", "0109998877", "DOMESTIC_TRAVEL", 100_000_000.0)
        engine.rate_accommodation("Resort Status Demo", "RESORT", 120, "Nha Trang", "5_STAR", has_swimming_pool=True)
        engine.issue_tour_guide_card("HDV Status Demo", "INTERNATIONAL", "Tiếng Anh", "Đại học")
        engine.audit_adventure_safety("Lặn biển Cù Lao Chàm", "SCUBA_DIVING", "Quảng Nam")
        engine.create_tour_booking("Booking Status Demo", "Australia", "INBOUND", 5, 10_000_000.0)

        status_data = engine.get_status()
        assert status_data["status"] == "online"
        metrics = status_data["metrics"]
        assert metrics["active_travel_licenses"] >= 1
        assert metrics["total_rated_accommodations"] >= 1
        assert metrics["certified_star_hotels"] >= 1
        assert metrics["certified_tour_guides"] >= 1
        assert metrics["adventure_safety_audits"] >= 1
        assert metrics["total_tour_bookings"] >= 1
        assert metrics["total_tourists_served"] >= 5
        assert metrics["total_tourism_revenue_vnd"] >= 50_000_000.0


# ---------------------------------------------------------------------------
# CLI Command Integration Tests
# ---------------------------------------------------------------------------


class TestTourismCLI:
    """Ensure all Typer CLI commands run cleanly in console and --json modes."""

    @pytest.fixture
    def app(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        return build_app()

    def test_tourism_help(self, app) -> None:
        result = runner.invoke(app, ["tourism", "--help"])
        assert result.exit_code == 0
        assert "Tourism — Vietnamese Tourism" in result.output

    def test_tourism_main_callback(self, app) -> None:
        res_con = runner.invoke(app, ["tourism"])
        assert res_con.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ DU LỊCH" in res_con.output

        res_json = runner.invoke(app, ["tourism", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"

    def test_tourism_license_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "tourism",
                "license",
                "Công ty Lữ hành Saigontourist CLI",
                "0300123999",
                "--type",
                "INTERNATIONAL_FULL",
                "--escrow",
                "500000000",
                "--bank",
                "VietinBank",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["license_profile"]["enterprise_name"] == "Công ty Lữ hành Saigontourist CLI"

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "tourism",
                "license",
                "Công ty Du lịch Nội Địa CLI",
                "0300123888",
                "--type",
                "DOMESTIC_TRAVEL",
                "--escrow",
                "100000000",
            ],
        )
        assert res_con.exit_code == 0
        assert "Giấy Phép Kinh Doanh Dịch Vụ Lữ Hành" in res_con.output

    def test_tourism_rating_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "tourism",
                "rating",
                "Mekong Riverside Grand Hotel",
                "--type",
                "HOTEL",
                "--rooms",
                "90",
                "--province",
                "Cần Thơ",
                "--star",
                "4_STAR",
                "--pool",
                "--restaurant",
                "--conference",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["rating_profile"]["is_rating_compliant"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "tourism",
                "rating",
                "Khách sạn Đà Nẵng Beach",
                "--type",
                "HOTEL",
                "--rooms",
                "25",
                "--province",
                "Đà Nẵng",
                "--star",
                "2_STAR",
            ],
        )
        assert res_con.exit_code == 0
        assert "Thẩm Định Xếp Hạng Sao Lưu Trú Du Lịch" in res_con.output

    def test_tourism_guide_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "tourism",
                "guide",
                "Trần Văn Hướng Dẫn",
                "--type",
                "INTERNATIONAL",
                "--language",
                "Tiếng Hàn (TOPIK 5)",
                "--qualification",
                "Đại học Ngoại ngữ",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["guide_profile"]["full_name"] == "Trần Văn Hướng Dẫn"

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "tourism",
                "guide",
                "Nguyễn Thị Điểm",
                "--type",
                "ON_SITE",
                "--language",
                "Tiếng Việt",
            ],
        )
        assert res_con.exit_code == 0
        assert "Thẻ Hành Nghề Hướng Dẫn Viên Du Lịch" in res_con.output

    def test_tourism_adventure_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "tourism",
                "adventure",
                "Tour Leo Núi Fansipan Đỉnh Cao",
                "--type",
                "ROCK_CLIMBING",
                "--location",
                "Lào Cai",
                "--instructor",
                "--gear",
                "--rescue",
                "--insurance",
                "120000000",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["safety_profile"]["is_safety_cleared"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "tourism",
                "adventure",
                "Chèo Thuyền Vượt Thác Sông Lô",
                "--type",
                "WHITE_WATER_RAFTING",
                "--location",
                "Tuyên Quang",
            ],
        )
        assert res_con.exit_code == 0
        assert "Thẩm Định An Toàn Du Lịch Mạo Hiểm" in res_con.output

    def test_tourism_booking_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "tourism",
                "booking",
                "Đoàn Khách Du Lịch Pháp",
                "--nationality",
                "France",
                "--type",
                "INBOUND",
                "--pax",
                "8",
                "--price",
                "12000000",
                "--date",
                "2026-10-20",
                "--duration",
                "5",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["booking_profile"]["total_revenue_vnd"] == 96_000_000.0

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "tourism",
                "booking",
                "Gia Đình Nguyễn Du",
                "--pax",
                "4",
                "--price",
                "5000000",
            ],
        )
        assert res_con.exit_code == 0
        assert "Xác Nhận Booking Tour Du Lịch" in res_con.output

    def test_tourism_list_cmd(self, app) -> None:
        # Prepopulate
        runner.invoke(app, ["tourism", "license", "Tour Co CLI", "0109990001", "--escrow", "100000000"])
        runner.invoke(app, ["tourism", "rating", "Hotel CLI", "--rooms", "30", "--star", "2_STAR"])
        runner.invoke(app, ["tourism", "guide", "HDV CLI", "--type", "DOMESTIC"])
        runner.invoke(app, ["tourism", "adventure", "Tour Adventure CLI"])
        runner.invoke(app, ["tourism", "booking", "Booking CLI", "--pax", "2", "--price", "3000000"])

        resources = ["licenses", "accommodations", "guides", "adventure", "bookings"]
        for r in resources:
            # JSON mode
            res_json = runner.invoke(app, ["tourism", "list", r, "--json"])
            assert res_json.exit_code == 0
            items = json.loads(res_json.output)
            assert isinstance(items, list)
            assert len(items) >= 1

            # Console mode
            res_con = runner.invoke(app, ["tourism", "list", r])
            assert res_con.exit_code == 0

    def test_tourism_status_cmd(self, app) -> None:
        res_con = runner.invoke(app, ["tourism", "status"])
        assert res_con.exit_code == 0
        assert "Báo Cáo Telemetry Ngành Du Lịch" in res_con.output

        res_json = runner.invoke(app, ["tourism", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"


# ---------------------------------------------------------------------------
# MCP Server Tool Parity Tests
# ---------------------------------------------------------------------------


class TestTourismMCP:
    """Ensure FastMCP and Pure-Python JSON-RPC 2.0 dual server parity for tourism tools."""

    def test_src_core_mcp_tourism_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. license
        res_lic = json.loads(server._handle_tourism_license(
            enterprise_name="Công ty Du lịch MCP Core",
            tax_id="0109988771",
            license_type="DOMESTIC_TRAVEL",
            escrow_amount_vnd=100000000.0,
        ))
        assert res_lic["status"] == "success"

        # 2. rating
        res_rt = json.loads(server._handle_tourism_rating(
            establishment_name="Khách sạn MCP Core",
            accommodation_type="HOTEL",
            room_count=60,
            star_rating="3_STAR",
        ))
        assert res_rt["status"] == "success"

        # 3. guide
        res_gd = json.loads(server._handle_tourism_guide(
            full_name="Nguyễn Văn Hướng Dẫn MCP",
            card_type="INTERNATIONAL",
            language="Tiếng Anh",
        ))
        assert res_gd["status"] == "success"

        # 4. adventure
        res_adv = json.loads(server._handle_tourism_adventure(
            tour_name="Thám hiểm Hang Động MCP",
            adventure_type="CAVING_EXPEDITION",
        ))
        assert res_adv["status"] == "success"

        # 5. booking
        res_bk = json.loads(server._handle_tourism_booking(
            tourist_name="Đoàn Du Khách MCP",
            nationality="Vietnam",
            tour_type="DOMESTIC",
            passengers_count=4,
            price_per_pax_vnd=5000000.0,
        ))
        assert res_bk["status"] == "success"

        # 6. list
        res_lst = json.loads(server._handle_tourism_list(resource="licenses"))
        assert isinstance(res_lst, list)

        # 7. status
        res_st = json.loads(server._handle_tourism_status())
        assert res_st["status"] == "online"

    def test_scripts_mcp_tourism_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from scripts.mcp_server import (
            handle_tourism_adventure,
            handle_tourism_booking,
            handle_tourism_guide,
            handle_tourism_license,
            handle_tourism_list,
            handle_tourism_rating,
            handle_tourism_status,
        )

        # 1. license
        res_lic = json.loads(handle_tourism_license({
            "enterprise_name": "Công ty Du lịch Script",
            "tax_id": "0109988772",
            "license_type": "INTERNATIONAL_INBOUND",
            "escrow_amount_vnd": 250000000.0,
        }))
        assert res_lic["status"] == "success"

        # 2. rating
        res_rt = json.loads(handle_tourism_rating({
            "establishment_name": "Khách sạn Script",
            "room_count": 85,
            "star_rating": "4_STAR",
            "has_swimming_pool": True,
            "has_restaurant": True,
            "has_conference_room": True,
        }))
        assert res_rt["status"] == "success"

        # 3. guide
        res_gd = json.loads(handle_tourism_guide({
            "full_name": "Trần Thị Hướng Dẫn Script",
            "card_type": "DOMESTIC",
        }))
        assert res_gd["status"] == "success"

        # 4. adventure
        res_adv = json.loads(handle_tourism_adventure({
            "tour_name": "Lặn Biển Script",
            "adventure_type": "SCUBA_DIVING",
        }))
        assert res_adv["status"] == "success"

        # 5. booking
        res_bk = json.loads(handle_tourism_booking({
            "tourist_name": "Đoàn Script",
            "passengers_count": 6,
            "price_per_pax_vnd": 8000000.0,
        }))
        assert res_bk["status"] == "success"

        # 6. list
        res_lst = json.loads(handle_tourism_list({"resource": "bookings"}))
        assert isinstance(res_lst, list)

        # 7. status
        res_st = json.loads(handle_tourism_status({}))
        assert res_st["status"] == "online"

    def test_scripts_mcp_core_tools_spec_and_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tourism_tools = [
            "mekong_tourism_license",
            "mekong_tourism_rating",
            "mekong_tourism_guide",
            "mekong_tourism_adventure",
            "mekong_tourism_booking",
            "mekong_tourism_list",
            "mekong_tourism_status",
        ]

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for tt in tourism_tools:
            assert tt in spec_names, f"Tool {tt} missing from CORE_TOOLS_SPEC"
            assert tt in CORE_HANDLERS, f"Tool {tt} missing from CORE_HANDLERS"
            bare_name = tt.replace("mekong_", "")
            assert bare_name in CORE_HANDLERS, f"Alias {bare_name} missing from CORE_HANDLERS"
