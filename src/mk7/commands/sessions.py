"""Mekong CLI 7 — `sessions` command: list/tree/attach todos to sessions."""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.session import SessionStore
from ..core.todo import TodoStore

console = Console()


def sessions_list_cmd() -> None:
    """List sessions as a tree (parent/child) with todo counts."""
    store = SessionStore()
    sessions = store.list()
    if not sessions:
        console.print("[yellow]No sessions yet. Run mk auto or mk cook to create one.[/]")
        return

    by_id = {s.id: s for s in sessions}
    roots = [s for s in sessions if s.parent_id is None or s.parent_id not in by_id]
    children_of: dict[str, list] = {}
    for s in sessions:
        children_of.setdefault(s.parent_id or "", []).append(s)

    def render(s, depth: int) -> None:
        indent = "  " * depth
        todo_note = ""
        if s.todo_ids:
            try:
                first = TodoStore(s.todo_ids[0][:20])
                counts = first.summary()
                todo_note = f" todos: ✓{counts.get('completed', 0)} …{counts.get('in_progress', 0)}"
            except Exception:
                pass
        color = "green" if s.status == "completed" else ("yellow" if s.status == "active" else "red")
        console.print(f"{indent}[{color}]●[/] [bold]{s.title or s.id}[/] ({s.agent_id}) [{s.status}]{todo_note}")
        console.print(f"{indent}  [dim]{s.id} · {s.directory}[/]")
        for child in sorted(children_of.get(s.id, []), key=lambda c: c.updated_at, reverse=True):
            render(child, depth + 1)

    for root in sorted(roots, key=lambda s: s.updated_at, reverse=True):
        render(root, 0)


def sessions_attach_cmd(
    session_id: str = typer.Argument(..., help="Session id"),
    todo_id: str = typer.Argument(..., help="Todo id"),
) -> None:
    """Attach an existing todo to a session."""
    from ..core.session import SessionNotFound

    store = SessionStore()
    try:
        store.attach_todo(session_id, todo_id)
        console.print(f"[green]attached todo {todo_id} -> session {session_id}[/]")
    except SessionNotFound as e:
        console.print(f"[red]{e}[/]")
        sys.exit(1)


def sessions_todos_cmd(session_id: str = typer.Argument(..., help="Session id")) -> None:
    """Show todos attached to a session."""
    from ..core.session import SessionNotFound

    store = SessionStore()
    try:
        session = store.get(session_id)
    except SessionNotFound as e:
        console.print(f"[red]{e}[/]")
        sys.exit(1)
    if not session.todo_ids:
        console.print("[yellow]No todos attached.[/]")
        return
    for tid in session.todo_ids:
        try:
            tstore = TodoStore(tid)
            for todo in tstore.list():
                mark = "✓" if todo.status == "completed" else ("…" if todo.status == "in_progress" else "·")
                console.print(f"  [green]{mark}[/] {todo.content} ({todo.status})")
        except Exception:
            console.print(f"  [dim]{tid}[/]")
