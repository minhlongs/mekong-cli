# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Backward-compatibility shim for ``src.core.adapters.llm``.

The canonical LLM client moved to ``src/providers/llm/`` (DEPRECATION.md
resolution target). This shim re-exports it so legacy importers — including
the Gate 5 deployment smoke test in ``.github/workflows/ai-native-ci.yml``
which is outside this PR's ownership — keep resolving the historical path
without changes to their source.

New code should ``from src.providers.llm import ...`` directly. Importing
through this shim is permitted; it is a thin re-export, not a second
implementation.
"""

from src.providers.llm import *  # noqa: F401,F403
from src.providers.llm import __all__ as _all  # noqa: F401

__all__ = list(_all)