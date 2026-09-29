# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Zalo Official Account (OA) Customer Messaging & Marketing Engine (Phase 41)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    CORE_TOOLS_SPEC,
    handle_zalo_broadcast,
    handle_zalo_caption,
    handle_zalo_followers,
    handle_zalo_send,
    handle_zalo_status,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
from src.core.zalo_engine import (
    CANONICAL_FOLLOWERS,
    TONE_TEMPLATES,
    ZaloEngine,
)

runner = CliRunner()


class TestZaloEngine:
    """Unit test battery for ZaloEngine core business logic."""

    @pytest.fixture
    def engine(self, tmp_path: Path) -> ZaloEngine:
        db_file = tmp_path / "test_zalo.db"
        return ZaloEngine(db_path=db_file)

    def test_engine_init_and_preseeded_followers(self, engine: ZaloEngine) -> None:
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_followers"] == len(CANONICAL_FOLLOWERS)
        assert status["total_messages"] == 0
        assert status["total_broadcasts"] == 0
        assert "vip" in status["segments"]
        assert "active" in status["segments"]

    def test_list_followers_all_and_filtered(self, engine: ZaloEngine) -> None:
        all_followers = engine.list_followers(segment="all")
        assert len(all_followers) == len(CANONICAL_FOLLOWERS)

        vip_followers = engine.list_followers(segment="vip")
        assert len(vip_followers) > 0
        assert all(f["segment"] == "vip" for f in vip_followers)

        active_followers = engine.list_followers(segment="active")
        assert len(active_followers) > 0
        assert all(f["segment"] == "active" for f in active_followers)

    def test_add_or_update_follower(self, engine: ZaloEngine) -> None:
        engine.add_follower(
            user_id="user-999",
            name="Nguyễn Văn Test",
            phone="0911222333",
            segment="enterprise",
        )
        followers = engine.list_followers(segment="enterprise")
        assert len(followers) == 1
        assert followers[0]["name"] == "Nguyễn Văn Test"

        # Update existing
        engine.add_follower(
            user_id="user-999",
            name="Nguyễn Văn Test Updated",
            phone="0911222333",
            segment="enterprise",
        )
        followers_updated = engine.list_followers(segment="enterprise")
        assert len(followers_updated) == 1
        assert followers_updated[0]["name"] == "Nguyễn Văn Test Updated"

    def test_send_message_direct(self, engine: ZaloEngine) -> None:
        res = engine.send_message(
            user_id="zalo-user-001",
            text="Kính gửi quý khách thông tin đơn hàng #MK-102",
        )
        assert res["ok"] is True
        assert res["status"] == "delivered"
        assert res["user_id"] == "zalo-user-001"
        assert "ZMSG-" in res["message_id"]

        status = engine.get_status()
        assert status["total_messages"] == 1

    def test_send_message_with_template(self, engine: ZaloEngine) -> None:
        res = engine.send_message(
            user_id="zalo-user-002",
            text="Lịch hẹn tư vấn vào 14:00 ngày mai.",
            template="consultation_reminder",
        )
        assert res["ok"] is True
        assert res["template"] == "consultation_reminder"

    def test_broadcast_campaign(self, engine: ZaloEngine) -> None:
        res = engine.broadcast_campaign(
            title="Khuyến mãi mùa thu",
            text="Giảm 20% cho gói dịch vụ Mekong AI Agency OS.",
            target_segment="all",
        )
        assert res["ok"] is True
        assert res["status"] == "completed"
        assert res["title"] == "Khuyến mãi mùa thu"
        assert res["sent_count"] == len(CANONICAL_FOLLOWERS)
        assert res["delivered_count"] > 0
        assert res["read_count"] > 0
        assert "ZBC-" in res["broadcast_id"]

        status = engine.get_status()
        assert status["total_broadcasts"] == 1
        assert len(status["recent_broadcasts"]) == 1

    def test_generate_caption_tones(self, engine: ZaloEngine) -> None:
        tones = ["vui_ve", "chuyen_nghiep", "sang_tao", "khuyen_mai", "binh_phap"]
        for tone in tones:
            res = engine.generate_caption(topic="Trà xanh OCOP", tone=tone)
            assert res["ok"] is True
            assert res["topic"] == "Trà xanh OCOP"
            assert res["tone"] == tone
            assert len(res["caption"]) > 0
            assert len(res["hashtags"]) >= 3
            assert "#ZaloOA" in res["hashtags"]

    def test_generate_caption_unknown_tone_fallback(self, engine: ZaloEngine) -> None:
        res = engine.generate_caption(topic="Bất động sản", tone="unknown_tone")
        assert res["ok"] is True
        assert res["tone"] == "vui_ve"


class TestZaloCli:
    """CLI test battery for mekong zalo-oa command hierarchy."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_zalo_overview_console(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa"])
        assert res.exit_code == 0
        assert "ZALO OFFICIAL ACCOUNT" in res.output or "Followers" in res.output

    def test_zalo_overview_json(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert data["total_followers"] >= 5

    def test_zalo_caption_json(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "caption", "Cà phê Robusta Đắk Lắk", "--tone", "sang_tao", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["tone"] == "sang_tao"
        assert "Cà phê Robusta Đắk Lắk" in data["caption"]

    def test_zalo_send_mock(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "send", "zalo-user-001", "Chào quý khách", "--mock"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["user_id"] == "zalo-user-001"

    def test_zalo_send_mock_json(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "send", "zalo-user-001", "Thông báo xác nhận", "--mock", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["status"] == "delivered"

    def test_zalo_broadcast_mock(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "broadcast", "Thông báo bảo trì hệ thống", "--title", "Bảo trì", "--mock"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["status"] == "completed"

    def test_zalo_followers_mock(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "followers", "--mock"])
        assert res.exit_code == 0
        assert "Tổng followers:" in res.output

    def test_zalo_post_mock(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "post", "Sản phẩm mới", "Cập nhật sản phẩm tuần này", "--mock"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["title"] == "Sản phẩm mới"

    def test_zalo_status_json(self, app) -> None:
        res = runner.invoke(app, ["zalo-oa", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "total_followers" in data

    def test_zalo_send_live_without_token_exits_1(self, app, monkeypatch) -> None:
        monkeypatch.delenv("ZALO_OA_ACCESS_TOKEN", raising=False)
        res = runner.invoke(app, ["zalo-oa", "send", "zalo-user-001", "Direct msg"])
        assert res.exit_code == 1
        assert "Thiếu ZALO_OA_ACCESS_TOKEN" in res.output


class TestZaloMcpParity:
    """Test suite ensuring parity across FastMCP and pure-Python JSON-RPC 2.0 stdio engines."""

    def test_mcp_spec_registration(self) -> None:
        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        assert "mekong_zalo_send" in names
        assert "mekong_zalo_broadcast" in names
        assert "mekong_zalo_followers" in names
        assert "mekong_zalo_caption" in names
        assert "mekong_zalo_status" in names

    def test_script_mcp_handlers(self) -> None:
        # Status
        status_raw = handle_zalo_status({})
        status = json.loads(status_raw)
        assert status["status"] == "operational"

        # Caption
        cap_raw = handle_zalo_caption({"topic": "OCOP Gạo ST25", "tone": "binh_phap"})
        cap = json.loads(cap_raw)
        assert cap["ok"] is True
        assert cap["tone"] == "binh_phap"

        # Send
        send_raw = handle_zalo_send({"user_id": "zalo-user-003", "message": "Test via MCP"})
        send_data = json.loads(send_raw)
        assert send_data["ok"] is True

        # Broadcast
        bc_raw = handle_zalo_broadcast({"message": "Thông báo khuyến mãi", "title": "MCP Campaign"})
        bc = json.loads(bc_raw)
        assert bc["ok"] is True

        # Followers
        fol_raw = handle_zalo_followers({"segment": "all", "limit": 10})
        fol = json.loads(fol_raw)
        assert fol["total"] >= 5

    def test_core_mcp_server_handlers_and_aliases(self) -> None:
        server = MekongMcpServer(name="test-server")

        # Handlers
        status_res = json.loads(server._handle_zalo_status())
        assert status_res["status"] == "operational"

        cap_res = json.loads(server._handle_zalo_caption(topic="Trái cây sấy", tone="khuyen_mai"))
        assert cap_res["ok"] is True

        send_res = json.loads(server._handle_zalo_send(user_id="zalo-user-004", message="Hello MCP"))
        assert send_res["ok"] is True

        # Aliases
        assert server._handle_mekong_zalo_send == server._handle_zalo_send
        assert server._handle_mekong_zalo_broadcast == server._handle_zalo_broadcast
        assert server._handle_mekong_zalo_followers == server._handle_zalo_followers
        assert server._handle_mekong_zalo_caption == server._handle_zalo_caption
        assert server._handle_mekong_zalo_status == server._handle_zalo_status


class TestZaloCoreBoundary:
    """Ensure src/core/zalo_engine.py is pure Python standard library with zero external HTTP or vendor SDK imports."""

    def test_core_ast_imports(self) -> None:
        engine_path = Path("src/core/zalo_engine.py")
        assert engine_path.exists()

        tree = ast.parse(engine_path.read_text(encoding="utf-8"))
        disallowed_prefixes = (
            "requests",
            "urllib3",
            "httpx",
            "aiohttp",
            "zalo",
            "zalosdk",
            "flask",
            "fastapi",
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for disallowed in disallowed_prefixes:
                        assert not alias.name.startswith(disallowed), (
                            f"Disallowed import '{alias.name}' in pure core engine {engine_path}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for disallowed in disallowed_prefixes:
                    assert not module.startswith(disallowed), (
                        f"Disallowed from-import '{module}' in pure core engine {engine_path}"
                    )
