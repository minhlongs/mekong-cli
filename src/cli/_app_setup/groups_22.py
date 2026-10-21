"""Domain command group registrations (part 22)."""

from __future__ import annotations

import typer


def register_groups_22(root: typer.Typer) -> None:
    """Register domain command groups part 22 on root."""
    from src.cli.commands.maritime_safety_auxiliary_master_command import (  # noqa: E402
        maritime_aux_app,
    )
    root.add_typer(
        maritime_aux_app,
        name="maritime-aux",
        help="MaritimeAux — Stern Tube Gravity, Deck Water Seal, Scavenge Fire, FWG (Phases 463-466)",
    )
    root.add_typer(
        maritime_aux_app,
        name="phukienhanghai",
        help="PhuKienHangHai — Alias for Maritime Auxiliary Safety Engine (Phases 463-466)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch2_command import (  # noqa: E402
        maritime_aux2_app,
    )
    root.add_typer(
        maritime_aux2_app,
        name="maritime-aux2",
        help="MaritimeAux2 — Chilled Water, Incinerator Flue, Deepwell Stripping, Settling Tank (Phases 467-470)",
    )
    root.add_typer(
        maritime_aux2_app,
        name="phukienhanghai2",
        help="PhuKienHangHai2 — Alias for Maritime Safety Auxiliary Engine (Phases 467-470)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch3_command import (  # noqa: E402
        maritime_aux3_app,
    )
    root.add_typer(
        maritime_aux3_app,
        name="maritime-aux3",
        help="MaritimeAux3 — Bow Thruster, Emerg Fire Pump, Oil Mist, Scrubber Effluent (Phases 471-474)",
    )
    root.add_typer(
        maritime_aux3_app,
        name="phukienhanghai3",
        help="PhuKienHangHai3 — Alias for Maritime Safety Auxiliary Engine (Phases 471-474)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch4_command import (  # noqa: E402
        maritime_aux4_app,
    )
    root.add_typer(
        maritime_aux4_app,
        name="maritime-aux4",
        help="MaritimeAux4 — Stern Tube Seal, Nitrogen Gen, Scavenge Fire, BWMS UV (Phases 475-478)",
    )
    root.add_typer(
        maritime_aux4_app,
        name="phukienhanghai4",
        help="PhuKienHangHai4 — Alias for Maritime Safety Auxiliary Engine (Phases 475-478)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch5_command import (  # noqa: E402
        maritime_aux5_app,
    )
    root.add_typer(
        maritime_aux5_app,
        name="maritime-aux5",
        help="MaritimeAux5 — Cargo Hold Bilge, Aux Blower, Boiler Feedwater, Steering Gear (Phases 479-482)",
    )
    root.add_typer(
        maritime_aux5_app,
        name="phukienhanghai5",
        help="PhuKienHangHai5 — Alias for Maritime Safety Auxiliary Engine (Phases 479-482)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch6_command import (  # noqa: E402
        maritime_aux6_app,
    )
    root.add_typer(
        maritime_aux6_app,
        name="maritime-aux6",
        help="MaritimeAux6 — STP Aeration, Bearing Slowdown, EGB Circulation, Emergency Gen (Phases 483-486)",
    )
    root.add_typer(
        maritime_aux6_app,
        name="phukienhanghai6",
        help="PhuKienHangHai6 — Alias for Maritime Safety Auxiliary Engine (Phases 483-486)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch7_command import (  # noqa: E402
        maritime_aux7_app,
    )
    root.add_typer(
        maritime_aux7_app,
        name="maritime-aux7",
        help="MaritimeAux7 — Jacket Cooling, Deck Seal, Central Cooler, Starting Air (Phases 487-490)",
    )
    root.add_typer(
        maritime_aux7_app,
        name="phukienhanghai7",
        help="PhuKienHangHai7 — Alias for Maritime Safety Auxiliary Engine (Phases 487-490)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch8_command import (  # noqa: E402
        maritime_aux8_app,
    )
    root.add_typer(
        maritime_aux8_app,
        name="maritime-aux8",
        help="MaritimeAux8 — Thrust Bearing, Vacuum Sewage, Scrubber, Bow Thruster (Phases 491-494)",
    )
    root.add_typer(
        maritime_aux8_app,
        name="phukienhanghai8",
        help="PhuKienHangHai8 — Alias for Maritime Safety Auxiliary Engine (Phases 491-494)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch9_command import (  # noqa: E402
        maritime_aux9_app,
    )
    root.add_typer(
        maritime_aux9_app,
        name="maritime-aux9",
        help="MaritimeAux9 — Liner Stress, Incinerator Draft, Fire Pump & Purifier Seal (Phases 495-498)",
    )
    root.add_typer(
        maritime_aux9_app,
        name="phukienhanghai9",
        help="PhuKienHangHai9 — Alias for Maritime Safety Auxiliary Engine (Phases 495-498)",
    )
