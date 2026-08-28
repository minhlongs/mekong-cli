"""Tests for stream() and structured_output() on LLMRouter Protocol and adapter."""
from unittest.mock import MagicMock

from src.providers.llm.client import LLMClient, LLMResponse
from src.core.llm_router_adapter import LLMRouterAdapter
from src.core.protocols import LLMRouter


def _adapter_with_mock_client() -> tuple[LLMRouterAdapter, MagicMock]:
    """Build an adapter backed by a mocked LLMClient (no real API calls)."""
    adapter = LLMRouterAdapter()
    mock_client = MagicMock(spec=LLMClient)
    adapter._llm_client = mock_client
    return adapter, mock_client


class TestLLMRouterStream:
    """Test LLMRouter Protocol stream() method."""

    def test_stream_returns_iterator(self):
        """stream() must return an iterator."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.chat.return_value = LLMResponse(content="hello")
        result = adapter.stream("analyze this task")
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_stream_yields_content(self):
        """stream() must yield content chunks delegated from LLMClient.chat()."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.chat.return_value = LLMResponse(content="hello world")
        chunks = list(adapter.stream("test prompt"))
        assert len(chunks) >= 1
        assert chunks[0] == "hello world"
        mock_client.chat.assert_called_once()

    def test_stream_with_model_parameter(self):
        """stream() must forward model to LLMClient.chat()."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.chat.return_value = LLMResponse(content="ok")
        list(adapter.stream("test prompt", model="claude-3"))
        _, kwargs = mock_client.chat.call_args
        assert kwargs.get("model") == "claude-3"

    def test_stream_fallback_when_client_unavailable(self):
        """stream() must yield fallback content when LLMClient.chat() fails."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.chat.side_effect = RuntimeError("provider down")
        chunks = list(adapter.stream("some long prompt here"))
        assert len(chunks) >= 1
        assert isinstance(chunks[0], str)

    def test_stream_delegates_to_client_when_available(self):
        """stream() must delegate to underlying LLMClient.chat() when available."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.chat.return_value = LLMResponse(content="chunk1")
        chunks = list(adapter.stream("test"))
        assert chunks == ["chunk1"]
        mock_client.chat.assert_called_once()


class TestLLMRouterStructuredOutput:
    """Test LLMRouter Protocol structured_output() method."""

    def test_structured_output_returns_dict(self):
        """structured_output() must return a dict."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.generate_json.return_value = {"name": "Alice"}
        result = adapter.structured_output("test prompt", schema={"type": "object"})
        assert isinstance(result, dict)

    def test_structured_output_includes_schema(self):
        """structured_output() result must include the schema."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.generate_json.return_value = {"name": "Alice"}
        result = adapter.structured_output("extract name", schema=schema)
        assert result["schema"] == schema

    def test_structured_output_fallback_when_client_unavailable(self):
        """structured_output() must return fallback dict when LLMClient fails."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.generate_json.side_effect = RuntimeError("provider down")
        schema = {"type": "object"}
        result = adapter.structured_output("some prompt", schema=schema)
        assert isinstance(result, dict)
        assert "schema" in result
        assert result["schema"] == schema

    def test_structured_output_delegates_to_client_when_available(self):
        """structured_output() must delegate to LLMClient.generate_json()."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.generate_json.return_value = {"text": "ok", "data": {}}
        schema = {"type": "object"}
        result = adapter.structured_output("test", schema=schema)
        assert result["parsed"] == {"text": "ok", "data": {}}
        assert result["schema"] == schema
        mock_client.generate_json.assert_called_once()

    def test_structured_output_with_schema(self):
        """structured_output() must accept and use schema parameter."""
        adapter, mock_client = _adapter_with_mock_client()
        mock_client.generate_json.return_value = {"email": "a@b.com"}
        schema = {"type": "object", "properties": {"email": {"type": "string"}}}
        result = adapter.structured_output("extract email", schema=schema)
        assert result["schema"] == schema


class TestLLMRouterExpanded:
    """Test LLMRouter Protocol still satisfies after expansion."""

    def test_adapter_satisfies_expanded_protocol(self):
        """LLMRouterAdapter must satisfy expanded LLMRouter Protocol."""
        adapter = LLMRouterAdapter()
        assert isinstance(adapter, LLMRouter)