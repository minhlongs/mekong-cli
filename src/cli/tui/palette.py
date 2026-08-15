"""TUI palette / picker stubs for tests."""
from __future__ import annotations

from typing import List, Optional


class CommandMatch:
    def __init__(self, command: str, score: float, matched_keyword: str = "") -> None:
        self.command = command
        self.score = score
        self.matched_keyword = matched_keyword

    def __eq__(self, other):
        if isinstance(other, dict):
            return (
                other.get('command') == self.command
                and other.get('score') == self.score
                and other.get('matched_keyword') == self.matched_keyword
            )
        return NotImplemented


class CommandPicker:
    def __init__(self, commands: Optional[List[str]] = None):
        self.commands = commands or []

    def available(self) -> List[str]:
        return list(self.commands)

    def prompt(self, query: str) -> Optional[str]:
        matches = fuzzy_search(query, self.commands)
        return matches[0].command if matches else None


def fuzzy_search(query: str, commands: List[str], n: int = 5) -> List[CommandMatch]:
    q = query.lower()
    scored: List[CommandMatch] = []
    for cmd in commands:
        c = cmd.lower()
        if c == q:
            scored.append(CommandMatch(command=cmd, score=1.0, matched_keyword=cmd))
        elif c.startswith(q):
            scored.append(CommandMatch(command=cmd, score=0.8, matched_keyword=cmd))
        elif q in c:
            scored.append(CommandMatch(command=cmd, score=0.5, matched_keyword=cmd))
    scored.sort(key=lambda m: (-m.score, len(m.command)))
    return scored[:n]
