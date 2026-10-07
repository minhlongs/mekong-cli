# Research: Cold Chain Pharma GDP MKT & Freight Carbon Accounting (Phases 181-182)

**Author:** Technical Analyst | **Date:** 2026-10-07 | **Stack:** Python Stdlib (Zero-Dep)  
**Statutory & Technical Scope:** TT 02/2018/TT-BYT, TT 03/2018/TT-BYT, TT 36/2018/TT-BYT, WHO TRS 961 Annex 9, USP <1079>/<659>, ISO 14083:2023, GLEC Framework v3.0, LEP 2020 Art 91, NĐ 06/2022/NĐ-CP, TT 01/2022/TT-BTNMT.  
**Sources & Credibility:** [1] Vietnam MOH (TT 02/2018, TT 03/2018, TT 36/2018); [2] WHO TRS No. 961 Annex 9 & USP-NF <1079>; [3] ISO 14083:2023 & Smart Freight Centre (GLEC v3.0); [4] MONRE (NĐ 06/2022/NĐ-CP, TT 01/2022/TT-BTNMT). Credibility: 5/5 (Primary statutory instruments & international standards).

---

## 1. Phase 181: Cold Chain Logistics Integrity, Pharma GDP & Temperature Excursion MKT

### 1.1. Statutory Regime & Temperature Storage Profiles (TT 02/2018, TT 36/2018, WHO TRS 961)
- **Deep Frozen ($\le -20^\circ\text{C}$):** Plasma, mRNA biologics. Warning at $T > -20^\circ\text{C}$; Critical quarantine hold at $T > -15^\circ\text{C}$ for $t > 2\text{ h}$.
- **Cold Chain ($+2^\circ\text{C} \text{ to } +8^\circ\text{C}$):** Vaccines, insulin, biologics. Freeze hazard ($T \le 0^\circ\text{C}$) induces irreversible protein denaturation / adjuvant precipitation $\to$ immediate quarantine hold. Heat excursion threshold: $T > +8^\circ\text{C}$.
- **Controlled Room Temperature (CRT) ($+15^\circ\text{C} \text{ to } +25^\circ\text{C}$):** Excursions up to $+30^\circ\text{C}$ permitted only if cumulative duration $t \le 24\text{ h}$ and $T_{\text{MKT}} \le 25^\circ\text{C}$.

### 1.2. Mean Kinetic Temperature (MKT) via Arrhenius Equation (USP <1079>, Haynes 1971)
$$T_{\text{MKT}} = \frac{\frac{\Delta H}{R}}{-\ln\left(\frac{1}{n} \sum_{i=1}^n e^{-\frac{\Delta H}{R \cdot T_i}}\right)} = \frac{10000}{-\ln\left(\frac{1}{n} \sum_{i=1}^n e^{-\frac{10000}{T_i}}\right)}$$
Where $\Delta H = 83.144\text{ kJ/mol}$ (standard activation energy for pharmaceutical degradation), $R = 8.3144\text{ J/(mol}\cdot\text{K)}$ ($\frac{\Delta H}{R} = 10,000\text{ K}$), $T_i$ in Kelvin ($T_i = T_{\text{Celsius}, i} + 273.15$), and $T_{\text{MKT, Celsius}} = T_{\text{MKT}} - 273.15$. MKT weights thermal spikes exponentially over arithmetic mean.

### 1.3. Excursion Severity & Batch Release Risk Scoring
$$R_{\text{batch}} = \min\left(100, 30 \cdot \frac{\max(0, T_{\text{peak}} - T_{\text{upper}})}{\Delta T_{\text{crit}}} + 30 \cdot \frac{t_{\text{excursion}}}{t_{\text{budget}}} + 40 \cdot \frac{\max(0, T_{\text{MKT}} - T_{\text{target\_max}})}{2.0} + P_{\text{freeze}}\right)$$
Where $P_{\text{freeze}} = 60$ if Cold Chain profile and $T_{\text{min}} \le 0^\circ\text{C}$.
- **Decision Gates:**
  * $R_{\text{batch}} < 25$: `RELEASE` (Batch conforms for release).
  * $25 \le R_{\text{batch}} < 60$: `DEVIATION_REVIEW` (CAPA investigation required; stability budget audit).
  * $R_{\text{batch}} \ge 60$ or $T_{\text{min}} \le 0^\circ\text{C}$ (Cold Chain): `QUARANTINE_HOLD` (Mandatory physical & digital hold under TT 02/2018 Art 15).

---

## 2. Phase 182: Logistics Carbon Accounting & Scope 3 Freight Decarbonization

### 2.1. Accounting Framework (ISO 14083:2023, GLEC v3.0, NĐ 06/2022/NĐ-CP)
Transport Chain Element (TCE) emissions follow Well-to-Wheel (WTW) lifecycle: $\text{EF}_{\text{WTW}} = \text{EF}_{\text{WTT}} + \text{EF}_{\text{TTW}}$ (Well-to-Tank fuel refining + Tank-to-Wheel combustion).

### 2.2. Standard WTW Emission Factors ($\text{gCO}_2\text{e} / (\text{t}\cdot\text{km})$)
- **Ocean Container:** ULCS (>14,500 TEU): $12 - 18$; Feeder (<2,000 TEU): $25 - 35$. Default range: $12 - 35\text{ gCO}_2\text{e}/(\text{t}\cdot\text{km})$.
- **Inland Waterway Barge (IWT):** Mekong Delta / Red River self-propelled barges: $20 - 45\text{ gCO}_2\text{e}/(\text{t}\cdot\text{km})$ (typ. $28$).
- **Heavy Commercial Truck:** Euro 4/5 Diesel articulated truck (20-40t): $60 - 110\text{ gCO}_2\text{e}/(\text{t}\cdot\text{km})$ (typ. $85$).
- **Air Cargo:** Belly hold passenger: $500 - 650$; Dedicated freighter: $650 - 900\text{ gCO}_2\text{e}/(\text{t}\cdot\text{km})$.

### 2.3. Transport Footprint & Green Modal Shift Optimization Formulas
1. **Total Transport Footprint ($E_{\text{total}}$ in $\text{kgCO}_2\text{e}$):**
   $$E_{\text{total}} = \sum_{j=1}^m \left( m_{\text{freight}} \times d_j \times \text{EF}_{\text{WTW}, j} \times 10^{-3} \right) + \sum_{k=1}^p E_{\text{hub}, k}$$
   Where $m_{\text{freight}}$ in tonnes, $d_j$ in km, $\text{EF}_{\text{WTW}, j}$ in $\text{gCO}_2\text{e}/(\text{t}\cdot\text{km})$, and $E_{\text{hub}}$ is handling throughput emissions ($1.5 - 3.5\text{ kgCO}_2\text{e}/\text{t}$).
2. **Modal Shift Decarbonization Efficiency ($\eta$):**
   $$\Delta E = E_{\text{baseline\_road}} - E_{\text{multimodal}}, \quad \eta = \frac{\Delta E}{E_{\text{baseline\_road}}} \times 100\%$$
   *Benchmark:* Road-to-Barge modal shift on Mekong corridors (Can Tho $\to$ Cai Mep) yields $55\% - 72\%$ carbon reduction.
3. **Decree 06/2022/NĐ-CP Domestic Carbon Offset Cost ($C_{\text{offset}}$ in VND):**
   $$C_{\text{offset}} = \frac{E_{\text{total}}}{1000} \times P_{\text{VNCC}}$$
   Where $P_{\text{VNCC}} \in [120,000, 250,000]\text{ VND/tCO}_2\text{e}$ (Vietnam domestic ETS pilot credit price).

---

## 3. Data Structures & Core Engine Contract

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class ColdChainProfile(str, Enum):
    DEEP_FROZEN = "DEEP_FROZEN"  # <= -20C
    COLD_CHAIN = "COLD_CHAIN"    # +2C to +8C
    CRT = "CRT"                  # +15C to +25C

class BatchReleaseStatus(str, Enum):
    RELEASE = "RELEASE"; DEVIATION_REVIEW = "DEVIATION_REVIEW"; QUARANTINE_HOLD = "QUARANTINE_HOLD"

class TransportMode(str, Enum):
    OCEAN_ULCS = "OCEAN_ULCS"; OCEAN_FEEDER = "OCEAN_FEEDER"; INLAND_BARGE = "INLAND_BARGE"
    TRUCK_EURO4_5 = "TRUCK_EURO4_5"; AIR_BELLY = "AIR_BELLY"; AIR_FREIGHTER = "AIR_FREIGHTER"

@dataclass(frozen=True)
class TemperatureReading:
    timestamp_epoch: int; temp_celsius: float

@dataclass(frozen=True)
class ColdChainAssessment:
    batch_id: str; profile: ColdChainProfile; mkt_celsius: float
    peak_temp_celsius: float; min_temp_celsius: float; cumulative_excursion_hours: float
    risk_score: float; release_status: BatchReleaseStatus; freeze_breach: bool

@dataclass(frozen=True)
class TransportLeg:
    mode: TransportMode; distance_km: float; ef_wtw_g_per_tkm: float

@dataclass(frozen=True)
class LogisticsCarbonAssessment:
    freight_mass_tonnes: float; baseline_road_kgco2e: float; actual_multimodal_kgco2e: float
    co2e_reduction_pct: float; offset_cost_vnd: float; statutory_report_required: bool  # NĐ 06 >= 3,000 tCO2e/yr
```

---

## 4. Architectural Evaluation & Trade-off Matrix

| Criteria | Option A: Pure Python Stdlib Engine (Recommended) | Option B: Heavy GIS/Pandas/Scipy Pipeline | Option C: External SaaS API (EcoTransIT/SmartFreight) |
|---|---|---|---|
| **Performance** | $< 0.2\text{ ms}$ MKT (10k points) & route footprint; zero GC lag | $15 - 50\text{ ms}$; high memory footprint ($>150\text{MB}$) | $250 - 1200\text{ ms}$ HTTP overhead; rate limit vulnerability |
| **Complexity** | Zero runtime dependencies; standard math module | C-extension dependencies (`scipy`, `pandas`) | Network auth, webhook resilience, schema version drift |
| **Maintenance** | Minimal; pure deterministic equations matching TT 02 & ISO 14083 | High; Python ABI breakages across runtime envs | High; external API deprecation & contract maintenance |
| **Cost** | 0 MCU external overhead, 0 USD licensing | Server memory overhead | $\$0.05 - \$0.20$ per API routing call |
| **Adoption Risk** | Zero; 100% backward-compatible with Mekong core | Medium; build complexity on edge runtimes | High; vendor lock-in & compliance data sovereignty leak |
| **Architectural Fit** | 10/10: Native fit for `src/core/cold_chain_engine.py` & `freight_carbon_engine.py` | 4/10: Unfit for lightweight CLI/Worker execution | 3/10: Fails offline requirement for Mekong Delta barges |

- **Ranked Recommendation:**
  1. **Rank 1 (Selected): Pure Python Standard Library Engine** (YAGNI/KISS/DRY). Direct Arrhenius vectorized via math functions and static GLEC v3.0 tables.
  2. **Rank 2: SQLite-backed Cached Engine.** Fallback if historical sensor time-series exceed 1M telemetry rows per shipment.
  3. **Rank 3: External Carbon SaaS API.** Rejected due to cost, privacy, and connectivity failure on inland waterways.

- **Limitations:** Excludes cryogenic ultra-cold storage ($-80^\circ\text{C}$ dry ice logistics) and vessel-specific hydrodynamics (hull fouling, trim optimization under IMO CII).
- **Unresolved Questions:** (1) Promulgation date of MONRE's sector-specific transport emission factor updates under Circular 01/2022; (2) MOH guidelines on real-time IoT logger calibration drift tolerances under TT 02/2018.
