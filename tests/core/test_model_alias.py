# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Model Alias Map (src/core/model_alias.py).

Verifies translation of canonical model names to provider-specific names,
fallback mechanisms, ollama prefix handling, and primary provider bypass.
"""

from __future__ import annotations

import logging

import pytest

from src.core.model_alias import MODEL_ALIASES, resolve_model


class TestModelAliasesDict:
    """Validate structure and consistency of MODEL_ALIASES mapping."""

    def test_flagship_tier_present(self):
        assert "claude-opus-4-6" in MODEL_ALIASES
        opus = MODEL_ALIASES["claude-opus-4-6"]
        assert opus["qwen"] == "qwen3-coder-plus"
        assert opus["deepseek"] == "deepseek-chat"
        assert opus["openrouter"] == "anthropic/claude-opus-4"
        assert opus["openai-direct"] == "gpt-4o"

    def test_standard_tier_present(self):
        assert "claude-sonnet-4-6" in MODEL_ALIASES
        sonnet = MODEL_ALIASES["claude-sonnet-4-6"]
        assert sonnet["qwen"] == "qwen3-coder-plus"
        assert sonnet["deepseek"] == "deepseek-chat"
        assert sonnet["openrouter"] == "anthropic/claude-sonnet-4"
        assert sonnet["openai-direct"] == "gpt-4o"
        assert sonnet["ollama-local"] == "deepseek-coder-v2:16b"

    def test_fast_tier_present(self):
        assert "claude-haiku-4-5" in MODEL_ALIASES
        haiku = MODEL_ALIASES["claude-haiku-4-5"]
        assert haiku["qwen"] == "qwen-turbo"
        assert haiku["openrouter"] == "anthropic/claude-haiku-4-5"
        assert haiku["openai-direct"] == "gpt-4o-mini"
        assert haiku["ollama-local"] == "llama3.2:3b"

    def test_gemini_models_present(self):
        for model in ("gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.0-pro"):
            assert model in MODEL_ALIASES
            assert "qwen" in MODEL_ALIASES[model]
            assert "openrouter" in MODEL_ALIASES[model]

    def test_all_alias_values_non_empty_strings(self):
        for canonical, providers in MODEL_ALIASES.items():
            assert isinstance(canonical, str) and canonical
            for provider, target in providers.items():
                assert isinstance(provider, str) and provider
                assert isinstance(target, str) and target


class TestResolveModel:
    """Validate resolve_model() behavior for all execution paths."""

    def test_empty_or_none_canonical_returns_input(self):
        assert resolve_model("", "qwen") == ""
        # None passed dynamically should be returned safely
        assert resolve_model(None, "qwen") is None  # type: ignore[arg-type]

    def test_ollama_prefix_strips_prefix(self):
        assert resolve_model("ollama:llama3.2:3b", "qwen") == "llama3.2:3b"
        assert resolve_model("ollama:deepseek-r1:8b", "any") == "deepseek-r1:8b"
        assert resolve_model("ollama:custom:tag:v1", "any") == "custom:tag:v1"

    def test_primary_provider_bypasses_aliases(self):
        # Even if canonical model is in MODEL_ALIASES, "primary" preserves it
        assert resolve_model("claude-sonnet-4-6", "primary") == "claude-sonnet-4-6"
        assert resolve_model("claude-opus-4-6", "primary") == "claude-opus-4-6"
        assert resolve_model("custom-model", "primary") == "custom-model"

    def test_unknown_canonical_returns_canonical(self):
        assert resolve_model("unknown-model-xyz", "qwen") == "unknown-model-xyz"
        assert resolve_model("gpt-5-preview", "openrouter") == "gpt-5-preview"

    def test_unknown_provider_falls_back_to_canonical(self):
        # Known model, unknown provider -> returns canonical model unchanged
        assert resolve_model("claude-sonnet-4-6", "nonexistent-provider") == "claude-sonnet-4-6"

    @pytest.mark.parametrize("canonical,provider,expected", [
        ("claude-opus-4-6", "qwen", "qwen3-coder-plus"),
        ("claude-opus-4-6", "deepseek", "deepseek-chat"),
        ("claude-opus-4-6", "openrouter", "anthropic/claude-opus-4"),
        ("claude-opus-4-6", "agentrouter", "claude-opus-4-6-20250514"),
        ("claude-opus-4-6", "openai-direct", "gpt-4o"),
        ("claude-opus-4-6", "ollama-local", "deepseek-coder-v2:33b"),
        ("claude-sonnet-4-6", "qwen", "qwen3-coder-plus"),
        ("claude-sonnet-4-6", "deepseek", "deepseek-chat"),
        ("claude-sonnet-4-6", "openrouter", "anthropic/claude-sonnet-4"),
        ("claude-sonnet-4-6", "agentrouter", "claude-sonnet-4-6-20250514"),
        ("claude-sonnet-4-6", "openai-direct", "gpt-4o"),
        ("claude-sonnet-4-6", "ollama-local", "deepseek-coder-v2:16b"),
        ("claude-haiku-4-5", "qwen", "qwen-turbo"),
        ("claude-haiku-4-5", "deepseek", "deepseek-chat"),
        ("claude-haiku-4-5", "openrouter", "anthropic/claude-haiku-4-5"),
        ("claude-haiku-4-5", "agentrouter", "claude-haiku-4-5-20251001"),
        ("claude-haiku-4-5", "openai-direct", "gpt-4o-mini"),
        ("claude-haiku-4-5", "ollama-local", "llama3.2:3b"),
        ("gemini-2.0-flash", "anthropic-direct", "claude-haiku-4-5-20251001"),
        ("gemini-2.0-flash-lite", "openrouter", "google/gemini-2.0-flash-lite-001"),
        ("gemini-2.0-pro", "openai-direct", "gpt-4o"),
    ])
    def test_canonical_to_provider_translations(self, canonical, provider, expected):
        assert resolve_model(canonical, provider) == expected

    def test_debug_log_emitted_on_translation(self, caplog):
        caplog.set_level(logging.DEBUG, logger="src.core.model_alias")
        result = resolve_model("claude-sonnet-4-6", "qwen")
        assert result == "qwen3-coder-plus"
        assert any(
            "[ModelAlias] claude-sonnet-4-6 → qwen3-coder-plus (provider=qwen)" in record.message
            for record in caplog.records
        )

    def test_no_debug_log_when_untranslated(self, caplog):
        caplog.set_level(logging.DEBUG, logger="src.core.model_alias")
        result = resolve_model("claude-sonnet-4-6", "primary")
        assert result == "claude-sonnet-4-6"
        # No translation log for primary or untranslated
        assert not any("[ModelAlias]" in record.message for record in caplog.records)
