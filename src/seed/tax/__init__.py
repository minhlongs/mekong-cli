# Tax & Accounting Module - Vietnam tax compliance engine
# TNCN (Personal Income), TNDN (Corporate), GTGT (VAT) calculators
# TT78 invoice generation, compliance reports, MISA/CSV/Excel export

from .models import (
    TaxYear, ResidencyStatus, TaxType, GTGTCategory, TNDNPreferentialType,
    ExportFormat,
    TNCNInput, TNDNInput, GTGTInput,
    InvoiceHeader, InvoiceLineItem, InvoiceInput,
    ComplianceReportInput, MISAExportInput,
    TNCNResult, TNDNResult, GTGTResult,
    InvoiceResult, ComplianceReport, ExportResult,
    TaxRatesConfig,
    quantize_vnd, quantize_rate,
)
from .calculator import (
    TaxCalculator, TaxRateLoader,
    TNCCalculator, TNDNCalculator, GTGTCalculator,
    calculate_tncn, calculate_tndn, calculate_gtgt,
)
from .invoice import TT78InvoiceGenerator, generate_tt78_invoice
from .compliance import ComplianceReportGenerator, generate_compliance_report
from .exporters import (
    MISAExporter, CSVExporter, ExcelExporter, TaxDataExporter,
    export_misa_journal, export_misa_vat_register,
    export_invoices_csv, export_invoices_excel,
)

__all__ = [
    # Models
    "TaxYear", "ResidencyStatus", "TaxType", "GTGTCategory", "TNDNPreferentialType",
    "ExportFormat",
    "TNCNInput", "TNDNInput", "GTGTInput",
    "InvoiceHeader", "InvoiceLineItem", "InvoiceInput",
    "ComplianceReportInput", "MISAExportInput",
    "TNCNResult", "TNDNResult", "GTGTResult",
    "InvoiceResult", "ComplianceReport", "ExportResult",
    "TaxRatesConfig",
    "quantize_vnd", "quantize_rate",
    # Calculators
    "TaxCalculator", "TaxRateLoader",
    "TNCCalculator", "TNDNCalculator", "GTGTCalculator",
    "calculate_tncn", "calculate_tndn", "calculate_gtgt",
    # Invoice
    "TT78InvoiceGenerator", "generate_tt78_invoice",
    # Compliance
    "ComplianceReportGenerator", "generate_compliance_report",
    # Exporters
    "MISAExporter", "CSVExporter", "ExcelExporter", "TaxDataExporter",
    "export_misa_journal", "export_misa_vat_register",
    "export_invoices_csv", "export_invoices_excel",
]