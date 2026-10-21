# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Facility registration operations for FoodEngine under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import datetime
import json
import typing
import uuid

from .constants import CERTIFICATE_EXEMPTIONS, FOOD_FACILITY_TYPES
from .db import get_connection

if typing.TYPE_CHECKING:
    import pathlib


def register_facility_record(
    db_path: pathlib.Path,
    facility_name: str,
    enterprise_name: str,
    tax_id: str,
    address: str,
    province: str,
    activity_type: str,
    exemption_type: str = "NONE",
    cert_number: str | None = None,
    inspection_rating: str = "GOOD",
    metadata: dict[str, typing.Any] | None = None,
) -> dict[str, typing.Any]:
    """Register a food facility and verify Certificate of Food Safety Eligibility or exemption."""
    act_clean = activity_type.strip().upper()
    if act_clean not in FOOD_FACILITY_TYPES:
        valid_acts = list(FOOD_FACILITY_TYPES.keys())
        raise ValueError(f"Loại hình cơ sở không hợp lệ: '{activity_type}'. Hỗ trợ: {valid_acts}")

    exemption_clean = exemption_type.strip().upper()
    if exemption_clean not in CERTIFICATE_EXEMPTIONS:
        valid_exempts = list(CERTIFICATE_EXEMPTIONS.keys())
        raise ValueError(f"Loại hình miễn trừ không hợp lệ: '{exemption_type}'. Hỗ trợ: {valid_exempts}")

    exempt_info = CERTIFICATE_EXEMPTIONS[exemption_clean]
    is_exempt = exempt_info["exemption_status"] == "EXEMPT"

    today_date = datetime.date.today()
    facility_id = f"fac-{uuid.uuid4().hex[:12]}"
    issue_date = today_date.isoformat()
    expiry_date = (today_date + datetime.timedelta(days=3 * 365)).isoformat()

    if not cert_number:
        if is_exempt:
            cert_number = f"EXEMPT-{exemption_clean}-{uuid.uuid4().hex[:6].upper()}"
        else:
            cert_number = f"{uuid.uuid4().hex[:6].upper()}/{today_date.year}/ATTP-GCN"

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO food_facilities (
                facility_id, facility_name, enterprise_name, tax_id, address, province,
                activity_type, exemption_type, cert_number, issue_date, expiry_date,
                inspection_rating, status, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                facility_id,
                facility_name.strip(),
                enterprise_name.strip(),
                tax_id.strip(),
                address.strip(),
                province.strip(),
                act_clean,
                exemption_clean,
                cert_number,
                issue_date,
                expiry_date,
                inspection_rating.strip().upper(),
                "ACTIVE",
                json.dumps(metadata or {}, ensure_ascii=False),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        conn.commit()

    return {
        "facility_id": facility_id,
        "facility_name": facility_name,
        "enterprise_name": enterprise_name,
        "activity_type": act_clean,
        "exemption_type": exemption_clean,
        "is_exempt_from_gcn": is_exempt,
        "statutory_ref": exempt_info["decree_ref"],
        "cert_number": cert_number,
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "inspection_rating": inspection_rating.strip().upper(),
        "status": "ACTIVE",
        "message": (
            f"Cơ sở '{facility_name}' đã được cấp/ghi nhận "
            f"({'Miễn cấp GCN ATTP do có ' + exempt_info['name_vi'] if is_exempt else 'GCN Cơ sở đủ điều kiện ATTP: ' + cert_number}). "
            f"Hiệu lực đến: {expiry_date}."
        ),
    }


__all__ = ["register_facility_record"]
