"""Domain command group dispatcher for Mekong CLI."""

from __future__ import annotations

import typer

from src.cli._app_setup.groups_01 import register_groups_01
from src.cli._app_setup.groups_02 import register_groups_02
from src.cli._app_setup.groups_03 import register_groups_03
from src.cli._app_setup.groups_04 import register_groups_04
from src.cli._app_setup.groups_05 import register_groups_05
from src.cli._app_setup.groups_06 import register_groups_06
from src.cli._app_setup.groups_07 import register_groups_07
from src.cli._app_setup.groups_08 import register_groups_08
from src.cli._app_setup.groups_09 import register_groups_09
from src.cli._app_setup.groups_10 import register_groups_10
from src.cli._app_setup.groups_11 import register_groups_11
from src.cli._app_setup.groups_12 import register_groups_12
from src.cli._app_setup.groups_13 import register_groups_13
from src.cli._app_setup.groups_14 import register_groups_14
from src.cli._app_setup.groups_15 import register_groups_15
from src.cli._app_setup.groups_16 import register_groups_16
from src.cli._app_setup.groups_17 import register_groups_17
from src.cli._app_setup.groups_18 import register_groups_18
from src.cli._app_setup.groups_19 import register_groups_19
from src.cli._app_setup.groups_20 import register_groups_20
from src.cli._app_setup.groups_21 import register_groups_21
from src.cli._app_setup.groups_22 import register_groups_22
from src.cli._app_setup.groups_23 import register_groups_23
from src.cli._app_setup.groups_24 import register_groups_24


def register_domain_groups(root: typer.Typer) -> None:
    """Register all 24 domain command group batches onto root."""
    for register_fn in (
        register_groups_01,
        register_groups_02,
        register_groups_03,
        register_groups_04,
        register_groups_05,
        register_groups_06,
        register_groups_07,
        register_groups_08,
        register_groups_09,
        register_groups_10,
        register_groups_11,
        register_groups_12,
        register_groups_13,
        register_groups_14,
        register_groups_15,
        register_groups_16,
        register_groups_17,
        register_groups_18,
        register_groups_19,
        register_groups_20,
        register_groups_21,
        register_groups_22,
        register_groups_23,
        register_groups_24,
    ):
        register_fn(root)
