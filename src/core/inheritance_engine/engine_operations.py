# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mutating operations mixin for InheritanceEngine."""

from __future__ import annotations

import sqlite3
import typing

from .enums import SuccessionType
from .operations_agreement import execute_division_agreement_record
from .operations_assets import add_estate_asset_record, add_estate_obligation_record
from .operations_estate import create_estate_record, get_estate_record
from .operations_heir import record_disclaimer_record, register_heir_record
from .operations_will import register_will_record


class InheritanceOperationsMixin:
    """Mixin providing mutating methods for InheritanceEngine."""

    def _get_connection(self) -> sqlite3.Connection:
        raise NotImplementedError

    def create_estate(
        self, decedent_name: str, decedent_id_number: str, decedent_dob: str, date_of_death: str,
        place_of_death: str = "Hà Nội, Việt Nam", last_residence: str = "Hà Nội, Việt Nam",
        place_of_opening: str | None = None, administrator_name: str | None = None,
        administrator_contact: str | None = None, succession_type: str = SuccessionType.INTESTATE.value,
        dedicated_worship_amount: float = 0.0, dedicated_worship_description: str | None = None,
        notes: str | None = None, estate_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Open a new succession estate file under Articles 609, 611, 612 Civil Code 2015."""
        with self._get_connection() as conn:
            eid = create_estate_record(
                conn, decedent_name, decedent_id_number, decedent_dob, date_of_death,
                place_of_death, last_residence, place_of_opening, administrator_name,
                administrator_contact, succession_type, dedicated_worship_amount,
                dedicated_worship_description, notes, estate_id,
            )
            return get_estate_record(conn, eid)

    def add_estate_asset(
        self, estate_id: str, asset_name: str, category: str, estimated_value: float,
        is_sole_ownership: bool = True, ownership_share: float = 1.0,
        legal_document_ref: str | None = None, location: str | None = None,
        is_for_worship: bool = False, asset_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Add asset to estate inventory with ownership share calculation under Art. 612."""
        with self._get_connection() as conn:
            return add_estate_asset_record(
                conn, estate_id, asset_name, category, estimated_value,
                is_sole_ownership, ownership_share, legal_document_ref,
                location, is_for_worship, asset_id,
            )

    def add_estate_obligation(
        self,
        estate_id: str,
        creditor_name: str,
        obligation_name: str,
        priority: str,
        amount: float,
        legal_basis: str | None = None,
        obligation_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Add debt or liability with statutory payment priority ranking under Art. 658."""
        with self._get_connection() as conn:
            return add_estate_obligation_record(
                conn, estate_id, creditor_name, obligation_name, priority, amount, legal_basis, obligation_id,
            )

    def register_will(
        self,
        estate_id: str,
        will_form: str,
        date_created: str,
        place_created: str,
        notary_office_or_ubnd: str | None = None,
        notary_number: str | None = None,
        notary_date: str | None = None,
        witness_1_name: str | None = None,
        witness_1_id: str | None = None,
        witness_2_name: str | None = None,
        witness_2_id: str | None = None,
        oral_will_recorded_date: str | None = None,
        oral_will_certified_date: str | None = None,
        executor_name: str | None = None,
        worship_estate_assigned: float = 0.0,
        worship_manager_name: str | None = None,
        contents_summary: str | None = None,
        will_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Register and audit legality of will under Articles 627-640 Civil Code 2015."""
        with self._get_connection() as conn:
            return register_will_record(
                conn, estate_id, will_form, date_created, place_created,
                notary_office_or_ubnd, notary_number, notary_date,
                witness_1_name, witness_1_id, witness_2_name, witness_2_id,
                oral_will_recorded_date, oral_will_certified_date, executor_name,
                worship_estate_assigned, worship_manager_name, contents_summary, will_id,
            )

    def register_heir(
        self,
        estate_id: str,
        full_name: str,
        id_number: str,
        dob: str,
        relationship: str,
        heir_rank: str | None = None,
        is_alive_at_opening: bool = True,
        is_conceived_before_opening: bool = False,
        is_minor_or_disabled: bool = False,
        is_disqualified_art621: bool = False,
        is_forgiven_in_will: bool = False,
        is_substitutional_art652: bool = False,
        substituting_for_name: str | None = None,
        testamentary_share_percent: float = 0.0,
        testamentary_fixed_amount: float = 0.0,
        notes: str | None = None,
        heir_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Register heir with kinship mapping, forced heir check (Art. 644), or substitution (Art. 652)."""
        with self._get_connection() as conn:
            return register_heir_record(
                conn, estate_id, full_name, id_number, dob, relationship, heir_rank,
                is_alive_at_opening, is_conceived_before_opening, is_minor_or_disabled,
                is_disqualified_art621, is_forgiven_in_will, is_substitutional_art652,
                substituting_for_name, testamentary_share_percent, testamentary_fixed_amount,
                notes, heir_id,
            )

    def record_disclaimer(
        self,
        estate_id: str,
        heir_id: str,
        declaration_date: str,
        notary_or_ubnd_office: str,
        notary_document_number: str,
        reason: str | None = None,
        is_for_debt_evasion: bool = False,
        disclaimer_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Record renunciation of inheritance under Art. 620 Civil Code 2015."""
        with self._get_connection() as conn:
            return record_disclaimer_record(
                conn, estate_id, heir_id, declaration_date, notary_or_ubnd_office,
                notary_document_number, reason, is_for_debt_evasion, disclaimer_id,
            )

    def execute_division_agreement(
        self,
        estate_id: str,
        procedure_type: str,
        notary_office: str,
        division_date: str | None = None,
        public_posting_ubnd: str | None = None,
        public_posting_start_date: str | None = None,
        notary_doc_ref: str | None = None,
        agreement_id: str | None = None,
    ) -> dict[str, typing.Any]:
        """Formulate Notarized Estate Division Agreement under Articles 57, 58 Law on Notarization 2014."""
        with self._get_connection() as conn:
            return execute_division_agreement_record(
                conn, estate_id, procedure_type, notary_office, division_date,
                public_posting_ubnd, public_posting_start_date, notary_doc_ref, agreement_id,
            )


__all__ = ["InheritanceOperationsMixin"]
