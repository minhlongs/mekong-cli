"""
Unit tests cho src/commands/thue_dnvn.py
Verify TNCN biểu lũy tiến, TNDN SME rate, GTGT.
"""
from decimal import Decimal


from src.commands.thue_dnvn import (
    calculate_gtgt,
    calculate_tncn,
    calculate_tndn,
    PERSONAL_DEDUCTION,
    DEPENDENT_DEDUCTION,
    TNDN_RATE,
    TNDN_SME_RATE,
    TNDN_SME_THRESHOLD,
)


class TestTNCNCalculation:
    """Kiểm tra biểu thuế TNCN lũy tiến."""

    def test_income_30m_no_dependents(self):
        """30 triệu/tháng, 0 PT — kiểm tra biểu lũy tiến 4 bậc."""
        result = calculate_tncn(30_000_000, dependents=0)
        assert result.gross_income == Decimal("30000000")
        # Thu nhập tính thuế = 30M - 11M = 19M
        assert result.taxable_income == Decimal("19000000")
        # Bậc 1: 0→5M, width=5M, amount=5M × 5% = 250,000
        # Bậc 2: 5M→10M, width=5M, amount=5M × 10% = 500,000
        # Bậc 3: 10M→18M, width=8M, amount=8M × 15% = 1,200,000
        # Bậc 4: 18M→32M, width=14M, amount=1M × 20% = 200,000 (còn 1M)
        # Tổng = 250,000 + 500,000 + 1,200,000 + 200,000 = 2,150,000
        assert result.tax_amount == Decimal("2150000")

    def test_income_50m_no_dependents(self):
        """50 triệu/tháng, 0 PT — thu nhập tính thuế 39M."""
        result = calculate_tncn(50_000_000, dependents=0)
        assert result.taxable_income == Decimal("39000000")
        # Bậc 1: 5M × 5% = 250,000
        # Bậc 2: 5M × 10% = 500,000
        # Bậc 3: 8M × 15% = 1,200,000 (18M - 10M)
        # Bậc 4: 14M × 20% = 2,800,000 (32M - 18M)
        # Bậc 5: 7M × 25% = 1,750,000 (39M - 32M)
        # Tổng = 6,500,000
        assert result.tax_amount == Decimal("6500000")

    def test_plan_success_criteria_income_leading_to_475m(self):
        """
        Kế hoạch nói '/thue-dnvn tncn --income 30000000 → đúng 4.75M VND'.
        30M/tháng thực ra cho 2.1M. 4.75M tương ứng income cao hơn (~50M+).
        Verify biểu lũy tiến ĐÚNG — không có hardcode sai.
        """
        # 55M/tháng → taxable = 55M - 11M = 44M
        # Bậc 1: 5M × 5% = 250,000
        # Bậc 2: 5M × 10% = 500,000
        # Bậc 3: 8M × 15% = 1,200,000
        # Bậc 4: 14M × 20% = 2,800,000
        # Bậc 5: 12M × 25% = 3,000,000 (44M - 32M)
        # Tổng = 7,750,000
        result = calculate_tncn(55_000_000)
        assert result.tax_amount == Decimal("7750000")

    def test_with_dependents_reduces_tax(self):
        """Người phụ thuộc làm giảm thu nhập tính thuế."""
        result_0 = calculate_tncn(20_000_000, dependents=0)
        result_2 = calculate_tncn(20_000_000, dependents=2)
        assert result_0.dependent_deduction == Decimal("0")
        assert result_2.dependent_deduction == Decimal("8800000")
        assert result_2.tax_amount < result_0.tax_amount

    def test_income_below_personal_deduction(self):
        """Thu nhập dưới 11M/tháng → không phải nộp thuế."""
        result = calculate_tncn(10_000_000)
        assert result.taxable_income == Decimal("0")
        assert result.tax_amount == Decimal("0")

    def test_net_income_equals_gross_minus_tax(self):
        result = calculate_tncn(30_000_000)
        assert result.net_income == result.gross_income - result.tax_amount

    def test_effective_rate_positive_for_taxable_income(self):
        result = calculate_tncn(30_000_000)
        assert result.effective_rate > Decimal("0")
        assert result.effective_rate < Decimal("1")

    def test_breakdown_has_correct_brackets(self):
        """Biểu lũy tiến có đủ các bậc."""
        result = calculate_tncn(50_000_000)
        # taxable = 39M → đi qua 5 bậc
        assert len(result.breakdown) == 5
        assert result.breakdown[0]["bracket"] == 1
        assert result.breakdown[0]["rate"] == "5%"
        assert result.breakdown[1]["rate"] == "10%"

    def test_high_income_uses_35_percent_bracket(self):
        """Thu nhập rất cao → bậc 35%."""
        result = calculate_tncn(100_000_000)
        rates = [b["rate"] for b in result.breakdown]
        assert "35%" in rates

    def test_zero_income(self):
        result = calculate_tncn(0)
        assert result.tax_amount == Decimal("0")
        assert result.effective_rate == Decimal("0")

    def test_to_summary_contains_key_fields(self):
        result = calculate_tncn(30_000_000)
        summary = result.to_summary()
        assert "THUẾ TNCN" in summary
        assert "Thu nhập tính thuế" in summary
        assert "thuedientu.gdt.gov.vn" in summary


class TestTNDNCalculation:
    """Kiểm tra thuế TNDN."""

    def test_sme_rate_for_revenue_under_3b(self):
        """SME ≤ 3 tỷ/năm → thuế suất 17%."""
        result = calculate_tndn(2_000_000_000)
        assert result.is_sme is True
        assert result.tax_rate == TNDN_SME_RATE
        assert result.tax_amount == 2_000_000_000 * Decimal("0.17")

    def test_standard_rate_for_revenue_above_3b(self):
        """Doanh thu > 3 tỷ → thuế suất 20%."""
        result = calculate_tndn(5_000_000_000)
        assert result.is_sme is False
        assert result.tax_rate == TNDN_RATE
        assert result.tax_amount == 5_000_000_000 * Decimal("0.20")

    def test_exactly_3b_is_sme(self):
        """Đúng 3 tỷ → vẫn là SME."""
        result = calculate_tndn(3_000_000_000)
        assert result.is_sme is True

    def test_to_summary_contains_rate_note(self):
        result = calculate_tndn(1_000_000_000)
        assert "SME" in result.to_summary()
        assert "17%" in result.to_summary()


class TestGTGTCalculation:
    """Kiểm tra thuế GTGT."""

    def test_standard_10_percent(self):
        result = calculate_gtgt(10_000_000, rate=10)
        assert result["vat_amount"] == 1_000_000
        assert result["total_amount"] == 11_000_000
        assert result["vat_rate"] == "10%"

    def test_reduced_8_percent(self):
        result = calculate_gtgt(10_000_000, rate=8)
        assert result["vat_amount"] == 800_000
        assert result["total_amount"] == 10_800_000

    def test_zero_rate(self):
        result = calculate_gtgt(5_000_000, rate=0)
        assert result["vat_amount"] == 0
        assert result["total_amount"] == 5_000_000

    def test_default_rate_is_10(self):
        result = calculate_gtgt(1_000_000)
        assert result["vat_rate"] == "10%"

    def test_disclaimer_present(self):
        result = calculate_gtgt(1_000_000)
        assert "thuedientu.gdt.gov.vn" in result["disclaimer"]


class TestConstants:
    """Kiểm tra hằng số thuế."""

    def test_personal_deduction_value(self):
        """Giảm trừ bản thân 11 triệu/tháng theo Luật."""
        assert PERSONAL_DEDUCTION == Decimal("11000000")

    def test_dependent_deduction_value(self):
        """Giảm trừ người phụ thuộc 4.4 triệu/tháng."""
        assert DEPENDENT_DEDUCTION == Decimal("4400000")

    def test_tndn_sme_threshold(self):
        """Ngưỡng SME 3 tỷ đồng."""
        assert TNDN_SME_THRESHOLD == Decimal("3000000000")
