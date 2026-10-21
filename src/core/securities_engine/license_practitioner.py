# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Professional securities practitioner licensing."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .constants import PRACTITIONER_CERT_TYPES


def issue_practitioner_license_record(
    conn: sqlite3.Connection,
    practitioner_name: str,
    id_card_or_passport: str,
    license_type: str = "BROKERAGE",
    firm_affiliation: str = "Công ty Cổ phần Chứng khoán Mekong",
) -> dict[str, typing.Any]:
    """Issue an official professional securities practitioner license."""
    type_clean = license_type.strip().upper()
    if type_clean not in PRACTITIONER_CERT_TYPES:
        valid_types = list(PRACTITIONER_CERT_TYPES.keys())
        raise ValueError(f"Loại chứng chỉ hành nghề không hợp lệ: '{license_type}'. Hỗ trợ: {valid_types}")

    type_info = PRACTITIONER_CERT_TYPES[type_clean]
    today_date = datetime.date.today()
    issue_date = today_date.isoformat()
    expiry_date = (today_date + datetime.timedelta(days=5 * 365)).isoformat()

    license_id = f"cchnd-{uuid.uuid4().hex[:12]}"
    ssc_license_number = f"CCHN-UBCK-{type_clean[:4]}-{today_date.year}-{uuid.uuid4().hex[:4].upper()}"

    conn.execute(
        """
        INSERT INTO practitioner_licenses (
            license_id, practitioner_name, id_card_or_passport, license_type,
            ssc_license_number, issue_date, expiry_date, firm_affiliation,
            compliance_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            license_id,
            practitioner_name.strip(),
            id_card_or_passport.strip(),
            type_clean,
            ssc_license_number,
            issue_date,
            expiry_date,
            firm_affiliation.strip(),
            "ACTIVE",
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
        ),
    )
    conn.commit()

    return {
        "license_id": license_id,
        "practitioner_name": practitioner_name,
        "id_card_or_passport": id_card_or_passport,
        "license_type": type_clean,
        "license_name_vi": type_info["name_vi"],
        "ssc_license_number": ssc_license_number,
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "firm_affiliation": firm_affiliation,
        "compliance_status": "ACTIVE",
        "message": (
            f"Đã cấp Chứng chỉ hành nghề {type_info['name_vi']} số hiệu {ssc_license_number} "
            f"cho ông/bà {practitioner_name} trực thuộc {firm_affiliation}. Hiệu lực đến: {expiry_date}."
        ),
    }


__all__ = ["issue_practitioner_license_record"]
