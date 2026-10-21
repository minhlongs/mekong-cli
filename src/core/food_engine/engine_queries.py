# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mixin class providing query methods for FoodEngine."""

from __future__ import annotations

import typing

from .queries import (
    list_declarations_query,
    list_facilities_query,
    list_haccp_audits_query,
    list_inspections_query,
    list_recalls_query,
)
from .status import get_food_status

if typing.TYPE_CHECKING:
    import pathlib


class FoodQueryMixin:
    """Mixin for FoodEngine query and status methods."""

    db_path: pathlib.Path

    def list_declarations(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered or published food product declarations."""
        return list_declarations_query(self.db_path, limit=limit)

    def list_facilities(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List food facilities and their safety certification/exemption status."""
        return list_facilities_query(self.db_path, limit=limit)

    def list_inspections(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List state inspections of imported food shipments."""
        return list_inspections_query(self.db_path, limit=limit)

    def list_recalls(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List food product recall orders."""
        return list_recalls_query(self.db_path, limit=limit)

    def list_haccp_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List HACCP system audits."""
        return list_haccp_audits_query(self.db_path, limit=limit)

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate food safety compliance telemetry across all registered entities."""
        return get_food_status(self.db_path)


__all__ = ["FoodQueryMixin"]
