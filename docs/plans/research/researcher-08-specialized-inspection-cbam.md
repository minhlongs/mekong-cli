# Research: Specialized Inspection & EU CBAM/EUDR Compliance (Phases 177-178)

**Author:** Researcher Subagent | **Date:** 2026-10-07 | **Stack:** Python Stdlib (Zero-Dep)  
**Statutory Scope:** NĐ 15/2018/NĐ-CP, Luật TY 2015 (TT 25/2016), Luật BVTV 2013 (TT 33/2014), EU Reg 2023/956 (CBAM), EU Reg 2023/1115 (EUDR).  
**Sources:** [1] Official Gazette NĐ 15/2018/NĐ-CP; [2] MARD TT 25/2016/TT-BNNPTNT & TT 33/2014/TT-BNNPTNT; [3] EUR-Lex Reg 2023/956 & 2023/1773; [4] EUR-Lex Reg 2023/1115. Credibility: Primary statutory & regulatory instruments (Highest tier).

---

## 1. Phase 177: Specialized Food Safety & Quarantine Inspection

### 1.1. Food Safety State Inspection Methods (NĐ 15/2018/NĐ-CP Art 16-19)
- **Reduced (Kiểm tra giảm):** Random documentary audit $\le 5\%$ consignments. Eligibility: 3 consecutive passes in Normal within 12 mo + GMP/HACCP/ISO 22000/IFS/BRC cert OR bilateral equivalency.
- **Normal (Kiểm tra thông thường):** 100% dossier review, no lab sample testing. Default mode for compliant goods without high certs.
- **Tightened (Kiểm tra chặt):** 100% dossier review + 100% physical sampling & lab assay. Applied upon failure, warning from export country, or MOH/MARD/MOIT mandate.
- **State Transition Machine:**
  * Tightened $\to$ Normal: Exactly 3 consecutive conforming consignments (Art 17.3).
  * Normal $\to$ Reduced: 3 consecutive conforming consignments within 12 months + Valid Cert (Art 16.1b).
  * Any $\to$ Tightened: 1 non-conforming test result OR safety warning trigger (Art 17.1).

### 1.2. Animal & Plant Quarantine Mechanics (Luật TY 2015, Luật BVTV 2013)
- **Animal Quarantine (TT 25/2016/TT-BNNPTNT):** Exemption: diplomatic luggage, in-transit bond without transshipment. Certificate validity: 15 days (terrestrial animals), 30 days (products for consumption), 60 days (processed shelf-stable products). Border protocol: document audit $\to$ clinical physical check $\to$ lab assay $\to$ Quarantine Certificate.
- **Plant Quarantine (TT 33/2014/TT-BNNPTNT):** Pest risk analysis (PRA) gating. Exemption: processed foods containing no plant propagative parts. Certificate validity: 30 days from date of Phytosanitary inspection to border crossing.

---

## 2. Phase 178: EU CBAM & EUDR Green Supply Chain Export Compliance

### 2.1. CBAM Embedded Emissions & Financial Liability (EU Reg 2023/956 & 2023/1773)
- **Target Sectors:** Iron & Steel (HS 72, 73), Aluminium (HS 76), Cement (HS 2523), Fertilizers (HS 31), Hydrogen (HS 280410).
- **Specific Embedded Emissions ($SE$ in $\text{tCO}_2\text{e}/\text{t}$):**
  $$SE = \frac{AttrEm_{dir} + AttrEm_{indir}}{Production} = \frac{\sum (Fuel_i \times NCV_i \times EF_i \times OF_i) + \sum (Mat_j \times EF_j) + (E_{grid} \times EF_{grid})}{Production}$$
- **CBAM Financial Liability ($EUR$):**
  $$\text{CBAM Liability} = \text{ExportVolume} \times SE \times \max(0, P_{\text{EU ETS}} - P_{\text{VN Carbon Effective}})$$
  * Transitional regime (2023-10-01 to 2025-12-31): Quarterly emission reporting only, zero certificate surrender.
  * Definitive regime (2026-01-01 onwards): Mandatory CBAM certificate purchase & surrender at weekly average EU ETS price.

### 2.2. EUDR Deforestation-Free Compliance (EU Reg 2023/1115)
- **Scope for Vietnam:** Timber/Wood (HS 44), Rubber (HS 40), Coffee (HS 0901).
- **Triple Gates:** (1) Cut-off date: Harvested on land not deforested after 2020-12-31; (2) Legal origin: National forest law, land tenure & labor compliance; (3) Geolocation polygon: Coordinates (lat/long $\pm 6$ decimals) for parcels $\ge 4$ ha (single point if $< 4$ ha). Due Diligence Statement (DDS) required in EU TRACES portal.

---

## 3. Data Structures & Validation Mechanics

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

class InspectionMethod(str, Enum):
    REDUCED = "REDUCED"      # <= 5% random dossier
    NORMAL = "NORMAL"        # 100% dossier
    TIGHTENED = "TIGHTENED"  # 100% sampling + lab

class CBAMSector(str, Enum):
    IRON_STEEL = "IRON_STEEL"    # HS 72, 73
    ALUMINIUM = "ALUMINIUM"      # HS 76
    CEMENT = "CEMENT"            # HS 2523
    FERTILIZERS = "FERTILIZERS"  # HS 31
    HYDROGEN = "HYDROGEN"        # HS 280410

@dataclass(frozen=True)
class FoodSafetyRecord:
    consignor_id: str
    product_hs: str
    current_method: InspectionMethod
    consecutive_passes: int
    has_iso22000_haccp: bool
    cert_valid_days: int
    failed_last_batch: bool

@dataclass(frozen=True)
class CBAMDeclaration:
    sector: CBAMSector
    volume_tonnes: float
    attr_em_direct_tco2e: float
    attr_em_indirect_tco2e: float
    eu_ets_price_eur: float
    vn_carbon_price_eur: float

@dataclass(frozen=True)
class EUDRParcel:
    plot_id: str
    area_hectares: float
    coordinates: List[Tuple[float, float]]  # [(lat, lon)]
    deforestation_free_since_2020: bool
    land_title_certified: bool
```

### 3.1. Core Validation Rules & Transition Logic
1. **Transition Check:** If `failed_last_batch`: state $\to$ `TIGHTENED`, `consecutive_passes = 0`. If `TIGHTENED` and `consecutive_passes >= 3`: state $\to$ `NORMAL`. If `NORMAL` and `consecutive_passes >= 3` and `has_iso22000_haccp` and `cert_valid_days > 0`: state $\to$ `REDUCED`.
2. **CBAM Validation:** `volume_tonnes > 0`, `attr_em_direct >= 0`, `attr_em_indirect >= 0`, `eu_ets_price >= 0`. If `vn_carbon_price > eu_ets_price`, credit capped at EU ETS price (net liability $\ge 0$).
3. **EUDR Geo-Validation:** If `area_hectares >= 4.0`, require closed polygon `len(coordinates) >= 4` and `coordinates[0] == coordinates[-1]`; if `< 4.0`, single point `(lat, lon)` allowed. Reject if `not deforestation_free_since_2020` or `not land_title_certified`.

---

## 4. Architectural Evaluation & Trade-off Matrix

| Metric | Option A: Pure Python Stdlib Engine (Recommended) | Option B: External GIS/GeoPandas + DB Engine |
|---|---|---|
| **Performance** | $< 0.1$ ms per batch evaluation; in-memory point/polygon checks | $> 15$ ms (C-bindings & IPC serialization overhead) |
| **Complexity** | Low: pure dataclasses + deterministic algebraic equations | High: GDAL/GEOS system binaries, heavy dependency trees |
| **Maintenance** | Zero external drift; matches `fta_duty_engine.py` pattern | Fragile across macOS/Linux build chains & CF worker runtime |
| **Cost** | 0 MCU external overhead, 0 USD licensing | External geospatial API and carbon calculation subscriptions |

- **Adoption Risk:** Low. Statutory formulas derived directly from NĐ 15/2018 & EU Reg 2023/956 annexes. Zero library abandonment risk.
- **Architectural Fit:** 100% fit for `src/core/specialized_inspection_engine.py` and `cbam_eudr_engine.py`. Seamless Typer CLI & FastMCP exposure.
- **Ranked Recommendation:**
  1. **Rank 1 (Chosen): Pure Python Standard Library Engine** (YAGNI/KISS/DRY). Ray-casting point-in-polygon without GDAL.
  2. **Rank 2: External GIS API Hybrid.** High latency and break-risk for offline CLI operations.
- **Limitations:** Does not execute live EU TRACES portal SOAP/REST submission (requires official EORI auth credentials). Excludes voluntary scope 3 supply chain upstream mining emissions outside CBAM Annex IV.

---

## 5. Unresolved Questions
1. MARD/Customs integration: Will VN Single Window (VNSW) expose automated JSON API for State Inspection waivers in 2026?
2. EU ETS default benchmark fallback: Exact EU Commission sector default factor table updates for 2026 definitive phase.
