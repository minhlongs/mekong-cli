# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unified BankingEngine class composing statutory Vietnamese banking operations."""

from __future__ import annotations

import pathlib
import sqlite3

from src.core.banking_engine.basel_debt_liquidity_ops import (
    BaselDebtLiquidityOpsMixin,
)
from src.core.banking_engine.licensing_credit_ops import LicensingCreditOpsMixin
from src.core.banking_engine.query_telemetry_ops import QueryTelemetryOpsMixin
from src.core.banking_engine.schema import (
    get_connection,
    init_database,
    resolve_db_path,
)


class BankingEngine(
    LicensingCreditOpsMixin,
    BaselDebtLiquidityOpsMixin,
    QueryTelemetryOpsMixin,
):
    """Autonomous Vietnamese Commercial Banking, Credit & Basel II Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        self.db_path = resolve_db_path(db_path)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def _init_database(self) -> None:
        init_database(self.db_path)


__all__ = ["BankingEngine"]
