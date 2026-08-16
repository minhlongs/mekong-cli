"""Pytest configuration for CLI test suite."""
from __future__ import annotations


# Skip TUI tests when textual is not installed (no prompt_toolkit / textual)
try:
    import textual  # noqa: F401
except ImportError:
    try:
        import prompt_toolkit  # noqa: F401
    except ImportError:
        collect_ignore = ["tui/"]