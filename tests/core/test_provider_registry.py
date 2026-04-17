"""
Unit tests for src/core/provider_registry.py

Tests cover:
- ProviderRegistry: register, set_default, list_providers, list_models
- resolve(): colon-separated refs, plain model refs, alias resolution,
             default model fallback, unknown provider error
- _get_instance(): lazy init, caching, factory failure graceful handling
- Built-in providers: OpenAICompatProvider, GeminiProvider, OpenAIProvider
- OpenAIProvider capability differentiation (reasoning vs non-reasoning)
- create_default_registry() factory function
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.core.provider_registry import (
    GeminiProvider,
    OpenAICompatProvider,
    OpenAIProvider,
    ProviderRegistry,
    ResolvedModel,
    create_default_registry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_mock_provider(name: str, models: list[str] | None = None):
    """Create a minimal mock that satisfies ProviderSpec protocol."""
    provider = MagicMock()
    type(provider).provider_name = name
    type(provider).supported_models = models or ["model-a", "model-b"]
    provider.get_capabilities.return_value = {"tools": True, "streaming": True}
    return provider


def make_factory(provider_instance):
    """Return a callable factory that returns the given provider."""
    return lambda: provider_instance


# ---------------------------------------------------------------------------
# ProviderRegistry.register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_single_provider(self):
        registry = ProviderRegistry()
        provider = make_mock_provider("test-prov")
        registry.register("test-prov", make_factory(provider))
        assert "test-prov" in registry.list_providers()

    def test_first_registered_becomes_default(self):
        registry = ProviderRegistry()
        registry.register("first", make_factory(make_mock_provider("first")))
        registry.register("second", make_factory(make_mock_provider("second")))
        assert registry._default_provider == "first"

    def test_register_with_aliases_stored(self):
        registry = ProviderRegistry()
        registry.register(
            "myprov",
            make_factory(make_mock_provider("myprov")),
            aliases={"fast": "model-fast"},
        )
        assert registry._providers["myprov"].aliases == {"fast": "model-fast"}

    def test_register_with_default_model(self):
        registry = ProviderRegistry()
        registry.register(
            "myprov",
            make_factory(make_mock_provider("myprov")),
            default_model="model-default",
        )
        assert registry._providers["myprov"].default_model == "model-default"


# ---------------------------------------------------------------------------
# ProviderRegistry.set_default
# ---------------------------------------------------------------------------


class TestSetDefault:
    def test_set_default_to_registered_provider(self):
        registry = ProviderRegistry()
        registry.register("a", make_factory(make_mock_provider("a")))
        registry.register("b", make_factory(make_mock_provider("b")))
        registry.set_default("b")
        assert registry._default_provider == "b"

    def test_set_default_unregistered_raises_value_error(self):
        registry = ProviderRegistry()
        with pytest.raises(ValueError, match="Provider not registered"):
            registry.set_default("unknown")


# ---------------------------------------------------------------------------
# ProviderRegistry.list_providers / list_models
# ---------------------------------------------------------------------------


class TestListProviders:
    def test_empty_registry(self):
        registry = ProviderRegistry()
        assert registry.list_providers() == []

    def test_lists_all_registered_names(self):
        registry = ProviderRegistry()
        registry.register("p1", make_factory(make_mock_provider("p1")))
        registry.register("p2", make_factory(make_mock_provider("p2")))
        providers = registry.list_providers()
        assert "p1" in providers
        assert "p2" in providers
        assert len(providers) == 2


class TestListModels:
    def test_returns_models_from_provider_instance(self):
        registry = ProviderRegistry()
        provider = make_mock_provider("mp", models=["gpt-4", "gpt-3.5"])
        registry.register("mp", make_factory(provider))
        models = registry.list_models("mp")
        assert "gpt-4" in models
        assert "gpt-3.5" in models

    def test_returns_empty_list_for_unknown_provider(self):
        registry = ProviderRegistry()
        assert registry.list_models("nonexistent") == []

    def test_returns_empty_list_when_factory_fails(self):
        registry = ProviderRegistry()
        registry.register("broken", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        assert registry.list_models("broken") == []


# ---------------------------------------------------------------------------
# ProviderRegistry.resolve — colon-separated refs
# ---------------------------------------------------------------------------


class TestResolveColonRef:
    def setup_method(self):
        self.registry = ProviderRegistry()
        self.provider = make_mock_provider("gemini", models=["gemini-2.5-pro"])
        self.registry.register("gemini", make_factory(self.provider))

    def test_colon_ref_resolves_correct_provider_and_model(self):
        resolved = self.registry.resolve("gemini:gemini-2.5-pro")
        assert resolved.provider_name == "gemini"
        assert resolved.model_id == "gemini-2.5-pro"

    def test_colon_ref_with_unknown_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            self.registry.resolve("openai:gpt-4o")

    def test_colon_ref_capabilities_fetched(self):
        self.provider.get_capabilities.return_value = {"tools": True}
        resolved = self.registry.resolve("gemini:gemini-2.5-pro")
        assert resolved.capabilities["tools"] is True


# ---------------------------------------------------------------------------
# ProviderRegistry.resolve — plain model refs (uses default provider)
# ---------------------------------------------------------------------------


class TestResolvePlainRef:
    def setup_method(self):
        self.registry = ProviderRegistry()
        self.provider = make_mock_provider("proxy", models=["gemini-3-pro-high"])
        self.registry.register(
            "proxy",
            make_factory(self.provider),
            default_model="gemini-3-pro-high",
        )

    def test_plain_ref_uses_default_provider(self):
        resolved = self.registry.resolve("gemini-3-pro-high")
        assert resolved.provider_name == "proxy"
        assert resolved.model_id == "gemini-3-pro-high"

    def test_plain_ref_is_raw_string_when_no_alias_match(self):
        resolved = self.registry.resolve("some-unknown-model")
        # Should still resolve with default provider but pass model string through
        assert resolved.provider_name == "proxy"
        assert resolved.model_id == "some-unknown-model"


# ---------------------------------------------------------------------------
# ProviderRegistry.resolve — alias resolution
# ---------------------------------------------------------------------------


class TestResolveAliases:
    def setup_method(self):
        self.registry = ProviderRegistry()
        self.provider = make_mock_provider("openai")
        self.registry.register(
            "openai",
            make_factory(self.provider),
            aliases={"fast": "gpt-4o-mini", "best": "gpt-4o"},
        )

    def test_alias_resolved_with_colon_ref(self):
        resolved = self.registry.resolve("openai:fast")
        assert resolved.model_id == "gpt-4o-mini"

    def test_alias_resolved_as_plain_ref_via_default_provider(self):
        self.registry.set_default("openai")
        resolved = self.registry.resolve("best")
        assert resolved.model_id == "gpt-4o"

    def test_non_alias_passed_through_unchanged(self):
        resolved = self.registry.resolve("openai:gpt-3.5-turbo")
        assert resolved.model_id == "gpt-3.5-turbo"


# ---------------------------------------------------------------------------
# ProviderRegistry.resolve — default model fallback
# ---------------------------------------------------------------------------


class TestResolveDefaultModelFallback:
    def test_empty_model_id_uses_default_model(self):
        registry = ProviderRegistry()
        provider = make_mock_provider("myp")
        registry.register(
            "myp",
            make_factory(provider),
            default_model="best-model",
        )
        # Colon with empty model part is edge case but default should kick in
        resolved = registry.resolve("myp:")
        assert resolved.model_id == "best-model"


# ---------------------------------------------------------------------------
# ProviderRegistry._get_instance — caching and error handling
# ---------------------------------------------------------------------------


class TestGetInstance:
    def test_returns_none_for_unknown_provider(self):
        registry = ProviderRegistry()
        assert registry._get_instance("ghost") is None

    def test_caches_instance_on_second_call(self):
        registry = ProviderRegistry()
        call_count = {"n": 0}

        def factory():
            call_count["n"] += 1
            return make_mock_provider("p")

        registry.register("p", factory)
        registry._get_instance("p")
        registry._get_instance("p")
        assert call_count["n"] == 1  # factory called only once

    def test_returns_none_when_factory_raises(self):
        registry = ProviderRegistry()

        def bad_factory():
            raise RuntimeError("init failed")

        registry.register("bad", bad_factory)
        result = registry._get_instance("bad")
        assert result is None


# ---------------------------------------------------------------------------
# ResolvedModel
# ---------------------------------------------------------------------------


class TestResolvedModel:
    def test_fields_set_correctly(self):
        rm = ResolvedModel(
            provider_name="gemini",
            model_id="gemini-2.5-pro",
            capabilities={"tools": True},
        )
        assert rm.provider_name == "gemini"
        assert rm.model_id == "gemini-2.5-pro"
        assert rm.capabilities["tools"] is True

    def test_default_capabilities_empty(self):
        rm = ResolvedModel(provider_name="p", model_id="m")
        assert rm.capabilities == {}


# ---------------------------------------------------------------------------
# Built-in provider: OpenAICompatProvider
# ---------------------------------------------------------------------------


class TestOpenAICompatProvider:
    def setup_method(self):
        self.provider = OpenAICompatProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "proxy"

    def test_supported_models_non_empty(self):
        assert len(self.provider.supported_models) > 0

    def test_get_capabilities_returns_all_true(self):
        caps = self.provider.get_capabilities("gemini-2.5-pro")
        assert caps["tools"] is True
        assert caps["streaming"] is True
        assert caps["structured_output"] is True


# ---------------------------------------------------------------------------
# Built-in provider: GeminiProvider
# ---------------------------------------------------------------------------


class TestGeminiProvider:
    def setup_method(self):
        self.provider = GeminiProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "gemini"

    def test_supported_models_contains_gemini_25_pro(self):
        assert "gemini-2.5-pro" in self.provider.supported_models

    def test_get_capabilities_tools_true(self):
        caps = self.provider.get_capabilities("gemini-2.5-pro")
        assert caps["tools"] is True


# ---------------------------------------------------------------------------
# Built-in provider: OpenAIProvider
# ---------------------------------------------------------------------------


class TestOpenAIProvider:
    def setup_method(self):
        self.provider = OpenAIProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "openai"

    def test_gpt_4o_supports_tools(self):
        caps = self.provider.get_capabilities("gpt-4o")
        assert caps["tools"] is True
        assert caps["system_message"] is True

    def test_reasoning_model_o1_no_tools(self):
        caps = self.provider.get_capabilities("o1")
        assert caps["tools"] is False
        assert caps["system_message"] is False

    def test_reasoning_model_o3_mini_no_system_message(self):
        caps = self.provider.get_capabilities("o3-mini")
        assert caps["system_message"] is False

    def test_gpt_4o_mini_supports_streaming(self):
        caps = self.provider.get_capabilities("gpt-4o-mini")
        assert caps["streaming"] is True

    def test_supported_models_includes_gpt_4o(self):
        assert "gpt-4o" in self.provider.supported_models


# ---------------------------------------------------------------------------
# create_default_registry
# ---------------------------------------------------------------------------


class TestCreateDefaultRegistry:
    def setup_method(self):
        self.registry = create_default_registry()

    def test_proxy_registered(self):
        assert "proxy" in self.registry.list_providers()

    def test_gemini_registered(self):
        assert "gemini" in self.registry.list_providers()

    def test_openai_registered(self):
        assert "openai" in self.registry.list_providers()

    def test_first_registered_is_proxy_as_default(self):
        assert self.registry._default_provider == "proxy"

    def test_resolve_proxy_best_alias(self):
        resolved = self.registry.resolve("proxy:best")
        assert resolved.model_id == "gemini-3-pro-high"

    def test_resolve_gemini_fast_alias(self):
        resolved = self.registry.resolve("gemini:fast")
        assert resolved.model_id == "gemini-2.0-flash"

    def test_resolve_openai_fast_alias(self):
        resolved = self.registry.resolve("openai:fast")
        assert resolved.model_id == "gpt-4o-mini"

    def test_resolve_colon_ref_returns_resolved_model(self):
        resolved = self.registry.resolve("openai:gpt-4o")
        assert isinstance(resolved, ResolvedModel)
        assert resolved.provider_name == "openai"
        assert resolved.model_id == "gpt-4o"

    def test_proxy_default_model_is_gemini_3_pro_high(self):
        resolved = self.registry.resolve("proxy:")
        assert resolved.model_id == "gemini-3-pro-high"

    def test_list_models_proxy(self):
        models = self.registry.list_models("proxy")
        assert len(models) > 0

    def test_unknown_provider_in_colon_ref_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            self.registry.resolve("anthropic:claude-3")
