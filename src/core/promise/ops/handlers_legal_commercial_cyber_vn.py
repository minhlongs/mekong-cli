# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Composite handlers for Wave 5B Vietnamese Commercial, Financial & Cyber Statutory Operations.

Binds ``etransaction``, ``cyber``, ``fdi``, ``customs``, ``banking``, and ``aml``
operations to workspace-scoped SQLite databases with deterministic statutory
postcondition verification under Law on Electronic Transactions 20/2023/QH15,
Cybersecurity Law 24/2018/QH14 & Decree 53/2022/NĐ-CP, Investment Law 61/2020/QH14,
Customs Law 54/2014/QH13, Law on Credit Institutions 32/2024/QH15, and Law on
Anti-Money Laundering 14/2022/QH15.
"""

from __future__ import annotations

import pathlib
import typing

from src.core.promise.ops.handlers_finance import engine_db
from src.core.promise.runtime import HandlerContext


def etransaction_create_contract(
    context: HandlerContext,
    contract_number: str,
    title: str,
    provider_name: str = "Công ty TNHH Mekong AI",
    provider_tax_id: str = "0101234567",
    client_name: str = "Công ty CP Bán Lẻ Số",
    client_tax_id: str = "0107654321",
    contract_value: float = 120_000_000.0,
) -> dict[str, typing.Any]:
    """Create a statutory electronic contract under Law 20/2023/QH15 in ``etransaction.db``."""
    from src.core.etransaction_engine import ETransactionEngine

    db_file = engine_db(context, "etransaction")
    engine = ETransactionEngine(db_path=str(db_file))
    parties = [
        {"name": provider_name.strip(), "role": "PROVIDER", "tax_id": provider_tax_id.strip()},
        {"name": client_name.strip(), "role": "CLIENT", "tax_id": client_tax_id.strip()},
    ]
    result = engine.create_electronic_contract(
        contract_number=contract_number.strip(),
        title=title.strip(),
        content=f"Hợp đồng giao dịch điện tử '{title.strip()}' tuân thủ Luật Giao dịch điện tử 20/2023/QH15.",
        parties=parties,
        contract_value=float(contract_value),
        currency="VND",
    )
    return {
        **result,
        "contract_id": str(result["contract_id"]),
        "contract_number": str(result["contract_number"]),
        "title": str(result["title"]),
        "contract_value": float(result["contract_value"]),
        "status": str(result["status"]),
    }


def etransaction_certify_ceca(
    context: HandlerContext,
    contract_number: str,
    title: str,
    provider_name: str = "Công ty TNHH Mekong AI",
    client_name: str = "Công ty CP Bán Lẻ Số",
    ceca_authority: str = "CeCA-Vietnam-Post",
    license_number: str = "BCT-CeCA-008/GP",
    contract_value: float = 150_000_000.0,
) -> dict[str, typing.Any]:
    """Execute qualified digital signatures and certify electronic contract via MOIT CeCA in ``etransaction.db``."""
    from src.core.etransaction_engine import ETransactionEngine

    db_file = engine_db(context, "etransaction")
    engine = ETransactionEngine(db_path=str(db_file))
    parties = [
        {"name": provider_name.strip(), "role": "PROVIDER", "tax_id": "0101234567"},
        {"name": client_name.strip(), "role": "CLIENT", "tax_id": "0107654321"},
    ]
    created = engine.create_electronic_contract(
        contract_number=contract_number.strip(),
        title=title.strip(),
        content=f"Hợp đồng điện tử có chứng thực CeCA '{title.strip()}' theo Nghị định 130/2018/NĐ-CP.",
        parties=parties,
        contract_value=float(contract_value),
        currency="VND",
    )
    cid = str(created["contract_id"])
    engine.sign_electronic_contract(
        contract_id=cid,
        party_name=provider_name.strip(),
        signer_role="PROVIDER",
        signature_type="QUALIFIED",
        ca_provider="VNPT-CA",
        cert_serial="VNPT-CA-2026-001",
        cert_valid_until="2028-12-31",
    )
    engine.sign_electronic_contract(
        contract_id=cid,
        party_name=client_name.strip(),
        signer_role="CLIENT",
        signature_type="QUALIFIED",
        ca_provider="VIETTEL-CA",
        cert_serial="VIETTEL-CA-2026-002",
        cert_valid_until="2028-12-31",
    )
    certified = engine.certify_ceca_contract(
        contract_id=cid,
        ceca_authority=ceca_authority.strip(),
        license_number=license_number.strip(),
    )
    return {
        **certified,
        "contract_id": cid,
        "contract_number": str(certified["contract_number"]),
        "ceca_verified": bool(certified["ceca_verified"]),
        "ceca_token_id": str(certified["ceca_token_id"]),
        "authority_name": str(certified["authority_name"]),
        "status": "CECA_CERTIFIED",
    }


def cyber_assess_system_level(
    context: HandlerContext,
    system_name: str,
    organization: str,
    data_classification: str = "CONFIDENTIAL_MAT",
    service_scale: str = "NATIONAL",
) -> dict[str, typing.Any]:
    """Assess information system security level (Cấp độ 1–5) under Decree 85/2016/NĐ-CP in ``cyber.db``."""
    from src.core.cyber_engine import CyberEngine

    db_file = engine_db(context, "cyber")
    engine = CyberEngine(db_path=str(db_file))
    result = engine.assess_information_system_level(
        system_name=system_name.strip(),
        organization=organization.strip(),
        data_classification=data_classification.strip().upper(),
        service_scale=service_scale.strip().upper(),
    )
    return {
        **result,
        "assessment_id": str(result["assessment_id"]),
        "system_name": str(result["system_name"]),
        "organization": str(result["organization"]),
        "recommended_level": int(result["recommended_level"]),
        "audit_frequency_months": int(result["audit_frequency_months"]),
    }


def cyber_audit_data_localization(
    context: HandlerContext,
    service_name: str,
    provider_type: str = "DOMESTIC_ENTERPRISE",
    local_storage_active: bool = True,
    retention_months: int = 24,
    has_local_branch: bool = True,
) -> dict[str, typing.Any]:
    """Audit data localization compliance under Art. 26 Cybersecurity Law & Decree 53/2022/NĐ-CP in ``cyber.db``."""
    from src.core.cyber_engine import CyberEngine

    db_file = engine_db(context, "cyber")
    engine = CyberEngine(db_path=str(db_file))
    result = engine.audit_data_localization(
        service_name=service_name.strip(),
        provider_type=provider_type.strip().upper(),
        stores_personal_data=True,
        stores_user_generated_data=True,
        stores_relationship_data=True,
        local_storage_active=bool(local_storage_active),
        retention_months=int(retention_months),
        has_local_branch=bool(has_local_branch),
    )
    return {
        **result,
        "audit_id": str(result["audit_id"]),
        "service_name": str(result["service_name"]),
        "provider_type": str(result["provider_type"]),
        "retention_months": int(result["retention_months"]),
        "is_compliant": bool(result["is_compliant"]),
        "compliance_status": "COMPLIANT" if result["is_compliant"] else "NON_COMPLIANT",
    }


def fdi_generate_irc_dossier(
    context: HandlerContext,
    project_name: str,
    capital_usd: float = 500_000.0,
    investor_country: str = "SG",
    sector_code: str = "IT_SOFTWARE",
    location: str = "Khu Công Nghệ Cao Hòa Lạc, Hà Nội",
) -> dict[str, typing.Any]:
    """Generate and persist an Investment Registration Certificate (IRC) dossier under Investment Law 61/2020/QH14."""
    from src.core.fdi_engine import FdiEngine

    db_file = engine_db(context, "fdi")
    engine = FdiEngine(db_path=pathlib.Path(db_file))
    result = engine.generate_irc_dossier(
        project_name=project_name.strip(),
        capital_usd=float(capital_usd),
        investor_country=investor_country.strip().upper(),
        sector_code=sector_code.strip().upper(),
        location=location.strip(),
        save=True,
    )
    return {
        **result,
        "project_id": str(result["project_id"]),
        "project_name": str(result["project_name"]),
        "investor_country": str(result["investor_country"]),
        "sector_code": str(result["sector_code"]),
        "capital_usd": float(result["capital_usd"]),
        "required_documents_count": int(result["required_documents_count"]),
    }


def fdi_evaluate_foreign_loan(
    context: HandlerContext,
    borrower_name: str,
    lender_name: str = "DBS Bank Ltd",
    lender_country: str = "SG",
    amount_usd: float = 1_000_000.0,
    tenor_months: int = 24,
    interest_rate_pct: float = 5.8,
) -> dict[str, typing.Any]:
    """Evaluate offshore loan SBV registration obligations under Circular 12/2022/TT-NHNN in ``fdi.db``."""
    from src.core.fdi_engine import FdiEngine

    db_file = engine_db(context, "fdi")
    engine = FdiEngine(db_path=pathlib.Path(db_file))
    result = engine.evaluate_foreign_loan(
        amount_usd=float(amount_usd),
        tenor_months=int(tenor_months),
        interest_rate_pct=float(interest_rate_pct),
        borrower_name=borrower_name.strip(),
        lender_name=lender_name.strip(),
        lender_country=lender_country.strip().upper(),
        save=True,
    )
    return {
        **result,
        "loan_id": str(result["loan_id"]),
        "borrower_name": str(result["borrower_name"]),
        "lender_name": str(result["lender_name"]),
        "amount_usd": float(result["amount_usd"]),
        "tenor_months": int(result["tenor_months"]),
        "sbv_registration_required": bool(result["sbv_registration_required"]),
        "is_compliant": bool(result["is_compliant"]),
    }


def customs_create_declaration(
    context: HandlerContext,
    enterprise_tax_id: str,
    commodity_name: str,
    invoice_value_usd: float,
    hs_code: str = "8471.30.20",
    origin_country: str = "SG",
    declaration_type: str = "IMPORT_BUSINESS",
) -> dict[str, typing.Any]:
    """Create a VNACCS/VCIS customs declaration with channeling & tax calculation in ``customs.db``."""
    from src.core.customs_engine import CustomsEngine

    db_file = engine_db(context, "customs")
    engine = CustomsEngine(db_path=pathlib.Path(db_file))
    result = engine.create_declaration(
        enterprise_tax_id=enterprise_tax_id.strip(),
        hs_code=hs_code.strip(),
        commodity_name=commodity_name.strip(),
        invoice_value_usd=float(invoice_value_usd),
        origin_country=origin_country.strip().upper(),
        declaration_type=declaration_type.strip().upper(),
        save=True,
    )
    return {
        **result,
        "declaration_id": str(result["declaration_id"]),
        "enterprise_tax_id": str(result["enterprise_tax_id"]),
        "commodity_name": str(result["commodity_name"]),
        "hs_code": str(result["hs_code"]),
        "channel": str(result["channel"]),
        "total_tax_vnd": float(result["total_tax_vnd"]),
        "status": str(result["status"]),
    }


def customs_verify_origin_co(
    context: HandlerContext,
    exporter_name: str,
    fob_value_usd: float,
    non_originating_value_usd: float,
    form_type: str = "FORM_D",
    hs_code: str = "8471.30.20",
    importer_country: str = "SG",
) -> dict[str, typing.Any]:
    """Verify ASEAN/FTA Rules of Origin (RVC >= 40%) and issue C/O record in ``customs.db``."""
    from src.core.customs_engine import CustomsEngine

    db_file = engine_db(context, "customs")
    engine = CustomsEngine(db_path=pathlib.Path(db_file))
    result = engine.verify_rules_of_origin(
        form_type=form_type.strip().upper(),
        hs_code=hs_code.strip(),
        fob_value_usd=float(fob_value_usd),
        non_originating_value_usd=float(non_originating_value_usd),
        exporter_name=exporter_name.strip(),
        importer_country=importer_country.strip().upper(),
        save=True,
    )
    return {
        **result,
        "co_id": str(result["co_id"]),
        "exporter_name": str(result["exporter_name"]),
        "form_type": str(result["form_type"]),
        "rvc_pct": float(result["rvc_pct"]),
        "is_eligible": bool(result["is_eligible"]),
        "status": str(result["status"]),
    }


def banking_audit_capital_adequacy(
    context: HandlerContext,
    institution_name: str,
    tier1_capital_vnd: float = 15_000_000_000_000.0,
    tier2_capital_vnd: float = 3_000_000_000_000.0,
    credit_rwa_vnd: float = 100_000_000_000_000.0,
    market_rwa_vnd: float = 10_000_000_000_000.0,
    operational_rwa_vnd: float = 10_000_000_000_000.0,
    reporting_quarter: str = "Q4/2026",
) -> dict[str, typing.Any]:
    """Audit Basel II Capital Adequacy Ratio (CAR >= 8%) under Circular 41/2016/TT-NHNN in ``banking.db``."""
    from src.core.banking_engine import BankingEngine

    db_file = engine_db(context, "banking")
    engine = BankingEngine(db_path=pathlib.Path(db_file))
    result = engine.audit_capital_adequacy(
        institution_name=institution_name.strip(),
        tier1_capital_vnd=float(tier1_capital_vnd),
        tier2_capital_vnd=float(tier2_capital_vnd),
        credit_rwa_vnd=float(credit_rwa_vnd),
        market_rwa_vnd=float(market_rwa_vnd),
        operational_rwa_vnd=float(operational_rwa_vnd),
        reporting_quarter=reporting_quarter.strip(),
    )
    return {
        **result,
        "audit_id": str(result["audit_id"]),
        "institution_name": str(result["institution_name"]),
        "car_ratio_pct": float(result["car_ratio_pct"]),
        "car_status": str(result["car_status"]),
        "is_compliant": bool(result["is_compliant"]),
    }


def banking_classify_credit_debt(
    context: HandlerContext,
    contract_number: str,
    borrower_name: str,
    outstanding_balance_vnd: float,
    overdue_days: int = 15,
    deductible_collateral_vnd: float = 0.0,
) -> dict[str, typing.Any]:
    """Classify credit debt groups (Nhóm 1–5) & calculate risk provisions under Circular 31/2024/TT-NHNN in ``banking.db``."""
    from src.core.banking_engine import BankingEngine

    db_file = engine_db(context, "banking")
    engine = BankingEngine(db_path=pathlib.Path(db_file))
    result = engine.classify_credit_debt(
        contract_number=contract_number.strip(),
        borrower_name=borrower_name.strip(),
        outstanding_balance_vnd=float(outstanding_balance_vnd),
        overdue_days=int(overdue_days),
        deductible_collateral_vnd=float(deductible_collateral_vnd),
    )
    return {
        **result,
        "record_id": str(result["record_id"]),
        "contract_number": str(result["contract_number"]),
        "borrower_name": str(result["borrower_name"]),
        "debt_group": int(result["debt_group"]),
        "total_provision_vnd": float(result["total_provision_vnd"]),
        "is_npl": bool(result["is_npl"]),
    }


def aml_perform_cdd(
    context: HandlerContext,
    customer_name: str,
    identifier: str,
    customer_type: str = "INDIVIDUAL",
    industry: str = "FINTECH",
    nationality: str = "VN",
    is_pep: bool = False,
    senior_mgmt_approved: bool = False,
) -> dict[str, typing.Any]:
    """Perform Customer Due Diligence (CDD/EDD) under AML Law 14/2022/QH15 & Decree 19/2023/NĐ-CP in ``aml.db``."""
    from src.core.aml_engine import AmlEngine

    db_file = engine_db(context, "aml")
    engine = AmlEngine(db_path=pathlib.Path(db_file))
    result = engine.perform_cdd(
        customer_name=customer_name.strip(),
        customer_type=customer_type.strip().upper(),
        identifier=identifier.strip(),
        industry=industry.strip().upper(),
        nationality=nationality.strip().upper(),
        is_pep=bool(is_pep),
        senior_mgmt_approved=bool(senior_mgmt_approved),
    )
    return {
        **result,
        "profile_id": str(result["profile_id"]),
        "customer_name": str(result["customer_name"]),
        "identifier": str(result["identifier"]),
        "risk_level": str(result["risk_level"]),
        "risk_score": int(result["risk_score"]),
        "status": str(result["status"]),
    }


def aml_file_str_report(
    context: HandlerContext,
    customer_name: str,
    suspicion_type: str = "STRUCTURING",
    amount: float = 650_000_000.0,
    rationale: str = "Chia nhỏ giao dịch tiền mặt vượt ngưỡng 400 triệu VNĐ theo QĐ 11/2023/QĐ-TTg",
    urgency: str = "HIGH",
) -> dict[str, typing.Any]:
    """File a Suspicious Transaction Report (STR) to PCRT (NHNN) under Art. 26 AML Law 14/2022/QH15 after founder confirmation."""
    from src.core.aml_engine import AmlEngine

    db_file = engine_db(context, "aml")
    engine = AmlEngine(db_path=pathlib.Path(db_file))
    result = engine.file_str(
        customer_name=customer_name.strip(),
        suspicion_type=suspicion_type.strip().upper(),
        amount=float(amount),
        indicators=["STRUCTURED_DEPOSITS", "THRESHOLD_EVASION"],
        rationale=rationale.strip(),
        urgency=urgency.strip().upper(),
    )
    return {
        **result,
        "str_id": str(result["str_id"]),
        "customer_name": str(result["customer_name"]),
        "suspicion_type": str(result["suspicion_type"]),
        "amount": float(result["amount"]),
        "urgency": str(result["urgency"]),
        "status": str(result["status"]),
    }
