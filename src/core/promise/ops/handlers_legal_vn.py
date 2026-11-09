# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Composite handlers for Vietnamese Legal & Statutory Operations (Wave 3B).

Binds ``corporate``, ``labor``, and ``contract`` operations to workspace-scoped
SQLite databases (``corporate.db``, ``labor.db``, ``contracts.db``) with
deterministic statutory verification under Law on Enterprises 2020, Labor Code
2019, Commercial Law 2005, and Law on Electronic Transactions 2023.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3
import typing
import uuid

from src.core.promise.ops.handlers_finance import engine_db
from src.core.promise.runtime import HandlerContext
from src.core.promise.signing import utc_now_iso


def corporate_incorporate(
    context: HandlerContext,
    company_name: str,
    entity_type: str = "TNHH_1TV",
    charter_capital: int = 1_000_000_000,
    legal_rep_name: str = "Nguyễn Văn A",
    address: str = "Hà Nội, Việt Nam",
    main_industry: str = "6201",
) -> dict[str, typing.Any]:
    """Synthesize incorporation dossier and persist dossier record to ``corporate.db``."""
    from src.core.corporate_engine import CorporateEngine

    db_file = engine_db(context, "corporate")
    engine = CorporateEngine(db_path=pathlib.Path(db_file))
    dossier = engine.create_filing_dossier(
        company_name=company_name,
        entity_type=entity_type,
        charter_capital=int(charter_capital),
        legal_rep_name=legal_rep_name,
        address=address,
        main_industry=main_industry,
    )
    now = utc_now_iso()
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO statutory_documents (
                doc_id, entity_id, company_name, doc_type, title, content_markdown, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dossier["dossier_id"],
                f"ENT-{dossier['dossier_id'][-6:]}",
                company_name,
                "INCORPORATION_DOSSIER",
                f"Hồ sơ đăng ký doanh nghiệp — {company_name}",
                json.dumps(dossier["documents"], ensure_ascii=False),
                now,
            ),
        )
        conn.commit()
    return {
        **dossier,
        "documents_count": len(dossier.get("documents", [])),
    }


def labor_calculate_overtime(
    context: HandlerContext,
    employee_name: str = "Nguyễn Văn B",
    month_year: str = "2026-11",
    hourly_rate_vnd: float = 100_000.0,
    normal_day_ot_hours: float = 10.0,
    weekend_ot_hours: float = 8.0,
    holiday_ot_hours: float = 0.0,
    night_shift_regular_hours: float = 0.0,
    night_shift_ot_hours: float = 0.0,
    yearly_cumulative_hours: float = 120.0,
    is_extended_industry: bool = False,
) -> dict[str, typing.Any]:
    """Calculate statutory overtime pay + caps under Articles 98 & 107 BLLĐ 2019 and persist to ``labor.db``."""
    from src.core.labor_engine import LaborEngine

    db_file = engine_db(context, "labor")
    engine = LaborEngine(db_path=pathlib.Path(db_file))
    pay = engine.calculate_overtime_pay(
        hourly_rate_vnd=float(hourly_rate_vnd),
        normal_day_ot_hours=float(normal_day_ot_hours),
        weekend_ot_hours=float(weekend_ot_hours),
        holiday_ot_hours=float(holiday_ot_hours),
        night_shift_regular_hours=float(night_shift_regular_hours),
        night_shift_ot_hours=float(night_shift_ot_hours),
    )
    monthly_total = float(pay["total_overtime_hours"])
    caps = engine.validate_overtime_caps(
        monthly_overtime_hours=monthly_total,
        yearly_cumulative_hours=float(yearly_cumulative_hours),
        is_extended_industry=bool(is_extended_industry),
    )
    record_id = f"OT-{uuid.uuid4().hex[:8].upper()}"
    now = utc_now_iso()
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            INSERT INTO overtime_records (
                record_id, employee_id, month_year, monthly_hours,
                yearly_cumulative_hours, overtime_pay_vnd, is_compliant, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                employee_name,
                month_year,
                monthly_total,
                float(yearly_cumulative_hours),
                float(pay["total_overtime_pay_vnd"]),
                1 if caps["is_compliant"] else 0,
                now,
            ),
        )
        conn.commit()
    return {
        "record_id": record_id,
        "employee_name": employee_name,
        "month_year": month_year,
        **pay,
        "is_compliant": caps["is_compliant"],
        "monthly_cap": caps["monthly_cap"],
        "yearly_cap": caps["yearly_cap"],
        "violations": caps["violations"],
        "statutory_risk": caps["statutory_risk"],
    }


def contract_draft(
    context: HandlerContext,
    template_type: str = "COMMERCIAL_SALE",
    party_a_name: str = "Công ty TNHH Mekong AI",
    party_b_name: str = "Công ty Cổ phần Đối Tác Số",
    contract_value_vnd: float = 120_000_000.0,
    party_a_tax_id: str = "0109998881",
    party_b_tax_id: str = "0318887772",
    scope_summary: str = "",
    penalty_rate_pct: float = 8.0,
    dispute_forum: str = "VIAC",
) -> dict[str, typing.Any]:
    """Synthesize commercial contract in ``contracts.db`` and validate template support."""
    from src.core.contract_engine import ContractEngine

    db_file = engine_db(context, "contracts")
    engine = ContractEngine(db_path=pathlib.Path(db_file))
    res = engine.draft_contract(
        template_type=template_type,
        party_a_name=party_a_name,
        party_b_name=party_b_name,
        contract_value_vnd=float(contract_value_vnd),
        party_a_tax_id=party_a_tax_id,
        party_b_tax_id=party_b_tax_id,
        scope_summary=scope_summary,
        penalty_rate_pct=float(penalty_rate_pct),
        dispute_forum=dispute_forum,
        save=True,
    )
    if not res.get("ok"):
        raise ValueError(str(res.get("error") or f"Invalid contract template: {template_type}"))
    return res


def contract_review(
    context: HandlerContext,
    contract_id: str = "",
    contract_text: str = "",
    penalty_pct: float | None = None,
) -> dict[str, typing.Any]:
    """Scan contract for Vietnamese statutory redlines and persist review to ``contracts.db``."""
    from src.core.contract_engine import ContractEngine

    db_file = engine_db(context, "contracts")
    engine = ContractEngine(db_path=pathlib.Path(db_file))
    resolved_id = contract_id.strip()
    text_to_scan = contract_text.strip()

    if resolved_id and not text_to_scan:
        with sqlite3.connect(db_file) as conn:
            row = conn.execute(
                "SELECT contract_id, content_text, penalty_rate_pct FROM contracts WHERE contract_id = ? OR contract_number = ?",
                (resolved_id, resolved_id),
            ).fetchone()
        if row is None:
            raise ValueError(f"Contract '{resolved_id}' not found in workspace contracts.db")
        resolved_id = str(row[0])
        text_to_scan = str(row[1])
        if penalty_pct is None:
            penalty_pct = float(row[2])

    if not text_to_scan:
        raise ValueError("Either contract_id or contract_text must be provided for contract.review")

    assessment = engine.assess_contract_risk(contract_text=text_to_scan, penalty_pct=penalty_pct)
    review_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
    now = utc_now_iso()
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            INSERT INTO contract_reviews (
                review_id, contract_id, risk_score, risk_level,
                red_flags_json, recommendations_json, reviewed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                resolved_id or "ADHOC",
                int(assessment["risk_score"]),
                str(assessment["risk_level"]),
                json.dumps(assessment["red_flags"], ensure_ascii=False),
                json.dumps(assessment["recommendations"], ensure_ascii=False),
                now,
            ),
        )
        conn.commit()
    return {
        "review_id": review_id,
        "contract_id": resolved_id or "ADHOC",
        **assessment,
        "reviewed_at": now,
    }


def contract_sign(
    context: HandlerContext,
    contract_id: str,
    signer_name: str,
    signer_title: str = "Giám đốc điều hành",
    signer_tax_id: str = "0109998881",
    organization_name: str = "",
) -> dict[str, typing.Any]:
    """Execute SHA-256 electronic signature on a contract in ``contracts.db`` after founder confirmation."""
    from src.core.contract_engine import ContractEngine

    db_file = engine_db(context, "contracts")
    engine = ContractEngine(db_path=pathlib.Path(db_file))
    sig = engine.sign_contract(
        contract_id=contract_id,
        signer_name=signer_name,
        signer_title=signer_title,
        signer_tax_id=signer_tax_id,
        organization_name=organization_name,
        save=True,
    )
    if not sig.get("ok"):
        raise ValueError(str(sig.get("error") or f"Contract '{contract_id}' not found"))
    return sig


__all__ = [
    "contract_draft",
    "contract_review",
    "contract_sign",
    "corporate_incorporate",
    "labor_calculate_overtime",
]
