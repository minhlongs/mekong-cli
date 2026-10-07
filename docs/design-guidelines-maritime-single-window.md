# Design Guidelines — Maritime Single Window & E-Quarantine Portal (Phases 191-194)

## 1. Visual Hierarchy & Color Palette
- **Obsidian Dark Mode**: Base background `#0F172A` (slate-900), Card background `rgba(24, 24, 27, 0.7)` (zinc-900 with opacity for glassmorphism), Border `#334155` (slate-700).
- **VNSW Cyan (`#22D3EE`)**: Used for e-Port Clearance, FAL form submissions, and single window notification timers.
- **Manning Emerald (`#34D399`)**: Used for STCW compliance, Shore Pass generation, and successful crew list audits.
- **Quarantine Amber (`#FBBF24`)**: Used for Free Pratique status, SSCEC/SSCC validities, and Yellow Fever surveillance.
- **MARPOL Green/Rose (`#10B981` / `#F43F5E`)**: Used for 15 ppm OWS alarm monitoring and Annex VI 0.50% sulfur compliance status.

## 2. Typography & Spatial System
- **Primary Font**: `Inter`, `SF Pro Display`, `system-ui`.
- **Monospace Data Font**: `JetBrains Mono` or `Fira Code` for FAL Form IDs, QR code payloads, Crew Passport numbers, and OWS metrics.
- **Spacing**: 8pt base grid system. Cards use `rounded-2xl` with `backdrop-blur-md` for the modern Cyber-Glass aesthetic.
- **Tab Layout**: Clean pill-shaped or bordered tabs for navigating between VNSW, Manning, Quarantine, and MARPOL views.

## 3. UI Components & Glassmorphism
- **Cards**: Use slightly translucent dark backgrounds (`bg-zinc-900/80`) paired with `backdrop-blur-md` and subtle borders (`border-slate-700`) to create depth.
- **KPI Metrics**: Large, high-contrast monospace values paired with small, uppercase, widely tracked labels. Stat labels specify the corresponding statutory regulation (e.g., Decree 58/2017 for Maritime Dues, Decree 77/2017 for Border Control).
- **Status Badges**: Semi-transparent backgrounds (`bg-{color}-500/10`) with solid colored text (`text-{color}-400`) and borders.

## 4. Interaction & Motion
- **Hover States**: Cards lift slightly (`-translate-y-1`) or brighten borders (`hover:border-cyan-400/50`) with a smooth 200ms transition.
- **Tabs**: Vanilla JavaScript toggles hiding/showing sections (removing/adding `hidden` class) and dynamically highlighting the active tab.

## 5. Regulatory Context Injection
Provide clear context for maritime operators by referencing mandatory decrees in subtexts:
- VNSW & Maritime Dues: Decree 58/2017/ND-CP.
- Border Immigration: Decree 77/2017/ND-CP.
- Quarantine & Epidemic Surveillance: Decree 89/2018/ND-CP.
- MARPOL Annex VI & Environmental: Decree 08/2022/ND-CP.
