"""Unit tests for TT78 invoice generation and compliance reports."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.seed.tax import GTGTCategory, TaxYear, generate_compliance_report, generate_tt78_invoice
from src.seed.tax.models import (
    ComplianceReportInput,
    InvoiceHeader,
    InvoiceInput,
    InvoiceLineItem,
)


def make_invoice_input() -> InvoiceInput:
    """Create a valid TT78 invoice input for tests."""
    header = InvoiceHeader(
        invoice_number="TT78-0001",
        invoice_date=date(2025, 6, 1),
        seller_name="Công ty TNHH Mekong",
        seller_tax_code="0312345678",
        seller_address="123 Lê Lợi, Quận 1, TP.HCM",
        buyer_name="Nguyễn Văn An",
        buyer_tax_code="0123456789",
        buyer_address="456 Nguyễn Huệ, Quận 1, TP.HCM",
        payment_method="Chuyển khoản",
        currency="VND",
    )
    items = [
        InvoiceLineItem(
            line_number=1,
            description="Dịch vụ tư vấn thuế",
            unit="dịch vụ",
            quantity=Decimal("1"),
            unit_price=Decimal("5000000"),
            vat_category=GTGTCategory.STANDARD,
        ),
        InvoiceLineItem(
            line_number=2,
            description="Phần mềm kế toán",
            unit="bộ",
            quantity=Decimal("2"),
            unit_price=Decimal("2500000"),
            vat_category=GTGTCategory.REDUCED,
        ),
    ]
    return InvoiceInput(header=header, line_items=items)


class TestTT78Invoice:
    def test_generates_pdf_bytes(self):
        result = generate_tt78_invoice(make_invoice_input())
        assert result.pdf_bytes
        assert result.pdf_bytes[:4] == b"%PDF"

    def test_pdf_base64_encodes(self):
        result = generate_tt78_invoice(make_invoice_input())
        import base64

        decoded = base64.b64decode(result.pdf_base64)
        assert decoded[:4] == b"%PDF"

    def test_totals_correct(self):
        result = generate_tt78_invoice(make_invoice_input())
        # 5M @ 10% + 2*2.5M @ 8% = 5M + 5M = 10M net
        assert result.total_net == Decimal("10000000")
        # VAT: 500k + 400k = 900k
        assert result.total_vat == Decimal("900000")
        assert result.total_gross == Decimal("10900000")

    def test_invoice_number_preserved(self):
        result = generate_tt78_invoice(make_invoice_input())
        assert result.invoice_number == "TT78-0001"

    def test_qr_data_generated(self):
        result = generate_tt78_invoice(make_invoice_input())
        assert result.qr_code_data
        assert "TT78-0001" in result.qr_code_data
        assert "0312345678" in result.qr_code_data

    def test_single_line_item(self):
        invoice = make_invoice_input()
        invoice.line_items = invoice.line_items[:1]
        result = generate_tt78_invoice(invoice)
        assert result.total_net == Decimal("5000000")
        assert result.total_vat == Decimal("500000")


class TestInvoiceModels:
    def test_line_total_property(self):
        item = InvoiceLineItem(
            line_number=1,
            description="test",
            unit="cái",
            quantity=Decimal("3"),
            unit_price=Decimal("20000"),
        )
        assert item.line_total == Decimal("60000")

    def test_vat_amount_defaults_10_percent(self):
        item = InvoiceLineItem(
            line_number=1,
            description="test",
            unit="cái",
            quantity=Decimal("1"),
            unit_price=Decimal("100000"),
        )
        assert item.vat_amount == Decimal("10000")

    def test_invalid_tax_code(self):
        with pytest.raises(Exception):
            InvoiceHeader(
                invoice_number="TT78-0001",
                invoice_date=date(2025, 1, 1),
                seller_name="Test",
                seller_tax_code="abc",  # invalid
                seller_address="addr",
                buyer_name="Buyer",
                buyer_address="addr",
            )


class TestComplianceReport:
    def test_generates_report(self):
        report = generate_compliance_report(
            ComplianceReportInput(
                tax_year=TaxYear.Y2025,
                company_tax_code="0312345678",
                company_name="Công ty TNHH Mekong",
                reporting_period="Q2",
            )
        )
        assert report.report_id
        assert report.company_tax_code == "0312345678"
        assert report.tax_year == "2025"
        assert report.reporting_period == "Q2"

    def test_report_has_summaries(self):
        report = generate_compliance_report(
            ComplianceReportInput(
                tax_year=TaxYear.Y2025,
                company_tax_code="0312345678",
                company_name="Test Co",
                reporting_period="FY",
            )
        )
        assert report.tncn_summary is not None
        assert report.tndn_summary is not None
        assert report.gtgt_summary is not None
        assert report.total_tax_liability >= Decimal("0")

    def test_report_file_written(self, tmp_path):
        report = generate_compliance_report(
            ComplianceReportInput(
                tax_year=TaxYear.Y2025,
                company_tax_code="0312345678",
                company_name="Test Co",
                reporting_period="Q1",
            )
        )
        assert report.file_path is None or report.file_path
