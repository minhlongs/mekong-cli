"""
DEPRECATED shim — re-exports from src/core/binh_phap/ for backward compat.
Remove this file after all imports are migrated.
"""

from src.core.binh_phap.topology import TopologyEngine, EscalationLevel, COMMERCIAL_CHAPTERS  # noqa: F401
from src.core.binh_phap_escalation import resolve_llm_provider, create_provider_for_level  # noqa: F401

__all__ = [
    "TopologyEngine", "EscalationLevel", "COMMERCIAL_CHAPTERS",
    "resolve_llm_provider", "create_provider_for_level",
]
