"""Domain command group registrations (part 14)."""

from __future__ import annotations

import typer


def register_groups_14(root: typer.Typer) -> None:
    """Register domain command groups part 14 on root."""
    from src.cli.commands.maritime_agency_salvage_abandonment_cleanport_command import (  # noqa: E402
        shipagency_app,
        salvage_app as salvagescopic_app,
        abandonment_app,
        greentug_app,
    )
    root.add_typer(
        shipagency_app,
        name="shipagency",
        help="ShipAgency — Maritime Ship Agency & Husbandry PDA/FDA Accounting (Phase 255)",
    )
    root.add_typer(
        shipagency_app,
        name="dailytaubien",
        help="DailyTauBien — Alias for Maritime Ship Agency & Husbandry PDA/FDA Accounting",
    )
    root.add_typer(
        salvagescopic_app,
        name="salvagescopic",
        help="SalvageScopic — Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement (Phase 256)",
    )
    root.add_typer(
        salvagescopic_app,
        name="cuuhohopdong",
        help="CuuHoHopDong — Alias for Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement",
    )
    root.add_typer(
        abandonment_app,
        name="abandonment",
        help="Abandonment — Seafarer Repatriation & Abandonment Financial Security Guarantee (Phase 257)",
    )
    root.add_typer(
        abandonment_app,
        name="bothuyenvien",
        help="BoThuyenVien — Alias for Seafarer Repatriation & Abandonment Financial Security Guarantee",
    )
    root.add_typer(
        greentug_app,
        name="greentug",
        help="GreenTug — Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives (Phase 258)",
    )
    root.add_typer(
        greentug_app,
        name="taulaixanh",
        help="TauLaiXanh — Alias for Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives",
    )
    from src.cli.commands.maritime_flag_collision_psc_reefer_command import (  # noqa: E402
        bareboat_app,
        collision_app,
        tokyomou_app,
        reeferport_app,
    )
    from src.cli.commands.maritime_admiralty_ga_collision_command import (  # noqa: E402
        collision_app as legacy_collision_app,
    )
    # Preserve the Phase 206 `collision assess` command on the later Phase 260 group.
    for command in legacy_collision_app.registered_commands:
        if command.name == "assess" and command.callback is not None:
            collision_app.command("assess")(command.callback)
    root.add_typer(
        bareboat_app,
        name="bareboat",
        help="Bareboat — Bareboat Charter Registry & Temporary Flag Suspension Under VMC 2015 (Phase 259)",
    )
    root.add_typer(
        bareboat_app,
        name="thuetran",
        help="ThueTran — Alias for Bareboat Charter Registry & Temporary Flag Suspension Under VMC 2015",
    )
    root.add_typer(
        collision_app,
        name="collision",
        help="Collision — Collision Cross-Liabilities & Both-to-Blame Clause Settlement Under VMC 2015 (Phase 260)",
    )
    root.add_typer(
        collision_app,
        name="damva",
        help="DamVa — Alias for Collision Cross-Liabilities & Both-to-Blame Clause Settlement Under VMC 2015",
    )
    root.add_typer(
        tokyomou_app,
        name="tokyomou",
        help="TokyoMOU — Tokyo MOU PSC Ship Risk Profile (SRP) & CIC Inspection Calculator (Phase 261)",
    )
    root.add_typer(
        tokyomou_app,
        name="kiemtrapsc",
        help="KiemTraPSC — Alias for Tokyo MOU PSC Ship Risk Profile (SRP) & CIC Inspection Calculator",
    )
    root.add_typer(
        reeferport_app,
        name="reeferport",
        help="ReeferPort — Seaport Reefer Container Electricity Tariff & Temperature Monitoring (Phase 262)",
    )
    root.add_typer(
        reeferport_app,
        name="containerlanh",
        help="ContainerLanh — Alias for Seaport Reefer Container Electricity Tariff & Temperature Monitoring",
    )
    from src.cli.commands.maritime_loi_ga_bunker_demurrage_command import (  # noqa: E402
        loi_app,
        ga_app,
        bunker_app,
        demurrage_app,
    )
    from src.cli.commands.maritime_passenger_mortgage_bunker_pilot_command import (  # noqa: E402
        audit_bunker_fuel as audit_legacy_bunker_fuel,
    )
    # Keep the Phase 217 `bunker audit` interface available after the newer
    # Bunker group is registered under the same top-level command name.
    bunker_app.command(name="audit")(audit_legacy_bunker_fuel)
    root.add_typer(
        loi_app,
        name="loi",
        help="LOI — Letter of Indemnity & Switch B/L Risk Evaluation Under VMC 2015 (Phase 263)",
    )
    root.add_typer(
        loi_app,
        name="thuboiduong",
        help="ThuBoiDuong — Alias for Letter of Indemnity & Switch B/L Risk Evaluation Under VMC 2015",
    )
    root.add_typer(
        ga_app,
        name="ga",
        help="GA — General Average Adjustment Calculator Under York-Antwerp Rules 2016 (Phase 264)",
    )
    root.add_typer(
        ga_app,
        name="tonthatchung",
        help="TonThatChung — Alias for General Average Adjustment Calculator Under York-Antwerp Rules 2016",
    )
    root.add_typer(
        bunker_app,
        name="bunker",
        help="Bunker — Bunker Delivery Note & MARPOL Annex VI Fuel Sulfur Compliance (Phase 265)",
    )
    root.add_typer(
        bunker_app,
        name="nhienlieutau",
        help="NhienLieuTau — Alias for Bunker Delivery Note & MARPOL Annex VI Fuel Sulfur Compliance",
    )
    root.add_typer(
        demurrage_app,
        name="demurrage",
        help="Demurrage — Seaport Container Demurrage & Detention Progressive Tariff Engine (Phase 266)",
    )
    root.add_typer(
        demurrage_app,
        name="luubai",
        help="LuuBai — Alias for Seaport Container Demurrage & Detention Progressive Tariff Engine",
    )
