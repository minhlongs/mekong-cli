"""Domain command group registrations (part 03)."""

from __future__ import annotations

import typer


def register_groups_03(root: typer.Typer) -> None:
    """Register domain command groups part 03 on root."""
    from src.cli.commands.food_command import food_app  # noqa: E402
    root.add_typer(
        food_app,
        name="food",
        help="Food — Vietnamese Food Safety, Dietary Supplements & Hygiene Certification",
    )
    from src.cli.commands.securities_command import securities_app  # noqa: E402
    root.add_typer(
        securities_app,
        name="securities",
        help="Securities — Vietnamese Securities, Stock Exchanges & Capital Markets",
    )
    from src.cli.commands.banking_command import banking_app  # noqa: E402
    root.add_typer(
        banking_app,
        name="banking",
        help="Banking — Vietnamese Commercial Banking, Credit Institutions & Basel II",
    )
    from src.cli.commands.environment_command import environment_app  # noqa: E402
    root.add_typer(
        environment_app,
        name="environment",
        help="Environment — Vietnamese Environmental Protection, EIA & Carbon Credits",
    )
    from src.cli.commands.education_command import education_app  # noqa: E402
    root.add_typer(
        education_app,
        name="education",
        help="Education — Vietnamese Education, Higher Education, Accreditation & Degree Registry",
    )
    from src.cli.commands.automotive_command import automotive_app  # noqa: E402
    root.add_typer(
        automotive_app,
        name="automotive",
        help="Automotive — Vietnamese Automotive Manufacturing, Type Approval, Emission & EV Suite",
    )
    from src.cli.commands.advertising_command import advertising_app  # noqa: E402
    root.add_typer(
        advertising_app,
        name="advertising",
        help="Advertising — Vietnamese Advertising, Media & Digital Marketing Compliance Suite",
    )
    from src.cli.commands.cinema_command import cinema_app  # noqa: E402
    root.add_typer(
        cinema_app,
        name="cinema",
        help="Cinema — Vietnamese Cinema, Film Production, Age Classification & Censorship Suite",
    )
    from src.cli.commands.publishing_command import publishing_app  # noqa: E402
    root.add_typer(
        publishing_app,
        name="publishing",
        help="Publishing — Vietnamese Publishing, Printing, Distribution & Legal Depository Suite",
    )
    from src.cli.commands.standards_command import standards_app  # noqa: E402
    root.add_typer(
        standards_app,
        name="standards",
        help="Standards — Vietnamese Technical Standards, Metrology, CR Mark & Product Quality Suite",
    )
    from src.cli.commands.hitech_command import hitech_app  # noqa: E402
    root.add_typer(
        hitech_app,
        name="hitech",
        help="Hitech — Vietnamese High-Tech Enterprise, Science Parks & Tech Transfer Suite",
    )
    from src.cli.commands.notary_command import notary_app  # noqa: E402
    root.add_typer(
        notary_app,
        name="notary",
        help="Notary — Vietnamese Notary, Legal Practice & Judicial Authentication Suite",
    )
    from src.cli.commands.price_command import price_app  # noqa: E402
    root.add_typer(
        price_app,
        name="price",
        help="Price — Vietnamese Price Management, Anti-Price Gouging & Valuation Suite",
    )
    from src.cli.commands.geodesy_command import geodesy_app  # noqa: E402
    root.add_typer(
        geodesy_app,
        name="geodesy",
        help="Geodesy — Vietnamese Geodesy, National Coordinates (VN-2000), Sovereignty & Cadastral GIS Suite",
    )
    from src.cli.commands.fire_command import fire_app  # noqa: E402
    root.add_typer(
        fire_app,
        name="fire",
        help="Fire — Vietnamese Fire Prevention, Safety, Rescue & Engineering Standards Suite",
    )
    from src.cli.commands.chemical_command import chemical_app  # noqa: E402
    root.add_typer(
        chemical_app,
        name="chemical",
        help="Chemical — Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Suite",
    )
    from src.cli.commands.competition_command import competition_app  # noqa: E402
    root.add_typer(
        competition_app,
        name="competition",
        help="Competition — Vietnamese Competition, Antitrust, Anti-Monopoly & Economic Concentration Suite",
    )
    from src.cli.commands.cyber_command import cyber_app  # noqa: E402
    root.add_typer(
        cyber_app,
        name="cyber",
        help="Cyber — Vietnamese Cybersecurity, Critical Information Infrastructure & Network Security Suite",
    )
    from src.cli.commands.disaster_command import disaster_app  # noqa: E402
    root.add_typer(
        disaster_app,
        name="disaster",
        help="Disaster — Vietnamese Meteorology, Dam Safety & Natural Disaster Prevention Suite",
    )
    from src.cli.commands.radiation_command import radiation_app  # noqa: E402
    root.add_typer(
        radiation_app,
        name="radiation",
        help="Radiation — Vietnamese Radiation Safety, Radioactive Sources & Nuclear Technology Suite",
    )
