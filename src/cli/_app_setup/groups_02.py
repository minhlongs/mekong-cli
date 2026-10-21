"""Domain command group registrations (part 02)."""

from __future__ import annotations

import typer


def register_groups_02(root: typer.Typer) -> None:
    """Register domain command groups part 02 on root."""
    from src.cli.commands.energy_command import energy_app  # noqa: E402
    root.add_typer(
        energy_app,
        name="energy",
        help="Energy — Vietnamese Renewable Energy, Rooftop Solar (ĐMTMN), DPPA & EV charging infrastructure",
    )
    from src.cli.commands.privacy_command import privacy_app  # noqa: E402
    root.add_typer(
        privacy_app,
        name="privacy",
        help="Privacy — Vietnamese Personal Data Protection Decree (PDPD Nghị định 13/2023/NĐ-CP) & cross-border transfer compliance",
    )
    from src.cli.commands.aviation_command import aviation_app  # noqa: E402
    root.add_typer(
        aviation_app,
        name="aviation",
        help="Aviation — Vietnamese Civil Aviation, Air Cargo Freight, IATA DGR & Airport Ground Handling",
    )
    from src.cli.commands.ecommerce_command import ecom_app  # noqa: E402
    root.add_typer(
        ecom_app,
        name="ecom",
        help="E-Commerce — Vietnamese Cross-Border E-Commerce, Overseas Supplier Tax & Marketplace Compliance",
    )
    from src.cli.commands.telecom_command import telecom_app  # noqa: E402
    root.add_typer(
        telecom_app,
        name="telecom",
        help="Telecom — Vietnamese Telecommunications Law 2023, Radio Spectrum Auctions, BTS EMF & OTT Services",
    )
    from src.cli.commands.pharma_command import pharma_app  # noqa: E402
    root.add_typer(
        pharma_app,
        name="pharma",
        help="Pharma — Vietnamese Drug Law 2016, National Drug Bank, GSP Cold Chain & Price Regulation",
    )
    from src.cli.commands.petrol_command import petrol_app  # noqa: E402
    root.add_typer(
        petrol_app,
        name="petrol",
        help="Petrol — Vietnamese Petroleum Regulations, Weekly Price Adjustments, National Reserves & Pump E-Invoicing",
    )
    from src.cli.commands.fishery_command import fishery_app  # noqa: E402
    root.add_typer(
        fishery_app,
        name="fishery",
        help="Fishery — Vietnamese Fisheries Law 2017, VMS Fleet Tracking, eCDT Catch Cert & EU IUU Yellow Card Compliance",
    )
    from src.cli.commands.construction_command import construction_app  # noqa: E402
    root.add_typer(
        construction_app,
        name="construction",
        help="Construction — Vietnamese Construction Law 2020, Building Permits, FIDIC Contracts & QCVN 06:2022 Fire Safety",
    )
    from src.cli.commands.mining_command import mining_app  # noqa: E402
    root.add_typer(
        mining_app,
        name="mining",
        help="Mining — Vietnamese Mineral Law 2010, Concession Rights Fees, Resource Royalties & Environmental Rehabilitation",
    )
    from src.cli.commands.forestry_command import forestry_app  # noqa: E402
    root.add_typer(
        forestry_app,
        name="forestry",
        help="Forestry — Vietnamese Forestry Law 2017, VNTLAS Timber Legality, FSC & Forest Carbon Sinks",
    )
    from src.cli.commands.water_command import water_app  # noqa: E402
    root.add_typer(
        water_app,
        name="water",
        help="Water — Vietnamese Clean Water Supply, Urban Drainage, Wastewater & Tariff Regulations",
    )
    from src.cli.commands.medtech_command import medtech_app  # noqa: E402
    root.add_typer(
        medtech_app,
        name="medtech",
        help="MedTech — Vietnamese Medical Devices, Healthcare Facility Licensing & Clinical Trials",
    )
    from src.cli.commands.livestock_command import livestock_app  # noqa: E402
    root.add_typer(
        livestock_app,
        name="livestock",
        help="Livestock — Vietnamese Animal Husbandry, Livestock Farming, Feed Standards & Biosecurity",
    )
    from src.cli.commands.railway_command import railway_app  # noqa: E402
    root.add_typer(
        railway_app,
        name="railway",
        help="Railway — Vietnamese Railway Transport, High-Speed Rail & Urban Metro",
    )
    from src.cli.commands.transport_command import transport_app  # noqa: E402
    root.add_typer(
        transport_app,
        name="transport",
        help="Transport — Vietnamese Road Transport, Logistics, Highway Tolling & ETC Regulation",
    )
    from src.cli.commands.waterway_command import waterway_app  # noqa: E402
    root.add_typer(
        waterway_app,
        name="waterway",
        help="Waterway — Vietnamese Inland Waterway Transport, River Ports & Canal Navigation",
    )
    from src.cli.commands.postal_command import postal_app  # noqa: E402
    root.add_typer(
        postal_app,
        name="postal",
        help="Postal — Vietnamese Postal, Express Delivery & Courier Logistics",
    )
    from src.cli.commands.tourism_command import tourism_app  # noqa: E402
    root.add_typer(
        tourism_app,
        name="tourism",
        help="Tourism — Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating",
    )
    from src.cli.commands.insurance_command import insurance_app  # noqa: E402
    root.add_typer(
        insurance_app,
        name="insurance",
        help="Insurance — Vietnamese Insurance Business, Actuarial Solvency & Underwriting",
    )
