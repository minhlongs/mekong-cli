# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RouteTable implementation and keyword matching helpers for command fabric."""

from __future__ import annotations

from typing import List, Optional

from src.cli.tui.router import CommandMatch, RouteEntry, get_route_table


def _kw_matches(pattern: str, text: str) -> bool:
    """Case-insensitive keyword match (same rules as cli.tui.router._matches)."""
    if not text:
        return False
    p = pattern.lower().strip()
    if not p:
        return False
    if p.endswith("*"):
        needle = p[:-1].rstrip()
        if not needle:
            return False
        return needle in text or text.startswith(needle + " ")
    return p in text


def _cmd_match_sort_key(m: CommandMatch) -> tuple:
    return (m.score,)


class RouteTable:
    """Thin wrapper around the shared ROUTE_TABLE.

    Provides instance methods so callers can inject custom RouteEntry
    lists (e.g. derived from CommandRecords) without touching globals.
    """

    def __init__(self, entries: Optional[List[RouteEntry]] = None) -> None:
        seen: set = set()
        deduped: list = []
        src = entries if entries is not None else get_route_table()
        for entry in src:
            if entry.command in seen:
                continue
            seen.add(entry.command)
            deduped.append(entry)
        self._entries: List[RouteEntry] = deduped

    def match(self, query: str) -> List[str]:
        """Return all command names matched by *query* (deduplicated, order = priority)."""
        if not query or not query.strip():
            return []
        q = query.lower().strip()
        seen_cmds: set = set()
        results: list = []
        for entry in self._entries:
            if entry.command in seen_cmds:
                continue
            for kw in entry.vi_keywords + entry.en_keywords:
                if _kw_matches(kw, q):
                    results.append(entry.command)
                    seen_cmds.add(entry.command)
                    break
        return results

    def best(self, query: str) -> Optional[str]:
        """Return the single best-matching command, or None."""
        matches = self.match(query)
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        longest: Optional[str] = None
        best_len: int = -1
        q = query.lower().strip()
        for entry in self._entries:
            if entry.command not in matches:
                continue
            for kw in entry.vi_keywords + entry.en_keywords:
                needle = kw.lower().strip().rstrip("*")
                if not needle:
                    continue
                if q.startswith(needle + " ") or needle in q:
                    if len(needle) > best_len:
                        best_len = len(needle)
                        longest = entry.command
                    break
        return longest or matches[0]

    def fuzzy(self, query: str, max_results: int = 5) -> List[CommandMatch]:
        """Return scored CommandMatch results for interactive autocomplete."""
        if not query or not query.strip():
            return []
        q = query.lower().strip()
        seen_cmds: set = set()
        results: list = []
        for entry in self._entries:
            if entry.command in seen_cmds:
                continue
            for kw in entry.vi_keywords + entry.en_keywords:
                kw_lower = kw.lower().strip()
                if _kw_matches(kw_lower, q):
                    needle = kw_lower.rstrip("*").rstrip()
                    if not needle:
                        score = 0.5
                    elif q == needle:
                        score = 1.0
                    elif q.startswith(needle + " "):
                        score = 0.8
                    else:
                        score = 0.5
                    results.append(CommandMatch(entry.command, score, kw))
                    seen_cmds.add(entry.command)
                    break
        results.sort(key=_cmd_match_sort_key, reverse=True)
        return results[:max_results]

    @property
    def entries(self) -> List[RouteEntry]:
        return list(self._entries)

    @property
    def commands(self) -> List[str]:
        return [e.command for e in self._entries]

    def __len__(self) -> int:
        return len(self._entries)
