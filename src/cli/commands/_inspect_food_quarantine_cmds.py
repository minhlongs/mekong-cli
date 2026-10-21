# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 177: Specialized Food Safety & Quarantine Inspection CLI commands."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._inspect_chemical_cmds import console, inspect_app
from src.core.ecom_inspect_engine import (
    FoodInspectionMethod,
    FoodSafetyConsignmentRecord,
    QuarantineType,
    SpecializedInspectionEngine,
)


@inspect_app.command("food-tier")
def inspect_food_tier(
    consignor_id: str = typer.Argument(
        ..., help="Mã nhà sản xuất / xuất khẩu nước ngoài"
    ),
    current_method: str = typer.Option(
        "NORMAL",
        "--current",
        "-c",
        help="Phương thức hiện tại (REDUCED, NORMAL, TIGHTENED)",
    ),
    passes: int = typer.Option(0, "--passes", "-p", help="Số lô liên tiếp đạt yêu cầu"),
    has_iso_haccp: bool = typer.Option(
        False, "--haccp", help="Có chứng nhận GMP, HACCP, ISO 22000, IFS, BRC"
    ),
    cert_days: int = typer.Option(
        0, "--cert-days", help="Thời hạn hiệu lực chứng nhận ATTP (ngày)"
    ),
    failed_last: bool = typer.Option(
        False, "--failed", help="Lô gần nhất không đạt chỉ tiêu ATTP"
    ),
    warning: bool = typer.Option(
        False,
        "--warning",
        help="Có cảnh báo an toàn từ Bộ Y tế / NN&PTNT / Công Thương",
    ),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá phương thức kiểm tra ATTP nhập khẩu theo Nghị định 15/2018/NĐ-CP."""
    try:
        meth_enum = FoodInspectionMethod[current_method.upper()]
    except KeyError:
        meth_enum = FoodInspectionMethod.NORMAL

    record = FoodSafetyConsignmentRecord(
        consignor_id=consignor_id,
        product_hs="1905.90.00",
        current_method=meth_enum,
        consecutive_passes=passes,
        has_iso22000_or_haccp=has_iso_haccp,
        cert_valid_days=cert_days,
        failed_last_batch=failed_last,
        official_warning_issued=warning,
    )

    result = SpecializedInspectionEngine.evaluate_food_inspection_tier(record)

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    table = Table(
        title=f"🍎 Kiểm Tra Chuyên Ngành ATTP — Doanh nghiệp: {consignor_id}",
        box=box.ROUNDED,
    )
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Trạng thái", style="bold")
    table.add_column("Căn cứ Nghị định 15/2018/NĐ-CP", style="dim")

    table.add_row(
        "Phương thức áp dụng",
        f"[bold]{result.assigned_method.value}[/bold]",
        "Kiểm tra Giảm / Thông thường / Chặt",
    )
    table.add_row(
        "Tỷ lệ lấy mẫu kiểm nghiệm",
        f"{result.sample_inspection_rate_pct:.0f}%",
        "Kiểm tra thực tế mẫu",
    )
    table.add_row(
        "Yêu cầu thử nghiệm Lab",
        "CÓ (Bắt buộc)" if result.requires_lab_testing else "KHÔNG (Chỉ xét hồ sơ)",
        "100% chỉ tiêu ATTP",
    )
    table.add_row("Lý do áp dụng", result.transition_reason, "Điều 16, 17, 18")
    table.add_row(
        "Điều kiện chuyển bậc tiếp theo",
        result.next_milestone,
        "Chuỗi 3 lô liên tiếp đạt",
    )
    console.print(table)


@inspect_app.command("quarantine")
def inspect_quarantine(
    cert_id: str = typer.Argument(..., help="Số giấy chứng nhận kiểm dịch"),
    q_type: str = typer.Argument(
        ...,
        help="Loại kiểm dịch (ANIMAL_LIVE, ANIMAL_CONSUMPTION, ANIMAL_PROCESSED, PLANT_PHYTOSANITARY)",
    ),
    issue_date: str = typer.Argument(..., help="Ngày cấp giấy kiểm dịch (YYYY-MM-DD)"),
    inspect_date: str = typer.Argument(
        ..., help="Ngày làm thủ tục hải quan (YYYY-MM-DD)"
    ),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra thời hạn hiệu lực giấy chứng nhận kiểm dịch động thực vật."""
    type_map = {
        "ANIMAL_LIVE": QuarantineType.ANIMAL_LIVE,
        "ANIMAL_CONSUMPTION": QuarantineType.ANIMAL_CONSUMPTION,
        "ANIMAL_FOOD": QuarantineType.ANIMAL_CONSUMPTION,
        "ANIMAL_PROCESSED": QuarantineType.ANIMAL_PROCESSED,
        "PLANT_PHYTOSANITARY": QuarantineType.PLANT_PHYTOSANITARY,
        "PLANT_PHYTO": QuarantineType.PLANT_PHYTOSANITARY,
    }
    target_type = type_map.get(q_type.upper(), QuarantineType.PLANT_PHYTOSANITARY)

    result = SpecializedInspectionEngine.verify_quarantine_validity(
        certificate_id=cert_id,
        quarantine_type=target_type,
        issue_date_str=issue_date,
        inspection_date_str=inspect_date,
    )

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    style = "green" if result.is_valid else "red"
    content = (
        f"• Số giấy kiểm dịch: [bold]{result.certificate_id}[/bold]\n"
        f"• Loại hình kiểm dịch: {result.quarantine_type.value}\n"
        f"• Ngày cấp: {result.issue_date} | Ngày làm thủ tục: {result.inspection_date}\n"
        f"• Thời hạn tối đa: {result.max_validity_days} ngày\n"
        f"• Thời gian đã trôi qua: {result.elapsed_days} ngày\n"
        f"• Số ngày còn lại: [bold]{result.remaining_days} ngày[/bold]\n\n"
        f"[bold]Kết luận kiểm dịch:[/bold]\n{result.action}"
    )

    console.print(
        Panel(
            content,
            title="🌿 Thời Hiệu Giấy Chứng Nhận Kiểm Dịch (TT 25/2016 & TT 33/2014)",
            border_style=style,
            box=box.ROUNDED,
        )
    )
