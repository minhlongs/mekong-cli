"""Tests for stream() and structured_output() on LLMRouter Protocol and adapter."""
from unittest.mock import MagicMock, patch

from src.core.llm_router_adapter import LLMRouterAdapter
from src.core.protocols import LLMRouter


class TestLLMRouterStream:
    """Test LLMRouter Protocol stream() method."""

    def test_stream_returns_iterator(self):
        """stream() must return an iterator."""
        adapter = LLMRouterAdapter()
        result = adapter.stream("analyze this task")
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_stream_yields_content(self):
        """stream() must yield content chunks."""
        adapter = LLMRouterAdapter()
        chunks = list(adapter.stream("test prompt"))
        assert len(chunks) >= 1

    def test_stream_with_model_parameter(self):
        """stream() must accept model parameter."""
        adapter = LLMRouterAdapter()
        chunks = list(adapter.stream("test prompt", model="claude-3"))
        assert len(chunks) >= 1
        assert "claude-3" in chunks[0]

    def test_stream_fallback_when_no_router(self):
        """stream() must yield fallback content when router is unavailable."""
        adapter = LLMRouterAdapter()
        with patch.object(adapter, "_get_router", side_effect=RuntimeError("router down")):
            chunks = list(adapter.stream("some long prompt here"))
            assert len(chunks) >= 1
            assert "stream fallback" in chunks[0]

    def test_stream_delegates_to_router_when_available(self):
        """stream() must delegate to underlying router when it supports streaming."""
        adapter = LLMRouterAdapter()
        mock_router = MagicMock()
        mock_router.stream.return_value = iter(["chunk1", "chunk2"])
        adapter._router = mock_router
        chunks = list(adapter.stream("test"))
        assert chunks == ["chunk1", "chunk2"]
        mock_router.stream.assert_called_once()


class TestLLMRouterStructuredOutput:
    """Test LLMRouter Protocol structured_output() method."""

    def test_structured_output_returns_dict(self):
        """structured_output() must return a dict."""
        adapter = LLMRouterAdapter()
        result = adapter.structured_output("test prompt", schema={"type": "object"})
        assert isinstance(result, dict)

    def test_structured_output_includes_schema(self):
        """structured_output() result must include the schema."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        adapter = LLMRouterAdapter()
        result = adapter.structured_output("extract name", schema=schema)
        assert result["schema"] == schema

    def test_structured_output_fallback_when_no_router(self):
        """structured_output() must return fallback dict when router is unavailable."""
        adapter = LLMRouterAdapter()
        schema = {"type": "object"}
        with patch.object(adapter, "_get_router", side_effect=RuntimeError("router down")):
            result = adapter.structured_output("some prompt", schema=schema)
            assert isinstance(result, dict)
            assert "schema" in result
            assert "structured fallback" in result["text"]

    def test_structured_output_delegates_to_router_when_available(self):
        """structured_output() must delegate to underlying router when supported."""
        adapter = LLMRouterAdapter()
        mock_router = MagicMock()
        mock_router.structured_output.return_value = {"text": "ok", "data": {}}
        adapter._router = mock_router
        schema = {"type": "object"}
        result = adapter.structured_output("test", schema=schema)
        assert result == {"text": "ok", "data": {}}
        mock_router.structured_output.assert_called_once()

    def test_structured_output_with_schema(self):
        """structured_output() must accept and use schema parameter."""
        adapter = LLMRouterAdapter()
        schema = {"type": "object", "properties": {"email": {"type": "string"}}}
        result = adapter.structured_output("extract email", schema=schema)
        assert result["schema"] == schema


class TestLLMRouterExpanded:
    """Test LLMRouter Protocol still satisfies after expansion."""

    def test_adapter_satisfies_expanded_protocol(self):
        """LLMRouterAdapter must satisfy expanded LLMRouter Protocol."""
        adapter = LLMRouterAdapter()
        assert isinstance(adapter, LLMRouter)