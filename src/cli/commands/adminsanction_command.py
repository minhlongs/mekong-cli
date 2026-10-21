# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Commercial & Enterprise Administrative Sanctions Command Surface (Phase 151)."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console

from src.cli.commands._adminsanction_enforcement import (
    assess_jurisdiction,
    calculate_remedy,
    check_authority,
    generate_decision,
    register_enforcement_commands,
)
from src.cli.commands._adminsanction_renderers import (
    render_adminsanction_dashboard,
    render_case_result,
    render_fine_result,
)
from src.core.adminsanction_engine import (
    MAX_FINES_INDIVIDUAL_VND,
    TWO_YEAR_LIMITATION_SECTORS,
    AdminSanctionEngine,
    AuthorityBranch,
    EntityType,
    RemedialMeasureType,
    SanctionType,
    ViolationStatus,
)

adminsanction_app = typer.Typer(
    name="adminsanction",
    help="Vietnamese Administrative Sanctions & Violations Compliance Suite (Luật XLVPHC 2012/2020 & NĐ 118/2021/NĐ-CP).",
    no_args_is_help=False,
)
app = adminsanction_app
console = Console()


def _render_dashboard() -> None:
    render_adminsanction_dashboard(console)


def _output_dashboard(json_output: bool) -> None:
    data = AdminSanctionEngine().get_statutory_dashboard()
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2)) if json_output else _render_dashboard()


@adminsanction_app.callback(invoke_without_command=True)
def main(ctx: typer.Context, json_output: bool = typer.Option(False, "--json", help="Xuất dữ liệu dạng JSON")) -> None:
    """Vietnamese Administrative Sanctions & Violations Compliance Suite."""
    if ctx.invoked_subcommand is None:
        _output_dashboard(json_output)


@adminsanction_app.command("status")
def status(json_output: bool = typer.Option(False, "--json", help="Xuất dữ liệu dạng JSON")) -> None:
    """Hiển thị bảng điều khiển khung pháp lý xử lý vi phạm hành chính."""
    _output_dashboard(json_output)


@adminsanction_app.command("dashboard")
def dashboard(json_output: bool = typer.Option(False, "--json", help="Xuất dữ liệu dạng JSON")) -> None:
    """Hiển thị bảng điều khiển vi phạm hành chính (alias)."""
    _output_dashboard(json_output)


@adminsanction_app.command("create-case")
def create_case(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Tên cá nhân/tổ chức vi phạm"),
    subject_name: Optional[str] = typer.Option(None, "--subject-name", help="Tên cá nhân/tổ chức vi phạm"),
    entity: Optional[str] = typer.Option(None, "--entity", "-e", help="Loại đối tượng"),
    subject_type: Optional[str] = typer.Option(None, "--subject-type", help="Loại đối tượng: INDIVIDUAL hoặc ORGANIZATION"),
    sector: Optional[str] = typer.Option(None, "--sector", "-s", help="Lĩnh vực vi phạm"),
    category: Optional[str] = typer.Option(None, "--category", help="Lĩnh vực vi phạm"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Mô tả hành vi"),
    behavior: Optional[str] = typer.Option(None, "--behavior", help="Mô tả hành vi vi phạm hành chính"),
    violation_date: Optional[str] = typer.Option(None, "--violation-date", help="Ngày vi phạm (YYYY-MM-DD)"),
    date: Optional[str] = typer.Option(None, "--date", help="Ngày vi phạm (YYYY-MM-DD)"),
    location: Optional[str] = typer.Option(None, "--location", help="Địa điểm vi phạm"),
    discovery_date: Optional[str] = typer.Option(None, "--discovery-date", help="Ngày phát hiện vi phạm (YYYY-MM-DD)"),
    status: str = typer.Option("CONCLUDED", "--status", help="Trạng thái vi phạm: CONCLUDED hoặc ONGOING"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Lập hồ sơ vụ việc vi phạm hành chính và kiểm tra thời hiệu xử phạt."""
    res = AdminSanctionEngine().create_case(
        violator_name=subject_name or name or "Chưa xác định",
        entity_type=subject_type or entity or "ORGANIZATION",
        sector=category or sector or "ENVIRONMENTAL_PROTECTION",
        violation_description=behavior or description or "Hành vi vi phạm hành chính",
        violation_date=date or violation_date or "2026-01-01",
        discovery_date=discovery_date, violation_status=status, violation_location=location,
    )
    typer.echo(json.dumps(res, ensure_ascii=False, indent=2)) if json_output else render_case_result(console, res)


def _parse_factors(raw: Optional[str], label: str) -> list[str]:
    if not raw:
        return []
    return [f"{label} #{i + 1}" for i in range(int(raw.strip()))] if raw.strip().isdigit() else [x.strip() for x in raw.split(",") if x.strip()]


@adminsanction_app.command("calculate-fine")
def calculate_fine(
    min_fine: Optional[float] = typer.Option(None, "--min", "-m", help="Mức phạt tối thiểu khung cá nhân (VNĐ)"),
    min_fine_opt: Optional[float] = typer.Option(None, "--min-fine", help="Mức phạt tối thiểu"),
    max_fine: Optional[float] = typer.Option(None, "--max", "-M", help="Mức phạt tối đa khung cá nhân (VNĐ)"),
    max_fine_opt: Optional[float] = typer.Option(None, "--max-fine", help="Mức phạt tối đa"),
    entity: Optional[str] = typer.Option(None, "--entity", "-e", help="INDIVIDUAL hoặc ORGANIZATION (x2)"),
    subject_type: Optional[str] = typer.Option(None, "--subject-type", help="INDIVIDUAL hoặc ORGANIZATION"),
    mitigating: Optional[str] = typer.Option(None, "--mitigating", help="Danh sách hoặc số lượng tình tiết giảm nhẹ"),
    aggravating: Optional[str] = typer.Option(None, "--aggravating", help="Danh sách hoặc số lượng tình tiết tăng nặng"),
    case_id: Optional[str] = typer.Option(None, "--case-id", help="Mã hồ sơ liên kết (nếu có)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán mức tiền phạt luật định theo Nghị định 118/2021/NĐ-CP và Điều 23 Luật XLVPHC."""
    final_min = min_fine_opt if min_fine_opt is not None else (min_fine if min_fine is not None else 1_000_000.0)
    final_max = max_fine_opt if max_fine_opt is not None else (max_fine if max_fine is not None else 2_000_000.0)
    res = AdminSanctionEngine().calculate_statutory_fine(
        statutory_min_fine_individual=final_min, statutory_max_fine_individual=final_max,
        entity_type=subject_type or entity or "ORGANIZATION",
        mitigating_factors=_parse_factors(mitigating, "Tình tiết giảm nhẹ"),
        aggravating_factors=_parse_factors(aggravating, "Tình tiết tăng nặng"), case_id=case_id,
    )
    res["fine_calculation"] = {
        "calculated_fine_vnd": res["final_payable_fine_vnd"], "applied_min": res["applied_bracket"]["min"],
        "applied_max": res["applied_bracket"]["max"], "average": res["applied_bracket"]["average"],
    }
    typer.echo(json.dumps(res, ensure_ascii=False, indent=2)) if json_output else render_fine_result(console, res)


register_enforcement_commands(adminsanction_app)

__all__ = [
    "adminsanction_app", "app", "main", "status", "dashboard", "create_case", "calculate_fine",
    "assess_jurisdiction", "check_authority", "calculate_remedy", "generate_decision",
    "AdminSanctionEngine", "AuthorityBranch", "EntityType", "MAX_FINES_INDIVIDUAL_VND",
    "RemedialMeasureType", "SanctionType", "TWO_YEAR_LIMITATION_SECTORS", "ViolationStatus",
]
