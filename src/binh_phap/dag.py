"""Binh Phap DAG — Chapter graph and node definitions.

Sources from dna/binh-phap-operating-system.json (the trusted single source
of truth). The JSON is extended with an optional ``dag`` key; backwards-
compatible — absence of ``dag`` implies the default linear ordering.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OS_PATH = PROJECT_ROOT / "dna" / "binh-phap-operating-system.json"
STATE_DIR = PROJECT_ROOT / ".mekong"
STATE_FILE = STATE_DIR / "binh-phap-state.json"


# ---------- data model ----------


@dataclass(frozen=True)
class ChapterNode:
    """Single DAG node representing one Binh Phap chapter."""

    number: int
    name: str
    primary_agent: str
    commands: List[str]
    operating_rule: str
    # Recovery policy
    requires_human: bool = False
    max_auto_retries: int = 1
    # If set, branches to these chapter numbers on configured failure modes.
    fallback_chapters: List[int] = field(default_factory=list)

    @property
    def primary_command(self) -> str:
        return self.commands[0] if self.commands else ""


@dataclass(frozen=True)
class DagDefinition:
    """Full DAG graph for the 13-chapter chain."""

    chapters: Dict[int, ChapterNode]
    # Ordered adjacency list: chapter → list[chapter] that must finish first.
    edges: Dict[int, List[int]]
    # Human-only chapters (cannot be auto-executed without approval).
    human_only: frozenset[int] = frozenset({6, 11})

    def predecessors(self, chapter: int) -> List[int]:
        return list(self.edges.get(chapter, []))

    def successors(self, chapter: int) -> List[int]:
        return [ch for ch, pres in self.edges.items() if chapter in pres]

    def next_auto(self, completed: frozenset[int], current: int) -> Optional[int]:
        """Return the next runnable chapter number, or None."""
        for ch in range(current, 14):
            if ch in completed:
                continue
            if ch in self.human_only:
                continue
            if ch not in self.chapters:
                continue
            pres = set(self.predecessors(ch))
            if pres and not pres.issubset(completed):
                continue
            return ch
        return None

    def topological_order(self) -> List[int]:
        visited: set[int] = set()
        order: List[int] = []

        def _visit(n: int) -> None:
            if n in visited:
                return
            visited.add(n)
            for p in self.predecessors(n):
                _visit(p)
            order.append(n)

        for ch in range(1, 14):
            _visit(ch)
        return order


# ---------- loader ----------


def _inject_dag(os_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Return the JSON document with a default ``dag`` key if missing."""
    doc = dict(os_doc)
    if "dag" not in doc:
        # Default linear DAG: each chapter depends only on the previous one.
        doc["dag"] = {
            "edges": [[i, i + 1] for i in range(1, 13)],
            "human_only_chapters": [6, 11],
            "fallbacks": {
                "8": {
                    "strategies": [
                        "ops:health-sweep",
                        "debug",
                        "sre:incident",
                    ],
                    "max_attempts": 3,
                    "time_limit_minutes": 15,
                }
            },
        }
    return doc


def load_dag(os_path: str | Path | None = None) -> DagDefinition:
    """Build a DagDefinition from the OS manifest."""
    path = Path(os_path) if os_path else DEFAULT_OS_PATH
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw = _inject_dag(raw)

    chapters_raw: Dict[int, Dict[str, Any]] = {
        int(ch["id"]): ch for ch in raw.get("chapters", [])
    }

    nodes: Dict[int, ChapterNode] = {}
    for num, ch in chapters_raw.items():
        fallback_cfg = raw.get("dag", {}).get("fallbacks", {}).get(str(num), {})
        nodes[num] = ChapterNode(
            number=num,
            name=ch.get("name", ""),
            primary_agent=ch.get("primary_agent", ""),
            commands=ch.get("commands", []),
            operating_rule=ch.get("operating_rule", ""),
            requires_human=num
            in frozenset(raw.get("dag", {}).get("human_only_chapters", [6, 11])),
            max_auto_retries=fallback_cfg.get("max_attempts", 1),
            fallback_chapters=[
                int(x) for x in fallback_cfg.get("fallback_chapters", [])
            ],
        )

    edges: Dict[int, List[int]] = {i: [] for i in range(1, 14)}
    for src, dst in raw.get("dag", {}).get("edges", []):
        edges[int(dst)].append(int(src))

    human_only = frozenset(
        raw.get("dag", {}).get("human_only_chapters", [6, 11])
    )
    return DagDefinition(chapters=nodes, edges=edges, human_only=human_only)


CHAPTER_NODE_COUNT = 13

__all__ = ["DagDefinition", "ChapterNode", "load_dag", "CHAPTER_NODE_COUNT"]
