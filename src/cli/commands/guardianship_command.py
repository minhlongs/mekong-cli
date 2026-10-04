# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Guardianship, Custodianship & Ward Protection Command Surface (Phase 148).

Statutory framework:
- Civil Code 2015 (Luật Dân sự số 91/2015/QH13) - Chương III Mục 4: Giám hộ (Điều 46–63)
- Law on Civil Status 2014 (Luật Hộ tịch số 60/2014/QH13) - Điều 19–21 & 39–41
- Decree No. 126/2014/ND-CP detailing provisions on family and civil relations
- Decree No. 82/2020/ND-CP on administrative penalties in civil status & judicial assistance
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.guardianship_engine import (
    AssetCategory,
    GuardianRelationship,
    GuardianshipEngine,
    GuardianshipStatus,
    GuardianshipType,
    TerminationGrounds,
    TransactionType,
    WardCategory,
)

guardianship_app = typer.Typer(
    name="guardianship",
    help="Vietnamese Guardianship, Custodianship & Ward Protection Suite (BLDS 2015 Điều 46–63 & Luật Hộ tịch 2014).",
    no_args_is_help=False,
)
app = guardianship_app
console = Console()


def _render_status_dashboard(telemetry: dict, recent_cases: list) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG GIÁM HỘ & BẢO VỆ NGƯỜI ĐƯỢC GIÁM HỘ[/bold cyan]\n"
            "[bold green]QUẢN LÝ QUYỀN GIÁM HỘ, GIÁM SÁT & BẢO TOÀN TÀI SẢN (BLDS 2015 ĐIỀU 46–63)[/bold green]\n"
            "[dim]Civil Code 2015 (Articles 46–63) & Law on Civil Status 2014 (Articles 19–21 & 39–41)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    summary_table = Table(title="Chỉ số Vận hành & Giám hộ Toàn quốc (Guardianship & Asset Protection Telemetry)", box=box.ROUNDED)
    summary_table.add_column("Chỉ số giám hộ / Giám sát", style="cyan")
    summary_table.add_column("Giá trị ghi nhận", style="bold green")

    summary_table.add_row("Tổng số vụ việc giám hộ", str(telemetry.get("total_guardianship_cases", 0)))
    summary_table.add_row("Hồ sơ đang hiệu lực (ACTIVE)", str(telemetry.get("active_cases", 0)))
    summary_table.add_row("Hồ sơ đã chấm dứt (TERMINATED)", str(telemetry.get("terminated_cases", 0)))
    summary_table.add_row("Người chưa thành niên được bảo vệ", str(telemetry.get("minor_wards_protected", 0)))
    summary_table.add_row("Người mất/khó khăn NLHV dân sự", str(telemetry.get("adult_incapacitated_wards", 0)))
    summary_table.add_row("Người giám sát đã đăng ký (Điều 51)", str(telemetry.get("active_supervisors", 0)))
    summary_table.add_row("Tỷ lệ bao phủ giám sát", f"{telemetry.get('supervisor_coverage_pct', 0.0)}%")
    summary_table.add_row("Tổng số tài sản quản lý (Điều 59)", str(telemetry.get("total_managed_assets_count", 0)))
    summary_table.add_row("Tổng giá trị tài sản kiểm kê (VND)", f"{telemetry.get('total_managed_assets_vnd', 0.0):,.0f} VND")
    summary_table.add_row("Giao dịch tài sản đã thẩm định", str(telemetry.get("total_transactions_count", 0)))
    summary_table.add_row("Nhật ký tuân thủ (Audit Logs)", str(telemetry.get("compliance_audit_logs", 0)))

    console.print(summary_table)

    if recent_cases:
        table = Table(title="Hồ sơ Giám hộ Gần đây (Recent Guardianship Cases)", box=box.ROUNDED, show_header=True)
        table.add_column("Mã hồ sơ", style="bold green")
        table.add_column("Số xác nhận", style="dim")
        table.add_column("Người được giám hộ", style="cyan")
        table.add_column("Người giám hộ", style="white")
        table.add_column("Quan hệ", style="magenta")
        table.add_column("UBND cấp xã", style="yellow")
        table.add_column("Trạng thái", style="bold blue")

        for c in recent_cases[:10]:
            table.add_row(
                c.get("registration_id", "-"),
                c.get("certificate_code", "-"),
                c.get("ward_name", "-"),
                c.get("guardian_name", "-"),
                c.get("guardian_relationship", "-"),
                c.get("commune_ubnd", "-"),
                c.get("status", "-"),
            )
        console.print(table)


@guardianship_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Quản lý giám hộ, người giám sát & bảo vệ tài sản người được giám hộ (BLDS 2015)."""
    if ctx.invoked_subcommand is None:
        engine = GuardianshipEngine()
        telemetry = engine.get_telemetry_status()
        recent = engine.list_registrations(limit=10)
        if json_output:
            typer.echo(json.dumps({"telemetry": telemetry, "recent_cases": recent}, indent=2, ensure_ascii=False))
        else:
            _render_status_dashboard(telemetry, recent)


@guardianship_app.command(name="status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị bảng điều hành giám sát và bảo vệ người được giám hộ toàn quốc."""
    engine = GuardianshipEngine()
    telemetry = engine.get_telemetry_status()
    recent = engine.list_registrations(limit=10)
    if json_output:
        typer.echo(json.dumps({"telemetry": telemetry, "recent_cases": recent}, indent=2, ensure_ascii=False))
    else:
        _render_status_dashboard(telemetry, recent)


@guardianship_app.command(name="register")
def register_cmd(
    ward_name: str = typer.Argument(..., help="Họ và tên người được giám hộ"),
    ward_dob: str = typer.Argument(..., help="Ngày sinh người được giám hộ (YYYY-MM-DD)"),
    ward_id: str = typer.Argument(..., help="Số CCCD / Mã định danh cá nhân người được giám hộ"),
    guardian_name: str = typer.Argument(..., help="Họ và tên người giám hộ"),
    guardian_dob: str = typer.Argument(..., help="Ngày sinh người giám hộ (YYYY-MM-DD, từ đủ 18 tuổi)"),
    guardian_id: str = typer.Argument(..., help="Số CCCD của người giám hộ"),
    ward_address: str = typer.Option("123 Hai Bà Trưng, Quận 1, TP.HCM", "--ward-address", help="Địa chỉ cư trú người được giám hộ"),
    guardian_address: str = typer.Option("123 Hai Bà Trưng, Quận 1, TP.HCM", "--guardian-address", help="Địa chỉ cư trú người giám hộ"),
    guardian_phone: str = typer.Option("0901234567", "--guardian-phone", help="Số điện thoại người giám hộ"),
    category: str = typer.Option(WardCategory.MINOR_NO_PARENTS.value, "--category", help="Loại đối tượng được giám hộ"),
    relationship: str = typer.Option(GuardianRelationship.ELDER_SIBLING.value, "--relationship", help="Quan hệ với người được giám hộ"),
    guardianship_type: str = typer.Option(GuardianshipType.NATURAL.value, "--type", help="Căn cứ giám hộ (NATURAL/APPOINTED_COMMUNE/DESIGNATED_COURT)"),
    commune_ubnd: str = typer.Option("UBND Phường Bến Nghé", "--commune-ubnd", help="UBND cấp xã nơi đăng ký giám hộ"),
    district: str = typer.Option("Quận 1", "--district", help="Quận / Huyện"),
    province: str = typer.Option("TP. Hồ Chí Minh", "--province", help="Tỉnh / Thành phố"),
    notes: str = typer.Option("", "--notes", help="Ghi chú hồ sơ"),
    has_full_capacity: bool = typer.Option(True, "--has-full-capacity", help="Có năng lực hành vi dân sự đầy đủ"),
    has_conviction: bool = typer.Option(False, "--has-conviction", help="Có tiền án xâm phạm tính mạng, sức khỏe, danh dự, tài sản"),
    parental_restricted: bool = typer.Option(False, "--parental-restricted", help="Bị hạn chế quyền của cha mẹ đối với con chưa thành niên"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký giám hộ tại UBND cấp xã với kiểm tra điều kiện Điều 48 BLDS 2015."""
    engine = GuardianshipEngine()
    try:
        res = engine.register_guardianship(
            ward_name=ward_name,
            ward_dob=ward_dob,
            ward_id_number=ward_id,
            ward_address=ward_address,
            ward_category=category,
            guardian_name=guardian_name,
            guardian_dob=guardian_dob,
            guardian_id_number=guardian_id,
            guardian_address=guardian_address,
            guardian_phone=guardian_phone,
            guardian_relationship=relationship,
            guardianship_type=guardianship_type,
            commune_ubnd=commune_ubnd,
            district=district,
            province=province,
            notes=notes,
            has_full_capacity=has_full_capacity,
            has_conviction_against_life_property=has_conviction,
            parental_rights_restricted=parental_restricted,
        )
        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✓ Đăng ký giám hộ thành công![/bold green]")
            console.print(f"Mã hồ sơ: [cyan]{res['registration_id']}[/cyan]")
            console.print(f"Giấy xác nhận: [bold yellow]{res['certificate_code']}[/bold yellow]")
            console.print(f"Người được giám hộ: [white]{res['ward_name']}[/white] ({res['ward_category']})")
            console.print(f"Người giám hộ: [white]{res['guardian_name']}[/white] ({res['guardian_relationship']})")
            console.print(f"Cơ quan đăng ký: [cyan]{res['commune_ubnd']}, {res['district']}, {res['province']}[/cyan]")
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold red]✗ Lỗi đăng ký giám hộ:[/bold red] {exc}")
        raise typer.Exit(1)


@guardianship_app.command(name="supervisor")
def supervisor_cmd(
    registration_id: str = typer.Argument(..., help="Mã hồ sơ giám hộ"),
    supervisor_name: str = typer.Argument(..., help="Họ và tên người giám sát việc giám hộ"),
    supervisor_id: str = typer.Argument(..., help="Số CCCD người giám sát"),
    supervisor_dob: str = typer.Option("1980-05-15", "--dob", help="Ngày sinh người giám sát (YYYY-MM-DD)"),
    supervisor_address: str = typer.Option("456 Lê Lợi, Quận 1, TP.HCM", "--address", help="Địa chỉ người giám sát"),
    relationship: str = typer.Option("CLOSE_RELATIVE", "--relationship", help="Mối quan hệ họ hàng với người được giám hộ"),
    authority: str = typer.Option("UBND Phường Bến Nghé", "--authority", help="Cơ quan đăng ký/cử người giám sát"),
    has_full_capacity: bool = typer.Option(True, "--has-full-capacity", help="Có đầy đủ năng lực hành vi dân sự"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký người giám sát việc giám hộ theo quy định tại Điều 51 BLDS 2015."""
    engine = GuardianshipEngine()
    try:
        res = engine.register_supervisor(
            registration_id=registration_id,
            supervisor_name=supervisor_name,
            supervisor_dob=supervisor_dob,
            supervisor_id_number=supervisor_id,
            supervisor_address=supervisor_address,
            supervisor_relationship=relationship,
            appointing_authority=authority,
            has_full_capacity=has_full_capacity,
        )
        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✓ Đăng ký người giám sát thành công![/bold green]")
            console.print(f"Mã giám sát: [cyan]{res['supervisor_id']}[/cyan]")
            console.print(f"Họ tên người giám sát: [white]{res['supervisor_name']}[/white]")
            console.print(f"Cơ quan cử/công nhận: [yellow]{res['appointing_authority']}[/yellow]")
            console.print(f"Căn cứ pháp lý: [dim]{res['statutory_role']}[/dim]")
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold red]✗ Lỗi đăng ký người giám sát:[/bold red] {exc}")
        raise typer.Exit(1)


@guardianship_app.command(name="inventory")
def inventory_cmd(
    registration_id: str = typer.Argument(..., help="Mã hồ sơ giám hộ"),
    asset_name: str = typer.Argument(..., help="Tên tài sản của người được giám hộ"),
    category: str = typer.Argument(..., help="Loại tài sản (REAL_ESTATE, VEHICLE, BANK_DEPOSIT, LIVESTOCK, OTHER)"),
    value: float = typer.Argument(..., help="Giá trị ước tính (VND)"),
    identifier: str = typer.Option("GCN-001/2026", "--identifier", help="Mã định danh/số giấy tờ tài sản"),
    inventory_date: Optional[str] = typer.Option(None, "--date", help="Ngày kiểm kê tài sản (YYYY-MM-DD)"),
    is_verified: bool = typer.Option(True, "--is-verified", help="Có người giám sát/người làm chứng chứng kiến"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Kiểm kê tài sản của người được giám hộ trong thời hạn 10 ngày (Điều 59.1 BLDS 2015)."""
    engine = GuardianshipEngine()
    try:
        res = engine.record_asset_inventory(
            registration_id=registration_id,
            asset_name=asset_name,
            asset_category=category,
            estimated_value_vnd=value,
            identifier=identifier,
            inventory_date=inventory_date,
            is_verified_by_supervisor=is_verified,
        )
        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✓ Ghi nhận kiểm kê tài sản thành công![/bold green]")
            console.print(f"Mã tài sản: [cyan]{res['asset_id']}[/cyan]")
            console.print(f"Tài sản: [white]{res['asset_name']}[/white] ({res['category']})")
            console.print(f"Giá trị: [bold yellow]{res['estimated_value_vnd']:,.0f} VND[/bold yellow]")
            console.print(f"Thời hạn: [dim]{res['compliance_note']}[/dim]")
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold red]✗ Lỗi kiểm kê tài sản:[/bold red] {exc}")
        raise typer.Exit(1)


@guardianship_app.command(name="transact")
def transact_cmd(
    registration_id: str = typer.Argument(..., help="Mã hồ sơ giám hộ"),
    transaction_type: str = typer.Argument(..., help="Loại giao dịch (SALE, LEASE, EXPENSE_CARE, EXPENSE_EDUCATION, TREATMENT, INVESTMENT, GIFT)"),
    amount: float = typer.Argument(..., help="Số tiền giao dịch (VND)"),
    purpose: str = typer.Argument(..., help="Mục đích giao dịch phục vụ lợi ích người được giám hộ"),
    asset_id: Optional[str] = typer.Option(None, "--asset-id", help="Mã tài sản phát sinh giao dịch"),
    supervisor_consent: bool = typer.Option(False, "--supervisor-consent", help="Sự đồng ý của người giám sát việc giám hộ"),
    major: Optional[bool] = typer.Option(None, "--major", help="Giao dịch dân sự có giá trị lớn (Điều 59.2)"),
    notes: str = typer.Option("", "--notes", help="Ghi chú giao dịch"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thực hiện giao dịch tài sản người được giám hộ có kiểm soát bảo vệ (Điều 59 BLDS 2015)."""
    engine = GuardianshipEngine()
    try:
        res = engine.record_asset_transaction(
            registration_id=registration_id,
            transaction_type=transaction_type,
            amount_vnd=amount,
            purpose=purpose,
            asset_id=asset_id,
            supervisor_consent=supervisor_consent,
            is_major_transaction=major,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✓ Giao dịch tài sản hợp lệ và đã được phê duyệt![/bold green]")
            console.print(f"Mã giao dịch: [cyan]{res['transaction_id']}[/cyan]")
            console.print(f"Loại giao dịch: [white]{res['transaction_type']}[/white]")
            console.print(f"Số tiền: [bold yellow]{res['amount_vnd']:,.0f} VND[/bold yellow]")
            console.print(f"Giao dịch giá trị lớn: {'Có' if res['is_major_transaction'] else 'Không'}")
            console.print(f"Đồng ý của người giám sát: {'Đã có' if res['supervisor_consent'] else 'Không bắt buộc'}")
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold red]✗ Giao dịch bị từ chối/vi phạm bảo vệ tài sản:[/bold red] {exc}")
        raise typer.Exit(1)


@guardianship_app.command(name="terminate")
def terminate_cmd(
    registration_id: str = typer.Argument(..., help="Mã hồ sơ giám hộ"),
    grounds: str = typer.Argument(..., help="Căn cứ chấm dứt (WARD_ATTAINED_MAJORITY, WARD_REGAINED_CAPACITY, WARD_DECEASED, PARENTS_RESUMED_RIGHTS, WARD_ADOPTED)"),
    handover_notes: str = typer.Option("", "--handover-notes", help="Ghi chú biên bản bàn giao tài sản"),
    completed: bool = typer.Option(False, "--completed", help="Đã hoàn tất bàn giao và thanh toán tài sản"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Chấm dứt việc giám hộ và kích hoạt thời hạn 3 tháng chuyển giao tài sản (Điều 62 & 63 BLDS 2015)."""
    engine = GuardianshipEngine()
    try:
        res = engine.terminate_guardianship(
            registration_id=registration_id,
            grounds=grounds,
            handover_notes=handover_notes,
            is_handover_completed=completed,
        )
        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✓ Chấm dứt giám hộ thành công![/bold green]")
            console.print(f"Mã hồ sơ: [cyan]{res['registration_id']}[/cyan]")
            console.print(f"Lý do chấm dứt: [yellow]{res['grounds']}[/yellow]")
            console.print(f"Hạn chót thanh toán & bàn giao tài sản (3 tháng): [bold red]{res['handover_deadline']}[/bold red]")
            console.print(f"Quy định pháp luật: [dim]{res['statutory_timeline']}[/dim]")
    except Exception as exc:
        if json_output:
            typer.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold red]✗ Lỗi chấm dứt giám hộ:[/bold red] {exc}")
        raise typer.Exit(1)


@guardianship_app.command(name="search")
def search_cmd(
    query: str = typer.Argument("", help="Từ khóa tìm kiếm (Tên, CCCD, số giấy chứng nhận, địa chỉ)"),
    limit: int = typer.Option(20, "--limit", help="Số lượng kết quả tối đa"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tìm kiếm hồ sơ người được giám hộ và người giám hộ."""
    engine = GuardianshipEngine()
    records = engine.search_records(query=query, limit=limit)
    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        table = Table(title=f"Kết quả Tìm kiếm Hồ sơ Giám hộ ('{query}')", box=box.ROUNDED)
        table.add_column("Mã hồ sơ", style="bold green")
        table.add_column("Giấy chứng nhận", style="dim")
        table.add_column("Người được giám hộ", style="cyan")
        table.add_column("Người giám hộ", style="white")
        table.add_column("Quan hệ", style="magenta")
        table.add_column("Trạng thái", style="yellow")

        for r in records:
            table.add_row(
                r.get("registration_id", "-"),
                r.get("certificate_code", "-"),
                r.get("ward_name", "-"),
                r.get("guardian_name", "-"),
                r.get("guardian_relationship", "-"),
                r.get("status", "-"),
            )
        console.print(table)


@guardianship_app.command(name="list")
def list_cmd(
    status: Optional[str] = typer.Option(None, "--status", help="Lọc theo trạng thái (ACTIVE, CHANGED, TERMINATED)"),
    category: Optional[str] = typer.Option(None, "--category", help="Lọc theo loại đối tượng (MINOR_NO_PARENTS, etc.)"),
    limit: int = typer.Option(50, "--limit", help="Số lượng hồ sơ tối đa"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Danh sách các hồ sơ giám hộ đã đăng ký."""
    engine = GuardianshipEngine()
    records = engine.list_registrations(status=status, ward_category=category, limit=limit)
    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        table = Table(title="Danh sách Hồ sơ Giám hộ Đăng ký", box=box.ROUNDED)
        table.add_column("Mã hồ sơ", style="bold green")
        table.add_column("Người được giám hộ", style="cyan")
        table.add_column("Loại đối tượng", style="white")
        table.add_column("Người giám hộ", style="magenta")
        table.add_column("Quan hệ", style="dim")
        table.add_column("Trạng thái", style="bold yellow")

        for r in records:
            table.add_row(
                r.get("registration_id", "-"),
                r.get("ward_name", "-"),
                r.get("ward_category", "-"),
                r.get("guardian_name", "-"),
                r.get("guardian_relationship", "-"),
                r.get("status", "-"),
            )
        console.print(table)
