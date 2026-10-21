"""Domain command group registrations (part 07)."""

from __future__ import annotations

import typer


def register_groups_07(root: typer.Typer) -> None:
    """Register domain command groups part 07 on root."""
    from src.cli.commands.inheritance_command import inheritance_app  # noqa: E402
    root.add_typer(
        inheritance_app,
        name="inheritance",
        help="Inheritance — Vietnamese Inheritance, Wills, Estate Administration & Succession Regimes Suite (BLDS 2015)",
    )
    root.add_typer(
        inheritance_app,
        name="thuake",
        help="ThuaKe — Alias for Vietnamese Inheritance, Wills & Estate Administration Suite",
    )
    root.add_typer(
        inheritance_app,
        name="disan",
        help="DiSan — Alias for Vietnamese Inheritance, Wills & Estate Administration Suite",
    )
    from src.cli.commands.guardianship_command import guardianship_app  # noqa: E402
    root.add_typer(
        guardianship_app,
        name="guardianship",
        help="Guardianship — Vietnamese Guardianship, Custodianship & Ward Protection Suite (BLDS 2015 Điều 46–63)",
    )
    root.add_typer(
        guardianship_app,
        name="giamho",
        help="GiamHo — Alias for Vietnamese Guardianship, Custodianship & Ward Protection Suite",
    )
    root.add_typer(
        guardianship_app,
        name="guardian",
        help="Guardian — Alias for Vietnamese Guardianship, Custodianship & Ward Protection Suite",
    )
    from src.cli.commands.tort_command import tort_app  # noqa: E402
    root.add_typer(
        tort_app,
        name="tort",
        help="Tort — Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite (BLDS 2015 Điều 584–608 & NQ 02/2022/NQ-HĐTP)",
    )
    root.add_typer(
        tort_app,
        name="boithuong",
        help="BoiThuong — Alias for Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite",
    )
    root.add_typer(
        tort_app,
        name="ngoaihopdong",
        help="NgoaiHopDong — Alias for Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite",
    )
    from src.cli.commands.adminsanction_command import adminsanction_app  # noqa: E402
    root.add_typer(
        adminsanction_app,
        name="adminsanction",
        help="AdminSanction — Vietnamese Administrative Sanctions, Statutory Fines & Remedial Measures Suite (Luật XLVPHC 2012/2020 & NĐ 118/2021/NĐ-CP)",
    )
    root.add_typer(
        adminsanction_app,
        name="xuphat",
        help="XuPhat — Alias for Vietnamese Administrative Sanctions & Violations Compliance Suite",
    )
    root.add_typer(
        adminsanction_app,
        name="vphc",
        help="VPHC — Alias for Vietnamese Administrative Sanctions & Violations Compliance Suite",
    )
    from src.cli.commands.agy_command import agy_app  # noqa: E402
    root.add_typer(
        agy_app,
        name="agy",
        help="AGY — Agent Governance YAML & Antigravity CLI Operations",
    )
    from src.cli.commands.trade_command import trade_app  # noqa: E402
    root.add_typer(
        trade_app,
        name="trade",
        help="Trade — International Trade, Multimodal Transport, Aviation, CISG & Trade Remedies Suite (Phases 163-166)",
    )
    root.add_typer(
        trade_app,
        name="thuongmai",
        help="ThuongMai — Alias for International Trade, Multimodal Transport & Trade Remedies Suite",
    )
    from src.cli.commands.fta_command import fta_app  # noqa: E402
    root.add_typer(
        fta_app,
        name="fta",
        help="FTA — Vietnam Free Trade Agreements, EPE, AEO & Duty Exemption Suite (Phases 171-174)",
    )
    root.add_typer(
        fta_app,
        name="dncx",
        help="DNCX — Alias for Vietnam Free Trade Agreements, EPE, AEO & Duty Exemption Suite",
    )
    from src.cli.commands.ecom_inspect_command import ecom_app as ecom_customs_app, inspect_app  # noqa: E402
    root.add_typer(
        ecom_customs_app,
        name="ecom-customs",
        help="Ecom Customs — Vietnam Cross-Border E-Commerce Customs & Platform Withholding Suite (Phase 175)",
    )
    root.add_typer(
        ecom_customs_app,
        name="tmdt",
        help="TMDT — Alias for Vietnam Cross-Border E-Commerce Customs & Platform Withholding Suite",
    )
    root.add_typer(
        inspect_app,
        name="inspect",
        help="Inspect — Specialized Inspection, Hazardous Chemicals, Food Safety & CBAM/EUDR Suite (Phases 176-178)",
    )
    root.add_typer(
        inspect_app,
        name="kiemtra",
        help="KiemTra — Alias for Specialized Inspection, Hazardous Chemicals, Food Safety & CBAM/EUDR Suite",
    )
    from src.cli.commands.port_supply_chain_command import port_app, tradefinance_app  # noqa: E402
    root.add_typer(
        port_app,
        name="port",
        help="Port — Vietnam Seaport Terminal Operations, DEM/DET & SOLAS VGM Suite (Phase 179)",
    )
    root.add_typer(
        port_app,
        name="cangbien",
        help="CangBien — Alias for Vietnam Seaport Terminal Operations, DEM/DET & SOLAS VGM Suite",
    )
    root.add_typer(
        tradefinance_app,
        name="tradefinance",
        help="TradeFinance — L/C UCP 600, Pharma Cold Chain & Green Freight Carbon Suite (Phases 180-182)",
    )
    root.add_typer(
        tradefinance_app,
        name="scf",
        help="SCF — Alias for Trade Finance L/C, Pharma Cold Chain & Green Freight Carbon Suite",
    )
