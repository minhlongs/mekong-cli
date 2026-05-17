"""Mekong /idea autopilot — autonomous Plan→Execute→Verify→Reflect loop.

Public surface: `IdeaLoop`. Everything else is internal.
"""

from .idea_loop import IdeaLoop, RunOptions, RunResult

__all__ = ["IdeaLoop", "RunOptions", "RunResult"]
