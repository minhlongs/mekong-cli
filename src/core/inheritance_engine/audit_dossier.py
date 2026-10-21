# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Statute of limitations auditing, legal dossier packaging, and statutory compliance checks."""

from __future__ import annotations

import datetime
import sqlite3
import typing

from .calculator import calculate_statutory_shares_record
from .enums import WillStatus
from .operations_estate import get_estate_record


def check_statute_of_limitations_record(
    date_of_death: str,
    current_date: str | None = None,
) -> dict[str, typing.Any]:
    """Check inheritance statute of limitations under Art. 623 Civil Code 2015."""
    d_death = datetime.date.fromisoformat(date_of_death)
    d_curr = datetime.date.fromisoformat(current_date) if current_date else datetime.date.today()

    elapsed_days = (d_curr - d_death).days
    elapsed_years = elapsed_days / 365.25

    real_estate_deadline = d_death + datetime.timedelta(days=int(30 * 365.25))
    movable_deadline = d_death + datetime.timedelta(days=int(10 * 365.25))
    obligation_deadline = d_death + datetime.timedelta(days=int(3 * 365.25))

    is_real_estate_active = elapsed_years <= 30.0
    is_movable_active = elapsed_years <= 10.0
    is_obligation_active = elapsed_years <= 3.0

    return {
        "date_of_death": date_of_death,
        "current_date": d_curr.isoformat(),
        "elapsed_years": round(elapsed_years, 2),
        "real_estate_claim": {
            "limitation_years": 30, "deadline": real_estate_deadline.isoformat(),
            "is_active": is_real_estate_active, "remaining_years": max(0.0, round(30.0 - elapsed_years, 2)),
            "status": "WITHIN_LIMITATION" if is_real_estate_active else "EXPIRED",
            "legal_basis": "Điều 623 K1 BLDS 2015 (30 năm đối với bất động sản)",
        },
        "movable_property_claim": {
            "limitation_years": 10, "deadline": movable_deadline.isoformat(),
            "is_active": is_movable_active, "remaining_years": max(0.0, round(10.0 - elapsed_years, 2)),
            "status": "WITHIN_LIMITATION" if is_movable_active else "EXPIRED",
            "legal_basis": "Điều 623 K1 BLDS 2015 (10 năm đối với động sản)",
        },
        "creditor_obligation_claim": {
            "limitation_years": 3, "deadline": obligation_deadline.isoformat(),
            "is_active": is_obligation_active, "remaining_years": max(0.0, round(3.0 - elapsed_years, 2)),
            "status": "WITHIN_LIMITATION" if is_obligation_active else "EXPIRED",
            "legal_basis": "Điều 623 K2 BLDS 2015 (03 năm yêu cầu thực hiện nghĩa vụ tài sản)",
        },
    }


def generate_inheritance_dossier_record(conn: sqlite3.Connection, estate_id: str) -> dict[str, typing.Any]:
    """Generate comprehensive bilingual legal dossier for Notary Office, Land Registration Office, & Banks."""
    estate = get_estate_record(conn, estate_id)
    calc = calculate_statutory_shares_record(estate)
    limitation = check_statute_of_limitations_record(estate["date_of_death"])

    return {
        "dossier_id": f"DOS-{estate_id}",
        "generated_at": datetime.datetime.now().isoformat(),
        "estate_metadata": {
            "estate_id": estate["estate_id"], "decedent_name": estate["decedent_name"],
            "decedent_id_number": estate["decedent_id_number"], "date_of_death": estate["date_of_death"],
            "place_of_death": estate["place_of_death"], "last_residence": estate["last_residence"],
            "place_of_opening": estate["place_of_opening"], "succession_type": estate["succession_type"],
            "is_settled": bool(estate["is_settled"]),
        },
        "financial_summary": {
            "gross_assets": calc["gross_assets"], "total_obligations_paid": calc["total_obligations_paid"],
            "dedicated_worship_estate": calc["dedicated_worship_deducted"], "net_distributable_estate": calc["net_distributable_estate"],
        },
        "statute_of_limitations": limitation,
        "assets_inventory": estate["assets"],
        "obligations_ledger": calc["obligations_settlement"],
        "wills_record": estate["wills"],
        "heirs_distribution": calc["allocations"],
        "notary_requirements": [
            "Giấy chứng tử của người để lại di sản (Bản chính/trích lục).",
            "Giấy tờ chứng minh quan hệ thừa kế (Giấy khai sinh, Đăng ký kết hôn, Quyết định nhận nuôi con nuôi).",
            "Giấy chứng nhận quyền sử dụng đất, sổ đỏ, sổ hồng, sổ tiết kiệm, đăng ký xe (Bản chính).",
            "CCCD/Hộ chiếu và Giấy xác nhận thông tin cư trú của tất cả đồng thừa kế.",
            "Văn bản từ chối nhận di sản (nếu có người từ chối theo Điều 620 BLDS 2015).",
            "Biên bản niêm yết công khai 15 ngày tại UBND cấp xã (Điều 58 Luật Công chứng 2014).",
        ],
    }


def audit_compliance_record(conn: sqlite3.Connection, estate_id: str) -> dict[str, typing.Any]:
    """Audit estate file against statutory compliance rules of Civil Code 2015 & Law on Notarization 2014."""
    estate = get_estate_record(conn, estate_id)
    calc = calculate_statutory_shares_record(estate)
    limitation = check_statute_of_limitations_record(estate["date_of_death"])

    issues: list[str] = []
    warnings: list[str] = []

    if not limitation["real_estate_claim"]["is_active"]:
        warnings.append("Hết thời hiệu 30 năm yêu cầu chia di sản bất động sản (Điều 623 BLDS 2015).")
    if not limitation["movable_property_claim"]["is_active"]:
        warnings.append("Hết thời hiệu 10 năm yêu cầu chia di sản động sản (Điều 623 BLDS 2015).")

    for a in estate["assets"]:
        if not a["is_sole_ownership"] and a["ownership_share"] > 0.5:
            warnings.append(f"Tài sản chung '{a['asset_name']}' có tỷ lệ phân bổ người chết > 50% cần có văn bản chứng minh.")

    if calc["gross_assets"] < calc["total_obligations_claimed"]:
        issues.append(f"Tổng tài sản di sản ({calc['gross_assets']:,.0f} đ) không đủ thanh toán toàn bộ nghĩa vụ ({calc['total_obligations_claimed']:,.0f} đ). Người thừa kế chỉ chịu trách nhiệm trong phạm vi di sản (Điều 615).")

    for w in estate["wills"]:
        if w["will_status"] == WillStatus.VOID.value:
            issues.append(f"Di chúc {w['will_id']} bị vô hiệu.")
        elif w["will_status"] == WillStatus.EXPIRED_ORAL.value:
            issues.append(f"Di chúc miệng {w['will_id']} đã hết hiệu lực do quá 03 tháng.")

    for alloc in calc["allocations"]:
        if alloc.get("is_forced_heir") and alloc["allocated_amount"] < alloc.get("forced_minimum_required", 0.0):
            issues.append(f"Người thừa kế bắt buộc {alloc['full_name']} chưa nhận đủ 2/3 suất theo Điều 644 BLDS 2015.")

    is_compliant = len(issues) == 0
    compliance_rating = ("EXCELLENT" if len(warnings) == 0 else "PASSED") if is_compliant else "NON_COMPLIANT"

    return {
        "estate_id": estate_id, "decedent_name": estate["decedent_name"], "is_compliant": is_compliant,
        "compliance_rating": compliance_rating, "issues_count": len(issues), "warnings_count": len(warnings),
        "issues": issues, "warnings": warnings, "timestamp": datetime.datetime.now().isoformat(),
    }


__all__ = [
    "check_statute_of_limitations_record",
    "generate_inheritance_dossier_record",
    "audit_compliance_record",
]
