# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

# DEPRECATED: import from src.core.memory_canonical instead.
# This shim is retained only for backward compatibility.
# See Phase 8 memory consolidation.

"""Deprecated: use src.core.memory_canonical for the canonical implementation."""

from src.core.memory_canonical import MemoryEntry, MemoryStore  # noqa: F401

__all__ = ["MemoryEntry", "MemoryStore"]