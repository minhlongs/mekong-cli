"""Domain command group registrations (part 04)."""

from __future__ import annotations

import typer


def register_groups_04(root: typer.Typer) -> None:
    """Register domain command groups part 04 on root."""
    from src.cli.commands.crop_command import crop_app  # noqa: E402
    root.add_typer(
        crop_app,
        name="crop",
        help="Crop — Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Suite",
    )
    from src.cli.commands.consumer_command import consumer_app  # noqa: E402
    root.add_typer(
        consumer_app,
        name="consumer",
        help="Consumer — Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Suite",
    )
    from src.cli.commands.defense_command import defense_app  # noqa: E402
    root.add_typer(
        defense_app,
        name="defense",
        help="Defense — Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Suite",
    )
    from src.cli.commands.aml_command import aml_app  # noqa: E402
    root.add_typer(
        aml_app,
        name="aml",
        help="AML — Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Suite",
    )
    from src.cli.commands.press_command import press_app  # noqa: E402
    root.add_typer(
        press_app,
        name="press",
        help="Press — Vietnamese Press, Mass Media, Online Journalism & OTT Broadcasting Suite",
    )
    from src.cli.commands.archives_command import archives_app  # noqa: E402
    root.add_typer(
        archives_app,
        name="archives",
        help="Archives — Vietnamese Archives, Digital Records & State Secrets Declassification Suite",
    )
    from src.cli.commands.heritage_command import heritage_app  # noqa: E402
    root.add_typer(
        heritage_app,
        name="heritage",
        help="Heritage — Vietnamese Cultural Heritage, Antiquities & National Treasures Suite",
    )
    from src.cli.commands.sports_command import sports_app  # noqa: E402
    root.add_typer(
        sports_app,
        name="sports",
        help="Sports — Vietnamese Physical Training, Sports, Professional Athletics & Anti-Doping Suite",
    )
    from src.cli.commands.veterinary_command import veterinary_app  # noqa: E402
    root.add_typer(
        veterinary_app,
        name="veterinary",
        help="Veterinary — Vietnamese Veterinary Medicine, Animal Disease Surveillance & Livestock Quarantine Suite",
    )
    from src.cli.commands.arbitration_command import arbitration_app  # noqa: E402
    root.add_typer(
        arbitration_app,
        name="arbitration",
        help="Arbitration — Vietnamese Commercial Arbitration & Out-of-Court Dispute Resolution Suite",
    )
    from src.cli.commands.civil_status_command import civil_status_app  # noqa: E402
    root.add_typer(
        civil_status_app,
        name="civil-status",
        help="Civil Status — Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite",
    )
    from src.cli.commands.bailiff_command import bailiff_app  # noqa: E402
    root.add_typer(
        bailiff_app,
        name="bailiff",
        help="Bailiff — Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite",
    )
    from src.cli.commands.mediation_command import mediation_app  # noqa: E402
    root.add_typer(
        mediation_app,
        name="mediation",
        help="Mediation — Vietnamese Commercial Mediation, Conciliation & ADR Suite",
    )
    from src.cli.commands.forensic_command import forensic_app  # noqa: E402
    root.add_typer(
        forensic_app,
        name="forensic",
        help="Forensic — Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite",
    )
    from src.cli.commands.auction_command import auction_app  # noqa: E402
    root.add_typer(
        auction_app,
        name="auction",
        help="Auction — Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite",
    )
    from src.cli.commands.bankruptcy_command import bankruptcy_app  # noqa: E402
    root.add_typer(
        bankruptcy_app,
        name="bankruptcy",
        help="Bankruptcy — Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite",
    )
    from src.cli.commands.admiralty_command import admiralty_app  # noqa: E402
    root.add_typer(
        admiralty_app,
        name="admiralty",
        help="Admiralty — Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest & Maritime Liens Suite",
    )
    from src.cli.commands.competition_command import competition_app  # noqa: E402
    root.add_typer(
        competition_app,
        name="competition",
        help="Competition — Vietnamese Competition Law, Antitrust, Anti-Monopoly & Economic Concentration Suite",
    )
    from src.cli.commands.enforcement_command import enforcement_app  # noqa: E402
    root.add_typer(
        enforcement_app,
        name="enforcement",
        help="Enforcement — Vietnamese Civil Judgment Enforcement, Asset Attachment & Debt Recovery Suite",
    )
    from src.cli.commands.etransaction_command import etransaction_app  # noqa: E402
    root.add_typer(
        etransaction_app,
        name="etransaction",
        help="E-Transaction — Vietnamese Electronic Transactions, Digital Signatures, Trust Services & Data Messages Suite",
    )
