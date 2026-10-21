# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 148: Will Registration, Heir Registration & Inheritance Disclaimer CLI commands."""

from __future__ import annotations

import json
from typing import Optional

import typer

from src.cli.commands._inheritance_estate_cmds import console, inheritance_app
from src.core.inheritance_engine import (
    HeirRelationship,
    InheritanceEngine,
    WillForm,
)


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
                console.print("[bold red]✖ Văn bản từ chối vô hiệu theo Điều 620 K1 BLDS 2015 do trốn tránh nghĩa vụ![/bold red]")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi từ chối nhận di sản:[/bold red] {e}")
        raise typer.Exit(code=1)
