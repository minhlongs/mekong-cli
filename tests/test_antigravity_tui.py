# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_tui.py — Comprehensive Test Suite for Phase 10 TUI & Command Palette.

Covers:
1. Catalog indexing across skills, subagents, and CLI commands.
2. Bilingual (Vietnamese accented, unaccented, English) fuzzy search and scoring.
3. Category inference and filtering.
4. TUI dashboard telemetry aggregation and AGI subsystem health verification.
5. CLI command invocation with JSON output (mekong palette, mekong tui).
6. MCP tool handlers (FastMCP and fallback JSON-RPC parity).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from src.core.palette_bridge import (
    PaletteBridge,
    PaletteItem,
    SearchResult,
    remove_accents,
)
from scripts.mcp_server import (
    CORE_HANDLERS,
    CORE_TOOLS_SPEC,
    handle_palette_search,
    handle_tui_dashboard_status,
)


class TestAccentNormalization:
    """Test Vietnamese accent normalization logic."""

    def test_strip_common_accents(self):
        assert remove_accents("kế hoạch") == "ke hoach"
        assert remove_accents("sửa lỗi") == "sua loi"
        assert remove_accents("triển khai") == "trien khai"
        assert remove_accents("báo cáo tài chính") == "bao cao tai chinh"

    def test_handle_d_stroke(self):
        assert remove_accents("đặc tả") == "dac ta"
        assert remove_accents("Đơn hàng") == "don hang"
        assert remove_accents("điều phối") == "dieu phoi"

    def test_empty_and_ascii(self):
        assert remove_accents("") == ""
        assert remove_accents("cook") == "cook"
        assert remove_accents("debug-123") == "debug-123"


class TestPaletteIndexing:
    """Test indexing of skills, subagents, and CLI commands."""

    @pytest.fixture(scope="class")
    def bridge(self) -> PaletteBridge:
        pb = PaletteBridge()
        pb.refresh_index()
        return pb

    def test_indexing_counts(self, bridge: PaletteBridge):
        items = bridge._items
        # Must index canonical commands, 230+ skills, and 25 subagents
        assert len(items) >= 200, f"Expected >= 200 items, got {len(items)}"

        types = {it.item_type for it in items.values()}
        assert "command" in types
        assert "skill" in types
        assert "agent" in types

    def test_item_fields_complete(self, bridge: PaletteBridge):
        for item in bridge._items.values():
            assert item.id, "PaletteItem id must not be empty"
            assert item.name, "PaletteItem name must not be empty"
            assert item.command_syntax, "PaletteItem command_syntax must not be empty"
            assert item.category in [
                "strategy",
                "business",
                "product",
                "engineering",
                "operations",
                "vietnam",
                "general",
            ], f"Invalid category {item.category} for item {item.name}"
            assert isinstance(item.keywords, list)
            assert item.icon, "Icon must not be empty"

    def test_category_distribution(self, bridge: PaletteBridge):
        summary = bridge.get_tui_dashboard_summary()
        categories = summary["catalog"]["categories"]
        assert "engineering" in categories
        assert "product" in categories
        assert "strategy" in categories
        assert "vietnam" in categories
        assert "operations" in categories


class TestBilingualFuzzySearch:
    """Test search ranking with Vietnamese accented, unaccented, and English inputs."""

    @pytest.fixture(scope="class")
    def bridge(self) -> PaletteBridge:
        pb = PaletteBridge()
        pb.refresh_index()
        return pb

    def test_exact_command_search(self, bridge: PaletteBridge):
        res = bridge.search("cook", limit=5)
        assert len(res) > 0
        assert res[0].item.name == "cook"
        assert res[0].score == 1.0
        assert res[0].matched_by == "exact_name"

    def test_accented_vietnamese_search(self, bridge: PaletteBridge):
        # "sửa lỗi" should find "debug"
        res_fix = bridge.search("sửa lỗi", limit=5)
        assert len(res_fix) > 0
        names = [r.item.name for r in res_fix]
        assert "debug" in names
        assert res_fix[0].score >= 0.90

        # "kế hoạch" should find "plan"
        res_plan = bridge.search("kế hoạch", limit=5)
        assert len(res_plan) > 0
        names_plan = [r.item.name for r in res_plan]
        assert "plan" in names_plan
        assert res_plan[0].score >= 0.90

    def test_unaccented_vietnamese_search(self, bridge: PaletteBridge):
        # "ke hoach" without accents should still match "plan"
        res = bridge.search("ke hoach", limit=5)
        assert len(res) > 0
        names = [r.item.name for r in res]
        assert "plan" in names
        assert res[0].score >= 0.90

        # "sua loi" without accents should still match "debug"
        res_sua = bridge.search("sua loi", limit=5)
        assert len(res_sua) > 0
        names_sua = [r.item.name for r in res_sua]
        assert "debug" in names_sua

    def test_vietnam_hub_search(self, bridge: PaletteBridge):
        res_tax = bridge.search("thue", limit=5)
        assert any(r.item.name == "thue" for r in res_tax)

        res_acc = bridge.search("kế toán", limit=5)
        assert any(r.item.name == "ke-toan" for r in res_acc)

        res_zalo = bridge.search("zalo", limit=5)
        assert any("zalo" in r.item.name for r in res_zalo)

    def test_category_filter(self, bridge: PaletteBridge):
        res_eng = bridge.search(None, category="engineering", limit=20)
        assert all(r.item.category == "engineering" for r in res_eng)

        res_vn = bridge.search(None, category="vietnam", limit=20)
        assert all(r.item.category == "vietnam" for r in res_vn)

    def test_empty_query_returns_catalog(self, bridge: PaletteBridge):
        res = bridge.search("", limit=10)
        assert len(res) == 10
        # Commands should rank top in empty query
        assert res[0].item.item_type in ["command", "group"]

    def test_nonsense_query_returns_empty_or_low_score(self, bridge: PaletteBridge):
        res = bridge.search("xyzqzz999nonexistentword", limit=5)
        assert len(res) == 0


class TestTuiDashboardTelemetry:
    """Test dashboard summary aggregation and subsystem checks."""

    def test_dashboard_summary_health(self):
        bridge = PaletteBridge()
        summary = bridge.get_tui_dashboard_summary(detailed=True)

        assert summary["ok"] is True
        assert summary["version"] == "v2.0.0-agi"
        assert summary["agi_health"] in ["healthy", "degraded"]
        assert "subsystems_online" in summary
        assert "catalog" in summary
        assert summary["catalog"]["total_items"] >= 200
        assert "evals" in summary
        assert "checkpoints_count" in summary
        assert "goals" in summary

        # 9 AGI Subsystems detail
        subsystems = summary.get("subsystems_detail", {})
        assert len(subsystems) == 9
        assert subsystems["NLU"] is True
        assert subsystems["Memory"] is True
        assert subsystems["Reflection"] is True
        assert subsystems["VectorMemory"] is True


class TestCliCommands:
    """Test CLI execution for mekong palette and mekong tui."""

    def test_cli_palette_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "palette", "cook", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"CLI palette failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["query"] == "cook"
        assert len(data["matches"]) > 0
        assert data["matches"][0]["name"] == "cook"

    def test_cli_palette_vietnamese_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "palette", "sửa lỗi", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"CLI palette failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert any(m["name"] == "debug" for m in data["matches"])

    def test_cli_tui_dashboard_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "src.main", "tui", "--dashboard", "--json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"CLI tui dashboard failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["version"] == "v2.0.0-agi"
        assert data["catalog"]["total_items"] >= 200


class TestMcpToolsParity:
    """Test MCP tool specifications, handlers, and FastMCP registration."""

    def test_palette_search_handler(self):
        res_raw = handle_palette_search({"query": "kế hoạch", "limit": 3})
        res = json.loads(res_raw)
        assert res["ok"] is True
        assert res["total_matches"] > 0
        names = [m["name"] for m in res["matches"]]
        assert "plan" in names

    def test_tui_dashboard_status_handler(self):
        res_raw = handle_tui_dashboard_status({"detailed": True})
        res = json.loads(res_raw)
        assert res["ok"] is True
        assert res["agi_health"] in ["healthy", "degraded"]
        assert "subsystems_online" in res
        assert "catalog" in res

    def test_tool_specs_registered(self):
        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        assert "mekong_palette_search" in spec_names
        assert "mekong_tui_dashboard_status" in spec_names

    def test_handlers_registered(self):
        assert "mekong_palette_search" in CORE_HANDLERS
        assert "mekong_tui_dashboard_status" in CORE_HANDLERS
