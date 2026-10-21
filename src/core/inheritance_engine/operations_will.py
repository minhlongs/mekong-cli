# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Will registration and statutory validity auditing under Civil Code 2015."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .enums import SuccessionType, WillForm, WillStatus
from .operations_estate import get_estate_record


def register_will_record(
    conn: sqlite3.Connection,
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
    estate = get_estate_record(conn, estate_id)

    valid_forms = [f.value for f in WillForm]
    if will_form not in valid_forms:
        raise ValueError(f"Hình thức di chúc không hợp lệ: {will_form}")

    will_status = WillStatus.VALID.value
    invalid_reasons: list[str] = []

    if will_form == WillForm.ORAL_NUNCUPATIVE.value:
        if not witness_1_name or not witness_2_name:
            will_status = WillStatus.VOID.value
            invalid_reasons.append("Di chúc miệng phải có ít nhất 02 người làm chứng ghi chép lại và cùng ký tên (Điều 629 K1).")
        if oral_will_recorded_date and oral_will_certified_date:
            d_rec = datetime.date.fromisoformat(oral_will_recorded_date)
            d_cert = datetime.date.fromisoformat(oral_will_certified_date)
            delta_days = (d_cert - d_rec).days
            if delta_days > 5:
                will_status = WillStatus.VOID.value
                invalid_reasons.append(f"Di chúc miệng phải được công chứng/chứng thực trong vòng 05 ngày làm việc (Điều 629 K1). Quá hạn: {delta_days} ngày.")

        d_created = datetime.date.fromisoformat(date_created)
        d_death = datetime.date.fromisoformat(estate["date_of_death"])
        if (d_death - d_created).days > 90:
            will_status = WillStatus.EXPIRED_ORAL.value
            invalid_reasons.append("Sau 03 tháng kể từ thời điểm lập di chúc miệng, người lập di chúc còn sống, minh mẫn thì di chúc mặc nhiên bị hủy bỏ (Điều 629 K2).")

    if will_form == WillForm.WRITTEN_WITNESSED.value and (not witness_1_name or not witness_2_name):
        will_status = WillStatus.VOID.value
        invalid_reasons.append("Di chúc bằng văn bản có người làm chứng phải có ít nhất 02 người làm chứng (Điều 634).")

    if will_form in (WillForm.WRITTEN_NOTARIZED.value, WillForm.WRITTEN_CERTIFIED.value) and not notary_office_or_ubnd:
        invalid_reasons.append("Cần ghi rõ tổ chức hành nghề công chứng hoặc UBND xã chứng thực.")

    wid = will_id or f"WIL-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO wills (
            will_id, estate_id, will_form, will_status, date_created,
            place_created, notary_office_or_ubnd, notary_number, notary_date,
            witness_1_name, witness_1_id, witness_2_name, witness_2_id,
            oral_will_recorded_date, oral_will_certified_date, executor_name,
            worship_estate_assigned, worship_manager_name, contents_summary,
            is_revoked, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (
            wid, estate_id, will_form, will_status, date_created, place_created,
            notary_office_or_ubnd, notary_number, notary_date, witness_1_name,
            witness_1_id, witness_2_name, witness_2_id, oral_will_recorded_date,
            oral_will_certified_date, executor_name, worship_estate_assigned,
            worship_manager_name, contents_summary, now,
        ),
    )

    if will_status == WillStatus.VALID.value:
        conn.execute(
            "UPDATE estates SET succession_type = ?, dedicated_worship_amount = ?, updated_at = ? WHERE estate_id = ?",
            (SuccessionType.TESTAMENTARY.value, worship_estate_assigned, now, estate_id),
        )
    conn.commit()

    return {
        "will_id": wid, "estate_id": estate_id, "will_form": will_form,
        "will_status": will_status, "is_valid": 1 if will_status == WillStatus.VALID.value else 0,
        "date_created": date_created, "place_created": place_created,
        "notary_office_or_ubnd": notary_office_or_ubnd, "notary_number": notary_number,
        "executor_name": executor_name, "worship_estate_assigned": worship_estate_assigned,
        "worship_manager_name": worship_manager_name, "invalid_reasons": invalid_reasons,
    }


__all__ = ["register_will_record"]
