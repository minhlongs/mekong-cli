"""TUI utilities — lightweight stubs for tests."""

from .palette import CommandMatch, CommandPicker, fuzzy_search
from .router import (
    CommandMatch,
    RouteEntry,
    ROUTE_TABLE,
    _matches,
    fuzzy_match,
    get_all_commands,
    get_route_table,
    match_routes,
    route_ask,
)

__all__ = [
    "CommandMatch",
    "CommandPicker",
    "RouteEntry",
    "ROUTE_TABLE",
    "_matches",
    "fuzzy_match",
    "fuzzy_search",
    "get_all_commands",
    "get_route_table",
    "match_routes",
    "route_ask",
]
