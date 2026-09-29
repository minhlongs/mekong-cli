# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Enterprise SOX 404, ITGC & Internal Controls Audit (Phase 45)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
audit_app = typer.Typer(
    name="audit",
    help="Enterprise SOX 404, ITGC & Internal Controls Audit Suite",
    add_completion=False,
)


@audit_app.callback(invoke_without_command=True)
def audit_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan kiểm toán dạng JSON"),
) -> None:
    """Enterprise SOX 404, ITGC & Internal Controls Audit Suite."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.sox_audit_engine import SoxAuditEngine

    engine = SoxAuditEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    score = status_data["latest_compliance_score"]
    score_color = "green" if score >= 90.0 else ("yellow" if score >= 70.0 else "red")

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG KIỂM TOÁN NỘI BỘ SOX 404 & ITGC DOANH NGHIỆP[/]\n\n"
            f"  Trạng thái:            [bold green]{status_data['status'].upper()}[/]\n"
            f"  Khung quy chuẩn:       {', '.join(status_data['frameworks'])}\n"
            f"  Tổng số chốt kiểm soát: [bold]{status_data['total_controls_in_catalog']} controls[/] across 4 domains\n"
            f"  Điểm tuân thủ gần nhất: [bold {score_color}]{score:.1f}%[/bold {score_color}]\n"
            f"  Ý kiến kiểm toán:      [bold cyan]{status_data['latest_audit_opinion']}[/]\n"
            f"  Lượt kiểm toán đã chạy: [bold]{status_data['total_audit_runs']}[/]\n"
            f"  Số lỗi/khiếm khuyết mở: [{'red' if status_data['open_findings_count'] > 0 else 'green'}]{status_data['open_findings_count']} findings[/]",
            title="[bold blue]SOX & ITGC Internal Controls Posture[/]",
            border_style="green",
        )
    )

    table = Table(title="Lịch Sử Các Đợt Kiểm Toán Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã Kiểm Toán", style="dim", width=16)
    table.add_column("Framework", style="cyan", width=12)
    table.add_column("Chốt Đạt", justify="center", width=10)
    table.add_column("Chốt Không Đạt", justify="center", width=12)
    table.add_column("Điểm Số", justify="right", width=12)
    table.add_column("Thời Gian", style="dim", width=22)

    for run in status_data.get("recent_audit_runs", []):
        r_score = run["compliance_score"]
        r_color = "green" if r_score >= 90.0 else ("yellow" if r_score >= 70.0 else "red")
        table.add_row(
            run["audit_id"],
            run["framework"],
            str(run["passed_controls"]),
            str(run["failed_controls"]),
            f"[{r_color}]{r_score:.1f}%[/]",
            run["executed_at"][:19],
        )

    console.print(table)


@audit_app.command(name="run")
def audit_run(
    framework: str = typer.Option("all", "--framework", "-f", help="Khung kiểm toán (sox, itgc, all)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả kiểm toán dạng JSON"),
) -> None:
    """Thực thi quy trình kiểm toán tự động các chốt kiểm soát nội bộ (SOX 404 / ITGC)."""
    from src.core.sox_audit_engine import SoxAuditEngine

    engine = SoxAuditEngine()
    res = engine.run_audit(framework=framework)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    score = res["compliance_score"]
    score_color = "green" if score >= 90.0 else ("yellow" if score >= 70.0 else "red")

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ KIỂM TOÁN NỘI BỘ HOÀN TẤT — {res['audit_id']}[/]\n\n"
            f"  Khung quy chuẩn:       [bold cyan]{res['framework']}[/]\n"
            f"  Tổng chốt kiểm soát:   [bold]{res['total_controls_tested']}[/]\n"
            f"  Chốt kiểm soát ĐẠT:    [bold green]{res['passed_controls']}[/]\n"
            f"  Chốt kiểm soát KHÔNG ĐẠT: [bold red]{res['failed_controls']}[/]\n"
            f"  Điểm tuân thủ:         [bold {score_color}]{score:.1f}%[/bold {score_color}]\n"
            f"  Ý kiến kiểm toán:      [bold]{res['audit_opinion']}[/]\n"
            f"  Số khiếm khuyết ghi nhận: [{'red' if res['findings_count'] > 0 else 'green'}]{res['findings_count']} findings[/]",
            title="[bold blue]Audit Execution Summary[/]",
            border_style="green",
        )
    )

    table = Table(title="Chi Tiết Đánh Giá Từng Chốt Kiểm Soát", show_header=True, header_style="bold cyan")
    table.add_column("Mã Chốt", style="dim", width=14)
    table.add_column("Tên Chốt Kiểm Soát", width=28)
    table.add_column("Miền", justify="center", width=8)
    table.add_column("Mức Rủi Ro", justify="center", width=12)
    table.add_column("Kết Quả", justify="center", width=10)
    table.add_column("Bằng Chứng Kiểm Toán", width=35)

    for t in res["test_results"]:
        status_styled = "[bold green]PASS[/]" if t["status"] == "PASSED" else "[bold red]FAIL[/]"
        table.add_row(
            t["control_id"],
            t["control_name"],
            t["domain"],
            t["risk_level"],
            status_styled,
            t["evidence"],
        )

    console.print(table)


@audit_app.command(name="controls")
def audit_controls(
    domain: str = typer.Option("all", "--domain", "-d", help="Lọc theo miền (AC, CM, CO, SD, all)"),
    framework: str = typer.Option("all", "--framework", "-f", help="Lọc theo framework (sox, itgc, all)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh mục chốt kiểm soát dạng JSON"),
) -> None:
    """Tra cứu ma trận các chốt kiểm soát nội bộ và thủ tục kiểm tra."""
    from src.core.sox_audit_engine import SoxAuditEngine

    engine = SoxAuditEngine()
    controls = engine.list_controls(domain=domain, framework=framework)

    if json_mode:
        typer.echo(json.dumps({"total": len(controls), "controls": controls}, indent=2, ensure_ascii=False))
        return

    table = Table(title="Ma Trận Chốt Kiểm Soát Nội Bộ (SOX 404 & ITGC)", show_header=True, header_style="bold magenta")
    table.add_column("Mã Chốt", style="dim", width=14)
    table.add_column("Miền", justify="center", width=8)
    table.add_column("Framework", justify="center", width=10)
    table.add_column("Mức Rủi Ro", justify="center", width=12)
    table.add_column("Tên Chốt Kiểm Soát", style="bold cyan", width=26)
    table.add_column("Mục Tiêu & Thủ Tục Kiểm Soát", width=38)

    for c in controls:
        table.add_row(
            c["control_id"],
            c["domain"],
            c["framework"],
            c["risk_level"],
            c["name"],
            c["description"],
        )

    console.print(table)


@audit_app.command(name="findings")
def audit_findings(
    severity: str = typer.Option("all", "--severity", "-s", help="Lọc theo mức độ nghiêm trọng (critical, high, medium, low, all)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách khiếm khuyết dạng JSON"),
) -> None:
    """Xem danh sách các phát hiện kiểm toán, khiếm khuyết nội bộ và phương án khắc phục."""
    from src.core.sox_audit_engine import SoxAuditEngine

    engine = SoxAuditEngine()
    findings = engine.list_findings(min_severity=severity)

    if json_mode:
        typer.echo(json.dumps({"total": len(findings), "findings": findings}, indent=2, ensure_ascii=False))
        return

    table = Table(title="Danh Sách Khiếm Khuyết Kiểm Toán & Kế Hoạch Khắc Phục", show_header=True, header_style="bold red")
    table.add_column("Mã Lỗi", style="dim", width=14)
    table.add_column("Chốt Liên Quan", style="cyan", width=14)
    table.add_column("Mức Độ", justify="center", width=12)
    table.add_column("Tiêu Đề Khiếm Khuyết", style="bold", width=26)
    table.add_column("Kế Hoạch Khắc Phục (Remediation)", width=35)
    table.add_column("Trạng Thái", justify="center", width=10)

    for f in findings:
        table.add_row(
            f["finding_id"],
            f["control_id"],
            f["severity"],
            f["title"],
            f["remediation"],
            f["status"],
        )

    console.print(table)


@audit_app.command(name="status")
def audit_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái hệ thống kiểm toán dạng JSON"),
) -> None:
    """Kiểm tra tổng quan vị thế kiểm toán và tỷ lệ tuân thủ nội bộ."""
    from src.core.sox_audit_engine import SoxAuditEngine

    engine = SoxAuditEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    score = status_data["latest_compliance_score"]
    score_color = "green" if score >= 90.0 else ("yellow" if score >= 70.0 else "red")

    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG KIỂM TOÁN NỘI BỘ[/]\n\n"
            f"Trạng thái:               [bold green]{status_data['status'].upper()}[/]\n"
            f"Tổng số chốt kiểm soát:   [bold]{status_data['total_controls_in_catalog']}[/]\n"
            f"Các miền kiểm soát:       {', '.join(status_data['domains'])}\n"
            f"Tổng lượt kiểm toán chạy: [cyan]{status_data['total_audit_runs']}[/]\n"
            f"Tổng số test chốt chạy:   [cyan]{status_data['total_control_tests_performed']}[/]\n"
            f"Số khiếm khuyết đang mở:  [{'red' if status_data['open_findings_count'] > 0 else 'green'}]{status_data['open_findings_count']}[/]\n"
            f"Điểm tuân thủ gần nhất:   [bold {score_color}]{score:.1f}%[/bold {score_color}]\n"
            f"Ý kiến kiểm toán:         [bold cyan]{status_data['latest_audit_opinion']}[/]",
            title="[bold blue]SOX / ITGC Telemetry[/]",
            border_style="green",
        )
    )
