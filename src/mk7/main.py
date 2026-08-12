"""Mekong CLI 7 — main entry (Typer app).

Rewrite v7: lấy ak CLI làm hoa tiêu — ít command mạnh, model qua OmniRoute.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("LANG", "C.UTF-8")
os.environ.setdefault("LC_ALL", "C.UTF-8")

import typer
from rich.console import Console

from .commands.ask import ask_cmd, strategist_cmd
from .commands.auto import auto_cmd
from .commands.cook import cook_cmd
from .commands.chat import chat_cmd
from .commands.dashboard import dashboard_cmd
from .commands.debug import debug_cmd
from .commands.doctor import doctor_cmd
from .commands.init import init_cmd
from .commands.mcp import mcp_call_cmd, mcp_list_cmd
from .commands.plan import plan_cmd
from .commands.orchestrate import orchestrate_cmd, sop_cmd
from .commands.omni import omni_config, omni_run_cmd, omni_status_cmd
from .commands.opc import loop_cmd, metrics_cmd, revenue_add_cmd, signal_add_cmd, signal_list_cmd
from .commands.opc2 import (analytics_cmd, breaker_cmd, cost_add_cmd, finance_cmd,
                            marketing_cmd, opc_init_cmd, opc_list_cmd, opc_use_cmd,
                            sales_advance_cmd, sales_cmd, sales_proposal_cmd,
                            spend_cmd, support_cmd, support_resolve_cmd,
                            support_response_cmd)
from .commands.sessions import sessions_attach_cmd, sessions_list_cmd, sessions_todos_cmd
from .commands.ui import ui_export_cmd, ui_init_cmd, ui_server_cmd

app = typer.Typer(
    name="mekong",
    help="🚀 Mekong CLI 7 — RaaS Agency Operating System (rewrite)",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

app.command("ask")(ask_cmd)
app.command("strategist")(strategist_cmd)
app.command("cook")(cook_cmd)
app.command("chat")(chat_cmd)
app.command("debug")(debug_cmd)
app.command("doctor")(doctor_cmd)
app.command("init")(init_cmd)
app.command("plan")(plan_cmd)
app.command("auto")(auto_cmd)
app.command("orchestrate")(orchestrate_cmd)
app.command("sop")(sop_cmd)
app.command("omni")(omni_run_cmd)
app.command("omni-status")(omni_status_cmd)
app.command("omni-config")(omni_config)
app.command("loop")(loop_cmd)
app.command("signal-add")(signal_add_cmd)
app.command("signal-list")(signal_list_cmd)
app.command("revenue-add")(revenue_add_cmd)
app.command("metrics")(metrics_cmd)
app.command("cost-add")(cost_add_cmd)
app.command("finance")(finance_cmd)
app.command("analytics")(analytics_cmd)
app.command("sales")(sales_cmd)
app.command("sales-advance")(sales_advance_cmd)
app.command("sales-proposal")(sales_proposal_cmd)
app.command("support")(support_cmd)
app.command("support-response")(support_response_cmd)
app.command("support-resolve")(support_resolve_cmd)
app.command("marketing")(marketing_cmd)
app.command("spend")(spend_cmd)
app.command("breaker")(breaker_cmd)
app.command("opc-init")(opc_init_cmd)
app.command("opc-use")(opc_use_cmd)
app.command("opc-list")(opc_list_cmd)
app.command("mcp")(mcp_list_cmd)
app.command("mcp-call")(mcp_call_cmd)
app.command("sessions")(sessions_list_cmd)
app.command("session-attach")(sessions_attach_cmd)
app.command("session-todos")(sessions_todos_cmd)
app.command("ui-export")(ui_export_cmd)
app.command("ui-init")(ui_init_cmd)
app.command("ui-server")(ui_server_cmd)
app.command("dashboard")(dashboard_cmd)


@app.command("list")
def list_cmd() -> None:
    """List available commands."""
    console.print("[bold]Mekong CLI 7 commands:[/]")
    for name, info in {
        "init": "Initialize config + test gateway",
        "doctor": "Diagnose gateway + model health",
        "ask": "Ask the model a question",
        "strategist": "Ask the strategist (qwen3.8-max)",
        "plan": "Create a phased implementation plan",
        "cook": "Plan -> Execute -> Verify pipeline",
        "debug": "Analyze issue + fix plan (dry-run)",
        "auto": "Natural language -> graph -> auto-execute with gates",
    }.items():
        console.print(f"  [cyan]{name:<12}[/] {info}")


@app.command("version")
def version_cmd() -> None:
    """Show version."""
    console.print("mekong 7.0.0 (rewrite)")


if __name__ == "__main__":
    app()
