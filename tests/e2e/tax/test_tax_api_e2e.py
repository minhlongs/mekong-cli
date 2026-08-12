"""End-to-end tests for the Tax & Accounting API funnel."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.tax_routes import router


@pytest.fixture
def client() -> TestClient:
    """Build a TestClient with only the tax router mounted."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestTaxHealthE2E:
    def test_health_returns_healthy(self, client: TestClient):
        resp = client.get("/api/v1/tax/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["service"] == "tax-engine"


class TestTNCNE2E:
    def test_calculate_tncn(self, client: TestClient):
        resp = client.post("/api/v1/tax/tncn", json={"gross_income": "15000000"})
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["tax_payable"]) == Decimal("200000")
        assert Decimal(body["net_income"]) == Decimal("14800000")

    def test_calculate_tncn_with_dependents(self, client: TestClient):
        resp = client.post(
            "/api/v1/tax/tncn",
            json={"gross_income": "20000000", "dependents": 1},
        )
        assert resp.status_code == 200
        body = resp.json()
        # 20M - 11M - 4.4M = 4.6M @ 5% = 230k
        assert Decimal(body["tax_payable"]) == Decimal("230000")

    def test_invalid_tncn_input(self, client: TestClient):
        resp = client.post("/api/v1/tax/tncn", json={"gross_income": "-5000"})
        assert resp.status_code == 400

    def test_invalid_tax_year(self, client: TestClient):
        resp = client.post(
            "/api/v1/tax/tncn",
            json={"gross_income": "15000000", "tax_year": "1999"},
        )
        assert resp.status_code == 400


class TestTNDNE2E:
    def test_calculate_tndn_standard(self, client: TestClient):
        resp = client.post("/api/v1/tax/tndn", json={"taxable_income": "100000000"})
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["applicable_rate"]) == Decimal("0.20")
        assert Decimal(body["tax_payable"]) == Decimal("20000000")

    def test_calculate_tndn_sme_preferential(self, client: TestClient):
        resp = client.post(
            "/api/v1/tax/tndn",
            json={"taxable_income": "100000000", "preferential_type": "sme", "preferential_years": 3},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["applicable_rate"]) == Decimal("0.17")
        assert Decimal(body["tax_payable"]) == Decimal("17000000")


class TestGTGTE2E:
    def test_calculate_gtgt_standard(self, client: TestClient):
        resp = client.post("/api/v1/tax/gtgt", json={"net_amount": "10000000"})
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["vat_amount"]) == Decimal("1000000")
        assert Decimal(body["gross_amount"]) == Decimal("11000000")

    def test_calculate_gtgt_reduced(self, client: TestClient):
        resp = client.post(
            "/api/v1/tax/gtgt",
            json={"net_amount": "10000000", "category": "reduced"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["vat_amount"]) == Decimal("800000")

    def test_calculate_gtgt_export_exempt(self, client: TestClient):
        resp = client.post(
            "/api/v1/tax/gtgt",
            json={"net_amount": "10000000", "is_export": True},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["vat_amount"]) == Decimal("0")


class TestRatesE2E:
    def test_get_rates_2025(self, client: TestClient):
        resp = client.get("/api/v1/tax/rates/2025")
        assert resp.status_code == 200
        body = resp.json()
        assert body["version"] == "2025"
        assert Decimal(body["tndn"]["standard_rate"]) == Decimal("0.20")

    def test_get_rates_invalid_year(self, client: TestClient):
        resp = client.get("/api/v1/tax/rates/1999")
        assert resp.status_code == 404


class TestInvoiceE2E:
    INVOICE_BODY = {
        "header": {
            "invoice_number": "TT78-0001",
            "invoice_date": "2025-06-01",
            "seller_name": "Công ty TNHH Mekong",
            "seller_tax_code": "0312345678",
            "seller_address": "123 Lê Lợi, Quận 1, TP.HCM",
            "buyer_name": "Nguyễn Văn An",
            "buyer_address": "456 Nguyễn Huệ, Quận 1, TP.HCM",
        },
        "line_items": [
            {
                "description": "Dịch vụ tư vấn thuế",
                "unit": "dịch vụ",
                "quantity": "1",
                "unit_price": "5000000",
                "vat_category": "standard",
            },
            {
                "description": "Phần mềm kế toán",
                "unit": "bộ",
                "quantity": "2",
                "unit_price": "2500000",
                "vat_category": "reduced",
            },
        ],
    }

    def test_generates_invoice_pdf(self, client: TestClient):
        resp = client.post("/api/v1/tax/invoice/tt78", json=self.INVOICE_BODY)
        assert resp.status_code == 200
        body = resp.json()
        assert body["invoice_number"] == "TT78-0001"
        assert body["pdf_base64"]

    def test_invoice_totals_correct(self, client: TestClient):
        resp = client.post("/api/v1/tax/invoice/tt78", json=self.INVOICE_BODY)
        assert resp.status_code == 200
        body = resp.json()
        assert Decimal(body["total_net"]) == Decimal("10000000")
        assert Decimal(body["total_vat"]) == Decimal("900000")
        assert Decimal(body["total_gross"]) == Decimal("10900000")

    def test_invoice_rejects_empty_line_items(self, client: TestClient):
        body = dict(self.INVOICE_BODY)
        body["line_items"] = []
        resp = client.post("/api/v1/tax/invoice/tt78", json=body)
        assert resp.status_code == 422

    def test_invoice_rejects_invalid_tax_code(self, client: TestClient):
        body = dict(self.INVOICE_BODY)
        body["header"] = {**body["header"], "seller_tax_code": "abc"}
        resp = client.post("/api/v1/tax/invoice/tt78", json=body)
        assert resp.status_code == 422


class TestComplianceE2E:
    def test_generates_compliance_report(self, client: TestClient):
        resp = client.post(
            "/api/v1/tax/compliance",
            json={
                "tax_year": "2025",
                "company_tax_code": "0312345678",
                "company_name": "Công ty TNHH Mekong",
                "reporting_period": "Q2",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["report_id"]
        assert body["tax_year"] == "2025"
        assert body["company_tax_code"] == "0312345678"
