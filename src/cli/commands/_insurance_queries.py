# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""List and status subcommands for Insurance CLI."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_insurance_queries(insurance_app: typer.Typer) -> None:
    """Register list and status commands onto insurance_app."""
    insurance_app.command("list")(list_cmd)
    insurance_app.command("status")(status_cmd)


def list_cmd(
    resource: str = typer.Argument("licenses", help="Tài nguyên: 'licenses', 'policies', 'solvency', 'claims', 'reserves'"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh mục giấy phép doanh nghiệp BH, hợp đồng, an toàn vốn, khiếu nại bồi thường, dự phòng."""
    from src.core.insurance_engine import InsuranceEngine

    engine = InsuranceEngine()
    res_type = resource.lower().strip()

    if res_type in ("licenses", "license"):
        items = engine.list_licenses(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giấy Phép Doanh Nghiệp Bảo Hiểm")
        for col, kw in [("Số Giấy Phép", {"style": "cyan"}), ("Tên Doanh Nghiệp BH", {"style": "bold"}), ("Mã Số Thuế", {}), ("Loại Hình", {}), ("Vốn Điều Lệ", {"justify": "right"}), ("Đại Diện", {})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["license_number"], item["enterprise_name"], item["tax_id"], item["license_type"], f"{item['charter_capital_vnd']:,.0f} VND", item["legal_representative"])
        console.print(table)

    elif res_type in ("policies", "policy"):
        items = engine.list_policies(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hợp Đồng Bảo Hiểm Đang Hiệu Lực")
        for col, kw in [("Mã Hợp Đồng", {"style": "cyan"}), ("Bên Mua Bảo Hiểm", {"style": "bold"}), ("Nghiệp Vụ", {}), ("STBH", {"justify": "right", "style": "bold green"}), ("Phí Bảo Hiểm", {"justify": "right", "style": "cyan"}), ("Khấu Trừ", {"justify": "right"}), ("Thời Hạn", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["policy_id"], item["policyholder_name"], item["product_line"], f"{item['sum_insured_vnd']:,.0f} VND", f"{item['premium_vnd']:,.0f} VND", f"{item['deductible_vnd']:,.0f} VND", f"{item['term_months']}T")
        console.print(table)

    elif res_type in ("solvency", "solvency_audits"):
        items = engine.list_solvency_audits(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Kiểm Tra Biên Khả Năng Thanh Toán (CAR)")
        for col, kw in [("Mã Audit", {"style": "cyan"}), ("Doanh Nghiệp BH", {"style": "bold"}), ("Biên Thực Tế", {"justify": "right"}), ("Biên Tối Thiểu", {"justify": "right"}), ("Tỷ Lệ CAR", {"justify": "center", "style": "bold"}), ("Trạng Thái", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in items.data:
            st_color = "green" if item["capital_adequacy_ratio"] >= 1.0 else "red"
            table.add_row(item["audit_id"], item["insurer_name"], f"{item['actual_margin_vnd']:,.0f} VND", f"{item['minimum_margin_vnd']:,.0f} VND", f"[{st_color}]{item['capital_adequacy_ratio'] * 100:.2f}%[/]", f"[{st_color}]{item['solvency_status']}[/]")
        console.print(table)

    elif res_type in ("claims", "claim"):
        items = engine.list_claims(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giải Quyết Khiếu Nại Bồi Thường")
        for col, kw in [("Mã Claim", {"style": "cyan"}), ("Mã Hợp Đồng", {}), ("Mô Tả Tổn Thất", {"style": "bold"}), ("Yêu Cầu", {"justify": "right"}), ("Chi Trả Thực Tế", {"justify": "right", "style": "bold green"}), ("Trạng Thái", {"justify": "center"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["claim_id"], item["policy_id"], item["incident_description"], f"{item['claimed_amount_vnd']:,.0f} VND", f"{item['net_settled_amount_vnd']:,.0f} VND", item["settlement_status"])
        console.print(table)

    elif res_type in ("reserves", "reserve"):
        items = engine.list_reserves(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Trích Lập Dự Phòng Nghiệp Vụ Kỹ Thuật")
        for col, kw in [("Mã Reserve", {"style": "cyan"}), ("Doanh Nghiệp BH", {"style": "bold"}), ("Nghiệp Vụ", {}), ("UPR", {"justify": "right"}), ("OCR", {"justify": "right"}), ("IBNR", {"justify": "right"}), ("Tổng Dự Phòng", {"justify": "right", "style": "bold green"})]:
            table.add_column(col, **kw)
        for item in items.data:
            table.add_row(item["reserve_id"], item["insurer_name"], item["product_line"], f"{item['unearned_premium_reserve_vnd']:,.0f} VND", f"{item['outstanding_claim_reserve_vnd']:,.0f} VND", f"{item['ibnr_reserve_vnd']:,.0f} VND", f"{item['total_reserves_vnd']:,.0f} VND")
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'licenses', 'policies', 'solvency', 'claims', 'reserves'")


def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của thị trường kinh doanh bảo hiểm và an toàn vốn."""
    from src.core.insurance_engine import InsuranceEngine

    status_data = InsuranceEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Thị Trường Bảo Hiểm Việt Nam")
    table.add_column("Chỉ số an toàn vốn & thị trường bảo hiểm", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")
    for k, v in [
        ("Doanh nghiệp bảo hiểm đang hoạt động", str(m["active_insurers"])),
        ("Số lượng đơn bảo hiểm đang hiệu lực", f"{m['in_force_policies']:,} đơn"),
        ("Tổng số tiền bảo hiểm cam kết (STBH)", f"{m['total_sum_insured_vnd']:,.0f} VND"),
        ("Tổng doanh thu phí bảo hiểm", f"{m['total_written_premium_vnd']:,.0f} VND"),
        ("Tổng số hồ sơ bồi thường đã tiếp nhận", f"{m['total_claims_processed']:,} vụ"),
        ("Tổng số tiền bồi thường đã chi trả", f"{m['total_claims_settled_vnd']:,.0f} VND"),
        ("Tỷ lệ bồi thường thị trường (Loss Ratio)", m["loss_ratio_percent"]),
        ("Đợt kiểm tra an toàn vốn biên thanh toán", str(m["solvency_audits_count"])),
        ("Số doanh nghiệp đạt chuẩn an toàn vốn", str(m["capital_compliant_insurers"])),
        ("Tổng quỹ dự phòng nghiệp vụ kỹ thuật", f"{m['total_technical_reserves_vnd']:,.0f} VND"),
    ]:
        table.add_row(k, v)
    console.print(table)
