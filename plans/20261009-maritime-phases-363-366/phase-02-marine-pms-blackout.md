# Phase 02: Marine Generator PMS & Blackout Prevention Engine

## Overview
- Module: `src/core/maritime/phase_364_marine_generator_pms_blackout.py`
- Regulatory Standards: SOLAS II-1/Reg 53, IEC 60092-202, DNV/ABS Marine Power Rules.

## Technical Requirements
- Active & reactive load sharing: $\Delta P_{\text{imbalance}} \le 10\%$.
- Standby generator auto-start trigger: $P_{\text{grid}} \ge 85.0\% \cdot \sum P_{\text{running\_MCR}}$.
- Preferential load shedding (3 stages: non-essential, auxiliary, non-critical heavy).
- Emergency blackout trip protection: frequency $f \le 57.0\text{ Hz}$ or voltage $U \le 0.85\,U_n$ for $> 0.5\text{ s}$.

## Data Schema
```python
@dataclass
class MarineGeneratorInput:
    gen_id: str
    rated_kw: float
    current_kw: float
    frequency_hz: float
    voltage_pct: float
    is_online: bool

@dataclass
class PmsEvaluationResult:
    total_running_kw: float
    total_capacity_kw: float
    total_load_pct: float
    is_auto_start_required: bool
    shedding_stage: int
    blackout_risk_status: str
    advisories: List[str]
```
