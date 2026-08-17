"""Phase 2A: LLMRouter Protocol expansion — generate/health methods."""
from unittest.mock import MagicMock, patch

from src.core.llm_router_adapter import LLMRouterAdapter
from src.core.protocols import LLMRouter


class TestLLMRouterExpanded:
    """Test expanded LLMRouter Protocol (generate + health)."""

    def test_adapter_satisfies_expanded_protocol(self):
        """LLMRouterAdapter must satisfy expanded LLMRouter Protocol."""
        adapter = LLMRouterAdapter()
        assert isinstance(adapter, LLMRouter)

    def test_generate_returns_string(self):
        """generate() must return a string."""
        adapter = LLMRouterAdapter()
        # Mock _get_router so route() is not called with string
        mock_router = MagicMock()
        mock_router.route.return_value = MagicMock(name="test-model")
        adapter._router = mock_router
        result = adapter.generate("Hello world")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_with_model(self):
        """generate(model=...) returns stub without calling router."""
        adapter = LLMRouterAdapter()
        result = adapter.generate("Test prompt here", model="claude-3")
        assert "claude-3" in result
        assert "Test prompt here" in result

    def test_generate_passes_kwargs(self):
        """generate() must accept **kwargs without error."""
        adapter = LLMRouterAdapter()
        mock_router = MagicMock()
        mock_router.route.return_value = MagicMock(name="test-model")
        adapter._router = mock_router
        result = adapter.generate("Test", temperature=0.7, max_tokens=100)
        assert isinstance(result, str)

    def test_generate_uses_model_when_provided(self):
        """generate(model=...) returns stub without calling router.route()."""
        adapter = LLMRouterAdapter()
        # When model is provided, router.route() is NOT called
        result = adapter.generate("Any prompt", model="custom-model")
        assert "custom-model" in result

    def test_health_returns_status_dict(self):
        """health() must return dict with status key."""
        adapter = LLMRouterAdapter()
        result = adapter.health()
        assert isinstance(result, dict)
        assert "status" in result

    def test_health_ok_when_router_available(self):
        """health() returns ok when router loads."""
        adapter = LLMRouterAdapter()
        result = adapter.health()
        assert result["status"] == "ok"
        assert "router" in result

    def test_health_error_on_router_failure(self):
        """health() returns error status when router fails."""
        adapter = LLMRouterAdapter()
        with patch.object(adapter, "_get_router", side_effect=RuntimeError("router down")):
            result = adapter.health()
            assert result["status"] == "error"
            assert "error" in result

    def test_classify_still_works(self):
        """Original classify() must still work after expansion."""
        adapter = LLMRouterAdapter()
        mock_router = MagicMock()
        mock_router.route.return_value = MagicMock(name="claude-3", tier="basic")
        adapter._router = mock_router
        result = adapter.classify("deploy to production")
        assert "model" in result
        assert "task" in result

    def test_estimate_cost_still_works(self):
        """Original estimate_cost() must still work."""
        adapter = LLMRouterAdapter()
        result = adapter.estimate_cost("claude-3", 1000)
        assert result["cost_usd"] == 1000 * 0.00001
        assert result["currency"] == "USD"