# Phase 03: Port Dredging Sediment Quality & Beneficial Reuse Engine

## Overview
- Module: `src/core/maritime/phase_365_dredging_sediment_beneficiation.py`
- Regulatory Standards: London Protocol 1996, Vietnam QCVN 43:2017/BTNMT.

## Technical Requirements
- Tributyltin (TBT) limit: $\le 0.001\text{ mg/kg}$ dry weight (strict zero tolerance for open sea dumping).
- Total Polycyclic Aromatic Hydrocarbons ($\sum 16\text{-PAH}$): $\le 10.0\text{ mg/kg}$ for Class 1.
- Heavy metals: As $\le 20$, Cd $\le 1.5$, Pb $\le 50$, Hg $\le 0.4$, Cu $\le 65$, Zn $\le 200\text{ mg/kg}$.
- Beneficial reuse geotechnical gate: Solids content $\ge 60.0\%$, Unconfined Compressive Strength $\text{UCS}_{28d} \ge 50.0\text{ kPa}$.

## Data Schema
```python
@dataclass
class DredgedSedimentInput:
    batch_id: str
    tbt_mg_kg: float
    total_pah_mg_kg: float
    heavy_metals: Dict[str, float]
    solids_content_pct: float
    stabilized_ucs_kpa: float

@dataclass
class SedimentReuseResult:
    batch_id: str
    sediment_class: str
    is_open_sea_dump_permitted: bool
    is_beneficial_reuse_approved: bool
    reuse_destination: str
    compliance_status: str
    advisories: List[str]
```
