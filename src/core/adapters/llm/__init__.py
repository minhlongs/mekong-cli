# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""LLM adapter package.

Canonical home of the LLM client (moved from src/core/llm_client.py).
Re-exports the public surface so callers can import from the package root.
"""

from .client import LLMClient, ProviderHealth, get_client

__all__ = ["LLMClient", "ProviderHealth", "get_client"]
