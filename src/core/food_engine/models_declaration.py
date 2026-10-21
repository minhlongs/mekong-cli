# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Food safety data models under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import datetime
import typing

from .models_inspection import FoodInspection


class FoodDeclaration:
    """Represents a product declaration or registration under Decree 15/2018/NĐ-CP."""

    def __init__(
        self,
        declaration_id: str,
        declaration_number: str,
        product_name: str,
        product_category: str,
        declaration_path: str,
        enterprise_name: str,
        tax_id: str,
        manufacturer_name: str,
        origin_country: str,
        ingredients: list[str],
        shelf_life_months: int,
        lab_test_cert: str,
        gmp_cert_number: str | None = None,
        status: str = "PUBLISHED",
        submission_date: str | None = None,
        approval_date: str | None = None,
        expiry_date: str | None = None,
        metadata: dict[str, typing.Any] | None = None,
        created_at: str | None = None,
    ) -> None:
        self.declaration_id = declaration_id
        self.declaration_number = declaration_number
        self.product_name = product_name
        self.product_category = product_category
        self.declaration_path = declaration_path
        self.enterprise_name = enterprise_name
        self.tax_id = tax_id
        self.manufacturer_name = manufacturer_name
        self.origin_country = origin_country
        self.ingredients = ingredients
        self.shelf_life_months = shelf_life_months
        self.lab_test_cert = lab_test_cert
        self.gmp_cert_number = gmp_cert_number
        self.status = status
        self.submission_date = submission_date or datetime.date.today().isoformat()
        self.approval_date = approval_date or datetime.date.today().isoformat()
        self.expiry_date = expiry_date
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "declaration_id": self.declaration_id,
            "declaration_number": self.declaration_number,
            "product_name": self.product_name,
            "product_category": self.product_category,
            "declaration_path": self.declaration_path,
            "enterprise_name": self.enterprise_name,
            "tax_id": self.tax_id,
            "manufacturer_name": self.manufacturer_name,
            "origin_country": self.origin_country,
            "ingredients": self.ingredients,
            "shelf_life_months": self.shelf_life_months,
            "lab_test_cert": self.lab_test_cert,
            "gmp_cert_number": self.gmp_cert_number,
            "status": self.status,
            "submission_date": self.submission_date,
            "approval_date": self.approval_date,
            "expiry_date": self.expiry_date,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class FoodFacility:
    """Represents a food production, processing, or catering facility."""

    def __init__(
        self,
        facility_id: str,
        facility_name: str,
        enterprise_name: str,
        tax_id: str,
        address: str,
        province: str,
        activity_type: str,
        exemption_type: str = "NONE",
        cert_number: str | None = None,
        issue_date: str | None = None,
        expiry_date: str | None = None,
        inspection_rating: str = "GOOD",
        status: str = "ACTIVE",
        metadata: dict[str, typing.Any] | None = None,
        created_at: str | None = None,
    ) -> None:
        self.facility_id = facility_id
        self.facility_name = facility_name
        self.enterprise_name = enterprise_name
        self.tax_id = tax_id
        self.address = address
        self.province = province
        self.activity_type = activity_type
        self.exemption_type = exemption_type
        self.cert_number = cert_number
        self.issue_date = issue_date or datetime.date.today().isoformat()
        self.expiry_date = expiry_date
        self.inspection_rating = inspection_rating
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "enterprise_name": self.enterprise_name,
            "tax_id": self.tax_id,
            "address": self.address,
            "province": self.province,
            "activity_type": self.activity_type,
            "exemption_type": self.exemption_type,
            "cert_number": self.cert_number,
            "issue_date": self.issue_date,
            "expiry_date": self.expiry_date,
            "inspection_rating": self.inspection_rating,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


__all__ = [
    "FoodDeclaration",
    "FoodFacility",
    "FoodInspection",
]
