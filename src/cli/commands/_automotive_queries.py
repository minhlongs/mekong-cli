# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""List and status subcommands for Automotive CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def register_automotive_queries(automotive_app: typer.Typer) -> None:
    """Register list and status commands onto automotive_app."""
    automotive_app.command("list")(list_cmd)
    automotive_app.command("status")(status_cmd)


def list_cmd(
    target: str = typer.Argument("manufacturers", help="Loại danh mục: manufacturers, vtas, batteries, inspections"),
    limit: int = typer.Option(20, "--limit", "-n", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục cơ sở sản xuất, hồ sơ kiểu loại VTA, kiểm định pin EV, hoặc sổ theo dõi chu kỳ đăng kiểm."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    tgt = target.lower().strip()

    if tgt in ("manufacturers", "factories", "makers"):
        records = engine.list_manufacturers(limit=limit)
        title = "DANH SÁCH DOANH NGHIỆP SẢN XUẤT LẮP RÁP Ô TÔ"
    elif tgt in ("vtas", "approvals", "models"):
        records = engine.list_type_approvals(limit=limit)
        title = "DANH MỤC CHỨNG NHẬN KIỂU LOẠI Ô TÔ (VTA)"
    elif tgt in ("batteries", "ev"):
        records = engine.list_ev_battery_audits(limit=limit)
        title = "HỒ SƠ THỬ NGHIỆM AN TOÀN PIN XE ĐIỆN (QCVN 91)"
    elif tgt in ("inspections", "schedules"):
        records = engine.list_inspections(limit=limit)
        title = "SỔ QUẢN LÝ HẠN ĐĂNG KIỂM PHƯƠNG TIỆN CƠ GIỚI"
    else:
        console.print(f"[bold red]Danh mục không hợp lệ:[/] '{target}'. Hỗ trợ: manufacturers, vtas, batteries, inspections")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"[bold green]{title}[/]")
    if tgt in ("manufacturers", "factories", "makers"):
        table.add_column("Mã DN", style="cyan")
        table.add_column("Tên doanh nghiệp", style="white")
        table.add_column("Đường thử (m)", justify="right")
        table.add_column("Trung tâm BH", justify="right")
        table.add_column("Số giấy phép", style="yellow")
        table.add_column("Trạng thái", style="green")
        for r in records:
            table.add_row(
                r["manufacturer_id"],
                r["company_name"],
                f"{r['test_track_length_m']:.1f}",
                str(r["authorized_service_centers_count"]),
                r["license_number"],
                r["status"],
            )
    elif tgt in ("vtas", "approvals", "models"):
        table.add_column("Mã VTA", style="cyan")
        table.add_column("Dòng xe", style="white")
        table.add_column("Động cơ", style="yellow")
        table.add_column("CO (g/km)", justify="right")
        table.add_column("RVC (%)", justify="right")
        table.add_column("Chứng chỉ VTA", style="green")
        for r in records:
            table.add_row(
                r["vta_id"],
                r["model_name"],
                r["powertrain_type"],
                f"{r['co_g_km']:.3f}",
                f"{r['rvc_rate_pct']:.1f}%",
                r["vta_certificate_no"],
            )
    elif tgt in ("batteries", "ev"):
        table.add_column("Mã Audit", style="cyan")
        table.add_column("Dòng xe", style="white")
        table.add_column("Loại pin", style="yellow")
        table.add_column("Dung lượng (kWh)", justify="right")
        table.add_column("Ngắt va chạm (ms)", justify="right")
        table.add_column("Kết luận", style="green")
        for r in records:
            table.add_row(
                r["audit_id"],
                r["model_name"],
                r["battery_chemistry"],
                f"{r['pack_capacity_kwh']:.1f}",
                f"{r['crash_cutoff_ms']:.1f}",
                r["verdict"],
            )
    else:
        table.add_column("Biển số", style="cyan")
        table.add_column("Hạng mục", style="white")
        table.add_column("Năm SX", justify="right")
        table.add_column("Chu kỳ (tháng)", justify="right")
        table.add_column("Hạn kiểm định", style="green")
        for r in records:
            table.add_row(
                r["plate_number"],
                r["vehicle_category"],
                str(r["manufacture_year"]),
                str(r["cycle_months"]),
                r["next_inspection_due_date"],
            )

    console.print(table)


def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xuất báo cáo trạng thái hệ thống ngành công nghiệp ô tô dạng JSON."""
    from src.core.automotive_engine import AutomotiveEngine

    engine = AutomotiveEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    mfg = status_data["manufacturers"]
    vta = status_data["type_approval"]
    ev = status_data["electric_vehicles"]
    ins = status_data["inspections"]

    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG CÔNG NGHIỆP Ô TÔ (AUTOMOTIVE ENGINE)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['statutory_law']}[/]\n"
            f"  Nhà máy đạt chuẩn:   [bold cyan]{mfg['compliant_facilities']}/{mfg['total_licensed']}[/] cơ sở sản xuất ô tô\n"
            f"  Kiểu loại VTA cấp:   [bold green]{vta['certified_models']}/{vta['total_vta_audits']}[/] kiểu loại xe cơ giới\n"
            f"  Ưu đãi thuế ATIGA:   [bold yellow]{vta['form_d_atiga_eligible']}[/] mẫu xe đạt RVC >= 40%\n"
            f"  Pin xe điện đạt chuẩn:[bold green]{ev['qcvn91_certified_packs']}[/] pack pin QCVN 91\n"
            f"  Phương tiện đăng kiểm:[bold cyan]{ins['total_scheduled']}[/] xe",
            title="[bold green]Automotive Industry Status[/]",
            border_style="green",
        )
    )
