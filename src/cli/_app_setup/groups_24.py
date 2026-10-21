"""Domain command group registrations (part 24)."""

from __future__ import annotations

import typer


def register_groups_24(root: typer.Typer) -> None:
    """Register domain command groups part 24 on root."""
    from src.cli.commands.maritime_isps_hazmat_oog_anchorage_command import (
        anchorage_app,
        hazmat_app,
        isps_app,
        oog_stevedore_app,
    )
    from src.cli.commands.maritime_safety_auxiliary_batch19_command import (  # noqa: E402
        maritime_aux19_app,
    )
    root.add_typer(
        maritime_aux19_app,
        name="maritime-aux19",
        help="MaritimeAux19 — Exhaust Valve, Cargo Pumproom, Hull Stress & Helideck JP-5 (Phases 535-538)",
    )
    root.add_typer(
        maritime_aux19_app,
        name="phukienhanghai19",
        help="PhuKienHangHai19 — Alias for Maritime Safety Auxiliary Engine (Phases 535-538)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch20_command import (  # noqa: E402
        maritime_aux20_app,
    )
    root.add_typer(
        maritime_aux20_app,
        name="maritime-aux20",
        help="MaritimeAux20 — Stuffing Box, BESS Thermal, Dry Powder & Common-Rail Booster (Phases 539-542)",
    )
    root.add_typer(
        maritime_aux20_app,
        name="phukienhanghai20",
        help="PhuKienHangHai20 — Alias for Maritime Safety Auxiliary Engine (Phases 539-542)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch21_command import (  # noqa: E402
        maritime_aux21_app,
    )
    root.add_typer(
        maritime_aux21_app,
        name="maritime-aux21",
        help="MaritimeAux21 — SCR Urea Slip, Cargo P/V Breaker, Azipod Propulsor & LNG ESD/ERC (Phases 543-546)",
    )
    root.add_typer(
        maritime_aux21_app,
        name="phukienhanghai21",
        help="PhuKienHangHai21 — Alias for Maritime Safety Auxiliary Engine (Phases 543-546)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch22_command import (  # noqa: E402
        maritime_aux22_app,
    )
    root.add_typer(
        maritime_aux22_app,
        name="maritime-aux22",
        help="MaritimeAux22 — FGSS Glycol GVU, CAC Condensate, High-Exp Foam & DP Bus-Tie (Phases 547-550)",
    )
    root.add_typer(
        maritime_aux22_app,
        name="phukienhanghai22",
        help="PhuKienHangHai22 — Alias for Maritime Safety Auxiliary Engine (Phases 547-550)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch23_command import (  # noqa: E402
        maritime_aux23_app,
    )
    root.add_typer(
        maritime_aux23_app,
        name="maritime-aux23",
        help="MaritimeAux23 — CPP Servo, Cargo Reliq GCU, Local Mist FWLA & Fin Stabilizer (Phases 551-554)",
    )
    root.add_typer(
        maritime_aux23_app,
        name="phukienhanghai23",
        help="PhuKienHangHai23 — Alias for Maritime Safety Auxiliary Engine (Phases 551-554)",
    )
    from src.cli.commands.maritime_safety_auxiliary_batch24_command import (  # noqa: E402
        maritime_aux24_app,
    )
    root.add_typer(
        maritime_aux24_app,
        name="maritime-aux24",
        help="MaritimeAux24 — Hull ALS, PTO Shaft Gen, Galley Hood & Ro-Ro Shell Door (Phases 555-558)",
    )
    root.add_typer(
        maritime_aux24_app,
        name="phukienhanghai24",
        help="PhuKienHangHai24 — Alias for Maritime Safety Auxiliary Engine (Phases 555-558)",
    )
    root.add_typer(
        isps_app,
        name="isps",
        help="ISPS — ISPS Code Port Security & DoS Engine (Phase 299)",
    )
    root.add_typer(
        isps_app,
        name="anninhcang",
        help="AnNinhCang — Alias for ISPS Code Security Engine",
    )
    root.add_typer(
        hazmat_app,
        name="hazmat",
        help="Hazmat — Hazmat Waste Port Clearance Engine (Phase 300)",
    )
    root.add_typer(
        hazmat_app,
        name="racthainguyhai",
        help="RacThaiNguyHai — Alias for Hazmat Waste Engine",
    )
    root.add_typer(
        oog_stevedore_app,
        name="oogstevedore",
        help="OOGStevedore — OOG Stevedoring & Overtime Tariffs Engine (Phase 301)",
    )
    root.add_typer(
        oog_stevedore_app,
        name="bocdoquakho",
        help="BocDoQuaKho — Alias for OOG Stevedoring Tariffs Engine",
    )
    root.add_typer(
        anchorage_app,
        name="anchorage",
        help="Anchorage — Anchorage Zone Capacity Booking Engine (Phase 302)",
    )
    root.add_typer(
        anchorage_app,
        name="bookphaoneo",
        help="BookPhaoNeo — Alias for Anchorage Capacity Booking Engine",
    )
    from src.cli.commands.opencore_saas_restructuring_command import (  # noqa: E402
        opencore_saas_app,
    )
    root.add_typer(
        opencore_saas_app,
        name="opencore-saas",
        help="OpenCoreSaaS — 25-Step Open-Core Public GitHub + SaaS Monetization (Phases 559-560)",
    )
    root.add_typer(
        opencore_saas_app,
        name="ma-nguon-mo-saas",
        help="MaNguonMoSaaS — Alias for 25-Step Open-Core Public GitHub + SaaS Monetization",
    )

