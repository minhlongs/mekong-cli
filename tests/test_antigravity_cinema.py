"""
Test Suite for Vietnamese Cinema, Film Production, Age Classification & Censorship Suite (Phase 85).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- CinemaEngine domain logic (age ratings P/K/T13/T16/T18/C, GPHPP permits, screen quotas >= 10%, OTT streaming post-audit, 24h takedown).
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
from src.core.cinema_engine import CinemaEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestCinemaBoundary:
    """Verifies that cinema_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "cinema_engine.py")
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


class TestCinemaEngine:
    """Tests core business logic of CinemaEngine."""

    def test_classify_film_p_rating(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.classify_film("Dế Mèn Phiêu Lưu Ký", violence_level=0, nudity_level=0, horror_level=0)
        assert res["rating"] == "P"
        assert res["is_prohibited"] is False
        assert len(res["warning_tags"]) == 0

    def test_classify_film_k_rating(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.classify_film("Gia Đình Siêu Nhân Trẻ", violence_level=1, horror_level=1)
        assert res["rating"] == "K"
        assert res["is_prohibited"] is False

    def test_classify_film_t13_rating(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.classify_film("Thám Tử Học Đường", violence_level=2, profanity_level=1)
        assert res["rating"] == "T13"
        assert "Cảnh báo bạo lực" in res["warning_tags"][0]

    def test_classify_film_t16_rating(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.classify_film("Biệt Đội Săn Bắt Cướp", violence_level=3, profanity_level=2)
        assert res["rating"] == "T16"

    def test_classify_film_t18_rating(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.classify_film("Góc Tối Sài Gòn", violence_level=4, nudity_level=3)
        assert res["rating"] == "T18"

    def test_classify_film_extreme_banned(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.classify_film("Hành Vi Cực Đoan", violence_level=5)
        assert res["rating"] == "C"
        assert res["is_prohibited"] is True

    def test_classify_film_sovereign_violation(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.classify_film("Phim Xuyên Tạc Lãnh Thổ", violence_level=0, sovereign_violation=True)
        assert res["rating"] == "C"
        assert res["is_prohibited"] is True
        assert any("CHỦ QUYỀN LÃNH THỔ" in tag for tag in res["warning_tags"])

    def test_issue_distribution_permit_success(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.issue_distribution_permit(
            film_title="Hành Trình Mekong",
            producer_name="Mekong Film Studios",
            rating="T16",
            duration_min=110,
        )
        assert res["permit_code"].startswith("GPHPP-")
        assert res["status"] == "ISSUED"
        assert res["rating"] == "T16"

    def test_issue_distribution_permit_banned_film_error(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Không thể cấp Giấy phép"):
            engine.issue_distribution_permit(
                film_title="Phim Cấm Chiếu",
                producer_name="Studio X",
                rating="C",
                duration_min=90,
            )

    def test_audit_cinema_screen_quota_compliant(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.audit_cinema_screen_quota(
            cinema_name="CGV Landmark 81",
            total_screenings=500,
            vn_screenings=65,  # 13% >= 10%
            prime_time_total=150,
            prime_time_vn=25,  # 16.7% >= 10%
        )
        assert res["status"] == "COMPLIANT"
        assert res["shortfall_screenings"] == 0
        assert len(res["deficiencies"]) == 0

    def test_audit_cinema_screen_quota_deficient(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.audit_cinema_screen_quota(
            cinema_name="Rạp Quốc Tế Beta",
            total_screenings=500,
            vn_screenings=35,  # 7% < 10%
        )
        assert res["status"] == "NON_COMPLIANT"
        assert res["shortfall_screenings"] == 15  # Need 50, have 35 -> shortfall 15
        assert len(res["deficiencies"]) >= 1

    def test_audit_cinema_screen_quota_invalid_input(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="phải lớn hơn 0"):
            engine.audit_cinema_screen_quota("Rạp Rỗng", 0, 0)

    def test_verify_ott_film_compliance_ok(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.verify_ott_film_compliance(
            platform="Netflix",
            film_id="OTT-101",
            film_title="Đêm Mekong",
            rating="T16",
            has_warning_banner=True,
            sovereign_clean=True,
        )
        assert res["status"] == "COMPLIANT"
        assert res["sanction_risk"] == "None"

    def test_verify_ott_film_missing_warning(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.verify_ott_film_compliance(
            platform="VieON",
            film_id="OTT-102",
            film_title="Phim Hành Động 18+",
            rating="T18",
            has_warning_banner=False,
            sovereign_clean=True,
        )
        assert res["status"] == "NON_COMPLIANT"
        assert "40M - 50M" in res["sanction_risk"]

    def test_verify_ott_film_sovereignty_breach(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        res = engine.verify_ott_film_compliance(
            platform="FPT Play",
            film_id="OTT-103",
            film_title="Bản Đồ Tranh Chấp",
            rating="T13",
            has_warning_banner=True,
            sovereign_clean=False,
        )
        assert res["status"] == "NON_COMPLIANT"
        assert "80M - 100M" in res["sanction_risk"]

    def test_track_ott_takedown_on_time(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        notice = "2026-09-29T06:00:00"
        resolved = "2026-09-29T20:00:00"  # 14 hours <= 24h
        res = engine.track_ott_takedown(
            platform="Netflix",
            film_id="MOV-9988",
            reason="Hình ảnh đường lưỡi bò phi pháp",
            notice_timestamp=notice,
            resolved_timestamp=resolved,
        )
        assert res["status"] == "COMPLIANT_REMOVED_ON_TIME"
        assert res["hours_elapsed"] == 14.0

    def test_track_ott_takedown_overdue(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        notice = "2026-09-27T08:00:00"
        resolved = "2026-09-29T10:00:00"  # 50 hours > 24h
        res = engine.track_ott_takedown(
            platform="Galaxy Play",
            film_id="MOV-9989",
            reason="Nội dung xuyên tạc lịch sử",
            notice_timestamp=notice,
            resolved_timestamp=resolved,
        )
        assert res["status"] == "VIOLATION_TAKEDOWN_OVERDUE"

    def test_list_records_and_status(self, temp_db):
        engine = CinemaEngine(db_path=temp_db)
        engine.classify_film("Phim Thử Nghiệm", 1, 1, 1)
        engine.issue_distribution_permit("Phim Đã Cấp Phép", "Hãng Phim A", "T13", 100)
        engine.audit_cinema_screen_quota("Rạp Chiếu A", 100, 15)

        cls = engine.list_records("classifications")
        permits = engine.list_records("permits")
        quotas = engine.list_records("quotas")

        assert len(cls) >= 1
        assert len(permits) >= 1
        assert len(quotas) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_films_classified"] >= 1


class TestCinemaCLI:
    """Tests CLI commands using Typer CliRunner."""

    def setup_method(self):
        self.app = build_app()
        self.runner = CliRunner()

    def test_cli_help(self):
        result = self.runner.invoke(self.app, ["cinema", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Cinema" in result.output

    def test_cli_status_json(self):
        result = self.runner.invoke(self.app, ["cinema", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"

    def test_cli_classify_json(self):
        result = self.runner.invoke(
            self.app,
            ["cinema", "classify", "Đất Rừng Phương Nam", "--violence", "2", "--nudity", "0", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["rating"] == "T13"

    def test_cli_permit_json(self):
        result = self.runner.invoke(
            self.app,
            ["cinema", "permit", "Mưa Trên Cánh Đồng", "--producer", "Hãng Phim 1", "--rating", "T16", "--duration", "105", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ISSUED"

    def test_cli_quota_json(self):
        result = self.runner.invoke(
            self.app,
            ["cinema", "quota", "BHD Star Cineplex", "--total", "400", "--vn", "55", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "COMPLIANT"

    def test_cli_ott_json(self):
        result = self.runner.invoke(
            self.app,
            ["cinema", "ott", "Netflix", "--film-id", "NF-1234", "--title", "Ký Ức Mekong", "--rating", "T16", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "COMPLIANT"

    def test_cli_takedown_json(self):
        result = self.runner.invoke(
            self.app,
            ["cinema", "takedown", "Netflix", "--film-id", "NF-1234", "--reason", "Vi phạm chủ quyền", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["takedown_id"].startswith("TD-FILM-")

    def test_cli_list_json(self):
        result = self.runner.invoke(self.app, ["cinema", "list", "classifications", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


class TestCinemaMCP:
    """Tests FastMCP and JSON-RPC 2.0 dual engine parity for cinema tools."""

    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_cinema_classify,
            handle_cinema_permit,
            handle_cinema_quota,
            handle_cinema_ott,
            handle_cinema_takedown,
            handle_cinema_list,
            handle_cinema_status,
        )

        cls_res = json.loads(handle_cinema_classify({"title": "Phim Mẫu", "violence_level": 1}))
        assert cls_res["rating"] == "K"

        pm_res = json.loads(handle_cinema_permit({"film_title": "Phim Cấp Phép", "rating": "T13"}))
        assert pm_res["status"] == "ISSUED"

        qt_res = json.loads(handle_cinema_quota({"cinema_name": "Lotte Cinema", "total_screenings": 200, "vn_screenings": 30}))
        assert qt_res["status"] == "COMPLIANT"

        ott_res = json.loads(handle_cinema_ott({"platform": "VieON", "film_id": "V-001"}))
        assert "record_id" in ott_res

        td_res = json.loads(handle_cinema_takedown({"platform": "Netflix", "film_id": "V-001"}))
        assert "takedown_id" in td_res

        ls_res = json.loads(handle_cinema_list({"category": "classifications"}))
        assert isinstance(ls_res, list)

        st_res = json.loads(handle_cinema_status({}))
        assert st_res["status"] == "HEALTHY"

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        cls = json.loads(server._handle_cinema_classify(title="Phim Core Test", violence_level=0))
        assert cls["rating"] == "P"

        status = json.loads(server._handle_cinema_status())
        assert status["status"] == "HEALTHY"
