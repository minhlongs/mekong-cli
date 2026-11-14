"""MISA meInvoice / Sapo Invoice Pre-Accounting Draft Serializer (CSV, JSON, XML).

Compliance boundary (Decree 123/2020/NĐ-CP):
- Serializes ONLY uncertified pre-accounting drafts ('DRAFT_PENDING_TVAN').
- Rejects 'ISSUED', legal_certified=True, or requires_tvan_signature=False fail-closed.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Final
from xml.sax.saxutils import escape as xml_escape

from src.opc.accounting_draft import ALLOWED_ACCOUNTING_TARGETS, DRAFT_STATUS_PENDING_TVAN, AccountingDraftExport

MISA_SAPO_COLUMNS: Final[tuple[str, ...]] = (
    "MaHoSoNhap",
    "TrangThaiHoaDon",
    "TenNguoiMua",
    "TenHangHoaDichVu",
    "SoLuong",
    "DonGia",
    "ThanhTien",
    "ThueSuatGTGT",
    "TienThueGTGT",
    "TongTienThanhToan",
    "MaGiaoDichVietQR",
)

_CSV_FORMULA_PREFIXES: Final[tuple[str, ...]] = ("=", "+", "-", "@")


class DraftExportComplianceError(PermissionError):
    """Raised when an accounting draft violates Decree 123 pre-accounting draft boundaries."""


def _assert_draft_compliance(draft: AccountingDraftExport) -> None:
    if draft.invoice_status != DRAFT_STATUS_PENDING_TVAN:
        raise DraftExportComplianceError(
            f"Refusing to serialize invoice_status='{draft.invoice_status}'; only '{DRAFT_STATUS_PENDING_TVAN}' is permitted."
        )
    if draft.legal_certified is not False:
        raise DraftExportComplianceError("Refusing to serialize legally certified invoice; TVAN signature is external.")
    if draft.requires_tvan_signature is not True:
        raise DraftExportComplianceError("Draft must require external TVAN digital signature (requires_tvan_signature=True).")
    if draft.target_provider not in ALLOWED_ACCOUNTING_TARGETS:
        raise DraftExportComplianceError(f"Unsupported accounting target_provider '{draft.target_provider}'.")
    if not draft.line_items:
        raise DraftExportComplianceError("AccountingDraftExport must contain at least one line item.")


def _safe_csv_text(val: str) -> str:
    stripped = val.lstrip()
    return f"'{val}" if stripped.startswith(_CSV_FORMULA_PREFIXES) else val


def _build_misa_rows(draft: AccountingDraftExport) -> list[dict[str, Any]]:
    _assert_draft_compliance(draft)
    tx_ref = draft.bank_tx_id or ""
    rows: list[dict[str, Any]] = []
    vat_remaining = int(draft.vat_amount_vnd)
    n_items = len(draft.line_items)
    for idx, item in enumerate(draft.line_items):
        line_sub = int(item["line_subtotal_vnd"])
        if idx == n_items - 1:
            line_vat = vat_remaining
        else:
            line_vat = (line_sub * int(draft.vat_rate_pct)) // 100
            vat_remaining -= line_vat
        rows.append(
            {
                "MaHoSoNhap": draft.draft_id,
                "TrangThaiHoaDon": DRAFT_STATUS_PENDING_TVAN,
                "TenNguoiMua": draft.buyer_name,
                "TenHangHoaDichVu": str(item["item_name"]),
                "SoLuong": int(item["quantity"]),
                "DonGia": int(item["unit_price_vnd"]),
                "ThanhTien": line_sub,
                "ThueSuatGTGT": int(draft.vat_rate_pct),
                "TienThueGTGT": line_vat,
                "TongTienThanhToan": line_sub + line_vat,
                "MaGiaoDichVietQR": tx_ref,
            }
        )
    return rows


def export_misa_csv(draft: AccountingDraftExport) -> str:
    """Serialize pre-accounting draft to deterministic MISA meInvoice / Sapo CSV."""
    rows = _build_misa_rows(draft)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(MISA_SAPO_COLUMNS), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        sanitized = {
            k: (_safe_csv_text(v) if isinstance(v, str) else v)
            for k, v in row.items()
        }
        writer.writerow(sanitized)
    return buf.getvalue()


def _esc(val: object) -> str:
    return xml_escape(str(val), {'"': "&quot;", "'": "&apos;"})


def export_misa_xml(draft: AccountingDraftExport) -> str:
    """Serialize pre-accounting draft to escaped XML for MISA meInvoice / Sapo import."""
    rows = _build_misa_rows(draft)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<HoaDonNhap provider="{_esc(draft.target_provider)}" '
            f'run_id="{_esc(draft.run_id)}" sha256="{_esc(draft.payload_sha256)}" '
            f'requires_tvan_signature="true" legal_certified="false">'
        ),
        f"  <MaHoSoNhap>{_esc(draft.draft_id)}</MaHoSoNhap>",
        f"  <TrangThaiHoaDon>{_esc(DRAFT_STATUS_PENDING_TVAN)}</TrangThaiHoaDon>",
        f"  <TenNguoiMua>{_esc(draft.buyer_name)}</TenNguoiMua>",
        f"  <DonViTienTe>{_esc(draft.currency)}</DonViTienTe>",
        f"  <TongTienChuaThue>{draft.subtotal_vnd}</TongTienChuaThue>",
        f"  <ThueSuatGTGT>{draft.vat_rate_pct}</ThueSuatGTGT>",
        f"  <TienThueGTGT>{draft.vat_amount_vnd}</TienThueGTGT>",
        f"  <TongTienThanhToan>{draft.total_amount_vnd}</TongTienThanhToan>",
        f"  <MaGiaoDichVietQR>{_esc(draft.bank_tx_id or '')}</MaGiaoDichVietQR>",
        "  <DanhSachHangHoaDichVu>",
    ]
    for row in rows:
        lines.append("    <DongHangHoa>")
        for col in MISA_SAPO_COLUMNS:
            lines.append(f"      <{col}>{_esc(row[col])}</{col}>")
        lines.append("    </DongHangHoa>")
    lines.extend(["  </DanhSachHangHoaDichVu>", "</HoaDonNhap>"])
    return "\n".join(lines) + "\n"


def export_draft_bundle(draft: AccountingDraftExport, fmt: str = "json") -> str:
    """Export AccountingDraftExport in deterministic 'json', 'csv', or 'xml' format."""
    norm_fmt = (fmt or "").strip().lower()
    if norm_fmt == "csv":
        return export_misa_csv(draft)
    if norm_fmt == "xml":
        return export_misa_xml(draft)
    if norm_fmt == "json":
        rows = _build_misa_rows(draft)
        payload = {
            "schema_version": "opc-misa-sapo-draft/v1",
            "draft_id": draft.draft_id,
            "run_id": draft.run_id,
            "target_provider": draft.target_provider,
            "invoice_status": DRAFT_STATUS_PENDING_TVAN,
            "requires_tvan_signature": True,
            "legal_certified": False,
            "currency": draft.currency,
            "subtotal_vnd": draft.subtotal_vnd,
            "vat_rate_pct": draft.vat_rate_pct,
            "vat_amount_vnd": draft.vat_amount_vnd,
            "total_amount_vnd": draft.total_amount_vnd,
            "payload_sha256": draft.payload_sha256,
            "rows": rows,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    raise ValueError(f"Unsupported draft export format '{fmt}' (expected 'json', 'csv', or 'xml').")
