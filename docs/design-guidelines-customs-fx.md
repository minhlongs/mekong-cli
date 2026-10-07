# Design Guidelines — Vietnam Customs, FX & Bonded Logistics Terminal UI

**Document Version:** 1.0  
**Date:** 2026-10-07  
**Scope:** Terminal Interfaces & Rich Visualization for Phases 167 - 170

---

## 1. Visual Aesthetics & Token Palette

The Customs & Foreign Exchange terminal UI employs a distinct regulatory and trade logistics theme:

- **Border Style:** `box.ROUNDED` for institutional authority.
- **Customs Primary Blue:** `cyan` (`#00BCD4`) for customs classification & declarations.
- **Foreign Exchange Green:** `green` (`#4CAF50`) for capital accounts, loan approvals & positive origin status.
- **Warning / Audit Yellow:** `yellow` (`#FFC107`) for post-clearance audits & statutory limits.
- **Risk / Violation Red:** `bold red` (`#F44336`) for non-originating goods, unregistered loans, prohibited clauses, and expired storage.
- **Statutory Reference:** `dim` (`#888888`) for statutory citations (Decrees, Circulars, Laws).

---

## 2. Terminal UI Layouts

1. **Customs Valuation Panels:**
   - Detailed calculation table with breakdown of FOB/CIF price, additions (freight, insurance, royalties), deductions, and final assessable customs value.
2. **Rules of Origin (RVC) Status:**
   - Dual badge system: `[bold green]ĐẠT TIÊU CHÍ XUẤT XỨ (ORIGINATING)[/]` vs `[bold red]KHÔNG ĐẠT TIÊU CHÍ (NON-ORIGINATING)[/]`.
3. **SBV Foreign Loan & Bonded Storage Tracker:**
   - Remaining storage days gauge and expiration alert badges.
