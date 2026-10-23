# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""IP command patent & copyright panel construction — specifications and dossiers."""

from __future__ import annotations

from typing import Callable

from rich.panel import Panel


def build_patent_panel(spec: dict, format_vnd: Callable[[float], str]) -> Panel:
    """Build the patent specification & claims panel; the caller prints it."""
    claim_lines: list[str] = []
    for c in spec["claims"]:
        claim_lines.append(f"  [bold cyan]Điểm {c['claim_number']} ({c['type']}):[/] {c['text']}")
    claims_block = "\n".join(claim_lines)

    return Panel(
        f"[bold green]BẢN MÔ TẢ VÀ YÊU CẦU BẢO HỘ SÁNG CHẾ: {spec['patent_id']}[/]\n\n"
        f"  Tên sáng chế:        [bold]{spec['title']}[/]\n"
        f"  Lĩnh vực kỹ thuật:   {spec['technical_field']}\n"
        f"  Người nộp đơn:       [bold]{spec['applicant_name']}[/]\n"
        f"  Tổng số claims:      [bold yellow]{spec['total_claims_count']} điểm[/]\n"
        f"  Lệ phí nộp & tra cứu: [bold green]{format_vnd(spec['official_fee_vnd'])}[/]\n\n"
        f"  [bold]Nội dung điểm yêu cầu bảo hộ (Claims):[/]\n{claims_block}",
        title="[bold blue]Patent Specification & Claims Ready[/]",
        border_style="green",
    )


def build_copyright_panel(dossier: dict, format_vnd: Callable[[float], str]) -> Panel:
    """Build the software copyright registration panel; the caller prints it."""
    doc_lines = ["  - " + item for item in dossier["required_dossier_items"]]
    dossier_block = "\n".join(doc_lines)

    return Panel(
        f"[bold green]HỒ SƠ ĐĂNG KÝ QUYỀN TÁC GIẢ PHẦN MỀM: {dossier['copyright_id']}[/]\n\n"
        f"  Tên phần mềm:        [bold cyan]{dossier['software_name']}[/] (v{dossier['version']})\n"
        f"  Tác giả:             [bold]{dossier['author_name']}[/]\n"
        f"  Quy mô mã nguồn:     {dossier['lines_of_code']:,} lines of code\n"
        f"  Kho lưu trữ:         {dossier['repository_url']}\n"
        f"  Cơ quan cấp phép:    {dossier['statutory_authority']}\n"
        f"  Lệ phí nhà nước:     [bold green]{format_vnd(dossier['official_fee_vnd'])}[/]\n"
        f"  Thời hạn cấp bằng:   {dossier['timeline']}\n\n"
        f"  [bold]Hồ sơ thành phần theo NĐ 17/2023/NĐ-CP:[/{dossier_block}",
        title="[bold blue]Software Copyright Registration Ready[/]",
        border_style="green",
    )
