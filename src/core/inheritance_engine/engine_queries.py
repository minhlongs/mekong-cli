# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Query and audit mixin for InheritanceEngine."""

from __future__ import annotations

import sqlite3
import typing

from .audit_dossier import (
    audit_compliance_record,
    check_statute_of_limitations_record,
    generate_inheritance_dossier_record,
)
from .calculator import calculate_statutory_shares_record
from .operations_estate import get_estate_record, list_estates_record


class InheritanceQueryMixin:
    """Mixin providing query, calculation, and audit methods for InheritanceEngine."""

    def _get_connection(self) -> sqlite3.Connection:
        raise NotImplementedError

    def get_estate(self, estate_id: str) -> dict[str, typing.Any]:
        """Get full details of an estate including assets, obligations, will, heirs."""
        with self._get_connection() as conn:
            return get_estate_record(conn, estate_id)

    def list_estates(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List summary of all estate files."""
        with self._get_connection() as conn:
            return list_estates_record(conn, limit=limit)

    def calculate_statutory_shares(self, estate_id: str) -> dict[str, typing.Any]:
        """Precise mathematical algorithm for calculating inheritance shares under Civil Code 2015."""
        with self._get_connection() as conn:
            estate = get_estate_record(conn, estate_id)
            return calculate_statutory_shares_record(estate)

    def check_statute_of_limitations(
        self,
        date_of_death: str,
        current_date: str | None = None,
    ) -> dict[str, typing.Any]:
        """Check inheritance statute of limitations under Art. 623 Civil Code 2015."""
        return check_statute_of_limitations_record(date_of_death, current_date)

    def generate_inheritance_dossier(self, estate_id: str) -> dict[str, typing.Any]:
        """Generate comprehensive bilingual legal dossier."""
        with self._get_connection() as conn:
            return generate_inheritance_dossier_record(conn, estate_id)

    def audit_compliance(self, estate_id: str) -> dict[str, typing.Any]:
        """Audit estate file against statutory compliance rules of Civil Code 2015 & Law on Notarization 2014."""
        with self._get_connection() as conn:
            return audit_compliance_record(conn, estate_id)


__all__ = ["InheritanceQueryMixin"]
