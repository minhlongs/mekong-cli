# Tax Models - Pydantic models for Vietnam tax calculations
# All monetary values use Decimal for precision

from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime


class TaxYear(str, Enum):
    """Supported tax years"""
    Y2024 = "2024"
    Y2025 = "2025"
    Y2026 = "2026"


class ResidencyStatus(str, Enum):
    """Tax residency status"""
    RESIDENT = "resident"
    NON_RESIDENT = "non_resident"


class TaxType(str, Enum):
    """Vietnam tax types"""
    TNCN = "tncn"          # Personal Income Tax
    TNDN = "tndn"          # Corporate Income Tax
    GTGT = "gtgt"          # Value Added Tax
    SCTT = "sctt"          # Special Consumption Tax
    NATURAL_RESOURCES = "natural_resources"
    ENVIRONMENTAL = "environmental"


class GTGTCategory(str, Enum):
    """VAT categories"""
    STANDARD = "standard"
    REDUCED = "reduced"
    EXEMPT = "exempt"
    SPECIAL_CONSUMPTION = "special_consumption"


class TNDNPreferentialType(str, Enum):
    """Corporate tax preferential types"""
    ENCOURAGED_SECTORS = "encouraged_sectors"
    HIGH_TECH = "high_tech"
    EDUCATION_HEALTHCARE = "education_healthcare"
    SME = "sme"


# ============================================
# Input Models
# ============================================

class TNCNInput(BaseModel):
    """Input for Personal Income Tax calculation"""
    tax_year: TaxYear = TaxYear.Y2025
    residency: ResidencyStatus = ResidencyStatus.RESIDENT
    gross_income: Decimal = Field(..., ge=0, description="Gross monthly income in VND")
    dependents: int = Field(default=0, ge=0, description="Number of dependents")
    insurance_contributions: Decimal = Field(default=Decimal('0'), ge=0, description="Social/health/unemployment insurance paid")
    charity_donations: Decimal = Field(default=Decimal('0'), ge=0, description="Charitable donations (deductible)")
    other_deductions: Decimal = Field(default=Decimal('0'), ge=0, description="Other allowable deductions")


class TNDNInput(BaseModel):
    """Input for Corporate Income Tax calculation"""
    tax_year: TaxYear = TaxYear.Y2025
    taxable_income: Decimal = Field(..., ge=0, description="Taxable income in VND")
    revenue: Decimal = Field(default=Decimal('0'), ge=0, description="Total revenue for SME check")
    preferential_type: Optional[TNDNPreferentialType] = None
    preferential_years_remaining: int = Field(default=0, ge=0)
    brought_forward_losses: Decimal = Field(default=Decimal('0'), ge=0, description="Losses carried forward from previous years")


class GTGTInput(BaseModel):
    """Input for VAT calculation"""
    tax_year: TaxYear = TaxYear.Y2025
    category: GTGTCategory = GTGTCategory.STANDARD
    net_amount: Decimal = Field(..., ge=0, description="Net amount before VAT in VND")
    is_export: bool = Field(default=False, description="Whether this is an export transaction")


class InvoiceLineItem(BaseModel):
    """Line item for tax invoice"""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    unit: str = Field(..., min_length=1, max_length=50)
    quantity: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    vat_category: GTGTCategory = GTGTCategory.STANDARD
    vat_rate: Optional[Decimal] = None  # Auto-filled if not provided

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price

    @property
    def vat_amount(self) -> Decimal:
        rate = self.vat_rate if self.vat_rate is not None else Decimal('0.10')
        return (self.line_total * rate).quantize(Decimal('1'))


class InvoiceHeader(BaseModel):
    """Invoice header information (TT78 compliant)"""
    invoice_number: str = Field(..., pattern=r'^[A-Z0-9\-]{1,20}$')
    invoice_date: date
    invoice_template: str = Field(default="TT78", pattern=r'^TT\d{2}$')

    # Seller information
    seller_name: str = Field(..., min_length=1, max_length=200)
    seller_tax_code: str = Field(..., pattern=r'^\d{10,13}$')
    seller_address: str = Field(..., min_length=1, max_length=500)
    seller_bank_account: Optional[str] = None
    seller_bank_name: Optional[str] = None

    # Buyer information
    buyer_name: str = Field(..., min_length=1, max_length=200)
    buyer_tax_code: Optional[str] = Field(default=None, pattern=r'^\d{10,13}$')
    buyer_address: str = Field(..., min_length=1, max_length=500)
    buyer_bank_account: Optional[str] = None
    buyer_bank_name: Optional[str] = None

    # Payment
    payment_method: str = Field(default="Chuyển khoản", description="Payment method")
    currency: str = Field(default="VND")
    exchange_rate: Decimal = Field(default=Decimal('1'))


class InvoiceInput(BaseModel):
    """Complete invoice input for TT78 generation"""
    header: InvoiceHeader
    line_items: List[InvoiceLineItem] = Field(..., min_length=1)
    notes: Optional[str] = None
    digital_signature: Optional[str] = None  # Base64 encoded signature


class ComplianceReportInput(BaseModel):
    """Input for compliance report generation"""
    tax_year: TaxYear
    company_tax_code: str = Field(..., pattern=r'^\d{10,13}$')
    company_name: str
    reporting_period: str = Field(..., description="e.g., 'Q1', 'H1', 'FY'")
    include_tncn: bool = True
    include_tndn: bool = True
    include_gtgt: bool = True


class ExportFormat(str, Enum):
    """Export formats for tax data"""
    MISA = "misa"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class MISAExportInput(BaseModel):
    """Input for MISA export"""
    tax_year: TaxYear
    company_tax_code: str
    data_type: str = Field(..., description="Type of data: 'journal', 'ledger', 'vat_register'")
    start_date: date
    end_date: date


# ============================================
# Output Models
# ============================================

class TNCNResult(BaseModel):
    """Personal Income Tax calculation result"""
    tax_year: str
    residency: str
    gross_income: Decimal
    taxable_income: Decimal
    tax_payable: Decimal
    effective_rate: Decimal
    brackets_applied: List[Dict[str, Any]]
    deductions: Dict[str, Decimal]
    net_income: Decimal


class TNDNResult(BaseModel):
    """Corporate Income Tax calculation result"""
    tax_year: str
    taxable_income: Decimal
    applicable_rate: Decimal
    tax_before_incentives: Decimal
    incentives_applied: List[Dict[str, Any]]
    tax_payable: Decimal
    losses_carried_forward: Decimal


class GTGTResult(BaseModel):
    """VAT calculation result"""
    tax_year: str
    category: str
    net_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    gross_amount: Decimal


class InvoiceResult(BaseModel):
    """Invoice generation result"""
    invoice_number: str
    pdf_bytes: bytes
    pdf_base64: str
    total_net: Decimal
    total_vat: Decimal
    total_gross: Decimal
    qr_code_data: Optional[str] = None


class ComplianceReport(BaseModel):
    """Compliance report output"""
    report_id: str
    generated_at: datetime
    tax_year: str
    company_tax_code: str
    company_name: str
    reporting_period: str
    tncn_summary: Optional[Dict[str, Any]] = None
    tndn_summary: Optional[Dict[str, Any]] = None
    gtgt_summary: Optional[Dict[str, Any]] = None
    total_tax_liability: Decimal
    file_path: Optional[str] = None


class ExportResult(BaseModel):
    """Export operation result"""
    format: ExportFormat
    file_path: str
    record_count: int
    file_size_bytes: int
    generated_at: datetime


# ============================================
# Configuration Models
# ============================================

class TNCNRates(BaseModel):
    """TNCN tax rate configuration"""
    brackets: List[Dict[str, Any]]
    personal_deduction_monthly: Decimal
    dependent_deduction_monthly: Decimal
    non_resident_flat_rate: Decimal


class TNDNRates(BaseModel):
    """TNDN tax rate configuration"""
    standard_rate: Decimal
    preferential_rates: List[Dict[str, Any]]
    loss_carryforward_years: int


class GTGTRates(BaseModel):
    """GTGT tax rate configuration"""
    standard_rate: Decimal
    reduced_rate: Decimal
    exempt_rate: Decimal
    categories: List[Dict[str, Any]]


class TaxRatesConfig(BaseModel):
    """Complete tax rates configuration for a year"""
    version: str
    effective_from: str
    effective_to: str
    tncn: TNCNRates
    tndn: TNDNRates
    gtgt: GTGTRates
    currency: str
    rounding: str
    precision: int


# ============================================
# Utility Functions
# ============================================

def quantize_vnd(amount: Decimal) -> Decimal:
    """Quantize amount to VND (no decimal places)"""
    return amount.quantize(Decimal('1'))


def quantize_rate(rate: Decimal) -> Decimal:
    """Quantize tax rate to 4 decimal places"""
    return rate.quantize(Decimal('0.0001'))