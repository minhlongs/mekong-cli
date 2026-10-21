# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""State food inspection operations under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import datetime
import json
import typing
import uuid

from .constants import IMPORT_INSPECTION_MODES
from .db import get_connection

if typing.TYPE_CHECKING:
    import pathlib


def inspect_imported_food_record(
    db_path: pathlib.Path,
    shipment_id: str,
    importer_name: str,
    product_name: str,
    origin_country: str,
    quantity_kg: float,
    inspection_mode: str = "NORMAL",
    lab_test_results: dict[str, typing.Any] | None = None,
    inspector_agency: str = "Cục Kiểm tra An toàn Thực phẩm Nhập khẩu",
    notes: str = "",
) -> dict[str, typing.Any]:
    """Perform statutory state food safety inspection for imported shipments."""
    mode_clean = inspection_mode.strip().upper()
    if mode_clean not in IMPORT_INSPECTION_MODES:
        valid_modes = list(IMPORT_INSPECTION_MODES.keys())
        raise ValueError(f"Phương thức kiểm tra nhập khẩu không hợp lệ: '{inspection_mode}'. Hỗ trợ: {valid_modes}")

    mode_info = IMPORT_INSPECTION_MODES[mode_clean]
    sampling_mandatory = mode_info["sampling_mandatory"]

    test_results = lab_test_results or {}
    sampling_performed = bool(test_results) or sampling_mandatory

    result_status = "PASS"
    clearance_status = "CLEARED"

    if test_results:
        for _test_name, test_val in test_results.items():
            if isinstance(test_val, dict):
                status_field = str(test_val.get("status", "")).upper()
                if status_field in ["FAIL", "REJECTED", "EXCEEDED", "POSITIVE"]:
                    result_status = "FAIL"
                    clearance_status = "DETAINED"
                    break
            elif isinstance(test_val, str) and test_val.upper() in ["FAIL", "POSITIVE", "UNSAFE"]:
                result_status = "FAIL"
                clearance_status = "DETAINED"
                break

    if mode_clean == "TIGHTENED" and not test_results:
        result_status = "CONDITIONAL"
        clearance_status = "DETAINED"
        notes = (notes + " [Đang chờ lấy mẫu và kết quả kiểm nghiệm phòng thí nghiệm]").strip()

    inspection_id = f"insp-{uuid.uuid4().hex[:12]}"
    today_date = datetime.date.today().isoformat()

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO food_inspections (
                inspection_id, shipment_id, importer_name, product_name, origin_country,
                quantity_kg, inspection_mode, sampling_performed, test_results_json,
                result_status, inspector_agency, inspection_date, clearance_status,
                notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inspection_id,
                shipment_id.strip(),
                importer_name.strip(),
                product_name.strip(),
                origin_country.strip(),
                quantity_kg,
                mode_clean,
                1 if sampling_performed else 0,
                json.dumps(test_results, ensure_ascii=False),
                result_status,
                inspector_agency.strip(),
                today_date,
                clearance_status,
                notes.strip(),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        conn.commit()

    return {
        "inspection_id": inspection_id,
        "shipment_id": shipment_id,
        "importer_name": importer_name,
        "product_name": product_name,
        "origin_country": origin_country,
        "quantity_kg": quantity_kg,
        "inspection_mode": mode_clean,
        "mode_name_vi": mode_info["name_vi"],
        "sampling_performed": sampling_performed,
        "result_status": result_status,
        "clearance_status": clearance_status,
        "inspector_agency": inspector_agency,
        "inspection_date": today_date,
        "notes": notes,
    }


__all__ = ["inspect_imported_food_record"]
