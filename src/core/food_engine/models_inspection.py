# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""State inspection data model under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import datetime
import typing


class FoodInspection:
    """Represents a state inspection for imported food shipments."""

    def __init__(
        self,
        inspection_id: str,
        shipment_id: str,
        importer_name: str,
        product_name: str,
        origin_country: str,
        quantity_kg: float,
        inspection_mode: str,
        sampling_performed: bool,
        test_results: dict[str, typing.Any],
        result_status: str,
        inspector_agency: str,
        inspection_date: str | None = None,
        clearance_status: str = "CLEARED",
        notes: str = "",
        created_at: str | None = None,
    ) -> None:
        self.inspection_id = inspection_id
        self.shipment_id = shipment_id
        self.importer_name = importer_name
        self.product_name = product_name
        self.origin_country = origin_country
        self.quantity_kg = quantity_kg
        self.inspection_mode = inspection_mode
        self.sampling_performed = sampling_performed
        self.test_results = test_results
        self.result_status = result_status
        self.inspector_agency = inspector_agency
        self.inspection_date = inspection_date or datetime.date.today().isoformat()
        self.clearance_status = clearance_status
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "inspection_id": self.inspection_id,
            "shipment_id": self.shipment_id,
            "importer_name": self.importer_name,
            "product_name": self.product_name,
            "origin_country": self.origin_country,
            "quantity_kg": self.quantity_kg,
            "inspection_mode": self.inspection_mode,
            "sampling_performed": self.sampling_performed,
            "test_results": self.test_results,
            "result_status": self.result_status,
            "inspector_agency": self.inspector_agency,
            "inspection_date": self.inspection_date,
            "clearance_status": self.clearance_status,
            "notes": self.notes,
            "created_at": self.created_at,
        }


__all__ = ["FoodInspection"]
