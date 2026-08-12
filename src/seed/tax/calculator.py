# Tax Calculator - Vietnam TNCN/TNDN/GTGT Calculator
# Uses Decimal-only arithmetic for currency precision

from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from .models import (
    TNCNInput, TNDNInput, GTGTInput,
    TNCNResult, TNDNResult, GTGTResult,
    TaxYear, ResidencyStatus, GTGTCategory, TNDNPreferentialType,
    TaxRatesConfig, TNCNRates, TNDNRates, GTGTRates,
    quantize_vnd, quantize_rate
)

# Set high precision for Decimal calculations
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP


class TaxRateLoader:
    """Loads tax rate configurations from YAML files"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self._cache: Dict[str, TaxRatesConfig] = {}

    def load_rates(self, tax_year: TaxYear) -> TaxRatesConfig:
        """Load tax rates for a specific year"""
        year_str = tax_year.value
        if year_str in self._cache:
            return self._cache[year_str]

        config_file = self.config_dir / f"rates_{year_str}.yaml"
        if not config_file.exists():
            raise ValueError(f"Tax rate config not found for year {year_str}")

        with open(config_file, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        config = self._parse_config(raw_config)
        self._cache[year_str] = config
        return config

    def _parse_config(self, raw: Dict[str, Any]) -> TaxRatesConfig:
        """Parse raw YAML into typed config"""
        tncn_raw = raw['tncn']
        tndn_raw = raw['tndn']
        gtgt_raw = raw['gtgt']

        tncn = TNCNRates(
            brackets=[{
                'min_income': Decimal(str(b['min_income'])),
                'max_income': Decimal(str(b['max_income'])) if b['max_income'] is not None else None,
                'rate': quantize_rate(Decimal(str(b['rate'])))
            } for b in tncn_raw['resident']['brackets']],
            personal_deduction_monthly=Decimal(str(tncn_raw['personal_deduction_monthly'])),
            dependent_deduction_monthly=Decimal(str(tncn_raw['dependent_deduction_monthly'])),
            non_resident_flat_rate=quantize_rate(Decimal(str(tncn_raw['non_resident']['flat_rate'])))
        )

        tndn = TNDNRates(
            standard_rate=quantize_rate(Decimal(str(tndn_raw['standard_rate']))),
            preferential_rates=[{
                'condition': p['condition'],
                'rate': quantize_rate(Decimal(str(p['rate']))),
                'duration_years': p['duration_years']
            } for p in tndn_raw['preferential_rates']],
            loss_carryforward_years=tndn_raw['loss_carryforward_years']
        )

        gtgt = GTGTRates(
            standard_rate=quantize_rate(Decimal(str(gtgt_raw['standard_rate']))),
            reduced_rate=quantize_rate(Decimal(str(gtgt_raw['reduced_rate']))),
            exempt_rate=quantize_rate(Decimal(str(gtgt_raw['exempt_rate']))),
            categories=[{
                'name': c['name'],
                'rate': quantize_rate(Decimal(str(c['rate']))) if c['rate'] is not None else None,
                'description': c['description']
            } for c in gtgt_raw['categories']]
        )

        return TaxRatesConfig(
            version=raw['version'],
            effective_from=raw['effective_from'],
            effective_to=raw['effective_to'],
            tncn=tncn,
            tndn=tndn,
            gtgt=gtgt,
            currency=raw['currency'],
            rounding=raw['rounding'],
            precision=raw['precision']
        )


class TNCCalculator:
    """Personal Income Tax (TNCN) Calculator"""

    def __init__(self, rate_loader: Optional[TaxRateLoader] = None):
        self.rate_loader = rate_loader or TaxRateLoader()

    def calculate(self, input_data: TNCNInput) -> TNCNResult:
        """Calculate TNCN for given input"""
        rates = self.rate_loader.load_rates(input_data.tax_year)

        if input_data.residency == ResidencyStatus.NON_RESIDENT:
            return self._calculate_non_resident(input_data, rates)

        return self._calculate_resident(input_data, rates)

    def _calculate_resident(self, input_data: TNCNInput, rates: TaxRatesConfig) -> TNCNResult:
        """Calculate TNCN for tax resident"""
        gross = input_data.gross_income

        # Calculate deductions
        personal_deduction = rates.tncn.personal_deduction_monthly
        dependent_deduction = rates.tncn.dependent_deduction_monthly * input_data.dependents
        insurance_deduction = min(input_data.insurance_contributions, gross)  # Cannot exceed gross
        total_deductions = personal_deduction + dependent_deduction + insurance_deduction + input_data.charity_donations + input_data.other_deductions

        # Taxable income (cannot be negative)
        taxable_income = max(gross - total_deductions, Decimal('0'))

        # Apply progressive tax brackets
        tax_payable = Decimal('0')
        brackets_applied = []
        remaining_income = taxable_income

        for bracket in rates.tncn.brackets:
            if remaining_income <= 0:
                break

            bracket_min = bracket['min_income']
            bracket_max = bracket['max_income']
            bracket_rate = bracket['rate']

            if bracket_max is not None:
                bracket_width = bracket_max - bracket_min
                taxable_in_bracket = min(remaining_income, bracket_width)
            else:
                taxable_in_bracket = remaining_income

            if taxable_in_bracket > 0:
                bracket_tax = taxable_in_bracket * bracket_rate
                tax_payable += bracket_tax
                brackets_applied.append({
                    'bracket_min': quantize_vnd(bracket_min),
                    'bracket_max': quantize_vnd(bracket_max) if bracket_max else None,
                    'rate': bracket_rate,
                    'taxable_amount': quantize_vnd(taxable_in_bracket),
                    'tax_amount': quantize_vnd(bracket_tax)
                })
                remaining_income -= taxable_in_bracket

        tax_payable = quantize_vnd(tax_payable)
        effective_rate = quantize_rate(tax_payable / gross) if gross > 0 else Decimal('0')
        net_income = quantize_vnd(gross - tax_payable)

        return TNCNResult(
            tax_year=input_data.tax_year.value,
            residency=input_data.residency.value,
            gross_income=quantize_vnd(gross),
            taxable_income=quantize_vnd(taxable_income),
            tax_payable=tax_payable,
            effective_rate=effective_rate,
            brackets_applied=brackets_applied,
            deductions={
                'personal': quantize_vnd(personal_deduction),
                'dependents': quantize_vnd(dependent_deduction),
                'insurance': quantize_vnd(insurance_deduction),
                'charity': quantize_vnd(input_data.charity_donations),
                'other': quantize_vnd(input_data.other_deductions),
                'total': quantize_vnd(total_deductions)
            },
            net_income=net_income
        )

    def _calculate_non_resident(self, input_data: TNCNInput, rates: TaxRatesConfig) -> TNCNResult:
        """Calculate TNCN for non-resident (flat 20%)"""
        gross = input_data.gross_income
        flat_rate = rates.tncn.non_resident_flat_rate

        taxable_income = gross  # No deductions for non-residents
        tax_payable = quantize_vnd(gross * flat_rate)
        effective_rate = flat_rate
        net_income = quantize_vnd(gross - tax_payable)

        return TNCNResult(
            tax_year=input_data.tax_year.value,
            residency=input_data.residency.value,
            gross_income=quantize_vnd(gross),
            taxable_income=quantize_vnd(taxable_income),
            tax_payable=tax_payable,
            effective_rate=effective_rate,
            brackets_applied=[{
                'bracket_min': Decimal('0'),
                'bracket_max': None,
                'rate': flat_rate,
                'taxable_amount': quantize_vnd(gross),
                'tax_amount': tax_payable
            }],
            deductions={
                'personal': Decimal('0'),
                'dependents': Decimal('0'),
                'insurance': Decimal('0'),
                'charity': Decimal('0'),
                'other': Decimal('0'),
                'total': Decimal('0')
            },
            net_income=net_income
        )


class TNDNCalculator:
    """Corporate Income Tax (TNDN) Calculator"""

    # Maps TNDNPreferentialType enum value -> substring found in the
    # YAML `condition` strings (kept in sync with config/rates_*.yaml).
    _PREFERENTIAL_MATCH = {
        "encouraged_sectors": "encouraged sectors",
        "high_tech": "high-tech",
        "education_healthcare": "education",
        "sme": "small and medium enterprises",
    }

    def __init__(self, rate_loader: Optional[TaxRateLoader] = None):
        self.rate_loader = rate_loader or TaxRateLoader()

    def _match_preferential_rate(self, preferential_type: TNDNPreferentialType, rates: TaxRatesConfig) -> tuple[Decimal, dict]:
        """Find the preferential rate config matching a preferential type.

        Returns (applicable_rate, incentive_info). Falls back to standard
        rate when no config condition matches.
        """
        standard_rate = rates.tndn.standard_rate
        needle = self._PREFERENTIAL_MATCH.get(preferential_type.value, preferential_type.value)
        for pref in rates.tndn.preferential_rates:
            condition: str = pref.get("condition", "")
            if needle in condition:
                return pref["rate"], {"condition": condition, "rate": pref["rate"]}
        return standard_rate, {}

    def calculate(self, input_data: TNDNInput) -> TNDNResult:
        """Calculate TNDN for given input"""
        rates = self.rate_loader.load_rates(input_data.tax_year)

        # Determine applicable rate
        applicable_rate = rates.tndn.standard_rate
        incentives_applied = []

        if input_data.preferential_type and input_data.preferential_years_remaining > 0:
            applicable_rate, matched = self._match_preferential_rate(input_data.preferential_type, rates)
            if matched:
                incentives_applied.append({
                    'type': input_data.preferential_type.value,
                    'condition': matched['condition'],
                    'rate': applicable_rate,
                    'years_remaining': input_data.preferential_years_remaining
                })

        # Apply brought forward losses
        taxable_after_losses = max(input_data.taxable_income - input_data.brought_forward_losses, Decimal('0'))
        losses_used = min(input_data.brought_forward_losses, input_data.taxable_income)
        losses_remaining = input_data.brought_forward_losses - losses_used

        # Calculate tax
        tax_before_incentives = quantize_vnd(taxable_after_losses * rates.tndn.standard_rate)
        tax_payable = quantize_vnd(taxable_after_losses * applicable_rate)

        return TNDNResult(
            tax_year=input_data.tax_year.value,
            taxable_income=quantize_vnd(input_data.taxable_income),
            applicable_rate=applicable_rate,
            tax_before_incentives=tax_before_incentives,
            incentives_applied=incentives_applied,
            tax_payable=tax_payable,
            losses_carried_forward=quantize_vnd(losses_remaining)
        )


class GTGTCalculator:
    """Value Added Tax (GTGT) Calculator"""

    def __init__(self, rate_loader: Optional[TaxRateLoader] = None):
        self.rate_loader = rate_loader or TaxRateLoader()

    def calculate(self, input_data: GTGTInput) -> GTGTResult:
        """Calculate GTGT for given input"""
        rates = self.rate_loader.load_rates(input_data.tax_year)

        # Determine VAT rate
        if input_data.is_export:
            vat_rate = rates.gtgt.exempt_rate
        else:
            category_map = {
                GTGTCategory.STANDARD: rates.gtgt.standard_rate,
                GTGTCategory.REDUCED: rates.gtgt.reduced_rate,
                GTGTCategory.EXEMPT: rates.gtgt.exempt_rate,
                GTGTCategory.SPECIAL_CONSUMPTION: Decimal('0')  # Handled separately
            }
            vat_rate = category_map.get(input_data.category, rates.gtgt.standard_rate)

        net_amount = input_data.net_amount
        vat_amount = quantize_vnd(net_amount * vat_rate)
        gross_amount = quantize_vnd(net_amount + vat_amount)

        return GTGTResult(
            tax_year=input_data.tax_year.value,
            category=input_data.category.value,
            net_amount=quantize_vnd(net_amount),
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            gross_amount=gross_amount
        )


class TaxCalculator:
    """Main tax calculator facade"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.rate_loader = TaxRateLoader(config_dir)
        self.tncn = TNCCalculator(self.rate_loader)
        self.tndn = TNDNCalculator(self.rate_loader)
        self.gtgt = GTGTCalculator(self.rate_loader)

    def calculate_tncn(self, input_data: TNCNInput) -> TNCNResult:
        return self.tncn.calculate(input_data)

    def calculate_tndn(self, input_data: TNDNInput) -> TNDNResult:
        return self.tndn.calculate(input_data)

    def calculate_gtgt(self, input_data: GTGTInput) -> GTGTResult:
        return self.gtgt.calculate(input_data)


# Convenience functions
def calculate_tncn(
    gross_income: Decimal,
    tax_year: TaxYear = TaxYear.Y2025,
    residency: ResidencyStatus = ResidencyStatus.RESIDENT,
    dependents: int = 0,
    insurance: Decimal = Decimal('0'),
    charity: Decimal = Decimal('0'),
    other_deductions: Decimal = Decimal('0')
) -> TNCNResult:
    """Quick TNCN calculation"""
    input_data = TNCNInput(
        tax_year=tax_year,
        residency=residency,
        gross_income=gross_income,
        dependents=dependents,
        insurance_contributions=insurance,
        charity_donations=charity,
        other_deductions=other_deductions
    )
    calc = TaxCalculator()
    return calc.calculate_tncn(input_data)


def calculate_tndn(
    taxable_income: Decimal,
    tax_year: TaxYear = TaxYear.Y2025,
    revenue: Decimal = Decimal('0'),
    preferential_type: Optional[TNDNPreferentialType] = None,
    preferential_years: int = 0,
    brought_forward_losses: Decimal = Decimal('0')
) -> TNDNResult:
    """Quick TNDN calculation"""
    input_data = TNDNInput(
        tax_year=tax_year,
        taxable_income=taxable_income,
        revenue=revenue,
        preferential_type=preferential_type,
        preferential_years_remaining=preferential_years,
        brought_forward_losses=brought_forward_losses
    )
    calc = TaxCalculator()
    return calc.calculate_tndn(input_data)


def calculate_gtgt(
    net_amount: Decimal,
    tax_year: TaxYear = TaxYear.Y2025,
    category: GTGTCategory = GTGTCategory.STANDARD,
    is_export: bool = False
) -> GTGTResult:
    """Quick GTGT calculation"""
    input_data = GTGTInput(
        tax_year=tax_year,
        category=category,
        net_amount=net_amount,
        is_export=is_export
    )
    calc = TaxCalculator()
    return calc.calculate_gtgt(input_data)