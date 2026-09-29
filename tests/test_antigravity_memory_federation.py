# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Memory Federation & Semantic Associative Recall Engine (Phase 16).

Covers:
1. MemoryFederationEngine: Multi-domain ingestion, hybrid BM25 / cosine similarity, knowledge graph traversal.
2. CLI Command Surfaces: mekong recall & mekong memory-mesh (index, stats, graph, --json).
3. Native MCP Tools: mekong_semantic_recall and mekong_knowledge_graph_query dual-engine parity.
4. AST Core Boundary Compliance: strict standard library only, zero vendor SDKs or ML frameworks in memory_federation.py.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.memory_federation import (
    FederatedMemoryItem,
    GraphEdge,
    GraphNode,
    MemoryFederationEngine,
    MemoryMeshStats,
    _compute_tf,
    _cosine_similarity,
    _tokenize,
    get_memory_federation_engine,
)


@pytest.fixture
def temp_db(tmp_path: Path):
    """Create a temporary SQLite database path for memory federation tests."""
    return tmp_path / "test_memory_mesh.db"


class TestMemoryFederationEngine:
    """Tests for hybrid search scoring, domain indexing, and graph traversal."""

    def test_tokenization_and_vector_math(self):
        tokens1 = _tokenize("Autonomous PEV engine for Mekong CLI")
        tokens2 = _tokenize("Autonomous PEV swarm engine orchestration")

        assert "autonomous" in tokens1
        assert "pev" in tokens1
        # Stop words stripped
        assert "for" not in tokens1

        tf1 = _compute_tf(tokens1)
        tf2 = _compute_tf(tokens2)
        assert len(tf1) > 0
        assert len(tf2) > 0

        sim = _cosine_similarity(tf1, tf2)
        assert 0.0 < sim <= 1.0

    def test_store_and_query_item(self, temp_db: Path):
        engine = MemoryFederationEngine(db_path=temp_db)
        item1 = engine.store_item(
            domain="patterns",
            title="AST Syntax Auto-Repair",
            content="Heuristically fixes missing colons and unclosed delimiters in Python code.",
            tags=["ast", "repair", "syntax"],
        )
        item2 = engine.store_item(
            domain="decisions",
            title="Consensus Protocol on Redis Caching",
            content="Adopted Redis caching layer with supermajority quorum approval.",
            tags=["consensus", "redis", "cache"],
        )

        # Query matches item 1
        results1 = engine.query("syntax auto repair in python", domain="all", limit=5)
        assert len(results1) >= 1
        assert results1[0].item_id == item1.item_id
        assert results1[0].relevance_score > 0.0

        # Query matches item 2
        results2 = engine.query("redis caching quorum", domain="all", limit=5)
        assert len(results2) >= 1
        assert results2[0].item_id == item2.item_id

    def test_domain_filtering(self, temp_db: Path):
        engine = MemoryFederationEngine(db_path=temp_db)
        engine.store_item(
            domain="patterns",
            title="Rollback Pattern",
            content="Restores files from SQLite snapshot storage upon corruption.",
        )
        engine.store_item(
            domain="decisions",
            title="Rollback Decision",
            content="Voted unanimous to require rollback checkpoints before dangerous migrations.",
        )

        # Filter strictly by domain 'decisions'
        dec_results = engine.query("rollback", domain="decisions", limit=5)
        assert all(r.domain == "decisions" for r in dec_results)

        # Filter strictly by domain 'patterns'
        pat_results = engine.query("rollback", domain="patterns", limit=5)
        assert all(r.domain == "patterns" for r in pat_results)

    def test_knowledge_graph_traversal(self, temp_db: Path):
        engine = MemoryFederationEngine(db_path=temp_db)
        f_node = engine.store_graph_node(name="consensus_bridge.py", node_type="file")
        c_node = engine.store_graph_node(name="ConsensusBridge", node_type="class")
        fn_node = engine.store_graph_node(name="create_vote", node_type="function")

        engine.store_graph_edge(source_id=f_node.node_id, target_id=c_node.node_id, relation="defines")
        engine.store_graph_edge(source_id=c_node.node_id, target_id=fn_node.node_id, relation="defines")

        # Query knowledge graph starting from ConsensusBridge
        graph = engine.query_knowledge_graph(entity="ConsensusBridge", depth=2)
        assert graph["total_nodes"] >= 2
        assert graph["total_edges"] >= 1
        node_names = {n["name"] for n in graph["nodes"]}
        assert "ConsensusBridge" in node_names

    def test_index_all_and_stats(self, temp_db: Path, tmp_path: Path):
        engine = MemoryFederationEngine(db_path=temp_db)

        # Create a mock project workspace with Python files
        mock_src = tmp_path / "src" / "core"
        mock_src.mkdir(parents=True, exist_ok=True)
        (mock_src / "sample_service.py").write_text(
            "class SampleService:\n    def process_data(self):\n        pass\n",
            encoding="utf-8",
        )

        stats = engine.index_all(project_root=tmp_path)
        assert stats.total_items > 0
        assert stats.total_nodes > 0
        assert "patterns" in stats.items_by_domain

        stats_queried = engine.get_stats()
        assert stats_queried.total_items == stats.total_items
        assert stats_queried.total_nodes == stats.total_nodes


class TestMemoryCli:
    """Tests for Typer CLI recall and memory-mesh commands."""

    def test_cli_recall_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["recall", "checkpoint rollback", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_cli_recall_interactive(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["recall", "checkpoint rollback"])
        assert result.exit_code == 0
        # Output should be informative
        assert "Semantic Associative Recall" in result.output or "No associative memory items found" in result.output

    def test_cli_memory_mesh_stats_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["memory-mesh", "stats", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_items" in data
        assert "items_by_domain" in data

    def test_cli_memory_mesh_index_json(self, tmp_path: Path):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["memory-mesh", "index", "--project-dir", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_items" in data

    def test_cli_memory_mesh_graph_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["memory-mesh", "graph", "ConsensusBridge", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "entity" in data
        assert "nodes" in data


class TestMcpToolsParity:
    """Tests for native MCP semantic recall and knowledge graph tools dual-engine parity."""

    def test_mcp_semantic_recall_fallback(self):
        from scripts.mcp_server import handle_semantic_recall
        raw = handle_semantic_recall({"query": "rate limit token bucket", "domain": "all"})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["data"]["query"] == "rate limit token bucket"
        assert "items" in data["data"]

    def test_mcp_knowledge_graph_query_fallback(self):
        from scripts.mcp_server import handle_knowledge_graph_query
        raw = handle_knowledge_graph_query({"entity": "consensus", "depth": 2})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["data"]["entity"] == "consensus"
        assert "nodes" in data["data"]

    def test_core_mcp_server_recall_and_graph(self):
        from src.core.mcp_server import MekongMcpServer
        server = MekongMcpServer()
        recall_raw = server._handle_semantic_recall({"query": "checkpoint", "domain": "all"})
        recall_data = json.loads(recall_raw)
        assert recall_data["ok"] is True

        graph_raw = server._handle_knowledge_graph_query({"entity": "bridge", "depth": 1})
        graph_data = json.loads(graph_raw)
        assert graph_data["ok"] is True


class TestAstCoreBoundary:
    """Verify standard-library-only rule for memory_federation.py."""

    FORBIDDEN_MODULES = {"anthropic", "openai", "requests", "httpx", "fastapi", "pydantic", "aiohttp", "numpy", "torch"}

    def test_pure_standard_library_imports(self):
        rel_path = "src/core/memory_federation.py"
        full_path = Path(__file__).resolve().parents[1] / rel_path
        assert full_path.exists(), f"File {rel_path} does not exist"

        tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden import '{alias.name}' found in {rel_path} (line {node.lineno})"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden from-import '{node.module}' found in {rel_path} (line {node.lineno})"
                    )
