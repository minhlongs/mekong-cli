# Design Guidelines — Maritime Dangerous Cargo, Tugboat Escort, Berthage & Channel Clearance Suite (Phases 231–234)

## 1. Visual Aesthetics & CLI Theme
- **Color Palette & Semantic Tokens**:
  - `Hazard / Warning`: Bright Yellow / Amber (`bold yellow`, `#E5C07B`) for dangerous goods segregation violations and IMDG direct-discharge alerts.
  - `Critical / Detention`: Fiery Red (`bold red`, `#E06C75`) for prohibited yard storage, under-keel clearance (UKC) breaches, air draft collisions, and VMC Art. 101 refusal orders.
  - `Operational Clearance`: Marine Emerald (`bold green`, `#98C379`) for verified tug bollard pull allocations, compliant mooring line operations, and valid fairway clearances.
  - `Maritime Infrastructure & Navigational Data`: Deep Cyan / Steel Blue (`bold cyan`, `#56B6C2`) for channel depth, tidal levels, LOA/GT tonnage, and berthage fee calculations.
- **Typography & Layout**:
  - Rich Panels with double borders for critical statutory orders (Clearance Refusal, DG Emergency Buffer Breach).
  - High-density structured ASCII tables for segregation matrices, bollard pull allocation tiers, and mooring fee breakdowns.
  - Machine-readable JSON output via standard `--json` flag on all CLI commands.

## 2. Core Functional Pillars (Phases 231–234)
1. **Phase 231: Dangerous Cargo Terminal Handling & Hazardous Port Yard Storage**
   - Statutory: Decree 58/2017/NĐ-CP, Decree 34/2024/NĐ-CP, IMO IMDG Code Amdt 41-22.
   - Segregation matrix (longitudinal bay vs transverse row separation), Class 1/7/5.2 direct discharge mandates, max yard dwell hours (48h/72h), and 50m emergency buffer zones.
2. **Phase 232: Seaport Tugboat Towage Escort & Bollard Pull Allocation**
   - Statutory: Circular 39/2023/TT-BGTVT, Decree 58/2017/NĐ-CP harbor towage rules.
   - Statutory LOA/GT allocation tiers, minimum Bollard Pull (BP) requirements (20T–260T+), weather cutoff triggers (Beaufort $\ge 6$, current $> 3.0$ knots), and channel escort surcharges (+30% to +50%).
3. **Phase 233: Port Berthage / Anchorage Tariffs & Statutory Mooring Line Operations**
   - Statutory: Circular 39/2023/TT-BGTVT, Circular 12/2024/TT-BGTVT.
   - Berthage fee calculation (GT-hour rates for cargo vs waiting/repair), anchorage fee tiers, 5-tier GT mooring services, and statutory night (+30-50%) / holiday (+100%) surcharges.
4. **Phase 234: Maritime Safety Inspection, Under-Keel Clearance (UKC) & Fairway Clearance**
   - Statutory: Vietnam Maritime Code 2015 Arts. 88–102, Decree 58/2017/NĐ-CP, PIANC WG 121.
   - Dynamic UKC equation ($D_{\text{channel}} - (T_{\text{static}} + S_{\text{squat}} + H_{\text{wave}} + \Delta_{\text{salinity}})$), minimum statutory UKC margin (10% draft or 0.5m–1.2m), overhead air draft clearance ($\ge 2.0\text{m}$ buffer), and Harbormaster clearance refusal grounds under VMC Art. 101.
