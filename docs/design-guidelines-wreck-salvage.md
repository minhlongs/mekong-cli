# Design Guidelines: Maritime Wreck Removal, LLMC, Salvage & Penalties (Phases 199-202)

## 1. Visual Aesthetics & Design Philosophy
- **Domain Identity**: Maritime Emergency Operations, Sovereign Port State Enforcement & Admiralty Law.
- **Palette & Typography**:
  - Primary Background: Obsidian Cyber-Glass `#0a0e17`
  - Card & Container Surface: Midnight Slate `#121b2a` with border `#1e293b`
  - Accent Safe / Sovereign Compliance: Emerald Jade `#10b981`
  - Warning / Statutory Notice Active: Amber Horizon `#f59e0b`
  - Alert / Detained / Grounding / Clearance Refused: Crimson Red `#ef4444`
  - Accent Hydrodynamic & Legal: Ocean Azure `#38bdf8`
  - Typography: Inter / Plus Jakarta Sans for UI, JetBrains Mono for statutory codes, numbers, and monetary figures.

## 2. Component System & Layout Patterns
- **Executive KPI Cards**: Grid layout highlighting Gross Tonnage, SDR Limitation Cap, Total Encumbrance / Salved Fund, Statutory Notice Countdown (Days).
- **Compliance Status Chips**:
  - `[IN_CLASS]` / `[WRC_COMPLIANT]` / `[CLEARANCE_GRANTED]`: Emerald Badge
  - `[SALVAGE_NOTICE_ACTIVE]` / `[SCOPIC_INVOKED]`: Amber Badge
  - `[AUCTION_FORCED]` / `[LIMITATION_BROKEN]` / `[CLEARANCE_BLOCKED]`: Crimson Badge
- **Waterfall & Audit Tables**:
  - Monospace formatting for VND currency and SDR quantities.
  - Clear statutory citation in footer (e.g., *Vietnam Maritime Code 2015 Arts. 109-114, Decree 123/2021/NĐ-CP*).
- **Responsive Navigation**: Full mobile compatibility with 44px min tap targets and uncluttered vertical stack layouts.
