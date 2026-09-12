"""Tests for ALGO 8 — Agent Dispatcher."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.core.agent_dispatcher import (
    DEFAULT_PROMPTS,
    build_message_chain,
    inject_codebase_context,
    inject_metrics_context,
    load_agent_prompt,
    _load_matching_hub,
    _memory_context_for,
    _duplicate_warning,
)
from src.core.memory_store import MemoryEntry


class TestDefaultPrompts:
    def test_all_roles_have_prompts(self):
        expected_roles = ["cto", "editor", "analyst", "cfo", "cmo", "devops", "pm", "support"]
        for role in expected_roles:
            assert role in DEFAULT_PROMPTS
            assert len(DEFAULT_PROMPTS[role]) > 10

    def test_cto_mentions_code(self):
        assert "code" in DEFAULT_PROMPTS["cto"].lower()


class TestLoadAgentPrompt:
    def test_known_role_returns_prompt(self):
        prompt = load_agent_prompt("cto")
        assert len(prompt) > 0
        assert "CTO" in prompt

    def test_unknown_role_returns_generic(self):
        prompt = load_agent_prompt("unknown_role_xyz")
        assert "unknown_role_xyz" in prompt

    def test_all_defaults_loadable(self):
        for role in DEFAULT_PROMPTS:
            prompt = load_agent_prompt(role)
            assert len(prompt) > 0


class TestInjectCodebaseContext:
    def test_adds_context_to_last_message(self):
        messages = [{"role": "user", "content": "fix the bug"}]
        result = inject_codebase_context(messages, "fix the bug")
        assert "[Context:" in result[-1]["content"]
        assert "fix the bug" in result[-1]["content"]

    def test_preserves_original_messages(self):
        messages = [{"role": "user", "content": "hello"}]
        inject_codebase_context(messages, "hello")
        # Original should not be mutated
        assert "[Context:" not in messages[0]["content"]

    def test_empty_messages(self):
        result = inject_codebase_context([], "goal")
        assert result == []


class TestInjectMetricsContext:
    def test_adds_tenant_context(self):
        messages = [{"role": "user", "content": "analyze revenue"}]
        result = inject_metrics_context(messages, "tenant-123")
        assert "tenant-123" in result[-1]["content"]

    def test_preserves_original(self):
        messages = [{"role": "user", "content": "analyze"}]
        inject_metrics_context(messages, "t1")
        assert "[Context:" not in messages[0]["content"]


class TestBuildMessageChain:
    def test_returns_messages_and_prompt(self):
        messages, prompt, _tools = build_message_chain(
            goal="write tests",
            agent_role="cto",
            domain="code",
        )
        assert len(messages) > 0
        assert len(prompt) > 0

    def test_code_domain_injects_context(self):
        messages, _, _ = build_message_chain(
            goal="fix bug",
            agent_role="cto",
            domain="code",
        )
        assert "[Context:" in messages[-1]["content"]

    def test_analysis_domain_injects_metrics(self):
        messages, _, _ = build_message_chain(
            goal="analyze data",
            agent_role="analyst",
            domain="analysis",
            tenant_id="t-42",
        )
        assert "t-42" in messages[-1]["content"]

    def test_other_domain_no_injection(self):
        messages, _, _ = build_message_chain(
            goal="write blog post",
            agent_role="editor",
            domain="creative",
        )
        assert "[Context:" not in messages[-1]["content"]
        assert messages[-1]["content"] == "write blog post"

    def test_with_agent_and_tool_registry(self):
        mock_agent = MagicMock()
        mock_tool = MagicMock()
        mock_tool.name = "bash"
        mock_registry = MagicMock()
        mock_registry.list_for_agent.return_value = [mock_tool]

        messages, prompt, tools = build_message_chain(
            goal="run check",
            agent_role="devops",
            domain="ops",
            agent=mock_agent,
            tool_registry=mock_registry,
            inject_memory=False,
        )
        assert tools == ["bash"]
        mock_registry.list_for_agent.assert_called_once_with(mock_agent)

    def test_inject_memory_and_duplicate_warning(self):
        with patch("src.core.agent_dispatcher._memory_context_for", return_value=("[memory block]", True)), \
             patch("src.core.agent_dispatcher._duplicate_warning", return_value="[duplicate warning]"):
            messages, prompt, tools = build_message_chain(
                goal="fix parser error",
                agent_role="cto",
                domain="code",
                inject_memory=True,
            )
            assert any("[memory block]" in m.get("content", "") for m in messages if m["role"] == "user")
            assert any(m["role"] == "assistant" and "[duplicate warning]" in m.get("content", "") for m in messages)


class TestHubLoadingAndMemoryHelpers:
    def test_load_matching_hub_unknown_role(self):
        assert _load_matching_hub("nonexistent_role") == ""

    def test_load_matching_hub_nonexistent_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.agent_dispatcher.HUBS_DIR", tmp_path)
        assert _load_matching_hub("cto") == ""

    def test_load_matching_hub_frontmatter_stripped(self, tmp_path, monkeypatch):
        hubs_dir = tmp_path / "hubs"
        hubs_dir.mkdir()
        hub_file = hubs_dir / "engineering-hub.md"
        hub_file.write_text("---\ntitle: Engineering\n---\nActual Hub Content", encoding="utf-8")
        monkeypatch.setattr("src.core.agent_dispatcher.HUBS_DIR", hubs_dir)

        content = _load_matching_hub("cto")
        assert content == "Actual Hub Content"

    def test_load_matching_hub_oserror(self, tmp_path, monkeypatch):
        hubs_dir = tmp_path / "hubs"
        hubs_dir.mkdir()
        hub_file = hubs_dir / "engineering-hub.md"
        hub_file.write_text("content", encoding="utf-8")
        monkeypatch.setattr("src.core.agent_dispatcher.HUBS_DIR", hubs_dir)

        def mock_read(*args, **kwargs):
            raise OSError("Hub read failure")

        monkeypatch.setattr("pathlib.Path.read_text", mock_read)
        assert _load_matching_hub("cto") == ""

    def test_load_agent_prompt_include_hub_false(self):
        prompt = load_agent_prompt("cto", include_hub=False)
        assert len(prompt) > 0
        assert "Domain Expertise (from Hub)" not in prompt

    def test_load_agent_prompt_with_hub_enrichment(self, monkeypatch):
        monkeypatch.setattr("src.core.agent_dispatcher._load_matching_hub", lambda role: "Hub Knowledge Here")
        prompt = load_agent_prompt("cto", include_hub=True)
        assert "## Domain Expertise (from Hub)" in prompt
        assert "Hub Knowledge Here" in prompt

    def test_load_agent_prompt_from_md_file(self, tmp_path, monkeypatch):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        agent_md = agents_dir / "custom.md"
        agent_md.write_text("Custom Agent Identity Prompt", encoding="utf-8")
        monkeypatch.setattr("src.core.agent_dispatcher.AGENTS_DIR", agents_dir)

        prompt = load_agent_prompt("custom", include_hub=False)
        assert prompt == "Custom Agent Identity Prompt"

    def test_load_agent_prompt_from_md_file_oserror(self, tmp_path, monkeypatch):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        agent_md = agents_dir / "custom.md"
        agent_md.write_text("Custom Content", encoding="utf-8")
        monkeypatch.setattr("src.core.agent_dispatcher.AGENTS_DIR", agents_dir)

        def mock_read(*args, **kwargs):
            raise OSError("Agent read failure")

        monkeypatch.setattr("pathlib.Path.read_text", mock_read)
        prompt = load_agent_prompt("custom", include_hub=False)
        assert "helpful custom agent" in prompt

    def test_memory_context_for_hits(self, monkeypatch):
        h1 = MemoryEntry(agent="cto", action="act1", outcome="ok", tags=["t1"])
        h2 = MemoryEntry(agent="cfo", action="act2", outcome="ok", tags=[])

        mock_store = MagicMock()
        mock_store.search.return_value = [h1, h2]
        monkeypatch.setattr("src.core.memory_store.MemoryStore", lambda **kw: mock_store)

        block, found = _memory_context_for("goal", "cto")
        assert found is True
        assert "[memory: Step 8 Phase B — 2 similar past action(s) retrieved]" in block
        assert "act1 | tags=t1" in block
        assert "act2" in block

    def test_memory_context_for_empty(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.search.return_value = []
        monkeypatch.setattr("src.core.memory_store.MemoryStore", lambda **kw: mock_store)

        block, found = _memory_context_for("goal", "cto")
        assert found is False
        assert block == ""

    def test_duplicate_warning_found(self, monkeypatch):
        prior = MemoryEntry(
            agent="cto",
            action="refactor code",
            outcome="success",
            timestamp="2026-09-12T10:00:00Z",
        )
        mock_store = MagicMock()
        mock_store.has_similar.return_value = prior
        monkeypatch.setattr("src.core.memory_store.MemoryStore", lambda **kw: mock_store)

        warning = _duplicate_warning("goal", "context")
        assert warning is not None
        assert "[duplicate warning]" in warning
        assert "refactor code" in warning

    def test_duplicate_warning_none(self, monkeypatch):
        mock_store = MagicMock()
        mock_store.has_similar.return_value = None
        monkeypatch.setattr("src.core.memory_store.MemoryStore", lambda **kw: mock_store)

        warning = _duplicate_warning("goal", "context")
        assert warning is None

