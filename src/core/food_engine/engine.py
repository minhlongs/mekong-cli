# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Food safety compliance engine class definition under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import sqlite3
import typing

from .db import get_connection, get_db_path, init_db
from .engine_queries import FoodQueryMixin
from .operations_audit import audit_haccp_record
from .operations_declaration import declare_product_record
from .operations_facility import register_facility_record
from .operations_inspection import inspect_imported_food_record
from .operations_recall import initiate_recall_record, update_recall_recovery_record

if typing.TYPE_CHECKING:
    import pathlib


class FoodEngine(FoodQueryMixin):
    """Core autonomous manager for Vietnamese food safety, declarations & inspections."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        self.db_path = get_db_path(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def _init_db(self) -> None:
        init_db(self.db_path)

    def declare_product(
        self, product_name: str, product_category: str, enterprise_name: str, tax_id: str,
        manufacturer_name: str, origin_country: str, ingredients: list[str], shelf_life_months: int,
        lab_test_cert: str, gmp_cert_number: str | None = None, custom_number: str | None = None,
        metadata: dict[str, typing.Any] | None = None,
    ) -> dict[str, typing.Any]:
        """Declare or register a food product according to Decree 15/2018/NĐ-CP."""
        return declare_product_record(
            db_path=self.db_path, product_name=product_name, product_category=product_category,
            enterprise_name=enterprise_name, tax_id=tax_id, manufacturer_name=manufacturer_name,
            origin_country=origin_country, ingredients=ingredients, shelf_life_months=shelf_life_months,
            lab_test_cert=lab_test_cert, gmp_cert_number=gmp_cert_number,
            custom_number=custom_number, metadata=metadata,
        )

    def register_facility(
        self, facility_name: str, enterprise_name: str, tax_id: str, address: str,
        province: str, activity_type: str, exemption_type: str = "NONE",
        cert_number: str | None = None, inspection_rating: str = "GOOD",
        metadata: dict[str, typing.Any] | None = None,
    ) -> dict[str, typing.Any]:
        """Register a food facility and verify Certificate of Food Safety Eligibility."""
        return register_facility_record(
            db_path=self.db_path, facility_name=facility_name, enterprise_name=enterprise_name,
            tax_id=tax_id, address=address, province=province, activity_type=activity_type,
            exemption_type=exemption_type, cert_number=cert_number,
            inspection_rating=inspection_rating, metadata=metadata,
        )

    def inspect_imported_food(
        self, shipment_id: str, importer_name: str, product_name: str, origin_country: str,
        quantity_kg: float, inspection_mode: str = "NORMAL",
        lab_test_results: dict[str, typing.Any] | None = None,
        inspector_agency: str = "Cục Kiểm tra An toàn Thực phẩm Nhập khẩu", notes: str = "",
    ) -> dict[str, typing.Any]:
        """Perform statutory state food safety inspection for imported shipments."""
        return inspect_imported_food_record(
            db_path=self.db_path, shipment_id=shipment_id, importer_name=importer_name,
            product_name=product_name, origin_country=origin_country, quantity_kg=quantity_kg,
            inspection_mode=inspection_mode, lab_test_results=lab_test_results,
            inspector_agency=inspector_agency, notes=notes,
        )

    def initiate_recall(
        self, product_name: str, batch_number: str, recall_class: str, reason: str,
        hazard_description: str, affected_quantity: float, recovered_quantity: float = 0.0,
        recall_scope: str = "NATIONWIDE", disposal_method: str = "DESTROY", notes: str = "",
    ) -> dict[str, typing.Any]:
        """Issue an official food recall order with statutory deadlines."""
        return initiate_recall_record(
            db_path=self.db_path, product_name=product_name, batch_number=batch_number,
            recall_class=recall_class, reason=reason, hazard_description=hazard_description,
            affected_quantity=affected_quantity, recovered_quantity=recovered_quantity,
            recall_scope=recall_scope, disposal_method=disposal_method, notes=notes,
        )

    def update_recall_recovery(
        self,
        recall_id_or_number: str,
        additional_recovered_qty: float,
    ) -> dict[str, typing.Any]:
        """Update recovered quantity and check completion status for an active recall."""
        return update_recall_recovery_record(
            db_path=self.db_path,
            recall_id_or_number=recall_id_or_number,
            additional_recovered_qty=additional_recovered_qty,
        )

    def audit_haccp_system(
        self,
        facility_id_or_name: str,
        auditor_name: str,
        principles_scores: dict[str, float],
        total_ccps: int,
        critical_non_conformities: int = 0,
        major_non_conformities: int = 0,
        minor_non_conformities: int = 0,
        recommendations: list[str] | None = None,
    ) -> dict[str, typing.Any]:
        """Audit a food facility against the 7 HACCP Principles & Codex Alimentarius."""
        return audit_haccp_record(
            db_path=self.db_path,
            facility_id_or_name=facility_id_or_name,
            auditor_name=auditor_name,
            principles_scores=principles_scores,
            total_ccps=total_ccps,
            critical_non_conformities=critical_non_conformities,
            major_non_conformities=major_non_conformities,
            minor_non_conformities=minor_non_conformities,
            recommendations=recommendations,
        )


__all__ = ["FoodEngine"]
