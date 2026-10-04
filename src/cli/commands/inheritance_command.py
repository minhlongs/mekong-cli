# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Inheritance, Wills, Estate Administration & Succession Regimes Command Surface (Phase 148).

Statutory framework:
- Civil Code 2015 (Law No. 91/2015/QH13) - Part Four: Inheritance (Articles 609-662)
- Law on Notarization 2014 (Law No. 53/2014/QH13) - Articles 57, 58, 59
- Decree No. 23/2015/ND-CP on certification of legal documents & signatures
- Land Law 2024 (Law No. 31/2024/QH15) on land use rights inheritance
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.inheritance_engine import (
    AssetCategory,
    HeirRank,
    HeirRelationship,
    InheritanceEngine,
    NotaryProcedureType,
    ObligationPriority,
    SuccessionType,
    WillForm,
)

inheritance_app = typer.Typer(
    name="inheritance",
    help="Vietnamese Inheritance, Wills, Estate Administration & Succession Regimes Suite (BLDS 2015 Điều 609-662).",
    no_args_is_help=False,
)
app = inheritance_app
console = Console()


def _render_status_dashboard(estates: list) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — PHÁP LUẬT THỪA KẾ & DI SẢN[/bold cyan]\n"
            "[bold green]BẢNG ĐIỀU HÀNH QUẢN LÝ DI SẢN, DI CHÚC & PHÂN CHIA THỪA KẾ (BLDS 2015)[/bold green]\n"
            "[dim]Civil Code 2015 (Articles 609-662) & Law on Notarization 2014 (Articles 57-59)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Tổng quan Hồ sơ Quản lý Di sản Thừa kế (Estate Succession Telemetry)", box=box.ROUNDED, show_header=True)
    table.add_column("Mã Di sản (ID)", style="bold green")
    table.add_column("Người để lại di sản", style="cyan")
    table.add_column("Ngày mở thừa kế", style="white")
    table.add_column("Hình thức thừa kế", style="magenta")
    table.add_column("Trạng thái", style="bold yellow")

    if not estates:
        table.add_row("Chưa có dữ liệu", "-", "-", "-", "-")
    else:
        for est in estates[:10]:
            status_text = "[bold green]Đã phân chia[/bold green]" if est.get("is_settled") else "[yellow]Đang xử lý[/yellow]"
            table.add_row(
                est.get("estate_id", "-"),
                est.get("decedent_name", "-"),
                est.get("date_of_death", "-"),
                est.get("succession_type", "-"),
                status_text,
            )

    console.print(table)


@inheritance_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """National Inheritance, Wills & Estate Administration Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = InheritanceEngine()
        estates = engine.list_estates()
        if json_output:
            console.print(json.dumps(estates, indent=2, ensure_ascii=False))
        else:
            _render_status_dashboard(estates)


@inheritance_app.command("estate-create")
def estate_create(
    decedent_name: str = typer.Option(..., "--name", "-n", help="Họ và tên người để lại di sản"),
    decedent_id: str = typer.Option(..., "--id-number", "-i", help="Số CCCD/Định danh cá nhân của người chết"),
    dob: str = typer.Option(..., "--dob", help="Ngày sinh (YYYY-MM-DD)"),
    date_of_death: str = typer.Option(..., "--dod", help="Ngày chết / Ngày mở thừa kế (YYYY-MM-DD)"),
    place_of_death: str = typer.Option("Hà Nội, Việt Nam", "--pod", help="Nơi chết"),
    last_residence: str = typer.Option("Hà Nội, Việt Nam", "--residence", "-r", help="Nơi cư trú cuối cùng"),
    administrator_name: Optional[str] = typer.Option(None, "--admin", help="Người quản lý di sản (Điều 616)"),
    worship_amount: float = typer.Option(0.0, "--worship", help="Di sản dành cho việc thờ cúng (Điều 645)"),
    succession_type: str = typer.Option(SuccessionType.INTESTATE.value, "--type", "-t", help="TESTAMENTARY / INTESTATE / MIXED"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Ghi chú thêm"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Mở hồ sơ quản lý di sản thừa kế (Articles 609, 611, 612 BLDS 2015)."""
    engine = InheritanceEngine()
    try:
        res = engine.create_estate(
            decedent_name=decedent_name,
            decedent_id_number=decedent_id,
            decedent_dob=dob,
            date_of_death=date_of_death,
            place_of_death=place_of_death,
            last_residence=last_residence,
            administrator_name=administrator_name,
            dedicated_worship_amount=worship_amount,
            succession_type=succession_type,
            notes=notes,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Mở hồ sơ di sản thành công![/bold green] Mã hồ sơ: [cyan]{res['estate_id']}[/cyan]")
            console.print(f"Người để lại di sản: [bold]{res['decedent_name']}[/bold] (Ngày chết: {res['date_of_death']})")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi mở hồ sơ di sản:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("asset-add")
def asset_add(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    asset_name: str = typer.Option(..., "--name", "-n", help="Tên tài sản di sản"),
    category: str = typer.Option(AssetCategory.REAL_ESTATE.value, "--category", "-c", help="REAL_ESTATE, VEHICLE, BANK_DEPOSIT_SAVINGS, CORPORATE_SHARES_EQUITY, PRECIOUS_ASSET, CASH_MONETARY, OTHER"),
    value: float = typer.Option(..., "--value", "-v", help="Giá trị ước tính (VND)"),
    is_sole_ownership: bool = typer.Option(True, "--sole/--common", help="Tài sản riêng của người chết hay tài sản chung"),
    ownership_share: float = typer.Option(1.0, "--share", "-s", help="Tỷ lệ sở hữu của người chết (mặc định 1.0 cho tài sản riêng, 0.5 cho tài sản chung vợ chồng)"),
    doc_ref: Optional[str] = typer.Option(None, "--doc", help="Số giấy tờ sở hữu (Sổ đỏ, sổ tiết kiệm, cà vẹt xe)"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Địa chỉ / nơi tọa lạc của tài sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Thêm tài sản vào danh mục kiểm kê di sản thừa kế (Điều 612 BLDS 2015)."""
    engine = InheritanceEngine()
    try:
        res = engine.add_estate_asset(
            estate_id=estate_id,
            asset_name=asset_name,
            category=category,
            estimated_value=value,
            is_sole_ownership=is_sole_ownership,
            ownership_share=ownership_share,
            legal_document_ref=doc_ref,
            location=location,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Đã thêm tài sản di sản:[/bold green] [cyan]{res['asset_name']}[/cyan] (Mã: {res['asset_id']})")
            console.print(f"Giá trị di sản thực nhận: [bold yellow]{res['net_estate_value']:,.0f} VND[/bold yellow] (Tỷ lệ: {res['ownership_share']*100:.0f}%)")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi thêm tài sản:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("obligation-add")
def obligation_add(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    creditor: str = typer.Option(..., "--creditor", help="Tên chủ nợ / người có quyền"),
    obligation_name: str = typer.Option(..., "--name", "-n", help="Nội dung nghĩa vụ tài sản"),
    priority: str = typer.Option(ObligationPriority.P1_BURIAL_EXPENSES.value, "--priority", "-p", help="Thứ tự ưu tiên thanh toán theo Điều 658 BLDS 2015 (P1_BURIAL_EXPENSES đến P9_OTHER_OBLIGATIONS)"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền nghĩa vụ (VND)"),
    legal_basis: Optional[str] = typer.Option(None, "--basis", help="Căn cứ pháp lý / hợp đồng vay"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Ghi nhận nghĩa vụ tài sản và nợ của người chết theo thứ tự ưu tiên (Điều 615 & 658 BLDS 2015)."""
    engine = InheritanceEngine()
    try:
        res = engine.add_estate_obligation(
            estate_id=estate_id,
            creditor_name=creditor,
            obligation_name=obligation_name,
            priority=priority,
            amount=amount,
            legal_basis=legal_basis,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Đã ghi nhận nghĩa vụ tài sản:[/bold green] [yellow]{res['obligation_name']}[/yellow]")
            console.print(f"Chủ nợ: {res['creditor_name']} | Ưu tiên: {res['priority']} | Số tiền: [bold]{res['amount']:,.0f} VND[/bold]")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi ghi nhận nghĩa vụ tài sản:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("will-register")
def will_register(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    form: str = typer.Option(WillForm.WRITTEN_NOTARIZED.value, "--form", "-f", help="WRITTEN_NOTARIZED, WRITTEN_CERTIFIED, WRITTEN_WITNESSED, WRITTEN_UNWITNESSED, ORAL_NUNCUPATIVE"),
    date_created: str = typer.Option(..., "--date", "-d", help="Ngày lập di chúc (YYYY-MM-DD)"),
    place_created: str = typer.Option("Hà Nội, Việt Nam", "--place", help="Nơi lập di chúc"),
    notary_office: Optional[str] = typer.Option(None, "--office", help="Phòng/Văn phòng công chứng hoặc UBND xã chứng thực"),
    notary_number: Optional[str] = typer.Option(None, "--number", help="Số công chứng/chứng thực"),
    witness_1: Optional[str] = typer.Option(None, "--w1", help="Người làm chứng thứ 1 (Điều 634)"),
    witness_2: Optional[str] = typer.Option(None, "--w2", help="Người làm chứng thứ 2 (Điều 634)"),
    executor: Optional[str] = typer.Option(None, "--executor", help="Người thực hiện di chúc (Điều 657)"),
    worship_amount: float = typer.Option(0.0, "--worship", help="Di sản dùng vào việc thờ cúng (Điều 645)"),
    summary: Optional[str] = typer.Option(None, "--summary", "-s", help="Tóm tắt nội dung di chúc"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Đăng ký & thẩm định tính hợp pháp của Di chúc (Articles 624-648 BLDS 2015)."""
    engine = InheritanceEngine()
    try:
        res = engine.register_will(
            estate_id=estate_id,
            will_form=form,
            date_created=date_created,
            place_created=place_created,
            notary_office_or_ubnd=notary_office,
            notary_number=notary_number,
            witness_1_name=witness_1,
            witness_2_name=witness_2,
            executor_name=executor,
            worship_estate_assigned=worship_amount,
            contents_summary=summary,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            status_color = "green" if res["will_status"] == "VALID" else "red"
            console.print(f"[bold {status_color}]✔ Đã ghi nhận di chúc![/bold {status_color}] Trạng thái: [bold]{res['will_status']}[/bold]")
            if res.get("invalid_reasons"):
                for r in res["invalid_reasons"]:
                    console.print(f"[yellow]⚠ Cảnh báo pháp lý:[/yellow] {r}")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi đăng ký di chúc:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("heir-add")
def heir_add(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    name: str = typer.Option(..., "--name", "-n", help="Họ và tên người thừa kế"),
    id_number: str = typer.Option(..., "--id-number", "-i", help="Số CCCD/Định danh"),
    dob: str = typer.Option(..., "--dob", help="Ngày sinh (YYYY-MM-DD)"),
    relationship: str = typer.Option(HeirRelationship.BIOLOGICAL_CHILD.value, "--rel", "-r", help="SPOUSE, BIOLOGICAL_CHILD, ADOPTED_CHILD, BIOLOGICAL_PARENT, ADOPTIVE_PARENT, SIBLING, GRANDCHILD, STEPCHILD_STEPPARENT, NON_RELATIVE_BENEFICIARY..."),
    rank: Optional[str] = typer.Option(None, "--rank", help="FIRST_RANK, SECOND_RANK, THIRD_RANK, TESTAMENTARY_ONLY"),
    is_minor_disabled: bool = typer.Option(False, "--disabled/--able", help="Chưa thành niên hoặc không có khả năng lao động (Điều 644)"),
    is_disqualified: bool = typer.Option(False, "--disqualified", help="Không được quyền hưởng di sản theo Điều 621"),
    is_forgiven: bool = typer.Option(False, "--forgiven", help="Được người lập di chúc tha thứ cho hưởng (Điều 621 K2)"),
    is_substitutional: bool = typer.Option(False, "--substitutional", help="Thừa kế thế vị theo Điều 652"),
    substituting_for: Optional[str] = typer.Option(None, "--sub-for", help="Thế vị cho ai (cha/mẹ đã chết trước/cùng thời điểm)"),
    testamentary_share_pct: float = typer.Option(0.0, "--share-pct", help="Tỷ lệ % hưởng theo di chúc"),
    testamentary_amount: float = typer.Option(0.0, "--fixed-amt", help="Số tiền cố định hưởng theo di chúc"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Thêm người thừa kế theo luật hoặc di chúc (Articles 644, 651, 652, 653 BLDS 2015)."""
    engine = InheritanceEngine()
    try:
        res = engine.register_heir(
            estate_id=estate_id,
            full_name=name,
            id_number=id_number,
            dob=dob,
            relationship=relationship,
            heir_rank=rank,
            is_minor_or_disabled=is_minor_disabled,
            is_disqualified_art621=is_disqualified,
            is_forgiven_in_will=is_forgiven,
            is_substitutional_art652=is_substitutional,
            substituting_for_name=substituting_for,
            testamentary_share_percent=testamentary_share_pct,
            testamentary_fixed_amount=testamentary_amount,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Đã đăng ký người thừa kế:[/bold green] [cyan]{res['full_name']}[/cyan] (Mã: {res['heir_id']})")
            console.print(f"Quan hệ: {res['relationship']} | Hàng: {res['heir_rank']} | Trạng thái: [bold]{res['eligibility_status']}[/bold]")
            if res.get("is_forced_heir_candidate"):
                console.print("[yellow]ℹ Thuộc diện Người thừa kế không phụ thuộc nội dung di chúc (Điều 644 BLDS 2015).[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi thêm người thừa kế:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("disclaim")
def disclaim(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    heir_id: str = typer.Option(..., "--heir-id", "-h", help="Mã người thừa kế"),
    date: str = typer.Option(..., "--date", "-d", help="Ngày lập văn bản từ chối (YYYY-MM-DD)"),
    office: str = typer.Option(..., "--office", help="Nơi công chứng/chứng thực văn bản từ chối"),
    doc_number: str = typer.Option(..., "--doc-num", help="Số văn bản công chứng từ chối"),
    debt_evasion: bool = typer.Option(False, "--debt-evasion", help="Từ chối nhằm trốn tránh nghĩa vụ tài sản (vô hiệu)"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Lý do từ chối"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Ghi nhận văn bản từ chối nhận di sản thừa kế (Điều 620 BLDS 2015 & Điều 59 Luật Công chứng)."""
    engine = InheritanceEngine()
    try:
        res = engine.record_disclaimer(
            estate_id=estate_id,
            heir_id=heir_id,
            declaration_date=date,
            notary_or_ubnd_office=office,
            notary_document_number=doc_number,
            reason=reason,
            is_for_debt_evasion=debt_evasion,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            if res["is_valid"]:
                console.print(f"[bold green]✔ Đã ghi nhận từ chối nhận di sản hợp pháp cho:[/bold green] [cyan]{res['heir_name']}[/cyan]")
            else:
                console.print(f"[bold red]✖ Văn bản từ chối vô hiệu theo Điều 620 K1 BLDS 2015 do trốn tránh nghĩa vụ![/bold red]")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi từ chối nhận di sản:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("calculate")
def calculate(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Tính toán phân chia di sản thừa kế theo luật, di chúc & suất bắt buộc Điều 644."""
    engine = InheritanceEngine()
    try:
        res = engine.calculate_statutory_shares(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(Panel.fit(
                f"[bold cyan]KẾT QUẢ TÍNH TOÁN PHÂN CHIA DI SẢN — HỒ SƠ {res['estate_id']}[/bold cyan]\n"
                f"Người để lại di sản: [bold]{res['decedent_name']}[/bold] (Mở thừa kế: {res['date_of_death']})\n"
                f"Chế độ thừa kế: [bold green]{res['succession_mode']}[/bold green]\n"
                f"Tổng tài sản: [bold]{res['gross_assets']:,.0f} VND[/bold] | Nợ đã trả: [red]{res['total_obligations_paid']:,.0f} VND[/red]\n"
                f"Di sản thờ cúng: [yellow]{res['dedicated_worship_deducted']:,.0f} VND[/yellow] | Di sản ròng phân chia: [bold yellow]{res['net_distributable_estate']:,.0f} VND[/bold yellow]\n"
                f"1 Suất thừa kế theo luật: [cyan]{res['one_statutory_share_reference']:,.0f} VND[/cyan] | 2/3 Suất Điều 644: [magenta]{res['forced_heir_2_3_share_reference']:,.0f} VND[/magenta]",
                box=box.ROUNDED,
            ))

            table = Table(title="Bảng phân bổ di sản thừa kế cho từng đồng thừa kế", box=box.SIMPLE_HEAVY)
            table.add_column("Người thừa kế", style="bold green")
            table.add_column("Quan hệ", style="cyan")
            table.add_column("Hàng thừa kế", style="white")
            table.add_column("Số tiền nhận (VND)", style="bold yellow", justify="right")
            table.add_column("Tỷ lệ (%)", style="magenta", justify="right")
            table.add_column("Căn cứ pháp lý", style="dim")

            for a in res["allocations"]:
                table.add_row(
                    a["full_name"],
                    a["relationship"],
                    a["heir_rank"],
                    f"{a['allocated_amount']:,.0f}",
                    f"{a['allocated_percentage']:.2f}%",
                    a["rule_applied"],
                )
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Lỗi khi tính toán phân chia:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("divide")
def divide(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    office: str = typer.Option(..., "--office", "-o", help="Tổ chức hành nghề công chứng thực hiện phân chia"),
    procedure: str = typer.Option(NotaryProcedureType.DIVISION_AGREEMENT.value, "--procedure", "-p", help="DIVISION_AGREEMENT / ACCEPTANCE_DECLARATION"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Ngày công chứng phân chia"),
    ubnd: Optional[str] = typer.Option(None, "--ubnd", help="UBND cấp xã nơi niêm yết thông báo thừa kế 15 ngày"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Lập Văn bản thỏa thuận phân chia di sản / Khai nhận di sản & kiểm tra niêm yết 15 ngày (Điều 57, 58 Luật Công chứng)."""
    engine = InheritanceEngine()
    try:
        res = engine.execute_division_agreement(
            estate_id=estate_id,
            procedure_type=procedure,
            notary_office=office,
            division_date=date,
            public_posting_ubnd=ubnd,
        )
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(f"[bold green]✔ Lập văn bản phân chia di sản thành công![/bold green] Mã thỏa thuận: [cyan]{res['agreement_id']}[/cyan]")
            console.print(f"Thủ tục: [bold]{res['procedure_type']}[/bold] tại [yellow]{res['notary_office']}[/yellow]")
            console.print(f"Niêm yết công khai: {res['public_posting']['start_date']} đến {res['public_posting']['end_date']} tại UBND: [cyan]{res['public_posting']['ubnd_location']}[/cyan] (Đủ 15 ngày)")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi lập văn bản phân chia:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("statute-check")
def statute_check(
    dod: str = typer.Option(..., "--dod", help="Ngày mở thừa kế / ngày chết (YYYY-MM-DD)"),
    date: Optional[str] = typer.Option(None, "--current-date", help="Ngày kiểm tra thời hiệu"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Kiểm tra thời hiệu thừa kế 30 năm (BĐS), 10 năm (động sản), 03 năm (nghĩa vụ nợ) (Điều 623 BLDS 2015)."""
    engine = InheritanceEngine()
    try:
        res = engine.check_statute_of_limitations(dod, date)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            table = Table(title=f"Kiểm tra Thời hiệu Thừa kế (Điều 623 BLDS 2015) — Ngày chết: {dod}", box=box.ROUNDED)
            table.add_column("Loại quyền yêu cầu", style="bold green")
            table.add_column("Thời hiệu luật định", style="cyan")
            table.add_column("Hạn chót", style="white")
            table.add_column("Số năm còn lại", style="yellow")
            table.add_column("Trạng thái", style="bold magenta")

            re = res["real_estate_claim"]
            mv = res["movable_property_claim"]
            ob = res["creditor_obligation_claim"]

            table.add_row("Yêu cầu chia Di sản Bất động sản", f"{re['limitation_years']} năm", re["deadline"], f"{re['remaining_years']} năm", re["status"])
            table.add_row("Yêu cầu chia Di sản Động sản", f"{mv['limitation_years']} năm", mv["deadline"], f"{mv['remaining_years']} năm", mv["status"])
            table.add_row("Yêu cầu thực hiện nghĩa vụ tài sản", f"{ob['limitation_years']} năm", ob["deadline"], f"{ob['remaining_years']} năm", ob["status"])

            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Lỗi kiểm tra thời hiệu:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("dossier")
def dossier(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Xuất trọn bộ Hồ sơ Pháp lý thừa kế phục vụ Công chứng, Sang tên Sổ đỏ & Ngân hàng."""
    engine = InheritanceEngine()
    try:
        res = engine.generate_inheritance_dossier(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(Panel.fit(
                f"[bold green]HỒ SƠ PHÁP LÝ THỪA KẾ (INHERITANCE LEGAL DOSSIER) — {res['dossier_id']}[/bold green]\n"
                f"Người để lại di sản: [bold cyan]{res['estate_metadata']['decedent_name']}[/bold cyan] | CCCD: {res['estate_metadata']['decedent_id_number']}\n"
                f"Ngày mở thừa kế: {res['estate_metadata']['date_of_death']} | Nơi mở: {res['estate_metadata']['place_of_opening']}\n"
                f"Tổng di sản phân chia: [bold yellow]{res['financial_summary']['net_distributable_estate']:,.0f} VND[/bold yellow]",
                box=box.DOUBLE,
            ))
            console.print("[bold underline]Thành phần hồ sơ bắt buộc gửi cơ quan công chứng/đăng ký đất đai:[/bold underline]")
            for req in res["notary_requirements"]:
                console.print(f"  • {req}")
    except Exception as e:
        console.print(f"[bold red]Lỗi xuất hồ sơ:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("audit")
def audit(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Thẩm định tuân thủ pháp luật thừa kế toàn diện (Civil Code 2015 Compliance Audit)."""
    engine = InheritanceEngine()
    try:
        res = engine.audit_compliance(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            status_style = "bold green" if res["is_compliant"] else "bold red"
            console.print(Panel.fit(
                f"[{status_style}]KẾT QUẢ THẨM ĐỊNH TUÂN THỦ PHÁP LUẬT THỪA KẾ[/{status_style}]\n"
                f"Hồ sơ: [bold]{res['estate_id']}[/bold] ({res['decedent_name']})\n"
                f"Đánh giá: [{status_style}]{res['compliance_rating']}[/{status_style}]\n"
                f"Vi phạm phát hiện: [bold]{res['issues_count']}[/bold] | Cảnh báo: [yellow]{res['warnings_count']}[/yellow]",
                box=box.ROUNDED,
            ))
            if res["issues"]:
                console.print("[bold red]Các vi phạm pháp luật cần khắc phục:[/bold red]")
                for iss in res["issues"]:
                    console.print(f"  ✖ {iss}")
            if res["warnings"]:
                console.print("[yellow]Các lưu ý pháp lý:[/yellow]")
                for w in res["warnings"]:
                    console.print(f"  ⚠ {w}")
    except Exception as e:
        console.print(f"[bold red]Lỗi thẩm định tuân thủ:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("show")
def show(
    estate_id: str = typer.Option(..., "--estate-id", "-e", help="Mã hồ sơ di sản"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Xem chi tiết hồ sơ di sản thừa kế."""
    engine = InheritanceEngine()
    try:
        res = engine.get_estate(estate_id)
        if json_output:
            console.print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            console.print(Panel.fit(
                f"[bold cyan]CHI TIẾT HỒ SƠ DI SẢN: {res['estate_id']}[/bold cyan]\n"
                f"Người để lại di sản: [bold]{res['decedent_name']}[/bold] (CCCD: {res['decedent_id_number']})\n"
                f"Ngày mất: {res['date_of_death']} | Nơi mất: {res['place_of_death']}\n"
                f"Nơi cư trú cuối: {res['last_residence']}\n"
                f"Người quản lý di sản: {res.get('administrator_name') or 'Chưa cử'}\n"
                f"Tổng tài sản: [bold yellow]{res['summary']['total_gross_assets']:,.0f} VND[/bold yellow] | Nợ: [red]{res['summary']['total_obligations']:,.0f} VND[/red]\n"
                f"Di sản thờ cúng: [yellow]{res['summary']['dedicated_worship_amount']:,.0f} VND[/yellow] | Di sản ròng: [bold green]{res['summary']['net_distributable_estate']:,.0f} VND[/bold green]",
                box=box.ROUNDED,
            ))
    except Exception as e:
        console.print(f"[bold red]Lỗi khi đọc hồ sơ:[/bold red] {e}")
        raise typer.Exit(code=1)


@inheritance_app.command("list")
def list_cmd(
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ tối đa"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Danh sách các hồ sơ di sản thừa kế."""
    engine = InheritanceEngine()
    try:
        estates = engine.list_estates(limit)
        if json_output:
            console.print(json.dumps(estates, indent=2, ensure_ascii=False))
        else:
            _render_status_dashboard(estates)
    except Exception as e:
        console.print(f"[bold red]Lỗi khi liệt kê hồ sơ:[/bold red] {e}")
        raise typer.Exit(code=1)
