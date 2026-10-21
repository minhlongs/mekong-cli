# Phase 03: Port Container Terminal Automated Yard Stacking & RTG Dispatch Engine (Phase 377)

## Overview
- **Target File**: `src/core/maritime/phase_377_container_yard_rtg_dispatch.py` (< 200 LOC)
- **Standard**: UNCTAD Container Terminal Handbook, IAPH Smart Ports, Decision 1579/QD-TTg
- **Objective**: Manage 3D yard block assignment (Bays x Rows x Tiers), compute container reshuffling penalties, enforce IMDG dangerous goods segregation separation, and dispatch RTG cranes minimizing gantry travel distances.

## Key Formulas
- Reshuffling penalty: $N_{reshuffle} = \sum \max(0, Tier_i - Tier_{target})$ where retrieval urgency conflicts
- Cost-to-go metric: $J = \alpha \cdot D_{gantry} + \lambda \cdot N_{reshuffle}$
- IMDG Segregation buffer: Minimum 1 bay longitudinal separation between incompatible hazardous goods
- RTG to QC ratio: Minimum 1 RTG per 2 active Quay Cranes to avoid IMV vehicle queuing

## Todo Checklist
- [ ] Implement `ContainerItem`, `YardStackInput`, and `YardStackRtgReport` dataclasses
- [ ] Implement `ContainerYardRtgDispatchEngine` with heuristic optimization
- [ ] Verify < 200 LOC constraint
