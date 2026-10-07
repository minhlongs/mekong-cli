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

### 5. Vietnam E-Commerce Customs, Specialized Inspection, Chemicals & CBAM (Phases 175 - 178)
- **Cross-Border E-Commerce Customs (Decree 134/2016 & Circular 80/2021):** De minimis import duty exemption (<= 1M VND), 100% VAT liability from 0 VND CIF (repeal of Decision 78), platform withholding payable, voucher deductibility rules, and 72-hour sliding window anti-structuring fraud detection.
- **Hazardous Chemicals & NSW (Decree 113/2017 & Decree 82/2022):** Annex I-V classification, Annex III ban enforcement, Annex II MOIT license verification, Annex IV 50-tonne accident prevention plan threshold, VNSW electronic clearance tokens, and IMDG Code 41-22 co-loading dangerous goods segregation matrix.
- **Specialized Food Safety & Quarantine (Decree 15/2018):** 3-tier inspection methods (Reduced <= 5%, Normal 100% dossier, Tightened 100% lab sampling), 3-consecutive-batch dynamic state machine, and Circular 25/2016 animal & Circular 33/2014 plant quarantine validity tracking.
- **EU CBAM & EUDR Green Supply Chain (EU Reg 2023/956 & 2023/1115):** Scope 1 and Scope 2 specific embedded emissions calculation ($tCO_2e/\text{t}$), net financial certificate liability adjusted for Vietnamese carbon price, and EUDR closed polygon geolocation coordinates validation for plots >= 4 ha.

### 6. Vietnam Port Terminal, ICD Cold Chain & SCF Suite (Phases 179 - 182)
- **Seaport Terminal Operations & SOLAS VGM (Circular 39/2023/TT-BGTVT):** Terminal Handling Charges (THC) across Areas I-III, reefer monitoring, dangerous goods surcharges, 3-tier sliding scale DEM/DET with Art. 168 carrier lien enforcement, and SOLAS VGM gate-in tolerance validation.
- **Cross-Border Supply Chain Finance (ICC UCP 600 & ISBP 745):** 5-rule strict discrepancy detector (Shipment date, Expiry, Stale B/L, Description, Overdrawn) and Usance L/C discounting with Term SOFR spread.
- **Pharma Cold Chain GDP & Arrhenius MKT (Circular 02/2018/TT-BYT):** Numerical Arrhenius mean kinetic temperature integration and automated quarantine hold disposition rules.
- **Multimodal Freight Carbon Accounting (ISO 14083:2023 & GLEC v3.0):** Well-to-Wheel (WTW) multimodal GHG emission aggregation and green modal shift financial valuation.

### 7. Vietnam Maritime Operations, Pilotage, Ship Husbandry, P&I & PSC (Phases 183 - 186)
- **Maritime Pilotage & Tugboat Tariffs (Circular 39/2023/TT-BGTVT):** GT-NM tariff calculation for Areas I, II, III (Cái Mép), and Offshore; night (+50%), hazardous (+10%), dead ship (+150%) multipliers, pilot detention fees, and Tugboat Classes A-E with mandatory 2-hour minimum billing.
- **Ship Husbandry Agency & MLC 2006 (Decree 160/2016 & MLC 2006):** Disbursement accounting with prolonged stay surcharges, 1.5% CTM commission, and MLC Standard A2.3 seafarer rest hours audit ($\ge 10\text{h}/24\text{h}$, $\ge 77\text{h}/7\text{d}$) with 11-month repatriation threshold.
- **Marine Insurance H&M & P&I SDR Limits (ITC Hulls 83 & Bunkers 2001):** Particular Average deductible adjustment, Constructive Total Loss ($\ge 80\%$ casualty threshold) with 180-day Notice of Abandonment deadline (Art. 326 VN Maritime Code), and tiered SDR statutory bunker pollution liability limits.
- **Port State Control Tokyo MOU NIR (Tokyo MOU PSC Manual):** Ship Risk Profile (SRP) scoring (Generic + Historic points $\rightarrow$ LRS, SRS, HRS) with 2-4, 5-8, 9-18 month inspection windows and automated Code 30 Detention orders for serious SOLAS/MARPOL/MLC non-compliances.

### 8. Business Funnels
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

### E-Commerce Customs, Chemicals & Specialized Inspection (Phases 175 - 178)
```bash
# Thuế TMĐT xuyên biên giới (Bãi bỏ QĐ 78, thu VAT từ 0 VND, De minimis thuế NK <= 1M VND)
mekong ecom-customs duty-calc 800000 --duty-rate 0.15 --vat-rate 0.10 --platform "Shopee Global"
mekong ecom-customs fraud-detect "BUYER-88" 900000 850000 950000

# Khai báo hóa chất NSW & Ma trận phân cách IMDG Code 41-22
mekong inspect chem-declare "7664-93-9" 15000 --nsw-id "NSW-DEC-01" --annex-ii --license-num "LIC-MOIT-2026"
mekong inspect imdg-matrix 3 5.1

# Kiểm tra chuyên ngành ATTP & Hiệu lực kiểm dịch
mekong inspect food-inspect NORMAL --consecutive-passes 3 --has-haccp
mekong inspect quarantine-check 2026-09-15 --max-days 15 --type ANIMAL

# CBAM phát thải tích hợp & Thẩm định EUDR GPS polygon
mekong inspect cbam-liability 500.0 1.8 0.4 --carbon-price-eu 85.0 --carbon-price-vn 5.0
mekong inspect eudr-verify "PLOT-RUBBER-01" 6.5 --coords "11.55,107.12;11.55,107.15;11.58,107.15;11.58,107.12;11.55,107.12"
```

### Seaport Terminal, Trade Finance, Cold Chain & Carbon (Phases 179 - 182)
```bash
# Biểu cước bốc dỡ cảng biển (TT 39/2023/TT-BGTVT) & Giám sát container lạnh
mekong port tariff 20ft --area III --laden --reefer --hours 24
mekong port dem-det 18 --free-days 5 --tier1-rate 25.0 --tier2-rate 45.0 --tier3-rate 70.0 --cif-val 50000.0
mekong port vgm 28500.0 --measured 28750.0 --max-gross 30480.0

# Thẩm định chứng từ L/C (ICC UCP 600 / ISBP 745) & Chiết khấu hối phiếu Usance L/C
mekong tradefinance lc-exam "2026-10-15" "2026-10-10" "2026-10-01" "FROZEN SEAFOOD" "FROZEN SEAFOOD" 250000.0 250000.0
mekong tradefinance lc-discount 500000.0 --tenor 90 --sofr 4.85 --spread 1.50 --fx 25400.0

# Nhiệt độ động học trung bình Arrhenius MKT (TT 02/2018/TT-BYT) & Đánh giá Cold Chain GDP
mekong tradefinance mkt "BATCH-VAX-2026" "2.5,3.1,4.0,5.2,8.5,4.1,3.8" --storage COLD_CHAIN
mekong tradefinance coldchain "BATCH-INSULIN-01" "2.1,3.0,7.5,9.2,8.8,4.0" --hours 6 --freezing-breach

# Kiểm kê phát thải vận tải ISO 14083 / GLEC v3.0 & Tối ưu hóa chuyển đổi phương thức phát thải
mekong tradefinance carbon --weight 25.0 --dist-road 120.0 --dist-barge 80.0 --dist-feeder 350.0
mekong tradefinance modal-shift 1000.0 350.0 --offset-vnd 125000.0
```

---

## Testing & Quality

Run the test suite:
```bash
python3 -B -m pytest tests/test_port_supply_chain_suite.py -v
python3 -B -m pytest tests/test_ecom_inspect_suite.py -v
python3 -B -m pytest tests/test_fta_duty_suite.py -v
python3 -B -m pytest tests/test_customs_fx_suite.py -v
python3 -B -m pytest tests/test_trade_transport_suite.py -v
python3 -B -m pytest tests/test_dispute_maritime_suite.py -v
```

Lint with Ruff:
```bash
python3 -m ruff check src/ tests/
```
