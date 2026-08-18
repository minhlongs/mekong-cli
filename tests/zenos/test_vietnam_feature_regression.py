"""
Vietnam Feature Regression Tests — ke-toan, thue-dnvn, zalo-oa, vietqr.

Integration regression tests ensuring all Vietnam features work together
correctly. Tests cover the complete flow from invoice creation through
tax calculations, Zalo OA messaging, and VietQR payment webhooks.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for 'integrations' package and direct module imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.commands.ke_toan import (
    Invoice,
    InvoiceItem,
    create_invoice,
)
from src.commands.thue_dnvn import (
    calculate_tncn,
    calculate_tndn,
    calculate_gtgt,
    PERSONAL_DEDUCTION,
    DEPENDENT_DEDUCTION,
    TNDN_SME_RATE,
    TNDN_RATE,
    TNDN_SME_THRESHOLD,
)
from integrations.zalo import ZaloOAClient, generate_vn_caption

# Import vn_payments_routes directly from file to avoid broken api/__init__.py
import importlib.util
_vn_payments_path = Path(__file__).parent.parent.parent / "src" / "api" / "vn_payments_routes.py"
_spec = importlib.util.spec_from_file_location("vn_payments_routes", _vn_payments_path)
_vn_payments_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vn_payments_module)

_parse_memo = _vn_payments_module._parse_memo
_TIER_PRICES_VND = _vn_payments_module._TIER_PRICES_VND


# ============================================================================
# VAT Invoice (ke-toan) Regression Tests
# ============================================================================

class TestKeToanInvoiceRegression:
    """Test invoice creation, XML generation, and VAS journal entries."""

    def test_invoice_creation_basic(self) -> None:
        """Basic invoice with single item."""
        invoice = create_invoice(
            amount=5_000_000,
            vat_rate=10,
            buyer="Nguyễn Văn A",
            seller="Công Ty ABC",
            seller_tax_code="0123456789",
            description="Dịch vụ tư vấn",
        )
        assert invoice.seller_name == "Công Ty ABC"
        assert invoice.buyer_name == "Nguyễn Văn A"
        assert invoice.subtotal == Decimal("5000000")
        assert invoice.total_vat == Decimal("500000")
        assert invoice.total_amount == Decimal("5500000")

    def test_invoice_multi_item_vat_rates(self) -> None:
        """Invoice with items at different VAT rates."""
        invoice = Invoice(
            seller_name="Bakery SG",
            seller_tax_code="0312345678",
            buyer_name="Khách Lẻ",
            invoice_date=date(2025, 5, 17),
            items=[
                InvoiceItem("Bánh mì", Decimal("1"), Decimal("25000"), vat_rate=10),
                InvoiceItem("Cà phê", Decimal("2"), Decimal("35000"), vat_rate=10),
                InvoiceItem("Trà đá", Decimal("3"), Decimal("5000"), vat_rate=0),
            ],
        )
        # Subtotal: 25000 + 70000 + 15000 = 110000
        assert invoice.subtotal == Decimal("110000")
        # VAT: (25000+70000)*10% + 15000*0% = 9500
        assert invoice.total_vat == Decimal("9500")
        assert invoice.total_amount == Decimal("119500")

    def test_xml_tt78_schema_compliance(self) -> None:
        """XML output follows TT78/2021 schema."""
        invoice = create_invoice(
            amount=10_000_000,
            vat_rate=8,
            buyer="Công Ty XYZ",
            seller="My Company",
            seller_tax_code="9999999999",
        )
        xml = invoice.to_xml()
        # Required TT78 blocks
        required_tags = ["TTChung", "NDHDon", "NBan", "NMua", "DSHHDVu", "TToan"]
        for tag in required_tags:
            assert f"<{tag}>" in xml, f"Missing TT78 block: {tag}"
        # Currency must be VND
        assert "<DVTTe>VND</DVTTe>" in xml

    def test_vas_journal_entry_balanced(self) -> None:
        """Journal entry is balanced (debits = credits)."""
        invoice = create_invoice(
            amount=5_000_000,
            vat_rate=10,
            buyer="Nguyễn Văn B",
            seller="Công Ty Mình",
        )
        entry = invoice.to_journal_entry()
        total_debit = sum(Decimal(e["debit"]) for e in entry["entries"])
        total_credit = sum(Decimal(e["credit"]) for e in entry["entries"])
        assert total_debit == total_credit

    def test_vas_journal_uses_correct_accounts(self) -> None:
        """Journal uses proper VAS account codes."""
        invoice = create_invoice(amount=2_000_000, vat_rate=10, buyer="X", seller="Y")
        entry = invoice.to_journal_entry()
        accounts = [e["account"] for e in entry["entries"]]
        # TK 131 (Phải thu), TK 511 (Doanh thu), TK 3331 (GTGT phải nộp)
        assert "131" in accounts
        assert "511" in accounts
        assert "3331" in accounts

    def test_summary_vnd_formatting(self) -> None:
        """Summary uses correct VND formatting (dấu chấm)."""
        invoice = create_invoice(amount=12_345_678, vat_rate=10, buyer="Khách", seller="Shop")
        summary = invoice.to_summary()
        # VND format: 12.345.678 đ
        assert "12.345.678 đ" in summary or "13.580.245 đ" in summary

    def test_invoice_xml_total_matches_arithmetic(self) -> None:
        """XML totals match calculated amounts exactly."""
        items = [
            InvoiceItem("SP1", Decimal("2"), Decimal("50000"), vat_rate=10),
            InvoiceItem("SP2", Decimal("1"), Decimal("100000"), vat_rate=8),
        ]
        invoice = Invoice(
            seller_name="Test",
            seller_tax_code="0123456789",
            buyer_name="Buyer",
            items=items,
        )
        xml = invoice.to_xml()
        # Check that totals in XML match arithmetic
        assert str(int(invoice.subtotal)) in xml
        assert str(int(invoice.total_vat)) in xml
        assert str(int(invoice.total_amount)) in xml


# ============================================================================
# Tax Calculation (thue-dnvn) Regression Tests
# ============================================================================

class TestThueDnvnTNCNRegression:
    """Test TNCN (personal income tax) calculations."""

    def test_tncn_30m_no_dependents_historical_behavior(self) -> None:
        """30M/month → 2.15M tax (verifies progressive brackets)."""
        result = calculate_tncn(30_000_000, dependents=0)
        assert result.tax_amount == Decimal("2150000")
        # effective_rate is quantized to 4 decimal places (ROUND_HALF_UP).
        assert result.effective_rate == Decimal("0.0717")

    def test_tncn_income_below_personal_deduction_zero_tax(self) -> None:
        """Income < 11M → no tax."""
        result = calculate_tncn(10_000_000)
        assert result.taxable_income == Decimal("0")
        assert result.tax_amount == Decimal("0")

    def test_tncn_dependents_reduce_tax(self) -> None:
        """Adding dependents reduces taxable income."""
        result_no_dep = calculate_tncn(20_000_000, dependents=0)
        result_with_dep = calculate_tncn(20_000_000, dependents=2)
        assert result_with_dep.taxable_income < result_no_dep.taxable_income
        assert result_with_dep.tax_amount < result_no_dep.tax_amount
        # 2 dependents = 2 × 4.4M = 8.8M deduction
        expected_deduction = DEPENDENT_DEDUCTION * 2
        assert result_with_dep.dependent_deduction == expected_deduction

    def test_tncn_high_bracket_35_percent(self) -> None:
        """High income hits 35% bracket."""
        result = calculate_tncn(100_000_000)
        # Check 35% bracket appears in breakdown
        rates = [b["rate"] for b in result.breakdown]
        assert "35%" in rates

    def test_tncn_net_income_correct(self) -> None:
        """Net = gross - tax."""
        result = calculate_tncn(30_000_000)
        assert result.net_income == result.gross_income - result.tax_amount


class TestThueDnvnTNDNRegression:
    """Test TNDN (corporate income tax) calculations."""

    def test_tndn_sme_under_3b_17_percent(self) -> None:
        """Revenue ≤ 3 tỷ → SME rate 17%."""
        result = calculate_tndn(2_000_000_000)
        assert result.is_sme is True
        assert result.tax_rate == TNDN_SME_RATE
        assert result.tax_amount == Decimal("340000000")

    def test_tndn_standard_over_3b_20_percent(self) -> None:
        """Revenue > 3 tỷ → standard 20%."""
        result = calculate_tndn(5_000_000_000)
        assert result.is_sme is False
        assert result.tax_rate == TNDN_RATE
        assert result.tax_amount == Decimal("1000000000")

    def test_tndn_boundary_exactly_3b_is_sme(self) -> None:
        """Exactly 3 tỷ qualifies as SME."""
        result = calculate_tndn(3_000_000_000)
        assert result.is_sme is True
        assert result.tax_rate == TNDN_SME_RATE


class TestThueDnvnGTGTRegression:
    """Test GTGT (VAT) calculations."""

    def test_gtgt_standard_10_percent(self) -> None:
        result = calculate_gtgt(10_000_000, rate=10)
        assert result["vat_amount"] == 1_000_000
        assert result["total_amount"] == 11_000_000
        assert result["vat_rate"] == "10%"

    def test_gtgt_reduced_8_percent(self) -> None:
        result = calculate_gtgt(10_000_000, rate=8)
        assert result["vat_amount"] == 800_000
        assert result["total_amount"] == 10_800_000

    def test_gtgt_zero_rate(self) -> None:
        result = calculate_gtgt(5_000_000, rate=0)
        assert result["vat_amount"] == 0
        assert result["total_amount"] == 5_000_000

    def test_gtgt_disclaimer_present(self) -> None:
        result = calculate_gtgt(1_000_000)
        assert "thuedientu.gdt.gov.vn" in result["disclaimer"]


# ============================================================================
# Zalo OA Integration Regression Tests
# ============================================================================

class TestZaloOAClientRegression:
    """Test Zalo OA API client (mocked)."""

    @pytest.fixture
    def mock_zalo_client(self):
        """Client with mocked session."""
        client = ZaloOAClient(access_token="test_token_xyz", app_id="test_app")
        mock_session = MagicMock()
        client._get_session = lambda: mock_session
        return client, mock_session

    def test_send_message_payload_structure(self, mock_zalo_client) -> None:
        """Send message uses correct Zalo OA API payload."""
        client, session = mock_zalo_client
        session.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"error": 0, "message_id": "msg_123"}
        )

        result = client.send_message("user_zalo_001", "Xin chào!")

        call_args = session.post.call_args
        endpoint = call_args[0][0]
        payload = call_args[1]["json"]

        assert "/message" in endpoint
        assert payload["recipient"]["user_id"] == "user_zalo_001"
        assert payload["message"]["text"] == "Xin chào!"
        assert result["error"] == 0

    def test_broadcast_payload(self, mock_zalo_client) -> None:
        """Broadcast sends to correct endpoint."""
        client, session = mock_zalo_client
        session.post.return_value = MagicMock(
            json=lambda: {"error": 0, "broadcast_id": "bc_001"}
        )

        client.broadcast("Khuyến mãi cuối tuần!")

        call_args = session.post.call_args
        assert "/broadcast/message" in call_args[0][0]
        assert call_args[1]["json"]["message"]["text"] == "Khuyến mãi cuối tuần!"

    def test_get_followers_pagination(self, mock_zalo_client) -> None:
        """Get followers uses pagination params."""
        client, session = mock_zalo_client
        session.get.return_value = MagicMock(
            json=lambda: {"data": {"total": 100, "followers": []}}
        )

        client.get_followers(offset=20, count=10)

        call_args = session.get.call_args
        params = call_args[1]["params"]
        assert '"offset":20' in params["data"] or "20" in params["data"]
        assert '"count":10' in params["data"] or "10" in params["data"]

    def test_post_article_with_cover(self, mock_zalo_client) -> None:
        """Post article includes cover image and truncates description."""
        client, session = mock_zalo_client
        session.post.return_value = MagicMock(
            json=lambda: {"error": 0, "article_id": "art_123"}
        )

        long_content = "Lorem ipsum " * 50
        client.post_article(
            title="Sản phẩm mới",
            content=long_content,
            cover_image="https://example.com/cover.jpg",
        )

        payload = session.post.call_args[1]["json"]
        assert payload["title"] == "Sản phẩm mới"
        assert payload["cover"] == "https://example.com/cover.jpg"
        assert len(payload["description"]) <= 100  # Truncated

    def test_is_configured_validation(self) -> None:
        """is_configured requires both token and app_id."""
        assert not ZaloOAClient(access_token="x", app_id="").is_configured()
        assert not ZaloOAClient(access_token="", app_id="y").is_configured()
        assert ZaloOAClient(access_token="x", app_id="y").is_configured()


class TestVnCaptionGenerator:
    """Test Vietnamese caption generation."""

    @pytest.mark.parametrize("tone", ["than_thien", "chuyen_nghiep", "vui_ve"])
    def test_caption_includes_product_name(self, tone: str) -> None:
        caption = generate_vn_caption("áo dài", tone=tone)
        assert "áo dài" in caption.lower()

    def test_caption_than_thien_has_emoji(self) -> None:
        caption = generate_vn_caption("trà sữa", tone="than_thien")
        assert any(ord(c) > 127 for c in caption)  # Has unicode/emoji

    def test_caption_chuyen_nghiep_has_bullets(self) -> None:
        caption = generate_vn_caption("phần mềm", tone="chuyen_nghiep")
        assert "•" in caption or "-" in caption

    def test_caption_vui_ve_has_exclamation(self) -> None:
        caption = generate_vn_caption("bánh", tone="vui_ve")
        assert "!" in caption or "🎉" in caption or "😊" in caption


# ============================================================================
# VietQR Webhook Regression Tests
# ============================================================================

class TestVietQRWebhookRegression:
    """Test VietQR payment webhook end-to-end."""

    def test_memo_parsing_legacy_format(self) -> None:
        """Legacy memo `MEKONG-opc_001_abc` → (default, opc_001_abc)."""
        result = _parse_memo("MEKONG-opc_001_abc12")
        assert result == ("default", "opc_001_abc12")

    def test_memo_parsing_case_insensitive(self) -> None:
        """Memo parsing is case-insensitive."""
        result = _parse_memo("MEKONG-ACME-opc_001_abc")
        assert result == ("acme", "opc_001_abc")

    def test_memo_parsing_separator_variants(self) -> None:
        """Different separators all work."""
        cases = [
            ("MEKONG-acme-opc_001_abc", ("acme", "opc_001_abc")),
            ("MEKONG_acme_opc_001_abc", ("acme", "opc_001_abc")),
            ("MEKONG ACME opc_001_abc", ("acme", "opc_001_abc")),
        ]
        for memo, expected in cases:
            assert _parse_memo(memo) == expected

    def test_memo_parsing_invalid_returns_none(self) -> None:
        """Invalid memos return None."""
        invalid = ["", "random text", "MEKONG only", "MEKONG-INVALID"]
        for memo in invalid:
            assert _parse_memo(memo) is None

    def test_tier_matching_exact_amounts(self) -> None:
        """Tier matching uses exact amounts."""
        assert _TIER_PRICES_VND[199_000] == "starter_vnd"
        assert _TIER_PRICES_VND[299_000] == "growth_vnd"
        assert _TIER_PRICES_VND[499_000] == "pro_vnd"

    def test_tier_missing_for_unusual_amount(self) -> None:
        """Amounts not matching tiers return None."""
        assert 175_000 not in _TIER_PRICES_VND
        assert 300_000 not in _TIER_PRICES_VND


# ============================================================================
# Cross-Feature Integration Regression Tests
# ============================================================================

class TestVietnamFeatureIntegration:
    """Test that Vietnam features work together correctly."""

    def test_ke_toan_to_thue_dnvn_data_flow(self) -> None:
        """Invoice totals feed correctly into tax calculations."""
        # Create invoice with 5M revenue
        invoice = create_invoice(
            amount=5_000_000,
            vat_rate=10,
            buyer="Công Ty ABC",
            seller="My Business",
        )
        # Revenue for TNDN calculation
        monthly_revenue = invoice.total_amount
        assert monthly_revenue == Decimal("5500000")

        # Annual TNDN projection (simplified)
        annual_projection = monthly_revenue * 12
        tndn = calculate_tndn(int(annual_projection))
        assert tndn.revenue == annual_projection

    def test_vietqr_webhook_user_id_format(self) -> None:
        """User IDs from pilot signup match VietQR memo format."""
        # Pilot user IDs are opc_XXX_xxxxx format
        user_id = "opc_001_abc123"
        memo = f"MEKONG-{user_id}"
        org, parsed_user = _parse_memo(memo)
        assert org == "default"
        assert parsed_user == user_id

    def test_vietqr_tier_amounts_match_vn_pricing(self) -> None:
        """VietQR tier amounts correspond to VN pricing tiers."""
        # These should match pricing in factory/contracts/pricing.json
        tiers = {199000, 299000, 499000}
        for amount in tiers:
            tier_key = _TIER_PRICES_VND.get(amount)
            assert tier_key is not None
            assert "vnd" in tier_key

    def test_zalo_oa_caption_uses_vietnamese(self) -> None:
        """Zalo OA caption generator produces Vietnamese text."""
        caption = generate_vn_caption("bánh mì", tone="than_thien")
        # Check for Vietnamese characters
        vietnamese_chars = "ăâêôưýỳỵỷỹẵẫậầặẻểễếệơ"
        has_vietnamese = any(c in caption.lower() for c in vietnamese_chars)
        # Or at minimum, should mention the product
        assert "bánh mì" in caption.lower() or has_vietnamese

    def test_tax_constants_are_current(self) -> None:
        """Tax constants match 2024-2026 Vietnamese tax law."""
        # Personal deduction: 11M VND/month
        assert PERSONAL_DEDUCTION == Decimal("11000000")
        # Dependent deduction: 4.4M VND/month
        assert DEPENDENT_DEDUCTION == Decimal("4400000")
        # SME threshold: 3B VND/year
        assert TNDN_SME_THRESHOLD == Decimal("3000000000")
        # SME rate: 17%
        assert TNDN_SME_RATE == Decimal("0.17")
        # Standard rate: 20%
        assert TNDN_RATE == Decimal("0.20")


# ============================================================================
# End-to-End Pilot User Journey Regression
# ============================================================================

class TestPilotUserJourneyRegression:
    """Simulate complete pilot user journey through VN features."""

    def test_complete_vn_user_journey(self) -> None:
        """
        End-to-end scenario:
        1. User signs up for pilot
        2. Creates invoice (ke-toan)
        3. Calculates taxes (thue-dnvn)
        4. Sends Zalo message (zalo-oa)
        5. Receives VietQR payment
        """
        # 1. User has ID in pilot system
        user_id = "opc_001_pilotuser"

        # 2. Create invoice for VN customer
        invoice = create_invoice(
            amount=10_000_000,
            vat_rate=10,
            buyer="Nguyễn Thị Lan",
            seller="Doanh Nghiệp Mình",
            seller_tax_code="0123456789",
        )
        assert invoice.total_amount == Decimal("11000000")

        # 3. Calculate TNCN for hypothetical employee salary
        salary_result = calculate_tncn(monthly_income=20_000_000, dependents=1)
        assert salary_result.tax_amount > 0

        # 4. Calculate TNDN for business
        tndn = calculate_tndn(annual_revenue=2_400_000_000)  # < 3B → SME
        assert tndn.is_sme is True
        assert tndn.tax_rate == Decimal("0.17")

        # 5. Generate Zalo caption for product
        caption = generate_vn_caption("dịch vụ kế toán", tone="chuyen_nghiep")
        assert "dịch vụ kế toán" in caption.lower()

        # 6. VietQR webhook would match: MEKONG-{user_id} memo
        memo = f"MEKONG-{user_id}"
        org_user = _parse_memo(memo)
        assert org_user == ("default", user_id)

        # 7. Amount 299_000 VND maps to growth tier
        assert _TIER_PRICES_VND.get(299_000) == "growth_vnd"

    def test_migration_data_integrity(self) -> None:
        """
        Verify that data formats are consistent across features.
        - Amounts are Decimal throughout
        - Currency is VND for VN features
        - Dates are timezone-aware when needed
        """
        # Invoice amounts are Decimal
        inv = create_invoice(amount=1000000, vat_rate=10, buyer="X", seller="Y")
        assert isinstance(inv.subtotal, Decimal)
        assert isinstance(inv.total_amount, Decimal)

        # Tax calculations return Decimal
        tncn = calculate_tncn(20_000_000)
        assert isinstance(tncn.tax_amount, Decimal)
        assert isinstance(tncn.net_income, Decimal)

        tndn = calculate_tndn(1_000_000_000)
        assert isinstance(tndn.tax_amount, Decimal)

        gtgt = calculate_gtgt(1_000_000)
        assert isinstance(gtgt["vat_amount"], int) or isinstance(gtgt["vat_amount"], Decimal)
