# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Civil Judgment Enforcement, Asset Attachment & Debt Recovery Suite (Phase 116)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

enforcement_app = typer.Typer(
    name="enforcement",
    help="Vietnamese Civil Judgment Enforcement, Asset Attachment & Debt Recovery Suite.",
)
console = Console()


@enforcement_app.callback(invoke_without_command=True)
def enforcement_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động thi hành án dân sự, xác minh tài sản, cưỡng chế và phân bổ dòng tiền."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.enforcement_engine import EnforcementEngine

    engine = EnforcementEngine()
    telemetry = engine.get_enforcement_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    dos = telemetry["dossiers"]
    ver = telemetry["debtor_verifications"]
    coe = telemetry["coercive_measures"]
    dis = telemetry["proceeds_distributions"]

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN LÝ THI HÀNH ÁN DÂN SỰ & CƯỠNG CHẾ THU HỒI TÀI SẢN QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:               [bold]Luật Thi hành án dân sự 2008 (sửa đổi 2014 - Luật 64/2014/QH13)[/]\n"
            f"  Thời hiệu yêu cầu THADS:     [bold yellow]05 năm (Điều 30)[/] | Thời hạn tự nguyện: [bold yellow]10 ngày (Điều 45)[/]\n\n"
            f"  Hồ sơ bản án / phán quyết:   [bold]{dos['total_dossiers']}[/] vụ án ([bold green]{dos['active_enforcements']}[/] vụ đang thi hành)\n"
            f"  - Tổng số tiền phải thi hành:[bold yellow]{dos['total_claim_amount_vnd']:,.0f} VND[/]\n\n"
            f"  Xác minh điều kiện THADS:    [bold]{ver['total_verifications']}[/] lần xác minh tài sản, tài khoản\n"
            f"  - Tạm hoãn xuất cảnh (44a):  [bold red]{ver['exit_bans_imposed']}[/] đối tượng bị ngăn chặn xuất cảnh\n\n"
            f"  Biện pháp cưỡng chế áp dụng: [bold]{coe['total_measures']}[/] quyết định cưỡng chế\n"
            f"  - Giá trị tài sản kê biên:   [bold red]{coe['total_distrained_value_vnd']:,.0f} VND[/] (BĐS, phong tỏa TK, cổ phần)\n\n"
            f"  Phân bổ dòng tiền thu hồi:   [bold]{dis['total_distributions']}[/] đợt phân bổ theo thứ tự 6 bậc Điều 47\n"
            f"  - Tổng tiền đã thu hồi:      [bold green]{dis['total_recovered_vnd']:,.0f} VND[/]",
            title="[bold blue]Vietnam Civil Judgment Enforcement Telemetry (THADS)[/]",
            border_style="blue",
        )
    )


@enforcement_app.command("dossier")
def dossier_cmd(
    title: str = typer.Argument(..., help="Tiêu đề bản án / quyết định Tòa án hoặc phán quyết Trọng tài"),
    creditor: str = typer.Option(..., "--creditor", help="Người được thi hành án / Bên được thi hành"),
    debtor: str = typer.Option(..., "--debtor", help="Người phải thi hành án / Bên có nghĩa vụ"),
    claim: float = typer.Option(..., "--claim", help="Số tiền hoặc giá trị nghĩa vụ phải thi hành (VND)"),
    type: str = typer.Option("COURT_COMMERCIAL", "--type", help="Loại bản án (COURT_CIVIL, COURT_COMMERCIAL, ARBITRAL_AWARD, LABOR_DISPUTE)"),
    agency: str = typer.Option("Cục Thi hành án dân sự TP.HCM", "--agency", help="Cơ quan thi hành án thụ lý"),
    date: Optional[str] = typer.Option(None, "--date", help="Ngày ban hành bản án (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Lập hồ sơ thụ lý thi hành bản án, quyết định Tòa án hoặc phán quyết Trọng tài theo Điều 36."""
    from src.core.enforcement_engine import EnforcementEngine

    engine = EnforcementEngine()
    result = engine.create_judgment_dossier(
        judgment_title=title,
        creditor_name=creditor,
        debtor_name=debtor,
        total_claim_vnd=claim,
        judgment_type=type,
        enforcement_agency=agency,
        judgment_date=date,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"THỤ LÝ HỒ SƠ THI HÀNH ÁN: {title}", border_style="blue")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Chi tiết hồ sơ", style="bold")

    table.add_row("Mã hồ sơ THADS", result["id"])
    table.add_row("Người được thi hành án", result["creditor_name"])
    table.add_row("Người phải thi hành án", result["debtor_name"])
    table.add_row("Số tiền phải thi hành", f"{result['total_claim_vnd']:,.0f} VND")
    table.add_row("Phân loại bản án", result["judgment_type"])
    table.add_row("Cơ quan THADS thụ lý", result["enforcement_agency"])
    table.add_row("Ngày bản án", result["judgment_date"])
    table.add_row("Hạn tự nguyện THADS (10 ngày)", f"[bold yellow]{result['voluntary_deadline']}[/]")
    table.add_row("Trạng thái hồ sơ", f"[bold green]{result['status']}[/]")

    console.print(table)


@enforcement_app.command("verify")
def verify_cmd(
    dossier: str = typer.Argument(..., help="Mã hồ sơ thi hành án (DOS-XXXX)"),
    assets: float = typer.Option(..., "--assets", help="Giá trị tài sản xác minh được (VND)"),
    solvent: bool = typer.Option(True, "--solvent/--insolvent", help="Có điều kiện thi hành án hay không có điều kiện"),
    bank_frozen: bool = typer.Option(False, "--bank-frozen", help="Đã phong tỏa tài khoản ngân hàng"),
    salary_garnished: bool = typer.Option(False, "--salary-garnished", help="Đã khấu trừ thu nhập / lương"),
    exit_ban: bool = typer.Option(False, "--exit-ban", help="Áp dụng biện pháp tạm hoãn xuất cảnh theo Điều 44a"),
    notes: str = typer.Option("", "--notes", help="Ghi chú xác minh điều kiện tài sản"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác minh điều kiện thi hành án và áp dụng biện pháp ngăn chặn tạm hoãn xuất cảnh theo Điều 44 & 44a."""
    from src.core.enforcement_engine import EnforcementEngine

    engine = EnforcementEngine()
    result = engine.verify_debtor_condition(
        dossier_id=dossier,
        verified_assets_vnd=assets,
        is_solvent=solvent,
        bank_account_frozen=bank_frozen,
        salary_garnished=salary_garnished,
        exit_ban_imposed=exit_ban,
        notes=notes,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"KẾT QUẢ XÁC MINH ĐIỀU KIỆN THI HÀNH ÁN: {dossier}", border_style="cyan")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Nội dung xác minh", style="bold")

    table.add_row("Mã biên bản", result["id"])
    table.add_row("Mã hồ sơ THADS", result["dossier_id"])
    table.add_row("Giá trị tài sản xác minh", f"{result['verified_assets_vnd']:,.0f} VND")
    table.add_row(
        "Kết luận điều kiện THADS",
        "[bold green]CÓ ĐIỀU KIỆN THI HÀNH ÁN[/]"
        if result["is_solvent"]
        else "[bold red]CHƯA CÓ ĐIỀU KIỆN THI HÀNH ÁN[/]",
    )
    table.add_row("Phong tỏa tài khoản ngân hàng", "CÓ" if result["bank_account_frozen"] else "KHÔNG")
    table.add_row("Khấu trừ thu nhập / lương", "CÓ" if result["salary_garnished"] else "KHÔNG")
    table.add_row(
        "Tạm hoãn xuất cảnh (Điều 44a)",
        "[bold red]ĐANG ÁP DỤNG NGĂN CHẶN XUẤT CẢNH[/]"
        if result["exit_ban_imposed"]
        else "KHÔNG ÁP DỤNG",
    )
    if result["notes"]:
        table.add_row("Ghi chú xác minh", result["notes"])

    console.print(table)


@enforcement_app.command("coerce")
def coerce_cmd(
    dossier: str = typer.Argument(..., help="Mã hồ sơ thi hành án (DOS-XXXX)"),
    measure: str = typer.Option(..., "--measure", help="Biện pháp cưỡng chế (BANK_FREEZE, SALARY_GARNISHMENT, ASSET_DISTRAINT, EQUITY_SEIZURE, REAL_ESTATE_SEIZURE, EXIT_BAN)"),
    target: str = typer.Option(..., "--target", help="Mô tả đối tượng cưỡng chế hoặc tài sản kê biên"),
    value: float = typer.Option(..., "--value", help="Giá trị ước tính của tài sản hoặc khoản khấu trừ (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ra quyết định áp dụng biện pháp cưỡng chế thi hành án (Kê biên BĐS, phong tỏa TK, khấu trừ lương) theo Điều 71."""
    from src.core.enforcement_engine import EnforcementEngine

    engine = EnforcementEngine()
    result = engine.order_coercive_measure(
        dossier_id=dossier,
        measure_type=measure,
        target_description=target,
        estimated_value_vnd=value,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"QUYẾT ĐỊNH CƯỠNG CHẾ THI HÀNH ÁN: {dossier}", border_style="red")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Chi tiết cưỡng chế", style="bold")

    table.add_row("Mã quyết định cưỡng chế", result["id"])
    table.add_row("Mã hồ sơ THADS", result["dossier_id"])
    table.add_row("Biện pháp cưỡng chế", f"[bold red]{result['measure_type']}[/]")
    table.add_row("Tài sản / Đối tượng kê biên", result["target_description"])
    table.add_row("Giá trị ước tính", f"{result['estimated_value_vnd']:,.0f} VND")
    table.add_row("Trạng thái", f"[bold green]{result['status']}[/]")

    console.print(table)


@enforcement_app.command("distribute")
def distribute_cmd(
    dossier: str = typer.Argument(..., help="Mã hồ sơ thi hành án (DOS-XXXX)"),
    recovered: float = typer.Option(..., "--recovered", help="Tổng số tiền thu hồi được từ bán đấu giá / cưỡng chế (VND)"),
    costs: float = typer.Option(0.0, "--costs", help="Chi phí cưỡng chế thi hành án - Hạng 1 (VND)"),
    wages: float = typer.Option(0.0, "--wages", help="Tiền cấp dưỡng, lương, BHXH người lao động - Hạng 2 (VND)"),
    court_fees: float = typer.Option(0.0, "--court-fees", help="Án phí Tòa án - Hạng 3 (VND)"),
    state_fines: float = typer.Option(0.0, "--state-fines", help="Tiền phạt, tịch thu sung công - Hạng 4 (VND)"),
    secured: float = typer.Option(0.0, "--secured", help="Nghĩa vụ có biện pháp bảo đảm (thế chấp) - Hạng 5 (VND)"),
    unsecured: float = typer.Option(0.0, "--unsecured", help="Nghĩa vụ không có bảo đảm - Hạng 6 (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Phân bổ số tiền thi hành án thu hồi được theo thứ tự 6 bậc ưu tiên luật định tại Điều 47 Luật THADS."""
    from src.core.enforcement_engine import EnforcementEngine

    engine = EnforcementEngine()
    result = engine.distribute_enforcement_proceeds(
        dossier_id=dossier,
        recovered_amount_vnd=recovered,
        enforcement_costs_vnd=costs,
        wages_and_alimony_vnd=wages,
        court_fees_vnd=court_fees,
        state_fines_vnd=state_fines,
        secured_claims_vnd=secured,
        unsecured_claims_vnd=unsecured,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"KẾ HOẠCH PHÂN BỔ TIỀN THI HÀNH ÁN (ĐIỀU 47 LUẬT THADS): {dossier}", border_style="green")
    table.add_column("Thứ tự ưu tiên", style="cyan")
    table.add_column("Khoản mục thanh toán", style="bold")
    table.add_column("Số tiền chi trả (VND)", style="bold green", justify="right")

    table.add_row("Tổng thu hồi", "Tiền cưỡng chế / đấu giá tài sản", f"{result['recovered_amount_vnd']:,.0f}")
    table.add_row("Hạng 1", "Chi phí cưỡng chế & bảo quản tài sản", f"{result['enforcement_costs_paid_vnd']:,.0f}")
    table.add_row("Hạng 2", "Tiền cấp dưỡng, lương thuyền viên / lao động, BHXH", f"{result['wages_alimony_paid_vnd']:,.0f}")
    table.add_row("Hạng 3", "Án phí, lệ phí Tòa án", f"{result['court_fees_paid_vnd']:,.0f}")
    table.add_row("Hạng 4", "Tiền phạt, sung quỹ nhà nước, nghĩa vụ thuế", f"{result['state_fines_paid_vnd']:,.0f}")
    table.add_row("Hạng 5", "Nghĩa vụ có biện pháp bảo đảm (Thế chấp / Cầm cố)", f"{result['secured_paid_vnd']:,.0f}")
    table.add_row(
        "Hạng 6",
        f"Nghĩa vụ không có bảo đảm (Tỷ lệ thu hồi: {result['unsecured_recovery_rate_pct']:.1f}%)",
        f"{result['unsecured_paid_vnd']:,.0f}",
    )
    table.add_row("Còn lại", "Số dư hoàn trả cho người phải THADS", f"{result['remaining_balance_vnd']:,.0f}")

    console.print(table)


@enforcement_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu (all, dossiers, verifications, measures, distributions)"),
    limit: int = typer.Option(50, "--limit", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ thi hành án, kết quả xác minh điều kiện, biện pháp cưỡng chế và phân bổ dòng tiền."""
    from src.core.enforcement_engine import EnforcementEngine

    engine = EnforcementEngine()
    records = engine.list_enforcement_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "dossiers" in records:
        table = Table(title=f"DANH SÁCH HỒ SƠ THI HÀNH ÁN ({len(records['dossiers'])})", border_style="blue")
        table.add_column("Mã hồ sơ", style="dim")
        table.add_column("Tiêu đề bản án", style="bold")
        table.add_column("Người được THA → Người phải THA")
        table.add_column("Số tiền phải THA", justify="right")
        table.add_column("Hạn tự nguyện")
        table.add_column("Trạng thái")
        for r in records["dossiers"]:
            table.add_row(
                r["id"],
                r["judgment_title"],
                f"{r['creditor_name']} → {r['debtor_name']}",
                f"{r['total_claim_vnd']:,.0f} VND",
                r["voluntary_deadline"],
                r["status"],
            )
        console.print(table)

    if "verifications" in records:
        table = Table(title=f"DANH SÁCH XÁC MINH ĐIỀU KIỆN THA ({len(records['verifications'])})", border_style="cyan")
        table.add_column("Mã BB", style="dim")
        table.add_column("Mã hồ sơ", style="bold")
        table.add_column("Tài sản xác minh", justify="right")
        table.add_column("Điều kiện THA")
        table.add_column("Tạm hoãn xuất cảnh")
        for r in records["verifications"]:
            table.add_row(
                r["id"],
                r["dossier_id"],
                f"{r['verified_assets_vnd']:,.0f} VND",
                "CÓ ĐIỀU KIỆN" if r["is_solvent"] else "CHƯA CÓ ĐIỀU KIỆN",
                "ĐANG ÁP DỤNG" if r["exit_ban_imposed"] else "KHÔNG",
            )
        console.print(table)

    if "measures" in records:
        table = Table(title=f"DANH SÁCH BIỆN PHÁP CƯỠNG CHẾ THA ({len(records['measures'])})", border_style="red")
        table.add_column("Mã QĐ", style="dim")
        table.add_column("Mã hồ sơ", style="bold")
        table.add_column("Biện pháp")
        table.add_column("Đối tượng kê biên")
        table.add_column("Giá trị ước tính", justify="right")
        table.add_column("Trạng thái")
        for r in records["measures"]:
            table.add_row(
                r["id"],
                r["dossier_id"],
                r["measure_type"],
                r["target_description"],
                f"{r['estimated_value_vnd']:,.0f} VND",
                r["status"],
            )
        console.print(table)

    if "distributions" in records:
        table = Table(title=f"DANH SÁCH PHÂN BỔ TIỀN THI HÀNH ÁN ({len(records['distributions'])})", border_style="green")
        table.add_column("Mã PB", style="dim")
        table.add_column("Mã hồ sơ", style="bold")
        table.add_column("Thu hồi được", justify="right")
        table.add_column("Có bảo đảm (Hạng 5)", justify="right")
        table.add_column("Không bảo đảm (Hạng 6)", justify="right")
        table.add_column("Tỷ lệ Hạng 6")
        for r in records["distributions"]:
            table.add_row(
                r["id"],
                r["dossier_id"],
                f"{r['recovered_amount_vnd']:,.0f} VND",
                f"{r['secured_paid_vnd']:,.0f} VND",
                f"{r['unsecured_paid_vnd']:,.0f} VND",
                f"{r['unsecured_recovery_rate_pct']:.1f}%",
            )
        console.print(table)


@enforcement_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Hiển thị chỉ số telemetry toàn diện hệ thống thi hành án dân sự và cưỡng chế quốc gia."""
    from src.core.enforcement_engine import EnforcementEngine

    engine = EnforcementEngine()
    telemetry = engine.get_enforcement_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="CHỈ SỐ TELEMETRY THI HÀNH ÁN DÂN SỰ & THU HỒI NỢ QUỐC GIA (THADS)", border_style="blue")
    table.add_column("Hạng mục giám sát", style="cyan")
    table.add_column("Chỉ số đo lường", style="bold yellow")

    table.add_row("Khung pháp lý", telemetry["statutory_framework"])
    table.add_row("Tổng số bản án thụ lý", str(telemetry["dossiers"]["total_dossiers"]))
    table.add_row("Hồ sơ đang thi hành", str(telemetry["dossiers"]["active_enforcements"]))
    table.add_row("Tổng số tiền phải thi hành", f"{telemetry['dossiers']['total_claim_amount_vnd']:,.0f} VND")
    table.add_row("Tổng lượt xác minh điều kiện", str(telemetry["debtor_verifications"]["total_verifications"]))
    table.add_row("Số đối tượng bị hoãn xuất cảnh", str(telemetry["debtor_verifications"]["exit_bans_imposed"]))
    table.add_row("Số quyết định cưỡng chế", str(telemetry["coercive_measures"]["total_measures"]))
    table.add_row("Tổng giá trị tài sản kê biên", f"{telemetry['coercive_measures']['total_distrained_value_vnd']:,.0f} VND")
    table.add_row("Số đợt phân bổ dòng tiền", str(telemetry["proceeds_distributions"]["total_distributions"]))
    table.add_row("Tổng số tiền đã thu hồi chi trả", f"{telemetry['proceeds_distributions']['total_recovered_vnd']:,.0f} VND")
    table.add_row("Đường dẫn CSDL", telemetry["database_path"])

    console.print(table)
