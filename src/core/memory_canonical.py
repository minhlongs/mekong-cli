# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - Canonical Memory Store

Single source of truth for the goal-outcome memory store.
Re-exports MemoryStore and MemoryEntry from the implementation module.

New code MUST import from this module, not from src.core.memory directly.
See Phase 8 memory consolidation.
"""

from src.core.memory import MemoryEntry, MemoryStore

__all__ = [
    "MemoryEntry",
    "MemoryStore",
]