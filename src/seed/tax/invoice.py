# Invoice Generator - TT78 Compliant PDF Invoice
# Uses ReportLab for PDF generation with digital signature support

from decimal import Decimal
from typing import Optional, List, Any
from pathlib import Path
import base64
import qrcode
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    Table, TableStyle, Paragraph, Spacer,
    Frame, PageTemplate, BaseDocTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .models import (
    InvoiceInput, InvoiceLineItem,
    InvoiceResult, GTGTCategory, TaxYear, quantize_vnd
)
from .calculator import TaxRateLoader


class TT78InvoiceGenerator:
    """Generates TT78-compliant VAT invoices per Vietnam tax law"""

    # Vietnam tax invoice template codes
    TEMPLATE_CODE = "TT78"
    FORM_NUMBER = "01/GTKT"

    # Colors
    HEADER_BG = HexColor("#1B3A5C")
    HEADER_TEXT = white
    TABLE_HEADER_BG = HexColor("#E8EEF4")
    TABLE_HEADER_TEXT = HexColor("#1B3A5C")
    ROW_ALT_BG = HexColor("#F7FAFC")
    BORDER_COLOR = HexColor("#CBD5E0")
    TOTAL_BG = HexColor("#EDF2F7")

    def __init__(self, font_dir: Optional[Path] = None):
        self.font_dir = font_dir or Path(__file__).parent / "fonts"
        self.rate_loader = TaxRateLoader()
        self._register_fonts()

    def _resolve_vat_rate(self, item: InvoiceLineItem) -> Decimal:
        """Resolve the effective VAT rate for a line item.

        Uses the explicit vat_rate when set, otherwise looks up the
        category rate from the loaded tax config for the invoice year.
        """
        if item.vat_rate is not None:
            return item.vat_rate
        rates = self.rate_loader.load_rates(TaxYear(self._invoice_year))
        return self._category_rate(rates, item.vat_category)

    @staticmethod
    def _category_rate(rates: Any, category: GTGTCategory) -> Decimal:
        gtgt = rates.gtgt
        mapping = {
            GTGTCategory.STANDARD: gtgt.standard_rate,
            GTGTCategory.REDUCED: gtgt.reduced_rate,
            GTGTCategory.EXEMPT: gtgt.exempt_rate,
        }
        return Decimal(mapping.get(category, gtgt.standard_rate))

    def _item_vat_amount(self, item: InvoiceLineItem) -> Decimal:
        """VAT amount for a line item using the resolved rate."""
        rate = self._resolve_vat_rate(item)
        return (item.line_total * rate).quantize(Decimal('1'))

    def _register_fonts(self) -> None:
        """Register Vietnamese-compatible fonts"""
        try:
            # Try to register DejaVu Sans for Unicode support
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial.ttf",
            ]

            for fp in font_paths:
                path = Path(fp)
                if path.exists():
                    if "DejaVuSans" in fp and "Bold" not in fp:
                        pdfmetrics.registerFont(TTFont("DejaVu", str(path)))
                    elif "DejaVuSans-Bold" in fp:
                        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(path)))
                    return
        except Exception:
            pass  # Fall back to built-in fonts

    def generate(self, invoice: InvoiceInput) -> InvoiceResult:
        """Generate TT78 PDF invoice"""
        buffer = BytesIO()
        self._invoice_year = str(invoice.header.invoice_date.year)

        # Create document
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )

        # Register a single page frame (required for BaseDocTemplate)
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="main",
        )
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

        # Build story
        story = self._build_story(invoice)

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

        # Calculate totals
        total_net = Decimal(sum(item.line_total for item in invoice.line_items))
        total_vat = Decimal(sum(self._item_vat_amount(item) for item in invoice.line_items))
        total_gross = total_net + total_vat

        # Generate QR code data for e-invoice
        qr_data = self._generate_qr_data(invoice, total_net, total_vat, total_gross)

        return InvoiceResult(
            invoice_number=invoice.header.invoice_number,
            pdf_bytes=pdf_bytes,
            pdf_base64=pdf_base64,
            total_net=quantize_vnd(total_net),
            total_vat=quantize_vnd(total_vat),
            total_gross=quantize_vnd(total_gross),
            qr_code_data=qr_data
        )

    def _build_story(self, invoice: InvoiceInput) -> List:
        """Build the PDF story elements"""
        story = []

        # Header section
        story.extend(self._build_header(invoice))
        story.append(Spacer(1, 5*mm))

        # Seller/Buyer info
        story.extend(self._build_parties(invoice))
        story.append(Spacer(1, 5*mm))

        # Line items table
        story.extend(self._build_items_table(invoice))
        story.append(Spacer(1, 5*mm))

        # Totals
        story.extend(self._build_totals(invoice))
        story.append(Spacer(1, 10*mm))

        # Payment info
        story.extend(self._build_payment_info(invoice))
        story.append(Spacer(1, 10*mm))

        # Signatures
        story.extend(self._build_signatures(invoice))

        # QR Code at bottom
        story.append(Spacer(1, 10*mm))
        story.extend(self._build_qr_section(invoice))

        return story

    def _build_header(self, invoice: InvoiceInput) -> List:
        """Build invoice header"""
        elements = []

        # Title row
        title_style = ParagraphStyle(
            'InvoiceTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=self.HEADER_TEXT,
            alignment=TA_CENTER,
            spaceAfter=2,
        )

        subtitle_style = ParagraphStyle(
            'InvoiceSubtitle',
            fontName='Helvetica',
            fontSize=10,
            textColor=self.HEADER_TEXT,
            alignment=TA_CENTER,
        )

        header_data = [
            [Paragraph("HÓA ĐƠN GIÁ TRỊ GIA TĂNG", title_style)],
            [Paragraph(f"Mẫu số {self.FORM_NUMBER} - Ký hiệu: {self.TEMPLATE_CODE}", subtitle_style)],
        ]

        header_table = Table(header_data, colWidths=[180*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.HEADER_BG),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(header_table)

        # Invoice number and date
        info_style = ParagraphStyle(
            'InfoStyle',
            fontName='Helvetica',
            fontSize=9,
            textColor=black,
            alignment=TA_LEFT,
        )

        info_data = [
            [Paragraph(f"Số: <b>{invoice.header.invoice_number}</b>", info_style),
             Paragraph(f"Ngày: <b>{invoice.header.invoice_date.strftime('%d/%m/%Y')}</b>", info_style)],
        ]

        info_table = Table(info_data, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)

        return elements

    def _build_parties(self, invoice: InvoiceInput) -> List:
        """Build seller and buyer information"""
        elements = []

        label_style = ParagraphStyle(
            'LabelStyle',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=black,
        )

        value_style = ParagraphStyle(
            'ValueStyle',
            fontName='Helvetica',
            fontSize=9,
            textColor=black,
        )

        # Seller
        seller_data = [
            [Paragraph("NGƯỜI BÁN", label_style), Paragraph("NGƯỜI MUA", label_style)],
            [Paragraph(invoice.header.seller_name, value_style), Paragraph(invoice.header.buyer_name, value_style)],
            [Paragraph(f"Mã số thuế: {invoice.header.seller_tax_code}", value_style),
             Paragraph(f"Mã số thuế: {invoice.header.buyer_tax_code or 'Chưa cung cấp'}", value_style)],
            [Paragraph(f"Địa chỉ: {invoice.header.seller_address}", value_style),
             Paragraph(f"Địa chỉ: {invoice.header.buyer_address}", value_style)],
        ]

        if invoice.header.seller_bank_account:
            seller_data.append([
                Paragraph(f"TK: {invoice.header.seller_bank_account} - {invoice.header.seller_bank_name or ''}", value_style),
                Paragraph(f"TK: {invoice.header.buyer_bank_account or ''} - {invoice.header.buyer_bank_name or ''}", value_style),
            ])

        parties_table = Table(seller_data, colWidths=[90*mm, 90*mm])
        parties_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, self.BORDER_COLOR),
        ]))
        elements.append(parties_table)

        return elements

    def _build_items_table(self, invoice: InvoiceInput) -> List:
        """Build line items table"""
        elements = []

        # Headers
        headers = [
            "STT", "Tên hàng hóa, dịch vụ", "ĐVT", "Số lượng",
            "Đơn giá", "Thuế suất", "Thành tiền", "Tiền thuế GTGT"
        ]

        # Styles
        cell_style = ParagraphStyle(
            'TableCell',
            fontName='Helvetica',
            fontSize=8,
            textColor=black,
            alignment=TA_LEFT,
        )

        cell_style_center = ParagraphStyle(
            'TableCellCenter',
            fontName='Helvetica',
            fontSize=8,
            textColor=black,
            alignment=TA_CENTER,
        )

        cell_style_right = ParagraphStyle(
            'TableCellRight',
            fontName='Helvetica',
            fontSize=8,
            textColor=black,
            alignment=TA_RIGHT,
        )

        # Build rows
        table_data = [headers]
        for idx, item in enumerate(invoice.line_items, 1):
            vat_rate = self._resolve_vat_rate(item)
            vat_rate_pct = f"{vat_rate * 100:.0f}%"
            row = [
                Paragraph(str(idx), cell_style_center),
                Paragraph(item.description, cell_style),
                Paragraph(item.unit, cell_style_center),
                Paragraph(f"{item.quantity:,.0f}".replace(',', '.'), cell_style_center),
                Paragraph(f"{item.unit_price:,.0f}".replace(',', '.'), cell_style_right),
                Paragraph(vat_rate_pct, cell_style_center),
                Paragraph(f"{item.line_total:,.0f}".replace(',', '.'), cell_style_right),
                Paragraph(f"{self._item_vat_amount(item):,.0f}".replace(',', '.'), cell_style_right),
            ]
            table_data.append(row)

        # Column widths
        col_widths = [10*mm, 50*mm, 15*mm, 20*mm, 25*mm, 18*mm, 27*mm, 25*mm]

        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Table style
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), self.TABLE_HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.TABLE_HEADER_TEXT),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]

        # Alternate row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), self.ROW_ALT_BG))

        items_table.setStyle(TableStyle(style_cmds))
        elements.append(items_table)

        return elements

    def _build_totals(self, invoice: InvoiceInput) -> List:
        """Build totals section"""
        elements = []

        total_net = Decimal(sum(item.line_total for item in invoice.line_items))
        total_vat = Decimal(sum(self._item_vat_amount(item) for item in invoice.line_items))
        total_gross = total_net + total_vat

        total_style = ParagraphStyle(
            'TotalStyle',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=black,
            alignment=TA_RIGHT,
        )

        label_style = ParagraphStyle(
            'TotalLabel',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=black,
            alignment=TA_LEFT,
        )

        totals_data = [
            [Paragraph("Cộng tiền hàng hóa, dịch vụ (chưa có thuế GTGT):", label_style),
             Paragraph(f"{total_net:,.0f} VND".replace(',', '.'), total_style)],
            [Paragraph("Tiền thuế GTGT:", label_style),
             Paragraph(f"{total_vat:,.0f} VND".replace(',', '.'), total_style)],
            [Paragraph("Tổng cộng tiền thanh toán (đã có thuế GTGT):", label_style),
             Paragraph(f"{total_gross:,.0f} VND".replace(',', '.'), total_style)],
        ]

        totals_table = Table(totals_data, colWidths=[120*mm, 60*mm])
        totals_table.setStyle(TableStyle([
            ('BACKGROUND', (0, -1), (-1, -1), self.TOTAL_BG),
            ('LINEABOVE', (0, -1), (-1, -1), 2, self.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (1, 0), (1, -1), 10),
        ]))
        elements.append(totals_table)

        # Amount in words
        words_style = ParagraphStyle(
            'WordsStyle',
            fontName='Helvetica-Oblique',
            fontSize=9,
            textColor=grey,
            alignment=TA_LEFT,
        )
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(
            f"Số tiền viết bằng chữ: <i>{self._number_to_words_vn(total_gross)}</i>",
            words_style
        ))

        return elements

    def _build_payment_info(self, invoice: InvoiceInput) -> List:
        """Build payment information"""
        elements = []

        info_style = ParagraphStyle(
            'PaymentInfo',
            fontName='Helvetica',
            fontSize=9,
            textColor=black,
        )

        payment_data = [
            [Paragraph(f"Hình thức thanh toán: {invoice.header.payment_method}", info_style)],
            [Paragraph(f"Loại tiền: {invoice.header.currency} - Tỷ giá: {invoice.header.exchange_rate}", info_style)],
        ]

        if invoice.notes:
            payment_data.append([Paragraph(f"Ghi chú: {invoice.notes}", info_style)])

        payment_table = Table(payment_data, colWidths=[180*mm])
        payment_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(payment_table)

        return elements

    def _build_signatures(self, invoice: InvoiceInput) -> List:
        """Build signature section"""
        elements = []

        sig_style = ParagraphStyle(
            'SigStyle',
            fontName='Helvetica',
            fontSize=9,
            textColor=black,
            alignment=TA_CENTER,
        )

        sig_label_style = ParagraphStyle(
            'SigLabelStyle',
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=black,
            alignment=TA_CENTER,
        )

        sig_data = [
            [Paragraph("Người lập hóa đơn", sig_label_style),
             Paragraph("Người mua hàng", sig_label_style),
             Paragraph("Người bán hàng", sig_label_style)],
            [Paragraph("(Ký, ghi rõ họ tên)", sig_style),
             Paragraph("(Ký, ghi rõ họ tên, đóng dấu)", sig_style),
             Paragraph("(Ký, ghi rõ họ tên, đóng dấu)", sig_style)],
        ]

        sig_table = Table(sig_data, colWidths=[60*mm, 60*mm, 60*mm])
        sig_table.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(sig_table)

        return elements

    def _build_qr_section(self, invoice: InvoiceInput) -> List:
        """Build QR code section for e-invoice"""
        elements = []

        total_net = Decimal(sum(item.line_total for item in invoice.line_items))
        total_vat = Decimal(sum(self._item_vat_amount(item) for item in invoice.line_items))
        qr_data = self._generate_qr_data(invoice, total_net, total_vat, total_net + total_vat)

        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=3,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to reportlab image
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        from reportlab.platypus import Image
        qr_image = Image(img_buffer, width=30*mm, height=30*mm)

        qr_label_style = ParagraphStyle(
            'QrLabel',
            fontName='Helvetica',
            fontSize=8,
            textColor=grey,
            alignment=TA_CENTER,
        )

        qr_table = Table([
            [qr_image],
            [Paragraph("Mã QR tra cứu hóa đơn điện tử", qr_label_style)]
        ], colWidths=[30*mm])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(qr_table)

        return elements

    def _generate_qr_data(self, invoice: InvoiceInput, total_net: Decimal, total_vat: Decimal, total_gross: Decimal) -> str:
        """Generate QR code data string per Vietnam e-invoice standard"""
        # Format: standard Vietnam e-invoice QR format
        parts = [
            invoice.header.invoice_number,
            invoice.header.invoice_date.strftime("%Y%m%d"),
            invoice.header.seller_tax_code,
            invoice.header.buyer_tax_code or "",
            f"{total_net:,.0f}".replace(',', ''),
            f"{total_vat:,.0f}".replace(',', ''),
            f"{total_gross:,.0f}".replace(',', ''),
            invoice.header.currency,
        ]
        return "|".join(parts)

    def _number_to_words_vn(self, amount: Decimal) -> str:
        """Convert number to Vietnamese words"""
        # Simplified implementation - in production use a proper library
        units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
        scales = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ"]

        def three_digits(n: int) -> str:
            if n == 0:
                return ""
            hundreds = n // 100
            tens = (n % 100) // 10
            ones = n % 10
            parts = []
            if hundreds:
                parts.append(units[hundreds] + " trăm")
            if tens == 1:
                parts.append("mười")
            elif tens > 1:
                parts.append(units[tens] + " mươi")
            if ones:
                if tens == 0 and hundreds:
                    parts.append("lẻ " + units[ones])
                elif ones == 5 and tens:
                    parts.append("lăm")
                else:
                    parts.append(units[ones])
            return " ".join(parts)

        num = int(amount)
        if num == 0:
            return "Không đồng"

        parts = []
        scale_idx = 0
        while num > 0:
            chunk = num % 1000
            if chunk:
                chunk_words = three_digits(chunk)
                if chunk_words:
                    if scales[scale_idx]:
                        chunk_words += " " + scales[scale_idx]
                    parts.append(chunk_words)
            num //= 1000
            scale_idx += 1

        result = " ".join(reversed(parts))
        return result.capitalize() + " đồng"


# Convenience function
def generate_tt78_invoice(invoice: InvoiceInput) -> InvoiceResult:
    """Generate TT78 invoice"""
    generator = TT78InvoiceGenerator()
    return generator.generate(invoice)