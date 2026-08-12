"""Mekong CLI 7 — `auto` command.

Natural language -> intent router -> DAG graph -> gate protocol.
Exit codes: 0 success, 1 error, 42 gate blocked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.dispatch import dispatch_node
from ..core.gates import GATE_EXIT_CODE, GateRegistry
from ..core.graph import (
    BudgetExceeded,
    GraphExecutor,
    GraphState,
    GraphValidationError,
    Node,
    load_state,
    save_state,
)
from ..core.router import HitlGate, IntentRouter
from ..core.config import CONFIG_DIR

console = Console()

GATE_STATE = CONFIG_DIR / "gate_decisions.json"


def _load_gate_decisions() -> dict[str, str]:
    if GATE_STATE.exists():
        try:
            return json.loads(GATE_STATE.read_text())
        except Exception:
            return {}
    return {}


def _save_gate_decision(node_id: str, decision: str) -> None:
    GATE_STATE.parent.mkdir(parents=True, exist_ok=True)
    decisions = _load_gate_decisions()
    decisions[node_id] = decision
    GATE_STATE.write_text(json.dumps(decisions, indent=2))


def _plan_nodes(title: str) -> tuple[list[Node], list[tuple[str, str]]]:
    """Synchronous planner: sonnet decomposes the intent into graph nodes.

    Falls back to OpenRouter free (gpt-oss) and strategist (qwen3.8-max)
    when zuneF (sonnet) is unavailable.
    """
    from ..core.llm import LLMClient
    from ..core.models import resolve

    client = LLMClient()
    prompt = (
        f"Decompose this goal into 3-8 DAG nodes:\n\n{title}\n\n"
        "Return ONLY JSON: "
        '[{"id": "n1", "task": "...", "agent": "eng|pm|ops|ceo|ae", "depends_on": ["n1"], '
        '"gate": null | "deploy" | "rm" | "force_push" | "spend_money" | "delete_data"}]\n'
        "gate: set when the node performs that dangerous action; null otherwise."
    )
    raw = ""
    for key in ("sonnet", "openrouter-free", "strategist"):
        try:
            if key == "openrouter-free":
                raw = client.text("openrouter/openai/gpt-oss-20b:free", prompt, max_tokens=2048)
            else:
                entry = resolve_or_fallback(key)
                raw = client.text(entry.id, prompt, max_tokens=2048)
            break
        except Exception:
            continue
    try:
        data = json.loads(raw)
    except Exception:
        return [Node(id="n1", task=title, agent="eng")], []
    nodes: list[Node] = []
    edges: list[tuple[str, str]] = []
    for item in data:
        nid = str(item.get("id", f"n{len(nodes)+1}"))
        nodes.append(
            Node(
                id=nid,
                task=str(item.get("task", "")),
                agent=str(item.get("agent", "eng")),
                gate=item.get("gate"),
            )
        )
        for dep in item.get("depends_on", []) or []:
            edges.append((str(dep), nid))
    return nodes or [Node(id="n1", task=title, agent="eng")], edges


def auto_cmd(
    request: str = typer.Argument(..., help="Natural-language request"),
    resume: bool = typer.Option(False, "--resume", help="Resume from last checkpoint"),
    decision: Optional[str] = typer.Option(None, "--decision", help="Gate decision: approve|deny"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan only, don't execute"),
    max_tokens: int = typer.Option(2048, "--max-tokens", help="Max tokens per node LLM call"),
) -> None:
    """Auto-harness: natural language -> graph -> execute with gates."""
    try:
        # 1. Intent
        router = IntentRouter()
        intent = router.classify(request)
        console.print(
            Panel(
                f"[bold]{request}[/]\n"
                f"task_type={intent.task_type} · agent={intent.target_agent} · "
                f"skill={intent.skill_hint or '-'} · danger={intent.danger_level} · "
                f"confidence={intent.confidence:.2f}",
                title="Intent",
            )
        )

        # 2. Graph
        slug = "".join(c if c.isalnum() else "-" for c in request.lower())[:60]
        gs = load_state(slug) if resume else None
        if gs is None:
            nodes, edges = _plan_nodes(request)
            gs = GraphState(title=request)
            gs.nodes = nodes
            gs.edges = edges
        gs.validate()
        save_state(gs)

        if dry_run:
            console.print(Panel("Plan only (--dry-run)", title="Graph"))
            for n in gs.nodes:
                deps = gs.dependencies(n.id)
                console.print(f"  [cyan]{n.id}[/] {n.task}  deps={deps}  gate={n.gate}")
            return

        # 3. Execute with gates
        gates = GateRegistry()
        decisions = _load_gate_decisions()

        # Resume semantics: a node blocked by a gate that the operator now
        # approves must run — reset blocked nodes to pending.
        for n in gs.nodes:
            if n.status == "blocked":
                n.status = "pending"
        save_state(gs)

        def gate_cb(node: Node) -> bool | None:
            if node.gate is None:
                return None
            # Only honor gates the registry knows; planner may hallucinate
            # a gate key (e.g. "deploy" on a file-create node) — ignore those.
            known = gates.gates.get(node.gate) or gates.gates.get(node.gate.replace("-", " "))
            if not known:
                return None
            if node.id in decisions:
                return decisions[node.id] == "approve"
            if decision:
                _save_gate_decision(node.id, decision)
                return decision == "approve"
            return False  # block -> exit 42

        # Todo sync: 1 graph node = 1 todo item (opencode Todo contract)
        from ..core.todo import TodoStore, sync_todos_from_graph

        store = TodoStore(slug)

        # Session tracking: one session per auto run; attach todo ids.
        from ..core.session import SessionStore

        session_store = SessionStore()
        session = session_store.create(directory=".", agent_id=intent.target_agent, title=request)
        for t in store.list():
            session_store.attach_todo(session.id, t.id)

        def on_node_status(node: Node) -> None:
            sync_todos_from_graph(store, gs.nodes, {n.id: n.task for n in gs.nodes})

        # Seed todos for the graph before execution.
        sync_todos_from_graph(store, gs.nodes, {n.id: n.task for n in gs.nodes})

        # Context compaction: when shared context grows, summarize it once
        # and feed the summary to the next node instead of raw blocks.
        from ..core.compaction import Compactor
        from ..core.dispatch import dispatch_node

        compactor = Compactor(threshold_chars=12000)
        compacted_summary: dict[str, str] = {}

        def node_executor(node: Node, shared: dict[str, object]) -> dict[str, object]:
            summary = compacted_summary.get(node.id, "")
            if not summary and compactor.should_compact(shared, exclude_key=node.id):
                result = compactor.compact(shared, exclude_key=node.id)
                if result.compacted:
                    summary = result.summary
                    compacted_summary[node.id] = summary
            return dispatch_node(node, shared, compact_context=summary)

        executor = GraphExecutor(
            node_executor, gate_cb=gate_cb, max_llm_calls=60, on_node_status=on_node_status
        )

        try:
            gs = executor.run(gs)
        except BudgetExceeded as e:
            console.print(f"[red]Budget exceeded: {e}[/]")
            sys.exit(1)

        if gs.status == "blocked":
            blocked = [n for n in gs.nodes if n.status == "blocked"]
            for n in blocked:
                console.print(
                    f"[yellow]GATE:[/] node {n.id} ({n.task}) needs approval — "
                    f"rerun with --resume --decision approve|deny"
                )
            session_store.update(session.id, status="aborted")
            sys.exit(GATE_EXIT_CODE)

        if gs.status == "failed":
            failed = [n for n in gs.nodes if n.status == "failed"]
            for n in failed:
                console.print(f"[red]FAILED:[/] {n.id} {n.task} — {n.error[:200]}[/]")
            session_store.update(session.id, status="failed")
            sys.exit(1)

        session_store.update(session.id, status="completed")

        console.print(Panel(f"Auto-harness done — {len(gs.nodes)} nodes, {gs.llm_calls} LLM calls", title="Complete"))
        summary = store.summary()
        console.print(
            f"  Todos: [green]✓ {summary.get('completed', 0)}[/] "
            f"[yellow]… {summary.get('in_progress', 0)}[/] "
            f"[dim]pending {summary.get('pending', 0)} · cancelled {summary.get('cancelled', 0)}[/]"
        )
    except HitlGate as e:
        console.print(f"[yellow]Ambiguous request:[/] {e.hint} — please rephrase more specifically")
        sys.exit(1)
    except GraphValidationError as e:
        console.print(f"[red]Graph invalid:[/] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/] {str(e)[:300]}")
        sys.exit(1)
