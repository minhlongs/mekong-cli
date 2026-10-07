# Project Changelog

## v6.19.0 — 2026-10-07

**Maritime VNSW, Manning, Quarantine & MARPOL (Phases 191-194) (100% Complete):**

- **Phase 191: Maritime Single Window (VNSW) Port Clearance (`src/core/maritime_vnsw_quarantine_marpol_engine.py`):**
  - Statutory arrival/departure notification logic (24h/2h thresholds) with FAL 1-7 document checklist validation.
  - PKI permit generation with SHA-256 digital permit hashing and QR verification URL integration.
  - Statutory statutory math for International (15000 GT default) and Domestic (3000 GT default) vessel dues calculation (Tonnage: 0.034/0.045 USD/GT, Safety: 0.045 USD/GT, Clearance: 100k/50k VND).
- **Phase 192: Seafarer Manning & Border Control (`src/core/maritime_vnsw_quarantine_marpol_engine.py`):**
  - Minimum Safe Manning (MSMD) rank auditing (Master, Chief Mate, CE, 2nd Eng) & Seafarer Discharge Book validity.
  - STCW 78/2010 Manila Amendments fatigue enforcement (rest hours/intervals).
  - Shore Pass (Thẻ đi bờ) eligibility scoring based on STCW compliance & crew-list integrity.
- **Phase 193: Maritime International Health Quarantine (`src/core/maritime_vnsw_quarantine_marpol_engine.py`):**
  - IHR 2005 MDH evaluation, SSCEC validation audit, Epidemiological Risk Scoring ($ERS = 3 \cdot N_{inf} + 2.5_{exp} + 2.0_{endemic}$).
  - State machine triggering `FREE_PRATIQUE_GRANTED`, `QUARANTINE_ANCHORAGE_REQUIRED`, or `ISOLATION_AND_DISINFECTION`.
- **Phase 194: MARPOL 73/78 & Port Reception Facilities (`src/core/maritime_vnsw_quarantine_marpol_engine.py`):**
  - Annex I (OWS < 15 ppm) & Annex VI (Sulfur < 0.50%) compliance engine.
  - Automated PRF fee levy (1.5M/m³ Sludge, 400k/m³ Garbage) and VN-PRF receipt certification.
- **CLI Commands (`src/cli/commands/maritime_vnsw_quarantine_marpol_command.py`):**
  - Registered 4 command groups: `vnsw` (alias `motcua`), `seafarer` (alias `thuyenvien`), `quarantine` (alias `kiemdich`), `marpol` (alias `moitruongbien`).
- **MCP Tool Integration (`scripts/mcp_server.py`):**
  - 4 specialized FastMCP & JSON-RPC tools for VNSW clearance, Seafarer audits, Quarantine evaluation, and MARPOL environmental compliance.
- **TestSuite (`tests/test_maritime_vnsw_quarantine_marpol_suite.py`):**
  - 15 automated unit and integration tests covering business mathematics, CLI invocation contracts, MCP handlers, and zero-dependency AST invariants.
