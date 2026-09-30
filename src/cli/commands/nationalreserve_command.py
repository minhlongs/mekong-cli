"""
CLI command group for Vietnamese National Reserves, Strategic Stockpiling & Emergency Relief Suite.
Governed by Law on National Reserve 2012 (Law No. 22/2012/QH13) & Decree No. 94/2013/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.nationalreserve_engine import (
    VALID_AUTHORITIES,
    VALID_CATEGORIES,
    VALID_QUALITY_STATUSES,
    VALID_REGIONS,
    VALID_RELIEF_PURPOSES,
    VALID_ROTATION_TYPES,
    VALID_STORAGE_TYPES,
    NationalReserveEngine,
)

app = typer.Typer(
    name="nationalreserve",
    help="Vietnamese National Reserves, Strategic Stockpiling & Emergency Relief Suite (Law 22/2012/QH13).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def nationalreserve_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Strategic dashboard of national reserves, depot capacities, and relief metrics.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = NationalReserveEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        console.print(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    # Strategic Overview Panel
    total_val_str = f"{telemetry['total_reserve_stock_value_vnd']:,.0f} VND"
    util_color = "green" if telemetry["warehouse_utilization_rate_pct"] < 80 else "yellow" if telemetry["warehouse_utilization_rate_pct"] < 95 else "red"

    overview_text = (
        f"[bold cyan]Total Storage Depots (Kho DTQG):[/bold cyan] {telemetry['total_warehouses']}\n"
        f"[bold cyan]Total Capacity:[/bold cyan] {telemetry['total_capacity']:,.1f} units | "
        f"[bold cyan]Utilized:[/bold cyan] {telemetry['total_utilized_capacity']:,.1f} units "
        f"([{util_color}]{telemetry['warehouse_utilization_rate_pct']} %[/{util_color}])\n"
        f"[bold cyan]Total Reserve Commodity Items:[/bold cyan] {telemetry['total_inventory_items']}\n"
        f"[bold cyan]Total Reserve Value:[/bold cyan] [bold green]{total_val_str}[/bold green]\n"
        f"[bold cyan]Urgent Rotations Needed (≤60 Days):[/bold cyan] [bold {'yellow' if telemetry['urgent_rotations_needed_60d'] > 0 else 'green'}]{telemetry['urgent_rotations_needed_60d']}[/]\n"
        f"[bold cyan]Substandard / Warning Stock:[/bold cyan] [bold {'red' if telemetry['substandard_or_warning_items'] > 0 else 'green'}]{telemetry['substandard_or_warning_items']}[/]\n"
        f"[bold cyan]Emergency Relief Aid Executed:[/bold cyan] {telemetry['total_relief_allocations']} missions ({telemetry['total_relief_quantity_dispatched']:,.1f} units dispatched)\n"
        f"[bold cyan]State Budget Replenishment Due:[/bold cyan] [bold yellow]{telemetry['budget_replenishment_due_vnd']:,.0f} VND[/bold yellow]\n"
        f"[bold cyan]Active Stock Rotation Plans:[/bold cyan] {telemetry['active_rotation_plans']}"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]CỤC DỰ TRỮ NHÀ NƯỚC — HỆ THỐNG QUẢN LÝ DỰ TRỮ QUỐC GIA (LUẬT 22/2012/QH13)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    # Categories Breakdown Table
    cat_breakdown = telemetry.get("inventory_by_category", {})
    if cat_breakdown:
        cat_table = Table(
            title="Danh mục hàng dự trữ quốc gia theo chủng loại (Điều 27 Luật DTQG)",
            box=box.SIMPLE_HEAVY,
            header_style="bold blue",
        )
        cat_table.add_column("Category", style="cyan", justify="left")
        cat_table.add_column("Item Count", justify="right")
        cat_table.add_column("Total Quantity", justify="right")
        cat_table.add_column("Total Value (VND)", justify="right", style="green")

        for cat_name, cdata in cat_breakdown.items():
            cat_table.add_row(
                cat_name,
                str(cdata["count"]),
                f"{cdata['quantity']:,.1f}",
                f"{cdata['value_vnd']:,.0f}",
            )
        console.print(cat_table)


@app.command("warehouse")
def register_warehouse_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Unique warehouse depot code (e.g. KHO-DT-HN01)."),
    name: str = typer.Option(..., "--name", "-n", help="Depot name."),
    region: str = typer.Option(..., "--region", "-r", help="Region: NORTH, CENTRAL, SOUTH, CENTRAL_HIGHLANDS, MEKONG_DELTA."),
    unit: str = typer.Option(..., "--unit", "-u", help="Managing reserve department / ministry."),
    storage_type: str = typer.Option("REGULAR_STORAGE", "--storage-type", "-s", help="REGULAR_STORAGE, CONTROLLED_ATMOSPHERE_N2, HERMETIC_SILO, UNDERGROUND_TANK."),
    capacity: float = typer.Option(..., "--capacity", help="Total physical storage capacity."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a state reserve strategic storage depot / warehouse.
    """
    engine = NationalReserveEngine()
    try:
        res = engine.register_warehouse(
            warehouse_code=code,
            warehouse_name=name,
            region=region,
            managing_unit=unit,
            storage_type=storage_type,
            total_capacity=capacity,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering warehouse:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        console.print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký kho dự trữ quốc gia thành công", box=box.ROUNDED)
    table.add_column("Attribute", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("intake")
def intake_inventory_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Inventory batch code (e.g. DTQG-GAO-2026-01)."),
    warehouse: str = typer.Option(..., "--warehouse", "-w", help="Warehouse depot code."),
    category: str = typer.Option(..., "--category", help="GRAIN_FOOD, RESCUE_EQUIPMENT, PETROLEUM_ENERGY, MEDICAL_SUPPLIES, AGRICULTURAL_SEEDS, DEFENSE_SECURITY."),
    name: str = typer.Option(..., "--name", "-n", help="Item name."),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Intake quantity."),
    unit: str = typer.Option(..., "--unit", "-u", help="Unit of measurement (TAN, CHIEC, LIEU, LIT, BO)."),
    date: str = typer.Option(..., "--date", "-d", help="Intake date in YYYY-MM-DD."),
    months: int = typer.Option(12, "--months", "-m", help="Max allowable storage months under QCVN."),
    cost_vnd: float = typer.Option(0.0, "--cost-vnd", help="Unit cost in VND."),
    quality: str = typer.Option("PASSED", "--quality", help="Quality status: PASSED, WARNING, SUBSTANDARD."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record commodity intake into national reserve inventory with automated rotation deadline.
    """
    engine = NationalReserveEngine()
    try:
        res = engine.intake_inventory(
            inventory_code=code,
            warehouse_code=warehouse,
            item_category=category,
            item_name=name,
            quantity=quantity,
            unit=unit,
            intake_date=date,
            max_storage_months=months,
            unit_cost_vnd=cost_vnd,
            quality_status=quality,
        )
    except Exception as e:
        console.print(f"[bold red]Error intaking inventory:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        console.print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhập kho hàng dự trữ quốc gia thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f}" if isinstance(v, (int, float)) and "vnd" in str(k).lower() else str(v))
    console.print(table)


@app.command("inspect")
def inspect_quality_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Inventory batch code."),
    status: str = typer.Option(..., "--status", "-s", help="Quality status: PASSED, WARNING, SUBSTANDARD."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record technical inspection results of reserve stock per QCVN standards.
    """
    engine = NationalReserveEngine()
    try:
        res = engine.inspect_inventory_quality(
            inventory_code=code,
            quality_status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error updating inspection status:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        console.print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    status_color = "green" if status.upper() == "PASSED" else "yellow" if status.upper() == "WARNING" else "red"
    console.print(f"[{status_color}]Quality inspection updated for item {code}: {status.upper()}[/{status_color}]")


@app.command("relief")
def allocate_relief_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Relief allocation code (e.g. XUAT-CUUTRO-2026-001)."),
    decision: str = typer.Option(..., "--decision", help="Decision number (e.g. QĐ 142/QĐ-TTg)."),
    authority: str = typer.Option("PRIME_MINISTER", "--authority", "-a", help="PRIME_MINISTER, MINISTER_OF_FINANCE, MINISTER_OF_DEFENSE, MINISTER_OF_PUBLIC_SECURITY."),
    purpose: str = typer.Option(..., "--purpose", "-p", help="DISASTER_RELIEF, HUNGER_RELIEF_TET, EPIDEMIC_CONTROL, DEFENSE_SECURITY_MISSION, MARKET_STABILIZATION."),
    inventory: str = typer.Option(..., "--inventory", "-i", help="Inventory batch code to dispatch."),
    locality: str = typer.Option(..., "--locality", "-l", help="Beneficiary province/region (e.g. Tỉnh Quảng Bình)."),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Allocated relief quantity."),
    date: str = typer.Option(..., "--date", "-d", help="Dispatch date in YYYY-MM-DD."),
    requested: Optional[float] = typer.Option(None, "--requested", help="Requested quantity (if different from allocated)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Execute emergency dispatch & relief allocation of national reserve commodities.
    """
    engine = NationalReserveEngine()
    try:
        res = engine.allocate_relief(
            allocation_code=code,
            decision_number=decision,
            decision_authority=authority,
            purpose=purpose,
            inventory_code=inventory,
            beneficiary_locality=locality,
            allocated_quantity=quantity,
            dispatch_date=date,
            requested_quantity=requested,
        )
    except Exception as e:
        console.print(f"[bold red]Error executing relief allocation:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        console.print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Lệnh xuất cấp cứu trợ dự trữ quốc gia", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "budget" in str(k) else str(v))
    console.print(table)


@app.command("rotate")
def plan_stock_rotation_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Rotation plan code (e.g. XR-2026-GAO-01)."),
    inventory: str = typer.Option(..., "--inventory", "-i", help="Inventory batch code."),
    year: int = typer.Option(..., "--year", "-y", help="Plan year (e.g. 2026)."),
    rotation_type: str = typer.Option("AUCTION_SALE", "--type", "-t", help="AUCTION_SALE, DIRECT_PURCHASE_REPLACEMENT, EMERGENCY_REPURCHASE."),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Outgoing rotation quantity."),
    deadline: str = typer.Option(..., "--deadline", help="Replacement deadline date (YYYY-MM-DD)."),
    proceeds: float = typer.Option(0.0, "--proceeds", help="Realized sales proceeds in VND."),
    budget: float = typer.Option(0.0, "--budget", help="Reacquisition budget in VND."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Schedule statutory stock rotation (xuất đổi hàng/xoay vòng) under Art 45 Law 22/2012/QH13.
    """
    engine = NationalReserveEngine()
    try:
        res = engine.plan_stock_rotation(
            rotation_code=code,
            inventory_code=inventory,
            plan_year=year,
            rotation_type=rotation_type,
            outgoing_quantity=quantity,
            replacement_deadline=deadline,
            realized_proceeds_vnd=proceeds,
            reacquisition_budget_vnd=budget,
        )
    except Exception as e:
        console.print(f"[bold red]Error planning stock rotation:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        console.print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Kế hoạch xuất đổi hàng dự trữ quốc gia", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("replenish")
def replenish_rotation_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Rotation plan code."),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Replenished inventory quantity."),
    cost_vnd: float = typer.Option(0.0, "--cost-vnd", help="Unit cost in VND."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record completion of stock rotation by replenishing fresh inventory.
    """
    engine = NationalReserveEngine()
    try:
        res = engine.execute_rotation_replenishment(
            rotation_code=code,
            replenished_quantity=quantity,
            unit_cost_vnd=cost_vnd,
        )
    except Exception as e:
        console.print(f"[bold red]Error replenishing inventory:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        console.print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]Stock rotation {code} completed successfully. Fresh quantity replenished: {quantity:,.1f}[/bold green]")


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="Record type: warehouses, inventories, allocations, rotations, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List state reserve warehouses, inventories, relief allocations, and rotation plans.
    """
    engine = NationalReserveEngine()
    records = engine.list_records(record_type=record_type, limit=limit)

    if json_output:
        console.print(json.dumps(records, indent=2, ensure_ascii=False))
        return

    for category, items in records.items():
        table = Table(title=f"Danh sách {category.upper()} ({len(items)} bản ghi)", box=box.ROUNDED)
        if not items:
            console.print(f"[dim]No {category} found.[/dim]")
            continue

        columns = list(items[0].keys())
        for col in columns[:6]:  # Show first 6 columns
            table.add_column(col, style="cyan")
        for item in items:
            table.add_row(*[str(item.get(c, "")) for c in columns[:6]])
        console.print(table)


@app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Get aggregate telemetry metrics on national reserves and relief operations.
    """
    engine = NationalReserveEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        console.print(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số vận hành Hệ thống Dự trữ Quốc gia", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, dict):
            table.add_row(str(k), f"{len(v)} categories")
        elif isinstance(v, float) and "vnd" in str(k):
            table.add_row(str(k), f"{v:,.0f} VND")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
