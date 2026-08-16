# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ask_keyword_router — thin gateway over cli.tui.router.

Keeps route_ask() API stable for core_commands.py and other callers.
All matching logic lives in cli.tui.router; this module does not
duplicate the route table or cache it separately.
"""
from __future__ import annotations

from typing import List, Optional

from src.cli.tui.router import CommandMatch, get_route_table, match_routes


def route_ask(input_text: str) -> Optional[str]:
    """Return the best matching mekong subcommand, or None.

    Uses ``match_routes`` to collect all matching commands, then picks
    the entry whose matched keyword is most *specific* (longer match
    wins). This prevents broad commands (e.g. ``test``) from shadowing
    more specific ones (e.g. ``e2e-test``) when both match.
    """
    matches = match_routes(input_text)
    if not matches:
        return None
    # Stop early when there is exactly one match -- no ambiguity.
    if len(matches) == 1:
        return matches[0]
    # Multiple commands matched the same input. Pick the most specific
    # by choosing the entry whose FIRST matching keyword is longest
    # (after stripping the trailing wildcard). Longer = more specific.
    route_table: List[CommandMatch] = []
    for entry in get_route_table():
        if entry.command in matches:
            route_table.append(entry)
    longest: Optional[str] = None
    best_len: int = -1
    q = input_text.lower().strip()
    for entry in route_table:
        for kw in entry.vi_keywords + entry.en_keywords:
            needle = kw.lower().strip().rstrip("*")
            if q.startswith(needle + " ") or needle in q:
                if len(needle) > best_len:
                    best_len = len(needle)
                    longest = entry.command
                break
    return longest or matches[0]


__all__ = ["route_ask"]
