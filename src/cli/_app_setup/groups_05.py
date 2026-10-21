"""Domain command group registrations (part 05)."""

from __future__ import annotations

import typer


def register_groups_05(root: typer.Typer) -> None:
    """Register domain command groups part 05 on root."""
    from src.cli.commands.pubinvestment_command import pubinvestment_app  # noqa: E402
    root.add_typer(
        pubinvestment_app,
        name="pubinvestment",
        help="Public Investment — Vietnamese Public Investment, Capital Allocation, Feasibility & Medium-Term Planning Suite",
    )
    from src.cli.commands.statebudget_command import statebudget_app  # noqa: E402
    root.add_typer(
        statebudget_app,
        name="statebudget",
        help="State Budget — Vietnamese State Budget, Fiscal Discipline, Public Treasury Accounts & Budget Allocations Suite",
    )
    from src.cli.commands.taxadmin_command import taxadmin_app  # noqa: E402
    root.add_typer(
        taxadmin_app,
        name="taxadmin",
        help="Tax Administration — Vietnamese Tax Administration, Electronic Invoices & Tax Audit Compliance Suite (Luật Quản lý thuế 2019)",
    )
    from src.cli.commands.publicdebt_command import publicdebt_app  # noqa: E402
    root.add_typer(
        publicdebt_app,
        name="publicdebt",
        help="Public Debt — Vietnamese Public Debt, Sovereign Bonds, ODA On-Lending & Debt Safety Red Lines Suite (Luật Quản lý nợ công 2017)",
    )
    from src.cli.commands.nationalreserve_command import app as nationalreserve_app  # noqa: E402
    root.add_typer(
        nationalreserve_app,
        name="nationalreserve",
        help="National Reserves — Vietnamese National Reserves, Strategic Stockpiling & Emergency Relief Suite (Luật Dự trữ quốc gia 2012)",
    )
    from src.cli.commands.stateaudit_command import app as stateaudit_app  # noqa: E402
    root.add_typer(
        stateaudit_app,
        name="stateaudit",
        help="State Audit — Vietnamese State Audit, Supreme Audit Institution (SAV / KTNN) & Public Financial Oversight Suite (Luật Kiểm toán nhà nước 2015)",
    )
    from src.cli.commands.anticorruption_command import app as anticorruption_app  # noqa: E402
    root.add_typer(
        anticorruption_app,
        name="anticorruption",
        help="Anti-Corruption — Vietnamese Anti-Corruption, Asset Declaration & Integrity Oversight Suite (Luật Phòng, chống tham nhũng 2018)",
    )
    from src.cli.commands.antiterrorism_command import app as antiterrorism_app  # noqa: E402
    root.add_typer(
        antiterrorism_app,
        name="antiterrorism",
        help="Anti-Terrorism — Vietnamese Anti-Terrorism, Homeland Security & Target Protection Suite (Luật Phòng, chống khủng bố 2013)",
    )
    from src.cli.commands.statesecret_command import app as statesecret_app  # noqa: E402
    root.add_typer(
        statesecret_app,
        name="statesecret",
        help="State Secret — Vietnamese State Secrets & Classified Protection Suite (Luật Bảo vệ bí mật nhà nước 2018)",
    )
    from src.cli.commands.borderguard_command import app as borderguard_app  # noqa: E402
    root.add_typer(
        borderguard_app,
        name="borderguard",
        help="Border Guard — Vietnamese National Border, Territorial Sovereignty & Border Guard Defense Suite (Luật Biên phòng Việt Nam 2020)",
    )
    from src.cli.commands.civildefense_command import app as civildefense_app  # noqa: E402
    root.add_typer(
        civildefense_app,
        name="civildefense",
        help="Civil Defense — Vietnamese Civil Defense, Disaster Mitigation & Emergency Response Suite (Luật Phòng thủ dân sự 2023)",
    )
    from src.cli.commands.coastguard_command import app as coastguard_app  # noqa: E402
    root.add_typer(
        coastguard_app,
        name="coastguard",
        help="Coast Guard — Vietnamese Coast Guard & Maritime Law Enforcement Suite (Luật Cảnh sát biển Việt Nam 2018)",
    )
    from src.cli.commands.cipher_command import app as cipher_app  # noqa: E402
    root.add_typer(
        cipher_app,
        name="cipher",
        help="Cipher — Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite (Luật Cơ yếu 2011 & Nghị định 58/2016/NĐ-CP)",
    )
    from src.cli.commands.traffic_command import app as traffic_app  # noqa: E402
    root.add_typer(
        traffic_app,
        name="traffic",
        help="Traffic — Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite (Luật Trật tự, an toàn giao thông đường bộ 2024)",
    )
    from src.cli.commands.police_command import app as police_app  # noqa: E402
    root.add_typer(
        police_app,
        name="police",
        help="Police — Vietnamese People's Public Security & Grassroots Security Forces Suite (Luật CAND & Luật Lực lượng tham gia bảo vệ ANTT ở cơ sở)",
    )
    from src.cli.commands.identity_command import app as identity_app  # noqa: E402
    root.add_typer(
        identity_app,
        name="identity",
        help="Identity — Vietnamese National Identification, Electronic Identity (VNeID) & Biometrics Suite (Luật Căn cước 2023 & NĐ 69/2024/NĐ-CP)",
    )
    from src.cli.commands.prosecution_command import app as prosecution_app  # noqa: E402
    root.add_typer(
        prosecution_app,
        name="prosecution",
        help="Prosecution — Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite (Luật Tổ chức VKSND 2014 & BLTTHS 2015)",
    )
    from src.cli.commands.court_command import court_app  # noqa: E402
    root.add_typer(
        court_app,
        name="court",
        help="Court — Vietnamese People's Courts, Judicial Adjudication & Electronic Court Suite (Luật Tổ chức TAND 2024)",
    )
    from src.cli.commands.lawyer_command import lawyer_app  # noqa: E402
    root.add_typer(
        lawyer_app,
        name="lawyer",
        help="Lawyer — Vietnamese Legal Profession, Bar Association & Law Practice Suite (Luật Luật sư 2006/2012)",
    )
    from src.cli.commands.legalaid_command import legalaid_app  # noqa: E402
    root.add_typer(
        legalaid_app,
        name="legalaid",
        help="LegalAid — Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access Suite (Luật Trợ giúp pháp lý 2017)",
    )
