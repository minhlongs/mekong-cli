# Design Guidelines — Vietnam E-Commerce, Specialized Inspection, Chemicals & CBAM Suite (Phases 175 - 178)

**Date:** 2026-10-07  
**Design System:** Mekong Cyber-Glass Terminal & Web Dashboard  
**Compliance Target:** WCAG 2.1 AA, Contrast Ratio >= 4.5:1  

---

## 1. Visual Hierarchy & Color Tokens

- **Brand Primary (E-Commerce & Single Window):** `#06b6d4` (Cyan Teal)
- **Eco / Bio Green (EUDR Compliant / Reduced Inspection):** `#10b981` (Emerald Green)
- **Chemical Alert (Annex II / Normal Inspection / Split Warning):** `#f59e0b` (Amber Orange)
- **High Risk / Prohibition (Annex III Banned / Tightened Inspection / Deforestation):** `#ef4444` (Crimson Red)
- **Carbon Liability Purple (EU CBAM ETS Surcharge):** `#8b5cf6` (Electric Violet)
- **Background Deep:** `#090d16` (Deep Obsidian Glass)
- **Card Surface:** `rgba(15, 23, 42, 0.75)` with 1px border `rgba(255, 255, 255, 0.1)` and backdrop-blur `12px`

---

## 2. Component System

1. **Cross-Border E-Commerce Tax & Withholding Card:**
   - Dual-tier valuation breakdown: Order Price, International Freight/Insurance, minus Direct Discount.
   - Distinct display for 1,000,000 VND Import Duty de minimis status vs. Post-Repeal Decision 78 100% VAT withholding from 0 VND.
   - Platform Remittance Total with direct Shopee/Lazada/TikTok/Temu indicator.

2. **Split Consignment Fraud Risk Radar:**
   - Fraud risk meter ($R_{split} \in [0.0, 1.0]$) with Levenshtein entity similarity and 72-hour sliding window aggregation.
   - Risk tag: `LOW` (Green), `EVALUATE` (Yellow), `FRAUD_ALERT` (Red, forcing consolidated customs declaration).

3. **Hazardous Chemicals NSW Clearance Badge:**
   - Annex I-V classification chip with direct status on National Single Window (`vnsw.gov.vn`) clearance token.
   - IMDG Dangerous Goods 9-class segregation indicator with warning callouts for incompatible co-loading.

4. **Food Safety 3-Tier Inspection Transition Pill:**
   - Dynamic tier display: `REDUCED` (<= 5% random audit), `NORMAL` (100% dossier), `TIGHTENED` (100% lab sampling).
   - Streak counter displaying progress toward 3 consecutive passes required for normalization or reduction.

5. **EU CBAM & EUDR Green Supply Chain Dashboard:**
   - Specific Embedded Emissions ($SE$) per metric ton with Scope 1 + Scope 2 breakdown.
   - Net CBAM certificate financial liability ($EUR$) factoring EU ETS price vs. Vietnam carbon credit offset.
   - EUDR Deforestation-Free verification pill with closed polygon coordinate count.
