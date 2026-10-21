# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Inland Waterway Transport, River Ports & Navigation (Phase 74)."""

from __future__ import annotations

from src.cli.commands._waterway_infra_cmds import (
    channel_cmd,
    console,
    port_cmd,
    waterway_app,
    waterway_main,
)
from src.cli.commands._waterway_ops_cmds import (
    captain_cmd,
    freight_cmd,
)
from src.cli.commands._waterway_query_cmds import (
    list_cmd,
    status_cmd,
)
from src.cli.commands._waterway_vessel_cmds import (
    clearance_cmd,
    vessel_cmd,
)

__all__ = [
    "captain_cmd",
    "channel_cmd",
    "clearance_cmd",
    "console",
    "freight_cmd",
    "list_cmd",
    "port_cmd",
    "status_cmd",
    "vessel_cmd",
    "waterway_app",
    "waterway_main",
]
