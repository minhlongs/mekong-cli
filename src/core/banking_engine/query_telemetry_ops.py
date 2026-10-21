# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Listing and telemetry query operations for BankingEngine."""

from __future__ import annotations

import json
import pathlib
import sqlite3
import typing

from src.core.banking_engine.models_audit import (
    CapitalAdequacyAudit,
    DebtClassification,
)
from src.core.banking_engine.models_institution import (
    BankingInstitution,
    CreditFacility,
)


class QueryTelemetryOpsMixin:
    """Mixin for listing banking records and aggregating telemetry."""

    db_path: pathlib.Path

    def _get_connection(self) -> sqlite3.Connection:
        raise NotImplementedError

    def list_licenses(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List licensed credit institutions."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM banking_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                BankingInstitution(
                    license_id=r["license_id"], institution_name=r["institution_name"],
                    institution_type=r["institution_type"], tax_id=r["tax_id"],
                    charter_capital_vnd=r["charter_capital_vnd"], headquarters_address=r["headquarters_address"],
                    sbv_license_number=r["sbv_license_number"], license_date=r["license_date"],
                    governor_signed_by=r["governor_signed_by"], status=r["status"], created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_credit_facilities(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List underwritten credit facilities."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM credit_facilities ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                CreditFacility(
                    credit_id=r["credit_id"], contract_number=r["contract_number"],
                    borrower_name=r["borrower_name"], borrower_id=r["borrower_id"],
                    is_corporate=bool(r["is_corporate"]), institution_name=r["institution_name"],
                    loan_amount_vnd=r["loan_amount_vnd"], interest_rate_pct=r["interest_rate_pct"],
                    term_months=r["term_months"], purpose=r["purpose"],
                    collateral_type=r["collateral_type"], collateral_value_vnd=r["collateral_value_vnd"],
                    bank_equity_vnd=r["bank_equity_vnd"],
                    customer_exposure_ratio_pct=r["customer_exposure_ratio_pct"],
                    underwriting_verdict=r["underwriting_verdict"],
                    rejection_reasons=json.loads(r["rejection_reasons_json"]),
                    cic_debt_group=r["cic_debt_group"], created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_car_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List Basel II CAR audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM car_audits ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                CapitalAdequacyAudit(
                    audit_id=r["audit_id"], institution_name=r["institution_name"],
                    reporting_quarter=r["reporting_quarter"], tier1_capital_vnd=r["tier1_capital_vnd"],
                    tier2_capital_vnd=r["tier2_capital_vnd"], total_own_capital_vnd=r["total_own_capital_vnd"],
                    credit_rwa_vnd=r["credit_rwa_vnd"], market_rwa_vnd=r["market_rwa_vnd"],
                    operational_rwa_vnd=r["operational_rwa_vnd"], total_rwa_vnd=r["total_rwa_vnd"],
                    car_ratio_pct=r["car_ratio_pct"], car_status=r["car_status"],
                    is_compliant=bool(r["is_compliant"]), action_required=r["action_required"],
                    audit_date=r["audit_date"], created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_debt_classifications(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List debt classifications and provisions."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM debt_classifications ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                DebtClassification(
                    record_id=r["record_id"], contract_number=r["contract_number"],
                    borrower_name=r["borrower_name"], overdue_days=r["overdue_days"],
                    debt_group=r["debt_group"], group_name_vi=r["group_name_vi"],
                    outstanding_balance_vnd=r["outstanding_balance_vnd"],
                    deductible_collateral_vnd=r["deductible_collateral_vnd"],
                    specific_provision_rate_pct=r["specific_provision_rate_pct"],
                    specific_provision_vnd=r["specific_provision_vnd"],
                    general_provision_vnd=r["general_provision_vnd"],
                    total_provision_vnd=r["total_provision_vnd"],
                    is_npl=bool(r["is_npl"]), classification_date=r["classification_date"],
                    created_at=r["created_at"],
                ).to_dict()
                for r in rows
            ]

    def list_liquidity_audits(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List liquidity and LDR audits."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM liquidity_audits ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate Vietnamese commercial banking & credit institutions telemetry."""
        with self._get_connection() as conn:
            total_insts = conn.execute("SELECT COUNT(*) FROM banking_licenses").fetchone()[0]
            comm_banks = conn.execute(
                "SELECT COUNT(*) FROM banking_licenses WHERE institution_type = 'COMMERCIAL_BANK'"
            ).fetchone()[0]
            total_loans = conn.execute("SELECT COUNT(*) FROM credit_facilities").fetchone()[0]
            approved_loans = conn.execute(
                "SELECT COUNT(*) FROM credit_facilities WHERE underwriting_verdict = 'APPROVED'"
            ).fetchone()[0]
            total_disbursed_balance = conn.execute(
                "SELECT COALESCE(SUM(loan_amount_vnd), 0.0) FROM credit_facilities WHERE underwriting_verdict = 'APPROVED'"
            ).fetchone()[0]
            total_car_audits = conn.execute("SELECT COUNT(*) FROM car_audits").fetchone()[0]
            compliant_car = conn.execute("SELECT COUNT(*) FROM car_audits WHERE is_compliant = 1").fetchone()[0]
            total_classified_loans = conn.execute("SELECT COUNT(*) FROM debt_classifications").fetchone()[0]
            npl_count = conn.execute("SELECT COUNT(*) FROM debt_classifications WHERE is_npl = 1").fetchone()[0]
            total_outstanding_classified = conn.execute(
                "SELECT COALESCE(SUM(outstanding_balance_vnd), 0.0) FROM debt_classifications"
            ).fetchone()[0]
            total_npl_balance = conn.execute(
                "SELECT COALESCE(SUM(outstanding_balance_vnd), 0.0) FROM debt_classifications WHERE is_npl = 1"
            ).fetchone()[0]
            total_provisions = conn.execute(
                "SELECT COALESCE(SUM(total_provision_vnd), 0.0) FROM debt_classifications"
            ).fetchone()[0]
            npl_ratio_pct = (
                round((total_npl_balance / total_outstanding_classified * 100.0), 2)
                if total_outstanding_classified > 0
                else 0.0
            )
        return {
            "status": "HEALTHY",
            "engine": "BankingEngine",
            "statutory_law": "Luật Các tổ chức tín dụng 2024 (Luật số 32/2024/QH15)",
            "database_path": str(self.db_path),
            "institutions": {"total_licensed": total_insts, "commercial_banks": comm_banks},
            "credit_underwriting": {
                "total_facilities": total_loans,
                "approved_facilities": approved_loans,
                "total_approved_balance_vnd": total_disbursed_balance,
            },
            "basel_ii_car": {
                "total_audits": total_car_audits,
                "compliant_audits_ratio_gte_8pct": compliant_car,
                "statutory_min_car_pct": 8.0,
            },
            "asset_quality_cic": {
                "classified_loans_count": total_classified_loans,
                "npl_loans_count": npl_count,
                "npl_ratio_pct": npl_ratio_pct,
                "total_provisions_vnd": total_provisions,
            },
        }


__all__ = ["QueryTelemetryOpsMixin"]
