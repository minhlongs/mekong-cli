# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Suite (Phase 99)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

consumer_app = typer.Typer(
    name="consumer",
    help="Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Suite.",
)
console = Console()


@consumer_app.callback(invoke_without_command=True)
def consumer_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan bảo vệ quyền lợi người tiêu dùng, nền tảng số, hợp đồng mẫu, thu hồi sản phẩm và giải quyết tranh chấp."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.consumer_engine import ConsumerEngine

    engine = ConsumerEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN LÝ BẢO VỆ QUYỀN LỢI NGƯỜI TIÊU DÙNG QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan chuyên môn:        [bold yellow]{status_data['competent_authority']}[/]\n"
            f"  Nền tảng số & TMĐT:        [bold]{status_data['total_platforms_audited']}[/] nền tảng ([bold green]{status_data['compliant_digital_platforms']}[/] đạt chuẩn minh bạch)\n"
            f"  Hợp đồng theo mẫu rà soát: [bold cyan]{status_data['total_standard_contracts_reviewed']}[/] hợp đồng ([bold green]{status_data['valid_standard_contracts']}[/] không chứa điều khoản vô hiệu)\n"
            f"  Chương trình thu hồi SP:   [bold red]{status_data['active_product_recalls']}[/] đợt thu hồi sản phẩm khuyết tật\n"
            f"  Hồ sơ tranh chấp NTD:      [bold]{status_data['consumer_dispute_cases_total']}[/] vụ ([bold green]{status_data['summary_court_eligible_cases']}[/] đủ điều kiện áp dụng thủ tục rút gọn tại Tòa án)",
            title="[bold blue]Vietnam Consumer Rights Protection Telemetry Status[/]",
            border_style="blue",
        )
    )


@consumer_app.command("platform")
def platform_cmd(
    name: str = typer.Argument(..., help="Tên nền tảng số / Sàn thương mại điện tử / Ứng dụng"),
    p_type: str = typer.Option("E_COMMERCE_MARKETPLACE", "--type", "-t", help="Loại nền tảng: E_COMMERCE_MARKETPLACE, LARGE_DIGITAL_PLATFORM, SOCIAL_COMMERCE, CROSS_BORDER_APP"),
    algorithm: bool = typer.Option(True, "--algo/--no-algo", help="Có tùy chọn tắt quảng cáo hướng đối tượng (Targeted Advertising)"),
    dark_patterns: bool = typer.Option(False, "--dark/--no-dark", help="Có sử dụng thủ thuật giao diện ép buộc/thao túng tâm lý (Dark patterns)"),
    dispute: bool = typer.Option(True, "--dispute/--no-dispute", help="Có cơ chế tiếp nhận phản hồi khiếu nại trong 3 ngày làm việc"),
    return_days: int = typer.Option(15, "--return-days", "-r", help="Số ngày cho phép đổi trả/hoàn tiền - Tối thiểu 7 ngày"),
    verification_rate: float = typer.Option(100.0, "--verify-rate", help="Tỷ lệ xác minh danh tính người bán trên sàn (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định tính tuân thủ của nền tảng số và sàn TMĐT theo Điều 37-40 Luật BVQLNTD 2023."""
    from src.core.consumer_engine import ConsumerEngine

    engine = ConsumerEngine()
    res = engine.audit_digital_platform_compliance(
        platform_name=name,
        platform_type=p_type,
        has_transparent_algorithm_option=algorithm,
        has_dark_patterns=dark_patterns,
        dispute_mechanism_active=dispute,
        return_policy_days=return_days,
        seller_verification_rate_pct=verification_rate,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_compliant"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ THẨM ĐỊNH NỀN TẢNG SỐ & TMĐT (ĐIỀU 37-40 LUẬT BVQLNTD 2023)[/]\n\n"
            f"  Mã thẩm định:             [bold cyan]{res['audit_id']}[/]\n"
            f"  Tên nền tảng:             [bold]{res['platform_name']}[/] ([white]{res['platform_type']}[/])\n"
            f"  Minh bạch thuật toán:     [white]{'CÓ TÙY CHỌN TẮT TARGETED ADS' if res['has_transparent_algorithm_option'] else '[bold red]THIẾU TÙY CHỌN TẮT ADS[/]'}[/]\n"
            f"  Thao túng tâm lý:         [white]{'[bold red]PHÁT HIỆN DARK PATTERNS[/]' if res['has_dark_patterns'] else 'KHÔNG CÓ DARK PATTERNS'}[/]\n"
            f"  Tiếp nhận khiếu nại (3d): [white]{'HOẠT ĐỘNG' if res['dispute_mechanism_active'] else '[bold red]CHƯA THIẾT LẬP[/]'}[/]\n"
            f"  Thời hạn đổi trả hàng:    [yellow]{res['return_policy_days']} ngày[/] ({'ĐẠT >= 7 NGÀY' if res['return_policy_days'] >= 7 else '[bold red]VI PHẠM QUY ĐỊNH[/]'})\n"
            f"  Xác minh người bán:       [cyan]{res['seller_verification_rate_pct']}%[/]\n"
            f"  Đánh giá tuân thủ:        [bold {color}]{res['compliance_rating']}[/]\n\n"
            + (f"  Hành vi vi phạm:\n" + "\n".join(f"    - [bold red]{v}[/]" for v in res["violations"]) if res["violations"] else "  Đánh giá:                 [bold green]Nền tảng đáp ứng đầy đủ nghĩa vụ bảo vệ người tiêu dùng trên không gian mạng[/]"),
            title=f"[bold {color}]Digital Platform Compliance Audit[/]",
            border_style=color,
        )
    )


@consumer_app.command("contract")
def contract_cmd(
    title: str = typer.Argument(..., help="Tiêu đề hợp đồng theo mẫu hoặc điều kiện giao dịch chung"),
    industry: str = typer.Option("E_COMMERCE", "--industry", "-i", help="Lĩnh vực: E_COMMERCE, TELECOM, ELECTRICITY, CLEAN_WATER, REAL_ESTATE_APARTMENT, BANKING_CREDIT"),
    exclude_liability: bool = typer.Option(False, "--exclude-liability/--no-exclude-liability", help="Có điều khoản loại trừ/giảm bớt trách nhiệm bồi thường của bên bán"),
    restrict_dispute: bool = typer.Option(False, "--restrict-dispute/--no-restrict-dispute", help="Có điều khoản hạn chế quyền khiếu nại, khởi kiện ra Tòa án"),
    unilateral_price: bool = typer.Option(False, "--unilateral-price/--no-unilateral-price", help="Có điều khoản cho phép bên bán đơn phương thay đổi giá mà không báo trước"),
    ncc_registered: bool = typer.Option(True, "--ncc/--no-ncc", help="Đã đăng ký hợp đồng theo mẫu với Ủy ban Cạnh tranh Quốc gia"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Rà soát hợp đồng theo mẫu và điều kiện giao dịch chung (Điều 25 Luật BVQLNTD & QĐ 07/2024/QĐ-TTg)."""
    from src.core.consumer_engine import ConsumerEngine

    engine = ConsumerEngine()
    res = engine.audit_standard_contract_terms(
        contract_title=title,
        industry_type=industry,
        excludes_seller_liability=exclude_liability,
        restricts_consumer_dispute_rights=restrict_dispute,
        allows_unilateral_price_change=unilateral_price,
        registered_with_ncc=ncc_registered,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_valid"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]RÀ SOÁT HỢP ĐỒNG THEO MẪU & ĐIỀU KIỆN GIAO DỊCH CHUNG (ĐIỀU 25)[/]\n\n"
            f"  Mã thẩm tra:              [bold cyan]{res['review_id']}[/]\n"
            f"  Tên văn kiện:             [bold]{res['contract_title']}[/] (Ngành: [white]{res['industry_type']}[/])\n"
            f"  Đăng ký với UBCTQG:       [white]{'ĐÃ ĐĂNG KÝ HỢP LỆ' if res['registered_with_ncc'] else '[bold red]CHƯA ĐĂNG KÝ (NẾU THUỘC DIỆN BẮT BUỘC)[/]'}[/]\n"
            f"  Loại trừ trách nhiệm:     [white]{'[bold red]CÓ ĐIỀU KHOẢN VÔ HIỆU[/]' if res['excludes_seller_liability'] else 'KHÔNG CÓ'}[/]\n"
            f"  Hạn chế khởi kiện Tòa:    [white]{'[bold red]CÓ ĐIỀU KHOẢN VÔ HIỆU[/]' if res['restricts_consumer_dispute_rights'] else 'KHÔNG CÓ'}[/]\n"
            f"  Đơn phương thay đổi giá:  [white]{'[bold red]CÓ ĐIỀU KHOẢN VÔ HIỆU[/]' if res['allows_unilateral_price_change'] else 'KHÔNG CÓ'}[/]\n"
            f"  Kết luận thẩm tra:        [bold {color}]{'HỢP ĐỒNG HỢP PHÁP' if is_ok else 'CÓ ĐIỀU KHOẢN VÔ HIỆU (KHÔNG CÓ GIÁ TRỊ PHÁP LÝ)'}[/]\n\n"
            + (f"  Điều khoản vô hiệu:\n" + "\n".join(f"    - [bold red]{c}[/]" for c in res["void_clauses"]) + "\n\n" if res["void_clauses"] else "")
            + f"  Khuyến nghị sửa đổi:\n" + "\n".join(f"    - [white]{r}[/]" for r in res["recommendations"]),
            title=f"[bold {color}]Standard Contract Terms Review[/]",
            border_style=color,
        )
    )


@consumer_app.command("recall")
def recall_cmd(
    product: str = typer.Argument(..., help="Tên sản phẩm khuyết tật cần thu hồi"),
    defect_type: str = typer.Option("GROUP_A_LIFE_THREATENING", "--defect-type", "-t", help="Phân loại khuyết tật: GROUP_A_LIFE_THREATENING (Đe dọa tính mạng), GROUP_B_NORMAL"),
    batch: str = typer.Option("BAT-2026-X1", "--batch", "-b", help="Mã số lô hàng / Số serial sản phẩm"),
    distributed: int = typer.Option(10000, "--distributed", "-d", help="Tổng số lượng sản phẩm đã lưu thông ra thị trường"),
    recalled: int = typer.Option(8500, "--recalled", "-r", help="Số lượng sản phẩm đã thu hồi thành công"),
    announcement_24h: bool = typer.Option(True, "--announce/--no-announce", help="Đã công bố công khai trên thông tin đại chúng trong vòng 24 giờ"),
    ministry_reported: bool = typer.Option(True, "--report/--no-report", help="Đã gửi báo cáo chương trình thu hồi tới Bộ Công Thương"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Quản lý và giám sát chương trình thu hồi sản phẩm có khuyết tật (Điều 32-34 Luật BVQLNTD 2023)."""
    from src.core.consumer_engine import ConsumerEngine

    engine = ConsumerEngine()
    res = engine.manage_defective_product_recall(
        product_name=product,
        defect_type=defect_type,
        batch_serial=batch,
        units_distributed=distributed,
        units_recalled=recalled,
        public_announcement_made_24h=announcement_24h,
        reported_to_ministry=ministry_reported,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_danger = "CRITICAL" in res["recall_status"]
    color = "red" if is_danger else ("green" if res["completion_rate_pct"] >= 90.0 else "yellow")

    console.print(
        Panel(
            f"[bold {color}]QUẢN LÝ THU HỒI SẢN PHẨM CÓ KHUYẾT TẬT (ĐIỀU 32-34 LUẬT BVQLNTD)[/]\n\n"
            f"  Mã chương trình:          [bold cyan]{res['recall_id']}[/]\n"
            f"  Sản phẩm thu hồi:         [bold]{res['product_name']}[/] (Lô: [white]{res['batch_serial']}[/])\n"
            f"  Nhóm khuyết tật:          [bold red]{res['defect_type']}[/] ({'Đe dọa tính mạng/tài sản' if 'GROUP_A' in res['defect_type'] else 'Khuyết tật thông thường'})\n"
            f"  Số lượng lưu thông:       [white]{res['units_distributed']:,} đơn vị[/] | Đã thu hồi: [bold cyan]{res['units_recalled']:,} đơn vị[/]\n"
            f"  Tỷ lệ hoàn thành:         [bold {color}]{res['completion_rate_pct']}%[/]\n"
            f"  Công bố báo chí (24h):    [white]{'ĐÃ CÔNG BỐ' if res['public_announcement_made_24h'] else '[bold red]CHƯA CÔNG BỐ (VI PHẠM)[/]'}[/]\n"
            f"  Báo cáo Bộ Công Thương:   [white]{'ĐÃ BÁO CÁO' if res['reported_to_ministry'] else '[bold red]CHƯA BÁO CÁO[/]'}[/]\n"
            f"  Trạng thái chương trình:  [bold {color}]{res['recall_status']}[/]\n\n"
            f"  Biện pháp khắc phục:\n" + "\n".join(f"    - [white]{m}[/]" for m in res["remedial_measures"]),
            title=f"[bold {color}]Defective Product Recall Management[/]",
            border_style=color,
        )
    )


@consumer_app.command("dispute")
def dispute_cmd(
    complainant: str = typer.Argument(..., help="Họ tên người tiêu dùng khiếu nại"),
    merchant: str = typer.Option("Cửa hàng Điện máy ABC", "--merchant", "-m", help="Tên tổ chức, cá nhân kinh doanh"),
    value: float = typer.Option(25_000_000.0, "--value", "-v", help="Giá trị giao dịch tranh chấp (VND) - Trần 100 triệu cho thủ tục rút gọn"),
    method: str = typer.Option("SUMMARY_COURT_PROCEEDING", "--method", help="Phương thức: SUMMARY_COURT_PROCEEDING, NEGOTIATION, MEDIATION, ARBITRATION"),
    invoice: bool = typer.Option(True, "--invoice/--no-invoice", help="Có hóa đơn VAT, chứng từ hoặc dữ liệu điện tử giao dịch"),
    refused: bool = typer.Option(True, "--refused/--compromised", help="Bên bán từ chối thương lượng/hòa giải"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá hồ sơ tranh chấp người tiêu dùng và thủ tục rút gọn tại Tòa án (Điều 70-71 Luật BVQLNTD)."""
    from src.core.consumer_engine import ConsumerEngine

    engine = ConsumerEngine()
    res = engine.assess_consumer_dispute(
        complainant_name=complainant,
        merchant_name=merchant,
        transaction_value_vnd=value,
        dispute_method=method,
        has_evidence_invoice=invoice,
        seller_refused_compromise=refused,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_summary = res["eligible_for_summary_court"]
    color = "green" if is_summary else "yellow"

    console.print(
        Panel(
            f"[bold {color}]ĐÁNH GIÁ TRANH CHẤP & THỦ TỤC RÚT GỌN TẠI TÒA ÁN (ĐIỀU 70-71)[/]\n\n"
            f"  Mã vụ việc:               [bold cyan]{res['case_id']}[/]\n"
            f"  Người tiêu dùng:          [bold]{res['complainant_name']}[/] | Bên bán: [white]{res['merchant_name']}[/]\n"
            f"  Giá trị tranh chấp:       [bold yellow]{res['transaction_value_vnd']:,.0f} VND[/]\n"
            f"  Phương thức giải quyết:   [cyan]{res['dispute_method']}[/]\n"
            f"  Hóa đơn / Chứng từ:       [white]{'ĐẦY ĐỦ' if res['has_evidence_invoice'] else '[bold red]THIẾU CHỨNG TỪ[/]'}[/]\n"
            f"  Thương lượng ban đầu:     [white]{'[bold red]BÊN BÁN TỪ CHỐI THỎA THUẬN[/]' if res['seller_refused_compromise'] else 'ĐANG HÒA GIẢI'}[/]\n"
            f"  Thủ tục rút gọn Tòa án:   [bold {color}]{'ĐỦ ĐIỀU KIỆN (<= 100 TRIỆU ĐỒNG)' if is_summary else 'KHÔNG ĐỦ ĐIỀU KIỆN THỦ TỤC RÚT GỌN'}[/]\n"
            f"  Miễn tạm ứng án phí:      [bold green]{'ĐƯỢC MIỄN NỘP TẠM ỨNG ÁN PHÍ TÒA ÁN (KHOẢN 1 ĐIỀU 71)' if res['court_fee_exempt'] else 'KHÔNG ĐƯỢC MIỄN'}[/]\n\n"
            f"  Hướng dẫn xử lý tiếp theo:\n" + "\n".join(f"    - [white]{s}[/]" for s in res["recommended_next_steps"]),
            title=f"[bold {color}]Consumer Dispute Case Assessment[/]",
            border_style=color,
        )
    )


@consumer_app.command("list")
def list_cmd(
    category: str = typer.Argument("all", help="Phân loại tra cứu: 'all', 'platforms', 'contracts', 'recalls', 'disputes'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng hồ sơ hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục thẩm định nền tảng số, hợp đồng theo mẫu, thu hồi sản phẩm và hồ sơ tranh chấp."""
    from src.core.consumer_engine import ConsumerEngine

    engine = ConsumerEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if not records:
        console.print(f"[yellow]Không có dữ liệu trong danh mục '{category}'.[/]")
        return

    table = Table(title=f"Danh mục hồ sơ bảo vệ quyền lợi người tiêu dùng ({category})")
    table.add_column("Loại hồ sơ", style="cyan")
    table.add_column("Mã hồ sơ", style="bold")
    table.add_column("Tên đối tượng / Sản phẩm / Đương sự", style="green")
    table.add_column("Kết quả / Trạng thái", style="yellow")
    table.add_column("Thời gian khởi tạo", style="white")

    for r in records:
        rtype = r.get("type", "")
        if rtype == "platform_audit":
            table.add_row(
                "Nền tảng số",
                r["audit_id"],
                r["platform_name"],
                "Đạt chuẩn" if r["is_compliant"] else "Vi phạm",
                r["created_at"][:19],
            )
        elif rtype == "contract_review":
            table.add_row(
                "Hợp đồng mẫu",
                r["review_id"],
                r["contract_title"],
                "Hợp pháp" if r["is_valid"] else "Có điều khoản vô hiệu",
                r["created_at"][:19],
            )
        elif rtype == "product_recall":
            table.add_row(
                "Thu hồi sản phẩm",
                r["recall_id"],
                f"{r['product_name']} ({r['defect_type'][:15]})",
                f"{r['completion_rate_pct']}% ({r['recall_status'][:25]})",
                r["created_at"][:19],
            )
        elif rtype == "consumer_dispute":
            table.add_row(
                "Tranh chấp NTD",
                r["case_id"],
                f"{r['complainant_name']} vs {r['merchant_name']}",
                "Thủ tục rút gọn" if r["eligible_for_summary_court"] else "Thủ tục thường",
                r["created_at"][:19],
            )

    console.print(table)


@consumer_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp công tác bảo vệ quyền lợi người tiêu dùng toàn quốc."""
    from src.core.consumer_engine import ConsumerEngine

    engine = ConsumerEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]TELEMETRY BẢO VỆ QUYỀN LỢI NGƯỜI TIÊU DÙNG TOÀN QUỐC[/]\n\n"
            f"  Trạng thái:                [bold green]{data['status'].upper()}[/]\n"
            f"  Nền tảng số kiểm tra:      [bold]{data['total_platforms_audited']}[/] ([bold green]{data['compliant_digital_platforms']}[/] đạt chuẩn)\n"
            f"  Hợp đồng mẫu thẩm định:    [bold cyan]{data['total_standard_contracts_reviewed']}[/] ([bold green]{data['valid_standard_contracts']}[/] hợp lệ)\n"
            f"  Chương trình thu hồi SP:   [bold red]{data['active_product_recalls']}[/] chương trình\n"
            f"  Vụ việc tranh chấp:        [bold]{data['consumer_dispute_cases_total']}[/] vụ ([bold green]{data['summary_court_eligible_cases']}[/] đủ điều kiện thủ tục rút gọn Tòa án)\n"
            f"  Cơ sở dữ liệu SQLite WAL:  [white]{data['db_path']}[/]",
            title="[bold blue]Consumer Rights Protection Telemetry Status[/]",
            border_style="blue",
        )
    )
