# Phase 02: Port Berth Allocation & Quay Crane Scheduling (BAP/QCSP)

## Context & Standards
- UNCTAD Port Development Handbook, PIANC MarCom WG 158, Vietnam Decision 1579/QD-TTg.

## Requirements
- Safety clearance: $L_{\text{berth\_req}} = \text{LOA} + 30.0\text{ m}$ (15m each side).
- Draft check: $d_{\text{ship\_draft}} + \text{UKC}_{\text{min}} \le d_{\text{water}}$ where $\text{UKC}_{\text{min}} = 1.5\text{ m}$.
- Tidal window: Deep-draft access gated on high-tide delta for Cai Mep - Thi Vai & Lach Huyen.
- Quay Crane Assignment & Scheduling (QCSP): Non-crossing distance between adjacent cranes $D_{\text{crane}} \ge 35.0\text{ m}$.
- Turnaround time estimation based on 25–32 moves/hr per crane.

## Target File
- `src/core/maritime/phase_372_port_berth_crane_bap_qcsp.py` (< 200 LOC)
