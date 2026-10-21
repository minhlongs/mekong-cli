# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer wrappers for the Vietnam business-funnel commands.

Reaches the existing library code in ``src/commands/zalo_oa.py``,
``src/commands/thue_dnvn.py``, ``src/commands/ke_toan.py``, and
``src/commands/sophia_video.py`` — which already have unit tests — and exposes
them as Typer sub-apps so the ``mekong`` binary can dispatch::

    mekong zalo-oa   send|broadcast|followers|caption|post
    mekong thue       tncn|tndn|gtgt
    mekong ke-toan    create|xml|journal|summary
    mekong tools video render|status|list|voices|avatars|templates|cost
"""

from __future__ import annotations

from src.cli.funnel_commands.bhxh_app import (
    bhxh_app,
    bhxh_calc,
    bhxh_declaration,
    bhxh_employees,
    bhxh_main,
    bhxh_status,
)
from src.cli.funnel_commands.ke_toan_app import (
    create_invoice,
    ke_toan_app,
    ke_toan_create,
    ke_toan_journal,
    ke_toan_list,
    ke_toan_main,
    ke_toan_status,
    ke_toan_summary,
    ke_toan_xml,
)
from src.cli.funnel_commands.thue_app import (
    calculate_gtgt,
    calculate_tncn,
    calculate_tndn,
    thue_app,
    thue_gtgt,
    thue_list,
    thue_main,
    thue_status,
    thue_tncn,
    thue_tndn,
)
from src.cli.funnel_commands.vietqr_app import (
    vietqr_app,
    vietqr_banks,
    vietqr_generate,
    vietqr_main,
    vietqr_record,
    vietqr_status,
    vietqr_transactions,
)
from src.cli.funnel_commands.zalo_app import (
    _zalo_client,
    zalo_app,
    zalo_broadcast,
    zalo_caption,
    zalo_followers,
    zalo_main,
    zalo_post,
    zalo_send,
    zalo_status,
)
from src.commands.sophia_video import app as sophia_app

__all__ = [
    "_zalo_client",
    "bhxh_app",
    "bhxh_calc",
    "bhxh_declaration",
    "bhxh_employees",
    "bhxh_main",
    "bhxh_status",
    "calculate_gtgt",
    "calculate_tncn",
    "calculate_tndn",
    "create_invoice",
    "ke_toan_app",
    "ke_toan_create",
    "ke_toan_journal",
    "ke_toan_list",
    "ke_toan_main",
    "ke_toan_status",
    "ke_toan_summary",
    "ke_toan_xml",
    "sophia_app",
    "thue_app",
    "thue_gtgt",
    "thue_list",
    "thue_main",
    "thue_status",
    "thue_tncn",
    "thue_tndn",
    "vietqr_app",
    "vietqr_banks",
    "vietqr_generate",
    "vietqr_main",
    "vietqr_record",
    "vietqr_status",
    "vietqr_transactions",
    "zalo_app",
    "zalo_broadcast",
    "zalo_caption",
    "zalo_followers",
    "zalo_main",
    "zalo_post",
    "zalo_send",
    "zalo_status",
]
