"""Domain command group registrations (part 23)."""

from __future__ import annotations

import typer


def register_groups_23(root: typer.Typer) -> None:
    """Register domain command groups part 23 on root."""
    from src.cli.commands.maritime_safety_auxiliary_batch10_command import (  # noqa: E402
        maritime_aux10_app,
    )
    root.add_typer(
        maritime_aux10_app,
        name="maritime-aux10",
        help="MaritimeAux10 — Turbocharger Surge, FWG Salinity, CO2 Flooding & Viscometer (Phases 499-502)",
    )
    root.add_typer(
        maritime_aux10_app,
        name="phukienhanghai10",
        help="PhuKienHangHai10 — Alias for Maritime Safety Auxiliary Engine (Phases 499-502)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch11_command import (  # noqa: E402
        maritime_aux11_app,
    )
    root.add_typer(
        maritime_aux11_app,
        name="maritime-aux11",
        help="MaritimeAux11 — Hull ICCP, Sea Chest MGPS, Galley HVAC & Provision Reefer (Phases 503-506)",
    )
    root.add_typer(
        maritime_aux11_app,
        name="phukienhanghai11",
        help="PhuKienHangHai11 — Alias for Maritime Safety Auxiliary Engine (Phases 503-506)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch12_command import (  # noqa: E402
        maritime_aux12_app,
    )
    root.add_typer(
        maritime_aux12_app,
        name="maritime-aux12",
        help="MaritimeAux12 — Shaft Grounding, Emergency Bilge, Watertight Doors & Helideck Foam (Phases 507-510)",
    )
    root.add_typer(
        maritime_aux12_app,
        name="phukienhanghai12",
        help="PhuKienHangHai12 — Alias for Maritime Safety Auxiliary Engine (Phases 507-510)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch13_command import (  # noqa: E402
        maritime_aux13_app,
    )
    root.add_typer(
        maritime_aux13_app,
        name="maritime-aux13",
        help="MaritimeAux13 — Scavenge Condensate, Medical O2, Mooring Brake & Water-Mist (Phases 511-514)",
    )
    root.add_typer(
        maritime_aux13_app,
        name="phukienhanghai13",
        help="PhuKienHangHai13 — Alias for Maritime Safety Auxiliary Engine (Phases 511-514)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch14_command import (  # noqa: E402
        maritime_aux14_app,
    )
    root.add_typer(
        maritime_aux14_app,
        name="maritime-aux14",
        help="MaritimeAux14 — Anchor Windlass, Switchboard Insulation, Bow Visor & Elevator (Phases 515-518)",
    )
    root.add_typer(
        maritime_aux14_app,
        name="phukienhanghai14",
        help="PhuKienHangHai14 — Alias for Maritime Safety Auxiliary Engine (Phases 515-518)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch15_command import (  # noqa: E402
        maritime_aux15_app,
    )
    root.add_typer(
        maritime_aux15_app,
        name="maritime-aux15",
        help="MaritimeAux15 — Turning Gear, Grey Water Tank, Deck Crane & Escape Trunk (Phases 519-522)",
    )
    root.add_typer(
        maritime_aux15_app,
        name="phukienhanghai15",
        help="PhuKienHangHai15 — Alias for Maritime Safety Auxiliary Engine (Phases 519-522)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch16_command import (  # noqa: E402
        maritime_aux16_app,
    )
    root.add_typer(
        maritime_aux16_app,
        name="maritime-aux16",
        help="MaritimeAux16 — Torsional BSR, BNWAS Cascade, Paint Locker & Accom Ladder (Phases 523-526)",
    )
    root.add_typer(
        maritime_aux16_app,
        name="phukienhanghai16",
        help="PhuKienHangHai16 — Alias for Maritime Safety Auxiliary Engine (Phases 523-526)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch17_command import (  # noqa: E402
        maritime_aux17_app,
    )
    root.add_typer(
        maritime_aux17_app,
        name="maritime-aux17",
        help="MaritimeAux17 — Cylinder Lubricator, Bilge Tank, Cargo Smoke & Freefall Boat (Phases 527-530)",
    )
    root.add_typer(
        maritime_aux17_app,
        name="phukienhanghai17",
        help="PhuKienHangHai17 — Alias for Maritime Safety Auxiliary Engine (Phases 527-530)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch18_command import (  # noqa: E402
        maritime_aux18_app,
    )
    root.add_typer(
        maritime_aux18_app,
        name="maritime-aux18",
        help="MaritimeAux18 — HP Fuel Pipe, IGG Stoichiometry, Stern Air-Guard & Enclosed Space (Phases 531-534)",
    )
    root.add_typer(
        maritime_aux18_app,
        name="phukienhanghai18",
        help="PhuKienHangHai18 — Alias for Maritime Safety Auxiliary Engine (Phases 531-534)",
    )
