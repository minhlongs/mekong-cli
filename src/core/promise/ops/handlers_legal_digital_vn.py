# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Composite handlers for Vietnamese Digital, E-Commerce & Intellectual Property Operations (Wave 4B).

Binds ``privacy``, ``ecom``, and ``ip`` operations to workspace-scoped SQLite
databases (``privacy.db``, ``ecommerce.db``, ``ip.db``) with deterministic
statutory verification under Decree 13/2023/NĐ-CP (PDPD), Decree 52/2013/NĐ-CP &
85/2021/NĐ-CP (E-Commerce), Circular 103/2014/TT-BTC & 80/2021/TT-BTC (FCT), and
Law on Intellectual Property 2005 (amended 2022) & Decree 17/2023/NĐ-CP.
"""

from __future__ import annotations

import pathlib
import typing

from src.core.promise.ops.handlers_finance import engine_db
from src.core.promise.runtime import HandlerContext


def privacy_assess_dpia(
    context: HandlerContext,
    activity_name: str,
    processing_purpose: str,
    data_categories: list[str] | None = None,
    legal_basis: str = "CONSENT",
    security_measures: str = "AES-256 Encryption, Role-Based Access Control, TLS 1.3",
) -> dict[str, typing.Any]:
    """Synthesize a DPIA (Form 04-A05) under Article 24 Decree 13/2023/NĐ-CP in ``privacy.db``."""
    from src.core.privacy_engine import PrivacyEngine

    db_file = engine_db(context, "privacy")
    engine = PrivacyEngine(db_path=pathlib.Path(db_file))
    categories = list(data_categories) if data_categories else ["FULL_NAME", "EMAIL", "PHONE_NUMBER"]
    result = engine.create_dpia_assessment(
        activity_name=activity_name,
        processing_purpose=processing_purpose,
        data_categories=categories,
        legal_basis=legal_basis,
        security_measures=security_measures,
        save=True,
    )
    risk = result.get("risk_assessment") or {}
    risk_level = str(risk.get("risk_level", "LOW_RISK"))
    return {
        **result,
        "risk_level": risk_level,
        "dpo_mandatory": bool(risk.get("dpo_mandatory", False)),
        "filing_deadline_days": int((result.get("form_04_a05") or {}).get("filing_deadline_days", 60)),
    }


def privacy_process_dsar(
    context: HandlerContext,
    request_type: str,
    subject_id: str,
    details: str = "Yêu cầu thực hiện quyền của chủ thể dữ liệu theo Điều 9 Nghị định 13/2023/NĐ-CP",
) -> dict[str, typing.Any]:
    """Process a Data Subject Access/Deletion Request under Art. 9–16 Decree 13/2023/NĐ-CP (72h SLA)."""
    from src.core.privacy_engine import PrivacyEngine

    db_file = engine_db(context, "privacy")
    engine = PrivacyEngine(db_path=pathlib.Path(db_file))
    result = engine.handle_dsar_request(
        request_type=request_type,
        subject_id=subject_id,
        details=details,
        save=True,
    )
    deadline = result.get("statutory_deadline") or {}
    deadline_days = int(deadline.get("deadline_days", 3))
    return {
        **result,
        "deadline_days": deadline_days,
        "sla_hours": deadline_days * 24,
    }


def ecom_assess_platform_filing(
    context: HandlerContext,
    platform_name: str,
    domain_url: str,
    platform_type: str = "MARKETPLACE",
    enterprise_tax_id: str = "0109998881",
    has_operating_regulations: bool = True,
    has_dispute_mechanism: bool = True,
    has_seller_kyc: bool = True,
    has_data_retention_3yr: bool = True,
    has_tax_reporting_system: bool = True,
) -> dict[str, typing.Any]:
    """Audit MOIT e-commerce filing obligation (Thông báo vs Đăng ký) under Decree 52/2013 & 85/2021."""
    from src.core.ecommerce_engine import EcommerceEngine

    db_file = engine_db(context, "ecommerce")
    engine = EcommerceEngine(db_path=pathlib.Path(db_file))
    result = engine.audit_platform_compliance(
        platform_name=platform_name,
        domain_url=domain_url,
        platform_type=platform_type,
        enterprise_tax_id=enterprise_tax_id,
        has_operating_regulations=bool(has_operating_regulations),
        has_dispute_mechanism=bool(has_dispute_mechanism),
        has_seller_kyc=bool(has_seller_kyc),
        has_data_retention_3yr=bool(has_data_retention_3yr),
        has_tax_reporting_system=bool(has_tax_reporting_system),
        save=True,
    )
    proc = result.get("licensing_procedure") or {}
    ev = result.get("compliance_evaluation") or {}
    return {
        **result,
        "platform_name": platform_name.strip(),
        "domain_url": domain_url.strip(),
        "statutory_procedure": str(proc.get("statutory_procedure", "NOTIFICATION")),
        "compliance_score": int(ev.get("compliance_score", 0)),
        "compliance_status": str(ev.get("compliance_status", "COMPLIANT_APPROVED")),
    }


def ecom_calculate_withholding_tax(
    context: HandlerContext,
    foreign_supplier_name: str,
    service_category: str = "CLOUD_SAAS",
    supplier_etax_code: str = "",
    revenue_usd: float = 0.0,
    revenue_vnd: float = 0.0,
    quarter: str = "Q4-2026",
) -> dict[str, typing.Any]:
    """Calculate Foreign Contractor Tax (FCT — VAT + CIT) under Circular 103/2014 & 80/2021/TT-BTC."""
    from src.core.ecommerce_engine import EcommerceEngine

    db_file = engine_db(context, "ecommerce")
    engine = EcommerceEngine(db_path=pathlib.Path(db_file))
    effective_vnd = float(revenue_vnd)
    if effective_vnd <= 0.0 and float(revenue_usd) <= 0.0:
        effective_vnd = 100_000_000.0
    result = engine.calculate_foreign_contractor_tax(
        foreign_supplier_name=foreign_supplier_name,
        supplier_etax_code=supplier_etax_code,
        service_category=service_category,
        revenue_usd=float(revenue_usd),
        revenue_vnd=effective_vnd,
        quarter=quarter,
        save=True,
    )
    breakdown = result.get("tax_breakdown_vnd") or {}
    return {
        **result,
        "foreign_supplier_name": foreign_supplier_name.strip(),
        "service_category": str((result.get("service_classification") or {}).get("category", service_category)),
        "vat_amount_vnd": float(breakdown.get("vat_amount_vnd", 0.0)),
        "cit_amount_vnd": float(breakdown.get("cit_amount_vnd", 0.0)),
        "total_fct_liability_vnd": float(breakdown.get("total_fct_liability_vnd", 0.0)),
        "filing_status": str((result.get("payment_and_filing") or {}).get("filing_status", "PENDING")),
    }


def ip_assess_trademark(
    context: HandlerContext,
    mark_name: str,
    nice_class: str = "09",
    applicant_name: str = "Công ty TNHH Mekong AI",
    goods_services_spec: str = "",
) -> dict[str, typing.Any]:
    """Run trademark similarity check (Art. 72–74 IP Law) and file application in ``ip.db``."""
    from src.core.ip_engine import IpEngine

    db_file = engine_db(context, "ip")
    engine = IpEngine(db_path=pathlib.Path(db_file))
    similarity = engine.search_trademark_similarity(mark_name=mark_name, nice_class=nice_class)
    registration = engine.register_trademark(
        mark_name=mark_name,
        nice_class=nice_class,
        applicant_name=applicant_name,
        goods_services_spec=goods_services_spec,
        save=True,
    )
    return {
        **registration,
        "highest_similarity_score": float(similarity["highest_similarity_score"]),
        "overall_conflict_risk": str(similarity["overall_conflict_risk"]),
        "legal_assessment": str(similarity["legal_assessment"]),
        "matches_count": int(similarity["matches_count"]),
        "top_similar_marks": similarity["top_similar_marks"],
    }


def ip_register_copyright(
    context: HandlerContext,
    software_name: str,
    author_name: str,
    version: str = "1.0.0",
    repository_url: str = "",
    lines_of_code: int = 10_000,
) -> dict[str, typing.Any]:
    """Compile software copyright registration dossier (Decree 17/2023/NĐ-CP) and persist in ``ip.db``."""
    from src.core.ip_engine import IpEngine

    db_file = engine_db(context, "ip")
    engine = IpEngine(db_path=pathlib.Path(db_file))
    dossier = engine.register_software_copyright(
        software_name=software_name,
        author_name=author_name,
        version=version,
        repository_url=repository_url,
        lines_of_code=int(lines_of_code),
        save=True,
    )
    return {
        **dossier,
        "dossier_items_count": len(dossier.get("required_dossier_items") or []),
    }


__all__ = [
    "ecom_assess_platform_filing",
    "ecom_calculate_withholding_tax",
    "ip_assess_trademark",
    "ip_register_copyright",
    "privacy_assess_dpia",
    "privacy_process_dsar",
]
