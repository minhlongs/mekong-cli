"""Unit tests for the Vietnam Tax Calculator (TNCN/TNDN/GTGT)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.seed.tax import (
    GTGTCategory,
    ResidencyStatus,
    TNDNPreferentialType,
    TaxCalculator,
    TaxYear,
    calculate_gtgt,
    calculate_tndn,
    calculate_tncn,
)
from src.seed.tax.models import (
    GTGTInput,
    TNDNInput,
    TNCNInput,
)


@pytest.fixture
def calculator() -> TaxCalculator:
    return TaxCalculator()


# ---------------------------------------------------------------------------
# TNCN — Personal Income Tax
# ---------------------------------------------------------------------------


class TestTNCNResident:
    def test_income_below_deduction_pays_zero(self, calculator: TaxCalculator):
        """Gross income below the 11M VND personal deduction → no tax."""
        result = calculate_tncn(gross_income=Decimal("10000000"), tax_year=TaxYear.Y2025)
        assert result.taxable_income == Decimal("0")
        assert result.tax_payable == Decimal("0")

    def test_first_bracket_five_percent(self, calculator: TaxCalculator):
        """Taxable income up to 5M VND is taxed at 5%."""
        # Gross 15M - 11M deduction = 4M taxable at 5% = 200k
        result = calculate_tncn(gross_income=Decimal("15000000"), tax_year=TaxYear.Y2025)
        assert result.taxable_income == Decimal("4000000")
        assert result.tax_payable == Decimal("200000")

    def test_two_brackets_progressive(self, calculator: TaxCalculator):
        """Taxable income spanning two brackets is taxed progressively."""
        # Gross 17M - 11M = 6M taxable: 5M@5% + 1M@10% = 250k + 100k = 350k
        result = calculate_tncn(gross_income=Decimal("17000000"), tax_year=TaxYear.Y2025)
        assert result.taxable_income == Decimal("6000000")
        assert result.tax_payable == Decimal("350000")

    def test_dependents_increase_deduction(self, calculator: TaxCalculator):
        """Each dependent adds 4.4M VND monthly deduction."""
        result = calculate_tncn(
            gross_income=Decimal("15000000"),
            tax_year=TaxYear.Y2025,
            dependents=1,
        )
        # 15M - 11M - 4.4M = -0.4M → taxable 0
        assert result.taxable_income == Decimal("0")

    def test_insurance_reduces_taxable_income(self, calculator: TaxCalculator):
        result = calculate_tncn(
            gross_income=Decimal("16000000"),
            tax_year=TaxYear.Y2025,
            insurance=Decimal("1000000"),
        )
        # 16M - 11M - 1M = 4M @ 5% = 200k
        assert result.taxable_income == Decimal("4000000")
        assert result.tax_payable == Decimal("200000")

    def test_high_income_top_bracket(self, calculator: TaxCalculator):
        """Very high income reaches the 35% bracket."""
        result = calculate_tncn(gross_income=Decimal("100000000"), tax_year=TaxYear.Y2025)
        assert result.taxable_income == Decimal("89000000")
        assert result.tax_payable > Decimal("0")
        assert len(result.brackets_applied) == 7  # all brackets

    def test_zero_income(self, calculator: TaxCalculator):
        result = calculate_tncn(gross_income=Decimal("0"), tax_year=TaxYear.Y2025)
        assert result.tax_payable == Decimal("0")
        assert result.effective_rate == Decimal("0")

    def test_effective_rate_calculation(self, calculator: TaxCalculator):
        result = calculate_tncn(gross_income=Decimal("15000000"), tax_year=TaxYear.Y2025)
        # 200k / 15M = 0.0133...
        assert result.effective_rate == Decimal("0.0133")

    def test_net_income(self, calculator: TaxCalculator):
        result = calculate_tncn(gross_income=Decimal("15000000"), tax_year=TaxYear.Y2025)
        assert result.net_income == Decimal("14800000")


class TestTNCNNonResident:
    def test_flat_20_percent(self, calculator: TaxCalculator):
        """Non-residents pay flat 20% with no deductions."""
        result = calculate_tncn(
            gross_income=Decimal("10000000"),
            tax_year=TaxYear.Y2025,
            residency=ResidencyStatus.NON_RESIDENT,
        )
        assert result.taxable_income == Decimal("10000000")
        assert result.tax_payable == Decimal("2000000")

    def test_non_resident_no_deductions(self, calculator: TaxCalculator):
        result = calculate_tncn(
            gross_income=Decimal("10000000"),
            tax_year=TaxYear.Y2025,
            residency=ResidencyStatus.NON_RESIDENT,
            dependents=2,
            insurance=Decimal("500000"),
        )
        assert result.deductions["total"] == Decimal("0")


class TestTNCNModel:
    def test_input_validation(self):
        with pytest.raises(ValueError):
            TNCNInput(gross_income=Decimal("-1000"))

    def test_input_defaults(self):
        inp = TNCNInput(gross_income=Decimal("10000000"))
        assert inp.tax_year == TaxYear.Y2025
        assert inp.residency == ResidencyStatus.RESIDENT
        assert inp.dependents == 0

    def test_tax_year_2024(self, calculator: TaxCalculator):
        result = calculate_tncn(gross_income=Decimal("15000000"), tax_year=TaxYear.Y2024)
        assert result.tax_payable == Decimal("200000")

    def test_tax_year_2026(self, calculator: TaxCalculator):
        result = calculate_tncn(gross_income=Decimal("15000000"), tax_year=TaxYear.Y2026)
        assert result.tax_payable == Decimal("200000")


# ---------------------------------------------------------------------------
# TNDN — Corporate Income Tax
# ---------------------------------------------------------------------------


class TestTNDN:
    def test_standard_rate_20_percent(self, calculator: TaxCalculator):
        result = calculate_tndn(taxable_income=Decimal("100000000"), tax_year=TaxYear.Y2025)
        assert result.applicable_rate == Decimal("0.20")
        assert result.tax_payable == Decimal("20000000")

    def test_sme_preferential_rate(self, calculator: TaxCalculator):
        result = calculate_tndn(
            taxable_income=Decimal("100000000"),
            tax_year=TaxYear.Y2025,
            preferential_type=TNDNPreferentialType.SME,
            preferential_years=2,
        )
        assert result.applicable_rate == Decimal("0.17")
        assert result.tax_payable == Decimal("17000000")

    def test_preferential_requires_remaining_years(self, calculator: TaxCalculator):
        """If preferential_years_remaining is 0, standard rate applies."""
        result = calculate_tndn(
            taxable_income=Decimal("100000000"),
            tax_year=TaxYear.Y2025,
            preferential_type=TNDNPreferentialType.HIGH_TECH,
            preferential_years=0,
        )
        assert result.applicable_rate == Decimal("0.20")

    def test_brought_forward_losses_reduce_tax(self, calculator: TaxCalculator):
        result = calculate_tndn(
            taxable_income=Decimal("100000000"),
            tax_year=TaxYear.Y2025,
            brought_forward_losses=Decimal("40000000"),
        )
        assert result.tax_payable == Decimal("12000000")  # 60M @ 20%
        assert result.losses_carried_forward == Decimal("0")

    def test_partial_loss_carryforward(self, calculator: TaxCalculator):
        result = calculate_tndn(
            taxable_income=Decimal("30000000"),
            tax_year=TaxYear.Y2025,
            brought_forward_losses=Decimal("50000000"),
        )
        assert result.tax_payable == Decimal("0")
        assert result.losses_carried_forward == Decimal("20000000")

    def test_zero_income(self, calculator: TaxCalculator):
        result = calculate_tndn(taxable_income=Decimal("0"), tax_year=TaxYear.Y2025)
        assert result.tax_payable == Decimal("0")

    def test_tax_before_incentives_uses_standard_rate(self, calculator: TaxCalculator):
        result = calculate_tndn(
            taxable_income=Decimal("100000000"),
            tax_year=TaxYear.Y2025,
            preferential_type=TNDNPreferentialType.SME,
            preferential_years=1,
        )
        assert result.tax_before_incentives == Decimal("20000000")
        assert result.tax_payable == Decimal("17000000")


class TestTNDNModel:
    def test_input_validation(self):
        with pytest.raises(ValueError):
            TNDNInput(taxable_income=Decimal("-1"))

    def test_preferential_enum(self):
        assert TNDNPreferentialType.ENCOURAGED_SECTORS.value == "encouraged_sectors"
        assert TNDNPreferentialType.HIGH_TECH.value == "high_tech"


# ---------------------------------------------------------------------------
# GTGT — Value Added Tax
# ---------------------------------------------------------------------------


class TestGTGT:
    def test_standard_10_percent(self, calculator: TaxCalculator):
        result = calculate_gtgt(net_amount=Decimal("10000000"), tax_year=TaxYear.Y2025)
        assert result.vat_rate == Decimal("0.10")
        assert result.vat_amount == Decimal("1000000")
        assert result.gross_amount == Decimal("11000000")

    def test_reduced_8_percent(self, calculator: TaxCalculator):
        result = calculate_gtgt(
            net_amount=Decimal("10000000"),
            tax_year=TaxYear.Y2025,
            category=GTGTCategory.REDUCED,
        )
        assert result.vat_rate == Decimal("0.08")
        assert result.vat_amount == Decimal("800000")

    def test_exempt_0_percent(self, calculator: TaxCalculator):
        result = calculate_gtgt(
            net_amount=Decimal("10000000"),
            tax_year=TaxYear.Y2025,
            category=GTGTCategory.EXEMPT,
        )
        assert result.vat_rate == Decimal("0.00")
        assert result.vat_amount == Decimal("0")
        assert result.gross_amount == Decimal("10000000")

    def test_export_zero_rated(self, calculator: TaxCalculator):
        result = calculate_gtgt(
            net_amount=Decimal("10000000"),
            tax_year=TaxYear.Y2025,
            is_export=True,
        )
        assert result.vat_amount == Decimal("0")

    def test_zero_amount(self, calculator: TaxCalculator):
        result = calculate_gtgt(net_amount=Decimal("0"), tax_year=TaxYear.Y2025)
        assert result.vat_amount == Decimal("0")
        assert result.gross_amount == Decimal("0")

    def test_rounding(self, calculator: TaxCalculator):
        # Odd amounts should round to nearest VND
        result = calculate_gtgt(net_amount=Decimal("1000003"), tax_year=TaxYear.Y2025)
        assert result.vat_amount == Decimal("100000")


class TestGTGTModel:
    def test_input_validation(self):
        with pytest.raises(ValueError):
            GTGTInput(net_amount=Decimal("-10"))

    def test_defaults(self):
        inp = GTGTInput(net_amount=Decimal("1000000"))
        assert inp.category == GTGTCategory.STANDARD
        assert inp.is_export is False


# ---------------------------------------------------------------------------
# Rate loader
# ---------------------------------------------------------------------------


class TestRateLoader:
    def test_loads_all_years(self, calculator: TaxCalculator):
        for year in ("2024", "2025", "2026"):
            config = calculator.rate_loader.load_rates(TaxYear(year))
            assert config.version == year
            assert config.tncn.brackets
            assert config.tndn.standard_rate == Decimal("0.20")
            assert config.gtgt.standard_rate == Decimal("0.10")

    def test_unknown_year_raises(self, calculator: TaxCalculator):
        from src.seed.tax.models import TaxYear as TY

        with pytest.raises(ValueError):
            calculator.rate_loader.load_rates(TY("1999"))

    def test_bracket_boundaries(self, calculator: TaxCalculator):
        config = calculator.rate_loader.load_rates(TaxYear.Y2025)
        brackets = config.tncn.brackets
        assert len(brackets) == 7
        assert brackets[0]["min_income"] == Decimal("0")
        assert brackets[0]["max_income"] == Decimal("5000000")
        assert brackets[0]["rate"] == Decimal("0.05")
        assert brackets[-1]["max_income"] is None
        assert brackets[-1]["rate"] == Decimal("0.35")
