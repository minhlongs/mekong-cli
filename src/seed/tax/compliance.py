# Compliance Report Generator
# Generates Vietnam tax compliance reports for TNCN, TNDN, GTGT

from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import json
import csv
from io import StringIO

from .models import (
    ComplianceReportInput, ComplianceReport,
    TNCNInput, TNDNInput, GTGTInput,
    TaxYear, ResidencyStatus, GTGTCategory,
    quantize_vnd
)
from .calculator import TaxCalculator


class ComplianceReportGenerator:
    """Generates comprehensive tax compliance reports"""

    def __init__(self, calculator: Optional[TaxCalculator] = None):
        self.calculator = calculator or TaxCalculator()

    def generate(self, input_data: ComplianceReportInput) -> ComplianceReport:
        """Generate full compliance report"""
        report_id = f"RPT-{input_data.tax_year.value}-{input_data.company_tax_code}-{input_data.reporting_period}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        tncn_summary = None
        tndn_summary = None
        gtgt_summary = None
        total_liability = Decimal('0')

        # Generate TNCN summary if requested
        if input_data.include_tncn:
            tncn_summary = self._generate_tncn_summary(input_data)
            total_liability += tncn_summary.get('total_tax', Decimal('0'))

        # Generate TNDN summary if requested
        if input_data.include_tndn:
            tndn_summary = self._generate_tndn_summary(input_data)
            total_liability += tndn_summary.get('total_tax', Decimal('0'))

        # Generate GTGT summary if requested
        if input_data.include_gtgt:
            gtgt_summary = self._generate_gtgt_summary(input_data)
            total_liability += gtgt_summary.get('total_vat_payable', Decimal('0'))

        total_liability = quantize_vnd(total_liability)

        return ComplianceReport(
            report_id=report_id,
            generated_at=datetime.now(),
            tax_year=input_data.tax_year.value,
            company_tax_code=input_data.company_tax_code,
            company_name=input_data.company_name,
            reporting_period=input_data.reporting_period,
            tncn_summary=tncn_summary,
            tndn_summary=tndn_summary,
            gtgt_summary=gtgt_summary,
            total_tax_liability=total_liability
        )

    def _generate_tncn_summary(self, input_data: ComplianceReportInput) -> Dict[str, Any]:
        """Generate TNCN summary for the reporting period"""
        # In production, this would query actual payroll data
        # For now, return a structured template
        return {
            'period': input_data.reporting_period,
            'employee_count': 0,
            'total_gross_income': Decimal('0'),
            'total_taxable_income': Decimal('0'),
            'total_tax_withheld': Decimal('0'),
            'total_tax_paid': Decimal('0'),
            'total_tax': Decimal('0'),
            'details': [],
            'notes': 'TNCN summary requires payroll data integration'
        }

    def _generate_tndn_summary(self, input_data: ComplianceReportInput) -> Dict[str, Any]:
        """Generate TNDN summary for the reporting period"""
        return {
            'period': input_data.reporting_period,
            'taxable_income': Decimal('0'),
            'applicable_rate': Decimal('0.20'),
            'tax_payable': Decimal('0'),
            'provisional_tax_paid': Decimal('0'),
            'final_tax_payable': Decimal('0'),
            'total_tax': Decimal('0'),
            'losses_carried_forward': Decimal('0'),
            'incentives_applied': [],
            'notes': 'TNDN summary requires financial statements integration'
        }

    def _generate_gtgt_summary(self, input_data: ComplianceReportInput) -> Dict[str, Any]:
        """Generate GTGT (VAT) summary for the reporting period"""
        return {
            'period': input_data.reporting_period,
            'output_vat': Decimal('0'),      # VAT on sales
            'input_vat': Decimal('0'),       # VAT on purchases
            'vat_payable': Decimal('0'),     # Output - Input
            'vat_refundable': Decimal('0'),  # If Input > Output
            'total_vat_payable': Decimal('0'),
            'transactions_count': 0,
            'by_category': {
                'standard': {'count': 0, 'net': Decimal('0'), 'vat': Decimal('0')},
                'reduced': {'count': 0, 'net': Decimal('0'), 'vat': Decimal('0')},
                'exempt': {'count': 0, 'net': Decimal('0'), 'vat': Decimal('0')},
            },
            'notes': 'GTGT summary requires invoice data integration'
        }

    def generate_monthly_tncn_report(
        self,
        tax_year: TaxYear,
        company_tax_code: str,
        company_name: str,
        month: int,
        payroll_data: List[Dict[str, Any]]
    ) -> ComplianceReport:
        """Generate monthly TNCN report from payroll data"""
        total_gross = Decimal('0')
        total_taxable = Decimal('0')
        total_tax = Decimal('0')
        details = []

        for emp in payroll_data:
            gross = Decimal(str(emp.get('gross_income', 0)))
            dependents = emp.get('dependents', 0)
            insurance = Decimal(str(emp.get('insurance', 0)))
            charity = Decimal(str(emp.get('charity', 0)))

            tncn_input = TNCNInput(
                tax_year=tax_year,
                residency=ResidencyStatus.RESIDENT,
                gross_income=gross,
                dependents=dependents,
                insurance_contributions=insurance,
                charity_donations=charity
            )
            result = self.calculator.calculate_tncn(tncn_input)

            total_gross += result.gross_income
            total_taxable += result.taxable_income
            total_tax += result.tax_payable

            details.append({
                'employee_id': emp.get('employee_id'),
                'employee_name': emp.get('employee_name'),
                'gross_income': result.gross_income,
                'taxable_income': result.taxable_income,
                'tax_payable': result.tax_payable,
                'net_income': result.net_income
            })

        period = f"{tax_year.value}-{month:02d}"
        report = ComplianceReport(
            report_id=f"TNCN-{company_tax_code}-{period}",
            generated_at=datetime.now(),
            tax_year=tax_year.value,
            company_tax_code=company_tax_code,
            company_name=company_name,
            reporting_period=period,
            tncn_summary={
                'period': period,
                'employee_count': len(payroll_data),
                'total_gross_income': quantize_vnd(total_gross),
                'total_taxable_income': quantize_vnd(total_taxable),
                'total_tax_withheld': quantize_vnd(total_tax),
                'total_tax_paid': Decimal('0'),
                'total_tax': quantize_vnd(total_tax),
                'details': details
            },
            total_tax_liability=quantize_vnd(total_tax)
        )
        return report

    def generate_quarterly_gtgt_report(
        self,
        tax_year: TaxYear,
        company_tax_code: str,
        company_name: str,
        quarter: int,
        invoice_data: List[Dict[str, Any]]
    ) -> ComplianceReport:
        """Generate quarterly GTGT (VAT) report from invoice data"""
        output_vat = Decimal('0')
        input_vat = Decimal('0')
        by_category: Dict[str, Dict[str, Any]] = {
            'standard': {'count': 0, 'net': Decimal('0'), 'vat': Decimal('0')},
            'reduced': {'count': 0, 'net': Decimal('0'), 'vat': Decimal('0')},
            'exempt': {'count': 0, 'net': Decimal('0'), 'vat': Decimal('0')},
        }

        for inv in invoice_data:
            net = Decimal(str(inv.get('net_amount', 0)))
            category = inv.get('vat_category', 'standard')
            is_export = inv.get('is_export', False)
            is_purchase = inv.get('is_purchase', False)

            gtgt_input = GTGTInput(
                tax_year=tax_year,
                category=GTGTCategory(category),
                net_amount=net,
                is_export=is_export
            )
            result = self.calculator.calculate_gtgt(gtgt_input)

            if is_purchase:
                input_vat += result.vat_amount
            else:
                output_vat += result.vat_amount
                cat_key = category if category in by_category else 'standard'
                by_category[cat_key]['count'] += 1
                by_category[cat_key]['net'] += result.net_amount
                by_category[cat_key]['vat'] += result.vat_amount

        vat_payable = output_vat - input_vat
        vat_refundable = Decimal('0')
        if vat_payable < 0:
            vat_refundable = -vat_payable
            vat_payable = Decimal('0')

        period = f"{tax_year.value}-Q{quarter}"
        report = ComplianceReport(
            report_id=f"GTGT-{company_tax_code}-{period}",
            generated_at=datetime.now(),
            tax_year=tax_year.value,
            company_tax_code=company_tax_code,
            company_name=company_name,
            reporting_period=period,
            gtgt_summary={
                'period': period,
                'output_vat': quantize_vnd(output_vat),
                'input_vat': quantize_vnd(input_vat),
                'vat_payable': quantize_vnd(vat_payable),
                'vat_refundable': quantize_vnd(vat_refundable),
                'total_vat_payable': quantize_vnd(vat_payable),
                'transactions_count': len(invoice_data),
                'by_category': {k: {**v, 'net': quantize_vnd(v['net']), 'vat': quantize_vnd(v['vat'])} for k, v in by_category.items()}
            },
            total_tax_liability=quantize_vnd(vat_payable)
        )
        return report

    def generate_annual_tndn_report(
        self,
        tax_year: TaxYear,
        company_tax_code: str,
        company_name: str,
        financial_data: Dict[str, Any]
    ) -> ComplianceReport:
        """Generate annual TNDN report from financial data"""
        taxable_income = Decimal(str(financial_data.get('taxable_income', 0)))
        revenue = Decimal(str(financial_data.get('revenue', 0)))
        preferential_type = financial_data.get('preferential_type')
        preferential_years = financial_data.get('preferential_years_remaining', 0)
        brought_forward_losses = Decimal(str(financial_data.get('brought_forward_losses', 0)))
        provisional_tax_paid = Decimal(str(financial_data.get('provisional_tax_paid', 0)))

        tndn_input = TNDNInput(
            tax_year=tax_year,
            taxable_income=taxable_income,
            revenue=revenue,
            preferential_type=preferential_type,
            preferential_years_remaining=preferential_years,
            brought_forward_losses=brought_forward_losses
        )
        result = self.calculator.calculate_tndn(tndn_input)

        final_tax = result.tax_payable - provisional_tax_paid
        if final_tax < 0:
            final_tax = Decimal('0')

        report = ComplianceReport(
            report_id=f"TNDN-{company_tax_code}-{tax_year.value}",
            generated_at=datetime.now(),
            tax_year=tax_year.value,
            company_tax_code=company_tax_code,
            company_name=company_name,
            reporting_period="FY",
            tndn_summary={
                'period': "FY",
                'taxable_income': result.taxable_income,
                'applicable_rate': result.applicable_rate,
                'tax_before_incentives': result.tax_before_incentives,
                'incentives_applied': result.incentives_applied,
                'tax_payable': result.tax_payable,
                'provisional_tax_paid': quantize_vnd(provisional_tax_paid),
                'final_tax_payable': quantize_vnd(final_tax),
                'total_tax': result.tax_payable,
                'losses_carried_forward': result.losses_carried_forward
            },
            total_tax_liability=quantize_vnd(final_tax)
        )
        return report

    def to_json(self, report: ComplianceReport) -> str:
        """Export report to JSON"""
        def decimal_serializer(obj: Any) -> str:
            if isinstance(obj, Decimal):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(report.model_dump(), default=decimal_serializer, indent=2, ensure_ascii=False)

    def to_csv(self, report: ComplianceReport) -> str:
        """Export report summary to CSV"""
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['Field', 'Value'])
        writer.writerow(['Report ID', report.report_id])
        writer.writerow(['Generated At', report.generated_at.isoformat()])
        writer.writerow(['Tax Year', report.tax_year])
        writer.writerow(['Company Tax Code', report.company_tax_code])
        writer.writerow(['Company Name', report.company_name])
        writer.writerow(['Reporting Period', report.reporting_period])
        writer.writerow(['Total Tax Liability', str(report.total_tax_liability)])

        # TNCN
        if report.tncn_summary:
            writer.writerow([])
            writer.writerow(['TNCN Summary', ''])
            for key, value in report.tncn_summary.items():
                if key != 'details':
                    writer.writerow([key, str(value)])

        # TNDN
        if report.tndn_summary:
            writer.writerow([])
            writer.writerow(['TNDN Summary', ''])
            for key, value in report.tndn_summary.items():
                writer.writerow([key, str(value)])

        # GTGT
        if report.gtgt_summary:
            writer.writerow([])
            writer.writerow(['GTGT Summary', ''])
            for key, value in report.gtgt_summary.items():
                if key != 'by_category':
                    writer.writerow([key, str(value)])

        return output.getvalue()


def generate_compliance_report(input_data: ComplianceReportInput) -> ComplianceReport:
    """Convenience function to generate compliance report"""
    generator = ComplianceReportGenerator()
    return generator.generate(input_data)