# Mekong CLI — Documentation Hub

Welcome to the documentation for **Mekong CLI**, the AI-operated business platform for Vietnamese enterprises and solo founders.

---

## Architecture Overview

```
mekong (CLI) / api-gateway (FastAPI)
  ├── src/core/        — Zero-dependency domain engines (Tax, Disputes, Maritime, etc.)
  ├── src/cli/         — Typer CLI application, formatting, and commands
  ├── src/harness/     — PEV engine (Plan-Execute-Verify), agents, observability
  ├── scripts/         — MCP JSON-RPC and FastMCP servers
  └── tests/           — Pytest automated test suites
```

---

## Core Modules & Features

### 1. Dispute Resolution & Maritime Law (Phases 159 - 162)
- **Arbitration (VIAC 2024):** Clause validity, 6-tier fee scale, Sole Arbitrator 30% discount.
- **Enforcement (THADS):** 5-year limitation, 3% fee with 200M cap, Article 47 priority queue.
- **Litigation (BLTTDS):** District vs Provincial jurisdiction, Resolution 326 court fee scale.
- **Maritime (BLHH 2015):** Hague-Visby SDR package/weight limits, York-Antwerp General Average, Salvage rewards, and maritime liens.

### 2. International Trade & Transport (Phases 163 - 166)
- **Multimodal Transport (NĐ 87/2009):** MTO loss limits (666.67 SDR/pkg vs 2 SDR/kg; 8.33 SDR/kg inland), 2x freight delay cap, 9-month limitation.
- **Civil Aviation (Luật HKDD & Montreal 1999):** Two-tier passenger injury (128,821 SDR strict liability), cargo limit (22 SDR/kg), baggage (1,288 SDR), delay (5,346 SDR), 2-year limitation.
- **CISG 1980 & Incoterms 2020:** Fundamental breach test (Article 25), Article 50 price reduction formula, 11 Incoterms 2020 rules, CIP/CIF mandatory insurance.
- **Trade Remedies & Anti-Dumping (Luật QLNT 2017):** Dumping margin calculation, 2.0% de minimis test, 3.0% import volume exemption, safeguard sudden surge evaluation.

### 3. Customs, FX, Tech Transfer & Bonded Logistics (Phases 167 - 170)
- **Customs Valuation & Rules of Origin (TT 39/2015, TT 60/2019 & NĐ 31/2018):** Method 1 Transaction Value with statutory additions/deductions, RVC Build-down & Build-up origin qualification, and 5-year Post-Clearance Audit (KTSTQ) window.
- **Foreign Exchange & Offshore Loans (TT 12/2022/TT-NHNN & TT 186/2010/TT-BTC):** SBV foreign loan registration validation (30-day window, debt ceiling check), dedicated loan account verification, and FDI profit remittance tax/loss clearance.
- **Technology Transfer & Royalties (Luật CGCN 2017 & NĐ 76/2018/NĐ-CP):** Mandatory registration evaluation (cross-border, state budget), net sales running royalty computation, and 25% operating profit split benchmark.
- **Bonded Logistics (Kho ngoại quan & CFS - Luật HQ 2014 & NĐ 08/2015):** 12-month bonded warehouse storage with 1-time 12-month extension, 90-day CFS deadline, and automated customs compliance alerts.

### 4. Vietnam FTAs, EPE, AEO & Duty Exemption (Phases 171 - 174)
- **FTA Preferential Tariffs & Rules of Origin (EVFTA, CPTPP, RCEP, ATIGA):** Tariff savings calculator, origin criteria engine (WO, CTC CC/CTH/CTSH, RVC >= 40%, De Minimis <= 10%), and statutory proof determination (EUR.1, CPTPP self-certification, ATIGA Form D, REX).
- **Export Processing Enterprises & Industrial Parks (NĐ 35/2022 & TT 38/2015):** 4 mandatory customs supervision criteria verification, 15-working-day on-spot declaration deadline tracking, and domestic scrap sale duty computation (Form A42).
- **Authorized Economic Operator & Risk Channeling (Luật HQ 2014, TT 72/2015 & QĐ 1399):** Multi-tier AEO qualification engine ($100M/$40M/$30M turnover, 2-year clean record, unqualified audit) and automated Green/Yellow/Red risk channeling.
- **Duty Exemption, Refund & BCQT 15 (NĐ 134/2016 & TT 39/2018):** SXXK & re-export duty refund calculations, Form 15 material reconciliation, and late payment interest (0.03%/day) on deficit duty arrears.

### 5. Business Funnels
- **Zalo OA:** Customer communication automation.
- **Tax & Accounting:** TNCN, TNDN, GTGT compliance, and Circular 78 electronic invoices.
- **Sophia AI Video Factory:** Multi-platform video generation via Cloudflare Workers.

---

## CLI Usage Examples

### Commercial Arbitration
```bash
mekong dispute viac-fee 1500000000 --sole
mekong dispute arbitration-clause "Mọi tranh chấp giải quyết tại VIAC"
```

### Civil Judgment Enforcement
```bash
mekong dispute enforcement-fee 500000000
mekong dispute enforcement-priority 100000000 --alimony 20000000 --labor 30000000 --court 10000000 --other 20000000
```

### Court Litigation
```bash
mekong dispute court-fee 500000000
mekong dispute court-jurisdiction --foreign --province "Đà Nẵng"
```

### Maritime Disputes & Shipping
```bash
mekong dispute carrier-liability 10 2000 500000000
mekong dispute general-average --ship-val 1000000000 --cargo-val 500000000 --ship-loss 50000000
```

### International Trade & Multimodal Transport
```bash
# Ưu đãi thuế quan FTA & Tiết kiệm thuế
mekong fta savings 1000000000 --mfn 15.0 --fta 0.0 --agreement EVFTA

# Quy tắc xuất xứ & Giám sát hải quan DNCX
mekong fta origin 6203.42 --criterion cth --non-orig-hs 5208.11 --agreement CPTPP
mekong dncx epe-check --barrier --camera --gate --erp
mekong dncx on-spot 2026-03-01 --import-date 2026-03-10

# Doanh nghiệp Ưu tiên (AEO) & Phân luồng tờ khai
mekong fta aeo --enterprise-type GENERAL_TRADER --turnover-usd 150000000
mekong fta channel --aeo

# Hoàn thuế SXXK & Đối soát BCQT Mẫu 15
mekong fta refund-sxxk 100000000 5000 3000
mekong dncx bcqt 1000 5000 2000 --bom 2.0 --actual 1900
```
mekong trade aviation-cargo 100 80000000

# Hợp đồng mua bán quốc tế CISG & Incoterms 2020
mekong trade cisg-reduction 1000000000 700000000 1000000000
mekong trade incoterms CIP

# Phòng vệ thương mại & Chống bán phá giá
mekong trade anti-dumping 15000 10000
mekong trade trade-remedy "China" 15.5 8.2
```

### Customs, FX, Tech Transfer & Bonded Logistics
```bash
# Trị giá hải quan (Method 1 Transaction Value)
mekong customs valuation 1000000000 --freight 50000000 --insurance 10000000 --post-install 20000000

# Xuất xứ hàng hóa (Rules of Origin - RVC)
mekong customs rvc 1000000000 --vnm 450000000 --method indirect

# Kiểm tra thời hiệu kiểm tra sau thông quan (KTSTQ 5 năm)
mekong customs audit-check 2024-05-10

# Đăng ký khoản vay nước ngoài NHNN (SBV Foreign Loan)
mekong customs sbv-loan 24 --amount 500000 --account-type DICA

# Đủ điều kiện chuyển lợi nhuận ra nước ngoài (FDI Profit Remittance)
mekong customs profit-remit --audited --tax-done --no-losses

# Bản quyền chuyển giao công nghệ & Định mức 25% Operating Profit Split
mekong customs royalty 50000000000 4.5 --profit 6000000000

# Kiểm tra thời hạn lưu kho ngoại quan / CFS
mekong customs storage-check 240 --type bonded
```

---

## Testing & Quality

Run the test suite:
```bash
python3 -m pytest tests/test_customs_fx_suite.py -v
python3 -m pytest tests/test_trade_transport_suite.py -v
python3 -m pytest tests/test_dispute_maritime_suite.py -v
```

Lint with Ruff:
```bash
python3 -m ruff check src/ tests/
```
