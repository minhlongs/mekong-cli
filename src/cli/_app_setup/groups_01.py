"""Domain command group registrations (part 01)."""

from __future__ import annotations

import typer


def register_groups_01(root: typer.Typer) -> None:
    """Register domain command groups part 01 on root."""
    from src.cli.funnel_commands import (
        bhxh_app,
        ke_toan_app,
        thue_app,
        vietqr_app,
        zalo_app,
    )
    root.add_typer(
        zalo_app,
        name="zalo-oa",
        help="Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài",
    )
    root.add_typer(
        thue_app,
        name="thue",
        help="Thuế VN — TNCN lũy tiến, TNDN, GTGT (offline)",
    )
    root.add_typer(
        ke_toan_app,
        name="ke-toan",
        help="Kế toán VN — hóa đơn TT78/2021, bút toán VAS, XML",
    )
    root.add_typer(
        bhxh_app,
        name="bhxh",
        help="Bảo hiểm xã hội VN — BHXH, BHYT, BHTN, hồ sơ D02-LT (NĐ 73/2024)",
    )
    from src.commands.ocop_commands import app as ocop_app  # noqa: E402
    root.add_typer(
        ocop_app,
        name="ocop",
        help="OCOP — nông sản Việt Nam, xếp hạng sao OCOP & xuất khẩu",
    )
    root.add_typer(
        vietqr_app,
        name="vietqr",
        help="VietQR — thanh toán chuyển khoản Napas 247, mã QR EMVCo & đối soát",
    )
    from src.cli.commands.audit_command import audit_app  # noqa: E402
    root.add_typer(
        audit_app,
        name="audit",
        help="Audit — Enterprise SOX 404, ITGC & COSO internal controls audit engine",
    )
    from src.cli.commands.payroll_command import payroll_app  # noqa: E402
    root.add_typer(
        payroll_app,
        name="payroll",
        help="Payroll — Vietnamese statutory payroll, Gross-to-Net & compensation engine",
    )
    from src.cli.commands.corporate_command import corporate_app  # noqa: E402
    root.add_typer(
        corporate_app,
        name="corporate",
        help="Corporate — Vietnamese corporate governance, incorporation & statutory legal filings",
    )
    from src.cli.commands.fdi_command import fdi_app  # noqa: E402
    root.add_typer(
        fdi_app,
        name="fdi",
        help="FDI — Foreign Direct Investment & SBV capital compliance engine",
    )
    from src.cli.commands.ip_command import ip_app  # noqa: E402
    root.add_typer(
        ip_app,
        name="ip",
        help="IP — Intellectual Property, Trademarks, Patents & Software Copyright",
    )
    from src.cli.commands.customs_command import customs_app  # noqa: E402
    root.add_typer(
        customs_app,
        name="customs",
        help="Customs — Vietnamese customs valuation, Rules of Origin, FX, tech transfer & bonded logistics suite (Phases 167-170)",
    )
    root.add_typer(
        customs_app,
        name="haiquan",
        help="HaiQuan — Alias for Vietnamese customs valuation, FX, tech transfer & bonded logistics suite",
    )
    from src.cli.commands.contract_command import contract_app  # noqa: E402
    root.add_typer(
        contract_app,
        name="contract",
        help="Contract — Vietnamese commercial contracts, e-signatures & legal risk assessment",
    )
    from src.cli.commands.tender_command import tender_app  # noqa: E402
    root.add_typer(
        tender_app,
        name="tender",
        help="Tender — Vietnamese public procurement, bidding dossiers & E-GP evaluation",
    )
    from src.cli.commands.realestate_command import realestate_app  # noqa: E402
    root.add_typer(
        realestate_app,
        name="realestate",
        help="RealEstate — Vietnamese commercial real estate, industrial land leasing & QCVN 01:2021 density compliance",
    )
    from src.cli.commands.esg_command import esg_app  # noqa: E402
    root.add_typer(
        esg_app,
        name="esg",
        help="ESG — Vietnamese environmental protection, GHG inventory, CBAM liability & carbon credit trading",
    )
    from src.cli.commands.supplychain_command import supplychain_app  # noqa: E402
    root.add_typer(
        supplychain_app,
        name="supplychain",
        help="SupplyChain — Vietnamese agricultural & timber traceability, EUDR anti-deforestation & EPCIS custody tracking",
    )
    from src.cli.commands.labor_command import labor_app  # noqa: E402
    root.add_typer(
        labor_app,
        name="labor",
        help="Labor — Vietnamese Labor Code 2019, foreign work permits, overtime caps & safety compliance",
    )
    from src.cli.commands.maritime_command import maritime_app  # noqa: E402
    root.add_typer(
        maritime_app,
        name="maritime",
        help="Maritime — Vietnamese Maritime Code 2015, seaport terminal operations, ICD & customs e-Manifest",
    )
    from src.cli.commands.dispute_command import dispute_app  # noqa: E402
    root.add_typer(
        dispute_app,
        name="dispute",
        help="Dispute — Commercial Arbitration VIAC 2024, Civil Enforcement, Court Fees & Maritime Law (Phases 159-162)",
    )
    root.add_typer(
        dispute_app,
        name="tranhchap",
        help="Tranh Chấp — Trọng tài VIAC, Thi hành án dân sự, Án phí Tòa án & Hàng hải",
    )
