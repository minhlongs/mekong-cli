# Research Report: Cross-Border E-Commerce Customs & Hazardous Chemicals NSW Engine (Phases 175-176)

**Author:** Technical Analyst  
**Date:** 2026-10-07  
**Scope:** Draft Decree E-Commerce Customs, Decision 78/2010/QD-TTg repeal, VAT Law amendment, Circular 80/2021/TT-BTC, Law on Chemicals 2007, Decrees 113/2017/ND-CP & 82/2022/ND-CP, Circulars 32/2017/TT-BCT & 17/2022/TT-BCT, IMDG Code 41-22 / IATA DGR 65th.

---

## 1. Statutory Frameworks & Credibility Assessment

| Source | Credibility | Regulatory Authority | Key Mandate |
|---|---|---|---|
| Draft Decree E-Commerce Customs & Amended VAT Law | 5/5 (Statutory) | National Assembly / MOF / GDC | Repeal Decision 78/2010/QD-TTg; eliminate VAT exemption for consignments < 1M VND; retain import duty de minimis < 1M VND (Decree 134/2016 Art. 29). |
| Circular 80/2021/TT-BTC & Decree 91/2022/ND-CP | 5/5 (Statutory) | General Dept of Taxation (GDT) | Cross-border platforms (Shopee, Lazada, TikTok, Temu) liable for tax registration, withholding, and remitting VAT/CIT at source. |
| Decrees 113/2017/ND-CP & 82/2022/ND-CP | 5/5 (Statutory) | Ministry of Industry & Trade (MOIT) | Annex I (Conditional), Annex II (Restricted), Annex III (Banned), Annex IV (Accident Plan), Annex V (NSW mandatory declaration). |
| IMO IMDG Code 41-22 & IATA DGR 65th | 5/5 (Convention) | IMO / ICAO / IATA | 9 hazard classes, Table 7.2.4 segregation matrix, flashpoint/packing group limits. |

---

## 2. Phase 175: Cross-Border E-Commerce Customs Management

### 2.1. Customs Valuation & Duty Computation Formulas
1. **Customs Value ($V_{c}$):**  
   $$V_{c} = P_{item} + F_{intl} + I_{intl} - D_{direct}$$  
   *Where $D_{direct}$ is eligible seller discount on platform. Platform subsidy vouchers not deductible.*
2. **Import Duty ($T_{imp}$):**  
   - If $V_{c} \le 1,000,000\text{ VND}$ (De minimis threshold): $T_{imp} = 0$.  
   - If $V_{c} > 1,000,000\text{ VND}$: $T_{imp} = V_{c} \times r_{imp}$.
3. **Special Consumption Tax ($T_{sct}$):** $T_{sct} = (V_{c} + T_{imp}) \times r_{sct}$.
4. **Value-Added Tax ($T_{vat}$):**  
   $$T_{vat} = (V_{c} + T_{imp} + T_{sct}) \times r_{vat}$$  
   *Post-repeal Decision 78/2010/QD-TTg: $T_{vat}$ applied from 0 VND ($r_{vat} = 8\%\text{ or }10\%$), no threshold exemption.*
5. **Platform Withholding Liability ($T_{platform}$):** $T_{platform} = T_{imp} + T_{sct} + T_{vat}$.

### 2.2. Split Consignment Risk Detection (Anti-Structuring Algorithm)
- **Target:** Detect artificial splitting of single shipments below 1,000,000 VND to evade import duty or specialized inspection.
- **Entity Matching Score:**  
  $$Sim = w_1 \cdot \mathbb{I}(Phone_1 = Phone_2) + w_2 \cdot \mathbb{I}(TIN_1 = TIN_2) + w_3 \cdot \text{LevenshteinRatio}(Addr_1, Addr_2)$$  
- **Structuring Risk Metric ($R_{split}$):** Sliding window $\Delta t \le 72\text{ hours}$, aggregated value $S_v = \sum_{i=1}^k V_{c,i}$:  
  $$R_{split} = \min\left(1.0, 0.4 \cdot Sim + 0.3 \cdot \left(\frac{k}{k_{max}}\right) + 0.3 \cdot \mathbb{I}\left(S_v > 10^6 \land \forall i: V_{c,i} \le 10^6\right)\right)$$  
  *Rule:* If $R_{split} \ge 0.70 \implies$ Flag `SPLIT_CONSIGNMENT_DETECTED`: force order consolidation, forfeit de minimis, route to Yellow/Red channel.

---

## 3. Phase 176: Hazardous Chemicals Import Declaration via NSW & Dangerous Goods

### 3.1. Chemical Compliance Matrices under Decrees 113/2017 & 82/2022
- **Annex I (Conditional):** Requires Industrial Chemical Production/Trading Eligibility Certificate.
- **Annex II (Restricted):** Requires MOIT Special License prior to customs clearance.
- **Annex III (Banned):** Absolute import prohibition (Customs stops clearance immediately).
- **Annex IV (Accident Prevention Plan):** If max storage $Q_{storage} \ge Q_{threshold} \implies$ mandatory MOIT-approved Prevention Plan. If $Q_{storage} < Q_{threshold} \implies$ enterprise-approved Prevention Measure.
- **Annex V (NSW Mandatory Declaration):** 100% declared via `vnsw.gov.vn` prior to customs declaration. Automated response clearance token issued. Exemption: $Q < 10\text{ kg/shipment}$ and not in Annex II or precursor list.

### 3.2. IMDG / IATA Dangerous Goods Segregation
- **9 DG Classes:** 1 (Explosives), 2 (Gases: 2.1 Flammable, 2.2 Non-flammable, 2.3 Toxic), 3 (Flammable Liquid), 4 (Flammable Solid: 4.1 Solid, 4.2 Spontaneous, 4.3 Dangerous when wet), 5 (Oxidizing: 5.1 Oxidizer, 5.2 Organic Peroxide), 6 (Toxic 6.1, Infectious 6.2), 7 (Radioactive), 8 (Corrosive: Acids vs Alkalis), 9 (Misc: Li-Ion).
- **Segregation Code:** $0$ = None, $1$ = Away from ($\ge 3\text{m}$), $2$ = Separated from ($\ge 6\text{m}$ / bulkhead), $3$ = Separated by complete compartment, $4$ = Longitudinal separation, $X$ = Specific entry check.

---

## 4. Technical Specifications: Data Classes, Validation & Error Handling

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class ChemicalAnnex(str, Enum):
    ANNEX_I_CONDITIONAL = "ANNEX_I"; ANNEX_II_RESTRICTED = "ANNEX_II"
    ANNEX_III_BANNED = "ANNEX_III"; ANNEX_IV_PLAN = "ANNEX_IV"; ANNEX_V_NSW = "ANNEX_V"

class IMDGSegregation(int, Enum):
    NONE = 0; AWAY_FROM = 1; SEPARATED_FROM = 2; COMPARTMENT = 3; LONGITUDINAL = 4

@dataclass(frozen=True)
class EcomOrderItem:
    item_id: str; hs_code: str; unit_price: float; qty: int
    seller_id: str; platform_id: str; import_duty_rate: float; sct_rate: float; vat_rate: float

@dataclass(frozen=True)
class ChemicalDeclaration:
    cas_number: str; chemical_name: str; hs_code: str; qty_kg: float
    annexes: List[ChemicalAnnex]; un_number: Optional[str]; dg_class: Optional[float]
    threshold_plan_kg: float; nsw_feedback_code: Optional[str]; license_number: Optional[str]

# Exceptions
class DeMinimisAbuseError(Exception): """Raised when split consignment fraud is identified."""
class BannedChemicalClearanceError(Exception): """Raised when Annex III chemical detected."""
class HazardousSegregationViolationError(Exception): """Raised on IMDG forbidden co-loading."""
```

---

## 5. Trade-off Matrix & Architectural Evaluation

| Evaluation Criteria | Option A: In-Memory Sliding Window + Static IMDG Matrix (Pure Python) | Option B: Graph Database (Neo4j) + ChemAxon API | Option C: SQLite + JSON Extension |
|---|---|---|---|
| **Performance** | Latency $< 0.5\text{ms}$ per order; O(1) segregation lookup | Latency $20-80\text{ms}$; high network roundtrips | Latency $5-15\text{ms}$; disk I/O dependent |
| **Complexity** | Zero dependency, Python standard library dataclasses | High; external daemon, specialized JVM services | Low-Medium; custom SQL functions needed |
| **Maintenance** | Minimal; static regulatory tables updated via json/py | High; graph schema migrations, driver version drift | Low; single file schema |
| **Adoption Risk** | Zero; 100% backward compatible with Mekong CLI core | High; heavy footprint, memory bloat | Low; portable file database |
| **Architectural Fit** | 10/10: Matches lightweight CLI/Worker execution model | 3/10: Unfit for standalone CLI distribution | 7/10: Good for persistent storage, slow for bulk |
| **Rank** | **Rank 1 (Selected)** | **Rank 3 (Rejected)** | **Rank 2 (Fallback)** |

---

## 6. Adoption Risk & Limitations
- **Adoption Risk:** Low. Mekong CLI standard library pattern has zero packaging risk. Regulatory logic isolated behind versioned enums.
- **Limitations:** Excludes biological weapons / dual-use military chemicals under Decree 69/2018/ND-CP and Universal Postal Union (UPU) terminal dues mechanics.

---

## 7. Unresolved Questions
1. Exact effective date of National Assembly revised VAT Law terminating Decision 78/2010/QD-TTg exemption.
2. Official API payload schema for National Single Window (NSW) automated clearance status webhook callback.
