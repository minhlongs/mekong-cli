# Design Guidelines — Vietnam Port Terminal, Cold Chain & Trade Finance Suite (Phases 179-182)

## 1. Color Palette & Semantics
- **Port Terminal Deep Navy**: `#0f172a` (Container stacks, maritime infrastructure, structural stability)
- **Logistics Electric Cyan**: `#06b6d4` (Real-time telemetry, GPS barge tracking, SOLAS compliance)
- **Cold Chain Sub-Zero Azure**: `#38bdf8` (Reefer monitoring, cryogenic, pharmaceutical cold storage)
- **Finance Emerald**: `#10b981` (Letter of Credit clean drawing, discount approval, liquidity)
- **Warning Amber**: `#f59e0b` (DEM/DET Tier 2 escalation, minor temperature drift)
- **Critical Crimson**: `#ef4444` (VGM gate-in rejection, L/C refusal notice, Pharma Quarantine Hold)

## 2. Typography & Spatial Rhythm
- **Primary Font**: Inter / Geist Sans for high density technical data.
- **Monospace Font**: JetBrains Mono for ISO container numbers, HS codes, L/C credit numbers, and GPS coordinates.
- **Border Radii**: `rounded-lg` (8px) for KPI stat cards, `rounded-xl` (12px) for modal inspection panels.
- **Elevation**: Subtle borders `border border-slate-700/60` with frosted cyber-glass backdrop `backdrop-blur-md bg-slate-900/80`.

## 3. UI Surfaces & Layout
- **Dashboard Grid**: 4 operational zones:
  1. *Zone 1: Seaport Terminal Gate & DEM/DET Watch*: Live free-time burn counters, SOLAS weighbridge verification.
  2. *Zone 2: UCP 600 Letter of Credit Document Desk*: 5-day examination countdown, discrepancy audit tree.
  3. *Zone 3: Pharma GDP Cold Chain Telemetry*: Real-time Arrhenius MKT curve, excursion cumulative alert.
  4. *Zone 4: Freight Carbon & Green Route Optimizer*: ISO 14083 multi-leg modal breakdown, carbon offset calculator.
