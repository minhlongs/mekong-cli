"""
End-to-end test cho /ke-toan: hóa đơn → XML TT78/2021 → bút toán VAS → summary.
Validates hành lang số liệu trước khi đưa pilot users sử dụng.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest

from src.commands.ke_toan import (
    Invoice,
    InvoiceItem,
    VAS_ACCOUNTS,
    VAT_RATES,
    create_invoice,
)


@pytest.fixture
def simple_invoice() -> Invoice:
    return create_invoice(
        amount=5_000_000,
        vat_rate=10,
        buyer="Nguyễn Văn A",
        seller="Cửa Hàng ABC",
        seller_tax_code="0123456789",
        description="Hàng hóa tiêu dùng",
    )


@pytest.fixture
def multi_item_invoice() -> Invoice:
    return Invoice(
        seller_name="Bakery Sài Gòn",
        seller_tax_code="0312345678",
        buyer_name="Khách bàn 3",
        invoice_date=date(2026, 5, 17),
        items=[
            InvoiceItem("Croissant bơ", Decimal("3"), Decimal("45000"), vat_rate=8),
            InvoiceItem("Cà phê đen", Decimal("2"), Decimal("35000"), vat_rate=10),
            InvoiceItem("Bánh mì pate", Decimal("1"), Decimal("25000"), vat_rate=5),
        ],
    )


class TestInvoiceArithmetic:
    """Số tiền phải khớp đến từng đồng — không được sai do floating point."""

    def test_simple_amount_5m_vat_10(self, simple_invoice: Invoice) -> None:
        assert simple_invoice.subtotal == Decimal("5000000")
        assert simple_invoice.total_vat == Decimal("500000")
        assert simple_invoice.total_amount == Decimal("5500000")

    def test_vat_rate_0_no_tax(self) -> None:
        inv = create_invoice(amount=2_000_000, vat_rate=0, buyer="X")
        assert inv.total_vat == Decimal("0")
        assert inv.total_amount == Decimal("2000000")

    def test_vat_rate_8_promotional(self) -> None:
        """VAT 8% theo NĐ 15/2022 (giảm thuế khôi phục kinh tế)."""
        inv = create_invoice(amount=10_000_000, vat_rate=8, buyer="Y")
        assert inv.total_vat == Decimal("800000")
        assert inv.total_amount == Decimal("10800000")

    def test_multi_item_aggregation(self, multi_item_invoice: Invoice) -> None:
        # 3×45000=135K + 2×35000=70K + 1×25000=25K = 230K
        assert multi_item_invoice.subtotal == Decimal("230000")
        # VAT: 135K×8% + 70K×10% + 25K×5% = 10800 + 7000 + 1250 = 19050
        assert multi_item_invoice.total_vat == Decimal("19050")
        assert multi_item_invoice.total_amount == Decimal("249050")

    def test_all_supported_vat_rates_have_decimals(self) -> None:
        assert set(VAT_RATES.keys()) == {0, 5, 8, 10}


class TestInvoiceXmlTt78:
    """XML phải tuân schema TT78/2021 cho hóa đơn điện tử."""

    def test_xml_parses_as_valid_xml(self, simple_invoice: Invoice) -> None:
        xml_str = simple_invoice.to_xml()
        # Strip prolog, parse root
        root = ET.fromstring(xml_str.split("?>", 1)[-1])
        assert root.tag == "HDon"

    def test_xml_contains_required_tt78_blocks(self, simple_invoice: Invoice) -> None:
        xml_str = simple_invoice.to_xml()
        # TT78/2021 yêu cầu các block sau:
        for required_tag in ("TTChung", "NDHDon", "NBan", "NMua", "DSHHDVu", "TToan"):
            assert f"<{required_tag}>" in xml_str, f"Missing TT78 block: {required_tag}"

    def test_xml_seller_tax_code_present(self, simple_invoice: Invoice) -> None:
        xml_str = simple_invoice.to_xml()
        assert "<MST>0123456789</MST>" in xml_str

    def test_xml_currency_is_vnd(self, simple_invoice: Invoice) -> None:
        xml_str = simple_invoice.to_xml()
        assert "<DVTTe>VND</DVTTe>" in xml_str

    def test_xml_total_matches_arithmetic(self, multi_item_invoice: Invoice) -> None:
        xml_str = multi_item_invoice.to_xml()
        assert "<TgTCThue>230000</TgTCThue>" in xml_str
        assert "<TgTThue>19050</TgTThue>" in xml_str
        assert "<TgTTTBSo>249050</TgTTTBSo>" in xml_str

    def test_xml_item_count_matches(self, multi_item_invoice: Invoice) -> None:
        xml_str = multi_item_invoice.to_xml()
        # 3 items → 3 <HHDVu> blocks
        assert xml_str.count("<HHDVu>") == 3


class TestVasJournalEntry:
    """Bút toán phải đúng Chuẩn Mực Kế Toán VN (VAS)."""

    def test_journal_balanced_debit_credit(self, simple_invoice: Invoice) -> None:
        entry = simple_invoice.to_journal_entry()
        total_debit = sum(Decimal(e["debit"]) for e in entry["entries"])
        total_credit = sum(Decimal(e["credit"]) for e in entry["entries"])
        assert total_debit == total_credit, "Bút toán phải cân — Nợ = Có"

    def test_journal_uses_tk_131_receivable(self, simple_invoice: Invoice) -> None:
        entry = simple_invoice.to_journal_entry()
        accounts = {e["account"] for e in entry["entries"]}
        assert VAS_ACCOUNTS["receivable"] in accounts  # TK 131
        assert VAS_ACCOUNTS["revenue"] in accounts  # TK 511
        assert VAS_ACCOUNTS["vat_output"] in accounts  # TK 3331

    def test_journal_includes_disclaimer(self, simple_invoice: Invoice) -> None:
        entry = simple_invoice.to_journal_entry()
        assert "Tư vấn AI" in entry["disclaimer"]
        assert "chứng chỉ" in entry["disclaimer"]


class TestSummaryReadability:
    """Summary phải dễ đọc cho user non-kỹ-thuật."""

    def test_summary_contains_vnd_format(self, simple_invoice: Invoice) -> None:
        out = simple_invoice.to_summary()
        # 5.500.000 đ (dấu chấm phân cách hàng nghìn theo chuẩn VN)
        assert "5.500.000 đ" in out
        assert "đ" in out  # ký hiệu VND

    def test_summary_includes_buyer_and_seller(self, simple_invoice: Invoice) -> None:
        out = simple_invoice.to_summary()
        assert "Nguyễn Văn A" in out
        assert "Cửa Hàng ABC" in out

    def test_summary_warns_about_ai_advisory(self, simple_invoice: Invoice) -> None:
        out = simple_invoice.to_summary()
        assert "Tư vấn AI" in out


class TestEdgeCases:
    """Phòng trường hợp pilot user nhập dữ liệu lạ."""

    def test_unicode_buyer_name_preserved(self) -> None:
        inv = create_invoice(amount=100_000, vat_rate=10, buyer="Trần Thị Hằng Nga")
        assert inv.buyer_name == "Trần Thị Hằng Nga"
        assert "Trần Thị Hằng Nga" in inv.to_summary()

    def test_large_amount_billion_vnd(self) -> None:
        inv = create_invoice(amount=2_000_000_000, vat_rate=10, buyer="Công Ty Lớn")
        assert inv.total_amount == Decimal("2200000000")
        assert "2.200.000.000 đ" in inv.to_summary()

    def test_invalid_vat_rate_raises(self) -> None:
        with pytest.raises(KeyError):
            inv = Invoice(
                seller_name="X", seller_tax_code="0",
                buyer_name="Y",
                items=[InvoiceItem("test", Decimal("1"), Decimal("100"), vat_rate=15)],
            )
            _ = inv.total_vat  # trigger lookup
