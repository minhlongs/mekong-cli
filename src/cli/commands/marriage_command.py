# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Marriage, Matrimonial Property Regimes & Family Law Command Surface (Phase 147).

Statutory framework:
- Law on Marriage and Family 2014 (Luật số 52/2014/QH13)
- Decree No. 126/2014/ND-CP detailing provisions of the Law on Marriage and Family
- Civil Code 2015 (Law No. 91/2015/QH13)
"""

from __future__ import annotations

import json
import typer
from rich.console import Console

from src.cli.commands.marriage_divorce_commands import (
    custody_cmd,
    divorce_cmd,
    list_records_cmd,
    search_cmd,
    settle_cmd,
    status_cmd,
)
from src.cli.commands.marriage_reg_asset_commands import (
    _render_status_dashboard,
    asset_cmd,
    prenuptial_cmd,
    register_cmd,
)
from src.core.marriage_engine import (
    AssetCategory,
    DivorceType,
    MarriageEngine,
    MarriageStatus,
    OwnershipType,
    PropertyRegimeType,
)

marriage_app = typer.Typer(
    name="marriage",
    help="Vietnamese Marriage, Matrimonial Property Regimes & Family Law Suite.",
    no_args_is_help=False,
)
app = marriage_app
console = Console()


@marriage_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """National Marriage, Matrimonial Property & Family Law Central Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = MarriageEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


marriage_app.command("register")(register_cmd)
marriage_app.command("prenuptial")(prenuptial_cmd)
marriage_app.command("asset")(asset_cmd)
marriage_app.command("divorce")(divorce_cmd)
marriage_app.command("custody")(custody_cmd)
marriage_app.command("settle")(settle_cmd)
marriage_app.command("search")(search_cmd)
marriage_app.command("list")(list_records_cmd)
marriage_app.command("status")(status_cmd)

__all__ = [
    "AssetCategory",
    "DivorceType",
    "MarriageEngine",
    "MarriageStatus",
    "OwnershipType",
    "PropertyRegimeType",
    "_render_status_dashboard",
    "app",
    "asset_cmd",
    "console",
    "custody_cmd",
    "divorce_cmd",
    "list_records_cmd",
    "main",
    "marriage_app",
    "prenuptial_cmd",
    "register_cmd",
    "search_cmd",
    "settle_cmd",
    "status_cmd",
]
