# Product Development Requirements (PDR) — Dispute Resolution & Maritime Law Suite

**Phase Target:** Phases 159 - 162  
**Status:** Completed & Tested (100% Pass)  
**Target User:** Vietnamese enterprises, legal counsels, shipping operators, cargo owners, and general counsel.

---

## 1. Executive Summary

Provides automated legal calculations, jurisdictional assessments, and liability limitations under Vietnamese Civil and Commercial Law and International Maritime Conventions.

## 2. Scope & Key Features

### Phase 159: Commercial Arbitration & VIAC 2024
- **Regulatory Framework:** Law on Commercial Arbitration 2010, VIAC Arbitration Rules 2024, Decision 89/QĐ-VIAC.
- **Features:**
  - Clause validity check (Articles 16 & 18).
  - 6-tier VIAC fee calculator with Sole Arbitrator discount (30% reduction).
  - 2-year arbitration statute of limitations tracker (Article 33).

### Phase 160: Civil Judgment Enforcement (THADS)
- **Regulatory Framework:** Law on Civil Judgment Enforcement 2008/2014, Circular 216/2016/TT-BTC.
- **Features:**
  - 5-year enforcement limitation check (Article 30).
  - 3% fee calculator with statutory 200M VND ceiling.
  - Multi-tier statutory payment distribution sequence (Article 47).

### Phase 161: Court Litigation & Civil Procedure
- **Regulatory Framework:** Civil Procedure Code 2015 (BLTTDS), Resolution 326/2016/UBTVQH14.
- **Features:**
  - Jurisdiction assignment (District vs Provincial).
  - 6-bracket first-instance court fee scale.
  - 50% court fee advance calculation.

### Phase 162: Maritime Law & Shipping
- **Regulatory Framework:** Vietnam Maritime Code 2015, Hague-Visby SDR Protocol 1979, York-Antwerp Rules 2016.
- **Features:**
  - Carrier cargo liability limitation: $\max(666.67 \text{ SDR/package}, 2.0 \text{ SDR/kg}) \times \text{SDR rate}$.
  - General Average (Tổn thất chung) distribution engine with zero-sum equilibrium guarantee.
  - Salvage reward evaluation ("No Cure No Pay", capped by property value).
  - Statutory ranking of maritime claims & liens (Articles 40-41).

## 3. Quality & Acceptance Criteria
- 100% Python Standard Library in `src/core/`.
- 100% test pass rate across unit, CLI, and MCP handlers.
- Both human-readable Rich output and JSON output (`--json`) available on CLI.
