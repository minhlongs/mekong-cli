# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 176: Specialized Inspection callback, Hazardous Chemicals NSW & DG Segregation CLI."""

from __future__ import annotations

import json
from typing import List, Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.ecom_inspect_engine import (
    ChemicalAnnex,
    ChemicalItem,
    HazardousChemicalNSWEngine,
)

console = Console()

inspect_app = typer.Typer(
    name="inspect",
    help="INSPECT — Specialized Inspection, Hazardous Chemicals & EU CBAM/EUDR Suite (Phases 176-178)",
    no_args_is_help=False,
)


@inspect_app.callback(invoke_without_command=True)
def inspect_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Kiểm tra Chuyên ngành, Khai báo Hóa chất NSW & EU CBAM/EUDR."""
    if ctx.invoked_subcommand is not None:
        return
    if json_mode:
        data = {
            "suite": "Mekong Specialized Inspection, Chemicals & CBAM Suite (Phases 176-178)",
            "statutory_basis": [
                "Decree 113/2017/ND-CP & Decree 82/2022/ND-CP (Hazardous Chemicals)",
                "IMDG Code 41-22 & IATA DGR (Dangerous Goods Segregation)",
                "Decree 15/2018/ND-CP (Imported Food Safety Inspection Tiers)",
                "Circular 25/2016/TT-BNNPTNT & Circular 33/2014/TT-BNNPTNT (Quarantine)",
                "EU Regulation 2023/956 (CBAM) & EU Regulation 2023/1115 (EUDR)",
            ],
            "commands": ["chemical", "dg-segregation", "food-tier", "quarantine", "cbam", "eudr"],
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(
        Panel(
            "[bold cyan]Mekong Specialized Inspection, Chemicals & CBAM Suite (Phases 176-178)[/bold cyan]\n"
            "[dim]Kiểm tra chuyên ngành ATTP, khai báo hóa chất một cửa quốc gia, phân cách hàng nguy hiểm và tuân thủ CBAM/EUDR.[/dim]\n\n"
            "• [bold yellow]chemical[/bold yellow]       : Kiểm tra phân loại Hóa chất NĐ 113/82 (PL I-V) & cấp token VNSW.\n"
            "• [bold red]dg-segregation[/bold red] : Ma trận phân cách hàng nguy hiểm IMDG/IATA (9 nhóm).\n"
            "• [bold green]food-tier[/bold green]      : Chuyển đổi phương thức kiểm tra ATTP NĐ 15/2018 (Chặt -> Thường -> Giảm).\n"
            "• [bold blue]quarantine[/bold blue]     : Kiểm tra thời hạn hiệu lực giấy kiểm dịch động vật / thực vật.\n"
            "• [bold magenta]cbam[/bold magenta]           : Tính phát thải tích hợp và nghĩa vụ tài chính CBAM xuất khẩu EU.\n"
            "• [bold green]eudr[/bold green]           : Thẩm định chuỗi cung ứng không phá rừng EUDR (Polygon GPS & Cut-off 2020).",
            title="🔬 [bold]KIỂM TRA CHUYÊN NGÀNH & HÓA CHẤT & CBAM[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)


@inspect_app.command("chemical")
def inspect_chemical(
    cas: str = typer.Argument(..., help="Mã định danh hóa chất CAS"),
    qty_kg: float = typer.Argument(..., help="Khối lượng nhập khẩu (kg)"),
    name: str = typer.Option("Chemical Compound", "--name", "-n", help="Tên hóa chất"),
    hs: str = typer.Option("2807.00.00", "--hs", help="Mã HS"),
    annexes_str: str = typer.Option("ANNEX_V", "--annexes", "-a", help="Các phụ lục thuộc NĐ 113/82 (phân tách dấu phẩy)"),
    moit_license: Optional[str] = typer.Option(None, "--license", "-l", help="Số giấy phép BCT (nếu thuộc PL II)"),
    vnsw_id: Optional[str] = typer.Option(None, "--vnsw", help="Mã hồ sơ khai báo NSW"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá điều kiện nhập khẩu hóa chất theo Nghị định 113/2017 & 82/2022."""
    annex_enums: List[ChemicalAnnex] = []
    for a in annexes_str.split(","):
        a_clean = a.strip().upper()
        if not a_clean.startswith("ANNEX_"):
            a_clean = f"ANNEX_{a_clean}"
        for member in ChemicalAnnex:
            if member.value == a_clean or member.name == a_clean:
                annex_enums.append(member)
                break

    item = ChemicalItem(
        cas_number=cas,
        chemical_name=name,
        hs_code=hs,
        quantity_kg=qty_kg,
        annexes=annex_enums,
        moit_license_number=moit_license,
        vnsw_declaration_id=vnsw_id,
    )
    result = HazardousChemicalNSWEngine.evaluate_chemical_compliance(item)
    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"🧪 Khai Báo Hóa Chất NSW — CAS: {cas}", box=box.ROUNDED)
    table.add_column("Chỉ số kiểm tra", style="cyan")
    table.add_column("Kết quả", style="bold")
    table.add_column("Chi tiết luật định", style="dim")
    table.add_row("Tên hóa chất / Khối lượng", f"{name} ({qty_kg:,.1f} kg)", f"HS: {hs}")
    table.add_row("Hóa chất Cấm (Phụ lục III)", "[bold red]CẤM NHẬP KHẨU[/bold red]" if result.is_banned else "[green]Không thuộc PL Cấm[/green]", "Nghị định 113/2017/NĐ-CP")
    table.add_row("Hóa chất Hạn chế (Phụ lục II)", "Bắt buộc Giấy phép BCT" if result.requires_moit_license else "Không thuộc PL II", f"Giấy phép: {moit_license or 'Chưa có'}")
    table.add_row("Kế hoạch / Biện pháp PC Sự cố", result.accident_document_type, "Đánh giá theo ngưỡng tồn trữ")
    nsw_txt = f"[green]{result.nsw_token}[/green]" if result.nsw_token else ("Miễn khai (<10kg)" if result.is_nsw_exempt else "Chưa khai báo")
    table.add_row("Khai báo Cổng Một cửa (VNSW)", nsw_txt, "Hệ thống NSW vnsw.gov.vn")
    table.add_row("Trạng thái Hải quan", f"[bold]{result.customs_status}[/bold]", result.action_required)
    console.print(table)


@inspect_app.command("dg-segregation")
def inspect_dg_segregation(
    un_a: str = typer.Argument(..., help="Số UN chất A (ví dụ UN1203)"),
    class_a: float = typer.Argument(..., help="Nhóm nguy hiểm chất A (ví dụ 3.0)"),
    un_b: str = typer.Argument(..., help="Số UN chất B (ví dụ UN1479)"),
    class_b: float = typer.Argument(..., help="Nhóm nguy hiểm chất B (ví dụ 5.1)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu ma trận phân cách hàng nguy hiểm theo IMDG Code 41-22 & IATA DGR."""
    result = HazardousChemicalNSWEngine.check_dg_segregation(
        un_a=un_a, dg_class_a=class_a, un_b=un_b, dg_class_b=class_b
    )
    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    style = "green" if result.is_coloading_permitted else "red"
    content = (
        f"• Chất A: [bold]{result.un_a}[/bold] (Class {result.dg_class_a})\n"
        f"• Chất B: [bold]{result.un_b}[/bold] (Class {result.dg_class_b})\n"
        f"• Cấp phân cách IMDG: [bold]{result.segregation_requirement}[/bold]\n"
        f"• Khoảng cách tối thiểu: [bold]{result.min_distance_meters} mét[/bold]\n"
        f"• Cho phép đóng chung container: [bold]{'CÓ' if result.min_distance_meters == 0 else 'KHÔNG'}[/bold]\n\n"
        f"[bold]Quy định luật định:[/bold]\n{result.statutory_rule}"
    )
    console.print(Panel(content, title="⚠️ Ma Trận Phân Cách Hàng Nguy Hiểm (IMDG Code 41-22)", border_style=style, box=box.ROUNDED))
