# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Phap Commerce Status — dispatches commerce_state from TopologyEngine."""
from __future__ import annotations

from rich.console import Console
from rich.table import Table

from src.core.binh_phap.topology import TopologyEngine

console = Console()


def render_commerce_status() -> None:
    engine = TopologyEngine()
    state = engine.state

    table = Table(title="Binh Phap Commerce Status")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Dimension", state.get("current_dimension", "vertical"))
    table.add_row("Cycle", str(state.get("cycle_number", 0)))
    table.add_row("Next Command", f"/{state.get('next_command', 'swot')}")
    table.add_row("Auto Dispatch", str(state.get("auto_dispatch", False)))
    table.add_row("Target MRR", f"${state.get('target_mrr', 1000)}")
    table.add_row("Failures", str(engine.consecutive_failures))

    commerce_mode = state.get("commerce_mode")
    table.add_row("Commerce Mode", str(commerce_mode) if commerce_mode is not None else "disabled")
    table.add_row("Revenue Events", str(len(state.get("revenue_events", []))))
    last_mrr_update = state.get("last_mrr_update")
    table.add_row("Last MRR Update", last_mrr_update or "(none)")

    for name, group in engine.groups.items():
        table.add_row(f"Group {name}", group.status.value)

    history = state.get("cycle_history", [])
    table.add_row("Cycles Completed", str(len(history)))
    if history:
        last = history[-1]
        table.add_row("Last MRR", f"${last['result']['mrr']}")
        table.add_row("Last Customers", str(last["result"]["customers"]))

    console.print(table)
