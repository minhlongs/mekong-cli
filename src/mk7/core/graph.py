"""Mekong CLI 7 — DAG execution graph.

State machine over Nodes/Edges with checkpoint/resume, retry, budgets and
parallel execution of independent nodes. State persists to ~/.mekong/state/
after every node completion so a crash can resume from the last checkpoint.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .config import CONFIG_DIR

STATE_DIR = CONFIG_DIR / "state"

MAX_NODES = 20
MAX_RETRIES = 3
MAX_LLM_CALLS = 60

NodeExecutor = Callable[["Node", dict[str, object]], dict[str, object]]


class BudgetExceeded(RuntimeError):
    pass


class GraphValidationError(RuntimeError):
    pass


@dataclass
class Node:
    id: str
    task: str
    agent: str = "eng"
    gate: str | None = None  # gate key if this node needs operator approval
    status: str = "pending"  # pending | running | done | failed | blocked
    result: dict[str, object] = field(default_factory=dict)
    retries: int = 0
    error: str = ""


@dataclass
class GraphState:
    title: str
    nodes: list[Node] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    status: str = "created"  # created | running | done | failed | blocked
    llm_calls: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def slug(self) -> str:
        s = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        return s[:60] or "graph"

    def node(self, node_id: str) -> Node | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    def dependents(self, node_id: str) -> list[Node]:
        deps = {a for a, _b in self.edges}
        return [n for n in self.nodes if n.id in deps]

    def dependencies(self, node_id: str) -> list[str]:
        return [a for a, b in self.edges if b == node_id]

    def ready(self) -> list[Node]:
        """Nodes whose deps are all done and not yet run."""
        out = []
        for n in self.nodes:
            if n.status != "pending":
                continue
            deps = self.dependencies(n.id)
            if all(self.node(d) and self.node(d).status == "done" for d in deps):
                out.append(n)
        return out

    def validate(self) -> None:
        ids = {n.id for n in self.nodes}
        for a, b in self.edges:
            if a not in ids or b not in ids:
                raise GraphValidationError(f"edge references unknown node: {a}->{b}")
        if len(self.nodes) > MAX_NODES:
            raise GraphValidationError(f"graph exceeds {MAX_NODES} nodes")
        # cycle check (simple DFS)
        visiting: set[str] = set()
        done_set: set[str] = set()

        def dfs(nid: str) -> None:
            if nid in done_set:
                return
            if nid in visiting:
                raise GraphValidationError(f"cycle detected at {nid}")
            visiting.add(nid)
            for n in self.nodes:
                if n.id in self.dependencies(nid):
                    dfs(n.id)
            visiting.remove(nid)
            done_set.add(nid)

        for n in self.nodes:
            dfs(n.id)


def save_state(gs: GraphState) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    gs.updated_at = time.time()
    path = STATE_DIR / f"{gs.slug}.json"
    path.write_text(
        json.dumps(
            {
                "title": gs.title,
                "status": gs.status,
                "nodes": [
                    {
                        "id": n.id,
                        "task": n.task,
                        "agent": n.agent,
                        "gate": n.gate,
                        "status": n.status,
                        "result": n.result,
                        "retries": n.retries,
                        "error": n.error,
                    }
                    for n in gs.nodes
                ],
                "edges": gs.edges,
                "llm_calls": gs.llm_calls,
                "created_at": gs.created_at,
                "updated_at": gs.updated_at,
            },
            indent=2,
        )
    )
    return path


def load_state(slug: str) -> GraphState | None:
    path = STATE_DIR / f"{slug}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    gs = GraphState(title=data["title"])
    gs.nodes = [
        Node(
            id=n["id"],
            task=n["task"],
            agent=n.get("agent", "eng"),
            gate=n.get("gate"),
            status=n.get("status", "pending"),
            result=n.get("result", {}),
            retries=n.get("retries", 0),
            error=n.get("error", ""),
        )
        for n in data.get("nodes", [])
    ]
    gs.edges = [tuple(e) for e in data.get("edges", [])]
    gs.status = data.get("status", "created")
    gs.llm_calls = data.get("llm_calls", 0)
    gs.created_at = data.get("created_at", 0)
    gs.updated_at = data.get("updated_at", 0)
    return gs


class GraphExecutor:
    """Runs a GraphState to completion with retry/budget/gate handling.

    executor_fn(node, shared) -> dict: node-level work (LLM call etc.).
    gate_cb(node) -> bool | None: None=auto-pass, False=block (exit 42).
    """

    def __init__(
        self,
        executor_fn: NodeExecutor,
        gate_cb: Callable[[Node], bool | None] | None = None,
        max_retries: int = MAX_RETRIES,
        max_nodes: int = MAX_NODES,
        max_llm_calls: int = MAX_LLM_CALLS,
        on_node_status: Callable[[Node], None] | None = None,
    ):
        self.executor_fn = executor_fn
        self.gate_cb = gate_cb
        self.max_retries = max_retries
        self.max_nodes = max_nodes
        self.max_llm_calls = max_llm_calls
        self.on_node_status = on_node_status

    def run(self, gs: GraphState) -> GraphState:
        gs.validate()
        shared: dict[str, object] = {}
        for n in gs.nodes:
            if n.status == "done":
                shared[n.id] = n.result

        # seed shared with already-done nodes
        gs.status = "running"
        save_state(gs)

        while True:
            ready = gs.ready()
            if not ready:
                break
            for node in ready:
                if gs.llm_calls >= self.max_llm_calls:
                    gs.status = "failed"
                    save_state(gs)
                    raise BudgetExceeded(f"LLM call budget ({self.max_llm_calls}) exceeded")
                if len(gs.nodes) > self.max_nodes:
                    gs.status = "failed"
                    save_state(gs)
                    raise BudgetExceeded(f"node budget ({self.max_nodes}) exceeded")

                if node.gate:
                    decision = self.gate_cb(node) if self.gate_cb else None
                    if decision is False:
                        node.status = "blocked"
                        gs.status = "blocked"
                        save_state(gs)
                        if self.on_node_status:
                            self.on_node_status(node)
                        return gs

                node.status = "running"
                save_state(gs)
                if self.on_node_status:
                    self.on_node_status(node)
                try:
                    node.result = self.executor_fn(node, shared)
                    gs.llm_calls += 1
                    node.status = "done"
                except Exception as e:
                    node.retries += 1
                    node.error = str(e)[:300]
                    if node.retries > self.max_retries:
                        node.status = "failed"
                        gs.status = "failed"
                        save_state(gs)
                        if self.on_node_status:
                            self.on_node_status(node)
                        return gs
                    node.status = "pending"
                shared[node.id] = node.result
                save_state(gs)
                if self.on_node_status:
                    self.on_node_status(node)

        # All nodes done?
        if all(n.status == "done" for n in gs.nodes):
            gs.status = "done"
        else:
            gs.status = "failed"
        save_state(gs)
        return gs
