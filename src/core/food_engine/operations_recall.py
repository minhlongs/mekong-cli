# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Food recall operations under Decree 15/2018/NĐ-CP."""

from __future__ import annotations

import datetime
import typing
import uuid

from .constants import FOOD_RECALL_CLASSES
from .db import get_connection

if typing.TYPE_CHECKING:
    import pathlib


def initiate_recall_record(
    db_path: pathlib.Path,
    product_name: str,
    batch_number: str,
    recall_class: str,
    reason: str,
    hazard_description: str,
    affected_quantity: float,
    recovered_quantity: float = 0.0,
    recall_scope: str = "NATIONWIDE",
    disposal_method: str = "DESTROY",
    notes: str = "",
) -> dict[str, typing.Any]:
    """Issue an official food recall order with statutory deadlines."""
    class_clean = recall_class.strip().upper()
    if class_clean not in FOOD_RECALL_CLASSES:
        valid_classes = list(FOOD_RECALL_CLASSES.keys())
        raise ValueError(f"Cấp độ thu hồi không hợp lệ: '{recall_class}'. Hỗ trợ: {valid_classes}")

    class_info = FOOD_RECALL_CLASSES[class_clean]
    notice_deadline_hours = class_info["notice_deadline_hours"]
    recall_days = class_info["recall_completion_days"]

    today_date = datetime.date.today()
    initiated_date = today_date.isoformat()
    deadline_date = (today_date + datetime.timedelta(days=recall_days)).isoformat()

    recall_id = f"recall-{uuid.uuid4().hex[:12]}"
    recall_number = f"REC-{class_clean}-{today_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    status = "COMPLETED" if (affected_quantity > 0 and recovered_quantity >= affected_quantity) else "ACTIVE"

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO food_recalls (
                recall_id, recall_number, product_name, batch_number, recall_class,
                reason, hazard_description, affected_quantity, recovered_quantity,
                recall_scope, initiated_date, deadline_date, status, disposal_method,
                notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recall_id,
                recall_number,
                product_name.strip(),
                batch_number.strip(),
                class_clean,
                reason.strip(),
                hazard_description.strip(),
                affected_quantity,
                recovered_quantity,
                recall_scope.strip().upper(),
                initiated_date,
                deadline_date,
                status,
                disposal_method.strip().upper(),
                notes.strip(),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )
        conn.commit()

    recovery_rate_pct = round((recovered_quantity / affected_quantity * 100.0), 2) if affected_quantity > 0 else 0.0

    return {
        "recall_id": recall_id,
        "recall_number": recall_number,
        "product_name": product_name,
        "batch_number": batch_number,
        "recall_class": class_clean,
        "class_name_vi": class_info["name_vi"],
        "hazard_level": class_info["hazard_level"],
        "notice_deadline_hours": notice_deadline_hours,
        "recall_completion_days": recall_days,
        "affected_quantity": affected_quantity,
        "recovered_quantity": recovered_quantity,
        "recovery_rate_pct": recovery_rate_pct,
        "initiated_date": initiated_date,
        "deadline_date": deadline_date,
        "status": status,
        "disposal_method": disposal_method.strip().upper(),
        "message": (
            f"Đã phát lệnh thu hồi {class_clean} ({class_info['name_vi']}) đối với lô hàng '{batch_number}'. "
            f"Hạn chót thu hồi triệt để: {deadline_date} (trong vòng {recall_days} ngày)."
        ),
    }


def update_recall_recovery_record(
    db_path: pathlib.Path,
    recall_id_or_number: str,
    additional_recovered_qty: float,
) -> dict[str, typing.Any]:
    """Update recovered quantity and check completion status for an active recall."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT * FROM food_recalls
            WHERE recall_id = ? OR recall_number = ?
            """,
            (recall_id_or_number, recall_id_or_number),
        ).fetchone()

        if not row:
            raise ValueError(f"Không tìm thấy lệnh thu hồi với mã: '{recall_id_or_number}'")

        current_recovered = float(row["recovered_quantity"])
        affected_qty = float(row["affected_quantity"])
        new_recovered = current_recovered + additional_recovered_qty

        new_status = "COMPLETED" if new_recovered >= affected_qty else "ACTIVE"

        conn.execute(
            """
            UPDATE food_recalls
            SET recovered_quantity = ?, status = ?
            WHERE recall_id = ?
            """,
            (new_recovered, new_status, row["recall_id"]),
        )
        conn.commit()

    recovery_rate_pct = round((new_recovered / affected_qty * 100.0), 2) if affected_qty > 0 else 0.0
    return {
        "recall_id": row["recall_id"],
        "recall_number": row["recall_number"],
        "product_name": row["product_name"],
        "batch_number": row["batch_number"],
        "affected_quantity": affected_qty,
        "recovered_quantity": new_recovered,
        "recovery_rate_pct": recovery_rate_pct,
        "status": new_status,
        "is_complete": new_status == "COMPLETED",
    }


__all__ = [
    "initiate_recall_record",
    "update_recall_recovery_record",
]
