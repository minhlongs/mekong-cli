"""
Kế Toán VN — Hóa đơn điện tử, bút toán VAS, MISA export.
Follows: Nghị định 123/2020/NĐ-CP, TT78/2021, VAS.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.dom.minidom


VAT_RATES = {10: Decimal("0.10"), 8: Decimal("0.08"), 5: Decimal("0.05"), 0: Decimal("0")}

# VAS account mapping (TK — Tài Khoản)
VAS_ACCOUNTS = {
    "receivable": "131",
    "revenue": "511",
    "vat_output": "3331",
    "cash": "111",
    "bank": "112",
}

DISCLAIMER = "Tư vấn AI — không thay thế kế toán có chứng chỉ hành nghề."


@dataclass
class InvoiceItem:
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate: int = 10

    @property
    def subtotal(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    @property
    def vat_amount(self) -> Decimal:
        return (self.subtotal * VAT_RATES[self.vat_rate]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.vat_amount


@dataclass
class Invoice:
    seller_name: str
    seller_tax_code: str
    buyer_name: str
    buyer_tax_code: str = ""
    invoice_date: date = field(default_factory=date.today)
    items: list[InvoiceItem] = field(default_factory=list)
    invoice_series: str = "C25TAA"  # Ký hiệu mẫu hóa đơn
    invoice_number: int = 1

    @property
    def subtotal(self) -> Decimal:
        return sum(item.subtotal for item in self.items)

    @property
    def total_vat(self) -> Decimal:
        return sum(item.vat_amount for item in self.items)

    @property
    def total_amount(self) -> Decimal:
        return self.subtotal + self.total_vat

    def format_vnd(self, amount: Decimal) -> str:
        return f"{int(amount):,} đ".replace(",", ".")

    def to_xml(self) -> str:
        """Tạo XML theo schema TT78/2021."""
        root = Element("HDon")

        # Thông tin chung
        tt_chung = SubElement(root, "TTChung")
        SubElement(tt_chung, "KHMSHDon").text = "1"
        SubElement(tt_chung, "KHHDon").text = self.invoice_series
        SubElement(tt_chung, "SHDon").text = str(self.invoice_number)
        SubElement(tt_chung, "NLap").text = self.invoice_date.strftime("%Y-%m-%d")
        SubElement(tt_chung, "DVTTe").text = "VND"
        SubElement(tt_chung, "TGia").text = "1"

        # Nội dung hóa đơn
        nd_hdon = SubElement(root, "NDHDon")

        # Người bán
        nb = SubElement(nd_hdon, "NBan")
        SubElement(nb, "Ten").text = self.seller_name
        SubElement(nb, "MST").text = self.seller_tax_code

        # Người mua
        nm = SubElement(nd_hdon, "NMua")
        SubElement(nm, "Ten").text = self.buyer_name
        if self.buyer_tax_code:
            SubElement(nm, "MST").text = self.buyer_tax_code

        # Danh sách hàng hóa
        ds_hhhd = SubElement(nd_hdon, "DSHHDVu")
        for i, item in enumerate(self.items, 1):
            hhhd = SubElement(ds_hhhd, "HHDVu")
            SubElement(hhhd, "STT").text = str(i)
            SubElement(hhhd, "MHang").text = f"SP{i:03d}"
            SubElement(hhhd, "THHDVu").text = item.description
            SubElement(hhhd, "DVTinh").text = "Cái"
            SubElement(hhhd, "SLuong").text = str(item.quantity)
            SubElement(hhhd, "DGia").text = str(item.unit_price)
            SubElement(hhhd, "ThTien").text = str(item.subtotal)
            SubElement(hhhd, "Tsuat").text = f"{item.vat_rate}%"
            SubElement(hhhd, "TThue").text = str(item.vat_amount)

        # Tổng tiền
        tt_toan = SubElement(nd_hdon, "TToan")
        SubElement(tt_toan, "TgTCThue").text = str(self.subtotal)
        SubElement(tt_toan, "TgTThue").text = str(self.total_vat)
        SubElement(tt_toan, "TgTTTBSo").text = str(self.total_amount)

        xml_str = tostring(root, encoding="unicode")
        return xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

    def to_journal_entry(self) -> dict:
        """Bút toán kế toán VAS."""
        return {
            "date": self.invoice_date.isoformat(),
            "description": f"Bán hàng cho {self.buyer_name}",
            "entries": [
                {"account": VAS_ACCOUNTS["receivable"], "debit": str(self.total_amount), "credit": "0",
                 "note": "Phải thu khách hàng"},
                {"account": VAS_ACCOUNTS["revenue"], "debit": "0", "credit": str(self.subtotal),
                 "note": "Doanh thu bán hàng"},
                {"account": VAS_ACCOUNTS["vat_output"], "debit": "0", "credit": str(self.total_vat),
                 "note": "Thuế GTGT phải nộp"},
            ],
            "disclaimer": DISCLAIMER,
        }

    def to_summary(self) -> str:
        """Human-readable invoice summary."""
        lines = [
            f"=== HÓA ĐƠN ĐIỆN TỬ ===",
            f"Số: {self.invoice_series}{self.invoice_number:06d}",
            f"Ngày: {self.invoice_date.strftime('%d/%m/%Y')}",
            f"Người bán: {self.seller_name} (MST: {self.seller_tax_code})",
            f"Người mua: {self.buyer_name}",
            "",
            "HÀNG HÓA/DỊCH VỤ:",
        ]
        for item in self.items:
            lines.append(f"  - {item.description}: {self.format_vnd(item.unit_price)} × {item.quantity} = {self.format_vnd(item.subtotal)}")
        lines += [
            "",
            f"Tổng trước thuế: {self.format_vnd(self.subtotal)}",
            f"Thuế GTGT:       {self.format_vnd(self.total_vat)}",
            f"TỔNG THANH TOÁN: {self.format_vnd(self.total_amount)}",
            "",
            f"BÚT TOÁN: Nợ TK {VAS_ACCOUNTS['receivable']} / Có TK {VAS_ACCOUNTS['revenue']}, {VAS_ACCOUNTS['vat_output']}",
            "",
            f"⚠️  {DISCLAIMER}",
        ]
        return "\n".join(lines)


def create_invoice(
    amount: int,
    vat_rate: int,
    buyer: str,
    seller: str = "Doanh Nghiệp",
    seller_tax_code: str = "0000000000",
    description: str = "Hàng hóa/Dịch vụ",
) -> Invoice:
    """Convenience function để tạo hóa đơn đơn giản."""
    item = InvoiceItem(
        description=description,
        quantity=Decimal("1"),
        unit_price=Decimal(str(amount)),
        vat_rate=vat_rate,
    )
    return Invoice(
        seller_name=seller,
        seller_tax_code=seller_tax_code,
        buyer_name=buyer,
        items=[item],
    )
