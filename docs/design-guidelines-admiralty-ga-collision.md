# Design Guidelines: Maritime Admiralty, General Average, Liens & Collision Cockpit (Phases 203-206)

## 1. Visual Hierarchy & Theme
- **Obsidian Nautical Theme**: Deep slate-navy background (`#0b1329`), border accents in maritime teal (`#0ea5e9`), maritime gold for priority liens (`#f59e0b`), alarm red for arrest/collisions (`#ef4444`), and emerald for releases/settlements (`#10b981`).
- **Typography**: Inter / Plus Jakarta Sans for UI elements, JetBrains Mono / Space Mono for currency and mathematical calculations.
- **Micro-Components**:
  - **Arrest Status Badge**: Judicial detention indicator (`ARRESTED`, `SECURITY_LODGED`, `RELEASED`).
  - **GA Contributory Waterfall**: Visual distribution chart for Ship, Cargo, and Freight.
  - **Lien Priority Staircase**: 5-tier statutory waterfall showing pre-mortgage ranking.
  - **Collision Vector Dial**: Relative fault ratio display ($\alpha\% : \beta\%$).
