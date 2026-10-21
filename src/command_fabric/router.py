# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Command-fabric NL router — unified intent layer.

Bridges cli.tui.router (single source of truth for RouteEntry / ROUTE_TABLE)
into the command-fabric namespace so catalog consumers can do NL routing
without depending on cli.tui internals.

Exports:
  - route_command(query) -> Optional[str]        — best command match
  - route_commands(query) -> list[str]            — all matches, deduplicated
  - fuzzy_match_commands(query, n) -> list[CommandMatch]
  - match_from_records(query, records) -> list[str]
  - RouteTable                                   — wrapper around ROUTE_TABLE

All matching logic lives in cli.tui.router; this module adds only the
CommandRecord bridge and convenience constructors.  Nothing is copied.
"""

from __future__ import annotations

from typing import List, Optional

from src.cli.tui.router import (
    CommandMatch,
    RouteEntry,
    get_all_commands,
    get_route_table,
)
from src.command_fabric.route_table import (
    RouteTable,
    _cmd_match_sort_key,
    _kw_matches,
)

__all__ = [
    "RouteEntry",
    "CommandMatch",
    "RouteTable",
    "_cmd_match_sort_key",
    "_default_table",
    "_kw_matches",
    "match_from_records",
    "route_commands",
    "route_command",
    "fuzzy_match_commands",
    "get_all_commands",
    "get_route_table",
]

# ── Module-level singleton (mirrors cli.tui.router's ROUTE_TABLE) ──────
_default_table = RouteTable()


# ── Convenience APIs (drop-in replacements for cli.tui.router calls) ───

def route_command(query: str) -> Optional[str]:
    """Best command match for *query*. Returns None if no match."""
    return _default_table.best(query)


def route_commands(query: str) -> List[str]:
    """All deduplicated command matches for *query*."""
    return _default_table.match(query)


def fuzzy_match_commands(query: str, max_results: int = 5) -> List[CommandMatch]:
    """Scored autocomplete results for *query*."""
    return _default_table.fuzzy(query, max_results)


def match_from_records(query: str, records: list) -> List[str]:
    """Match *query* against a list of command-fabric CommandRecords.

    Converts each record to a RouteEntry on-the-fly using its name and
    (empty) keyword lists — this is a structural match for records that
    carry their own NL metadata.  For records without keyword fields,
    falls back to name-only matching.
    """
    if not query or not query.strip():
        return []
    q = query.lower().strip()
    seen: set = set()
    results: list = []
    for rec in records:
        cmd = getattr(rec, "name", str(rec))
        if cmd in seen:
            continue
        vi_kw: tuple = ()
        en_kw: tuple = ()
        if hasattr(rec, "vi_keywords"):
            vi_kw = rec.vi_keywords
        if hasattr(rec, "en_keywords"):
            en_kw = rec.en_keywords
        entry = RouteEntry(command=cmd, vi_keywords=vi_kw, en_keywords=en_kw)
        for kw in entry.vi_keywords + entry.en_keywords:
            if _kw_matches(kw, q):
                results.append(cmd)
                seen.add(cmd)
                break
        else:
            if cmd in q:
                results.append(cmd)
                seen.add(cmd)
    return results
