"""Vietnam Tax & Accounting FastAPI Routes for Mekong CLI Gateway."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.seed.tax import (
    GTGTCategory,
    TNDNPreferentialType,
    TaxCalculator,
    TaxYear,
    ResidencyStatus,
    calculate_gtgt,
    calculate_tndn,
    calculate_tncn,
    generate_compliance_report,
    generate_tt78_invoice,
)
from src.seed.tax.models import (
    ComplianceReportInput,
    InvoiceHeader,
    InvoiceInput,
    InvoiceLineItem,
)

router = APIRouter(prefix="/api/v1/tax", tags=["Tax & Accounting"])

# Shared calculator instance
_tax_calculator: TaxCalculator | None = None


def get_tax_calculator() -> TaxCalculator:
    """Get or create the shared TaxCalculator."""
    global _tax_calculator
    if _tax_calculator is None:
        _tax_calculator = TaxCalculator()
    return _tax_calculator


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class TNCNRequest(BaseModel):
    """Request body for TNCN (personal income tax) calculation."""

    gross_income: str = Field(..., description="Gross monthly income in VND (string for Decimal precision)")
    tax_year: str = Field("2025", description="Tax year: 2024, 2025, 2026")
    residency: str = Field("resident", description="resident | non_resident")
    dependents: int = Field(0, ge=0)
    insurance_contributions: str = Field("0", description="Social/health/unemployment insurance paid")
    charity_donations: str = Field("0", description="Charitable donations")
    other_deductions: str = Field("0", description="Other allowable deductions")


class TNDNRequest(BaseModel):
    """Request body for TNDN (corporate income tax) calculation."""

    taxable_income: str = Field(..., description="Taxable income in VND")
    tax_year: str = Field("2025")
    revenue: str = Field("0", description="Total revenue for SME preferential check")
    preferential_type: str | None = Field(None, description="Preferential type slug")
    preferential_years: int = Field(0, ge=0)
    brought_forward_losses: str = Field("0", description="Losses carried forward")


class GTGTRequest(BaseModel):
    """Request body for GTGT (VAT) calculation."""

    net_amount: str = Field(..., description="Net amount before VAT in VND")
    tax_year: str = Field("2025")
    category: str = Field("standard", description="standard | reduced | exempt | special_consumption")
    is_export: bool = Field(False)


class LineItemModel(BaseModel):
    """Line item for TT78 invoice."""

    description: str = Field(..., min_length=1, max_length=500)
    unit: str = Field(..., min_length=1, max_length=50)
    quantity: str = Field(..., description="Quantity as string")
    unit_price: str = Field(..., description="Unit price as string")
    vat_category: str = Field("standard", description="VAT category slug")


class InvoiceHeaderModel(BaseModel):
    """TT78 invoice header."""

    invoice_number: str = Field(..., pattern=r"^[A-Z0-9\-]{1,20}$")
    invoice_date: str = Field(..., description="ISO date YYYY-MM-DD")
    seller_name: str = Field(..., min_length=1, max_length=200)
    seller_tax_code: str = Field(..., pattern=r"^\d{10,13}$")
    seller_address: str = Field(..., min_length=1, max_length=500)
    buyer_name: str = Field(..., min_length=1, max_length=200)
    buyer_tax_code: str | None = None
    buyer_address: str = Field(..., min_length=1, max_length=500)
    payment_method: str = Field("Chuyển khoản")
    currency: str = Field("VND")


class InvoiceRequest(BaseModel):
    """Request body for TT78 invoice generation."""

    header: InvoiceHeaderModel
    line_items: list[LineItemModel] = Field(..., min_length=1)
    notes: str | None = None


class ComplianceReportRequest(BaseModel):
    """Request body for compliance report generation."""

    tax_year: str = Field("2025")
    company_tax_code: str = Field(..., pattern=r"^\d{10,13}$")
    company_name: str = Field(..., min_length=1)
    reporting_period: str = Field(..., description="e.g. Q1, H1, FY")
    include_tncn: bool = True
    include_tndn: bool = True
    include_gtgt: bool = True


# ---------------------------------------------------------------------------
# Tax calculation endpoints
# ---------------------------------------------------------------------------


@router.post("/tncn", summary="Calculate TNCN (Personal Income Tax)")
def calc_tncn(body: TNCNRequest) -> dict[str, Any]:
    """Calculate Vietnam Personal Income Tax (TNCN)."""
    try:
        result = calculate_tncn(
            gross_income=Decimal(body.gross_income),
            tax_year=TaxYear(body.tax_year),
            residency=ResidencyStatus(body.residency),
            dependents=body.dependents,
            insurance=Decimal(body.insurance_contributions),
            charity=Decimal(body.charity_donations),
            other_deductions=Decimal(body.other_deductions),
        )
        return result.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/tndn", summary="Calculate TNDN (Corporate Income Tax)")
def calc_tndn(body: TNDNRequest) -> dict[str, Any]:
    """Calculate Vietnam Corporate Income Tax (TNDN)."""
    try:
        pref_type = TNDNPreferentialType(body.preferential_type) if body.preferential_type else None
        result = calculate_tndn(
            taxable_income=Decimal(body.taxable_income),
            tax_year=TaxYear(body.tax_year),
            revenue=Decimal(body.revenue),
            preferential_type=pref_type,
            preferential_years=body.preferential_years,
            brought_forward_losses=Decimal(body.brought_forward_losses),
        )
        return result.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/gtgt", summary="Calculate GTGT (Value Added Tax)")
def calc_gtgt(body: GTGTRequest) -> dict[str, Any]:
    """Calculate Vietnam Value Added Tax (GTGT)."""
    try:
        result = calculate_gtgt(
            net_amount=Decimal(body.net_amount),
            tax_year=TaxYear(body.tax_year),
            category=GTGTCategory(body.category),
            is_export=body.is_export,
        )
        return result.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/rates/{tax_year}", summary="Get tax rates for a year")
def get_rates(tax_year: str) -> dict[str, Any]:
    """Return the effective tax rates configuration for a given year."""
    try:
        loader = get_tax_calculator().rate_loader
        config = loader.load_rates(TaxYear(tax_year))
        return config.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Invoice endpoints
# ---------------------------------------------------------------------------


@router.post("/invoice/tt78", summary="Generate TT78 VAT invoice (PDF)")
def create_tt78_invoice(body: InvoiceRequest) -> dict[str, Any]:
    """Generate a TT78-compliant VAT invoice PDF."""
    try:
        from datetime import date

        invoice_date = date.fromisoformat(body.header.invoice_date)

        header = InvoiceHeader(
            invoice_number=body.header.invoice_number,
            invoice_date=invoice_date,
            seller_name=body.header.seller_name,
            seller_tax_code=body.header.seller_tax_code,
            seller_address=body.header.seller_address,
            buyer_name=body.header.buyer_name,
            buyer_tax_code=body.header.buyer_tax_code,
            buyer_address=body.header.buyer_address,
            payment_method=body.header.payment_method,
            currency=body.header.currency,
        )

        line_items = []
        for i, item in enumerate(body.line_items, start=1):
            line_items.append(
                InvoiceLineItem(
                    line_number=i,
                    description=item.description,
                    unit=item.unit,
                    quantity=Decimal(item.quantity),
                    unit_price=Decimal(item.unit_price),
                    vat_category=GTGTCategory(item.vat_category),
                )
            )

        invoice = InvoiceInput(header=header, line_items=line_items, notes=body.notes)
        result = generate_tt78_invoice(invoice)

        return {
            "invoice_number": result.invoice_number,
            "pdf_base64": result.pdf_base64,
            "total_net": str(result.total_net),
            "total_vat": str(result.total_vat),
            "total_gross": str(result.total_gross),
            "qr_code_data": result.qr_code_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Compliance & export endpoints
# ---------------------------------------------------------------------------


@router.post("/compliance", summary="Generate tax compliance report")
def create_compliance_report(body: ComplianceReportRequest) -> dict[str, Any]:
    """Generate a Vietnam tax compliance report."""
    try:
        input_data = ComplianceReportInput(
            tax_year=TaxYear(body.tax_year),
            company_tax_code=body.company_tax_code,
            company_name=body.company_name,
            reporting_period=body.reporting_period,
            include_tncn=body.include_tncn,
            include_tndn=body.include_tndn,
            include_gtgt=body.include_gtgt,
        )
        report = generate_compliance_report(input_data)
        return report.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/health", summary="Tax engine health check")
def tax_health() -> dict[str, str]:
    """Check the tax engine is functional."""
    try:
        loader = get_tax_calculator().rate_loader
        for year in ("2024", "2025", "2026"):
            loader.load_rates(TaxYear(year))
        return {"status": "healthy", "service": "tax-engine", "years": "2024,2025,2026"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
