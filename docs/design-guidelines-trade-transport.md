# Design Guidelines — Trade, Transport & Remedies Suite UI/UX

## 1. Visual Hierarchy & Theme
- **Theme**: Institutional Legal-Tech & Logistics Terminal (Dark Cyber-Glass / Deep Navy).
- **Background**: `#0a0e17` with subtle `#1e293b` container borders.
- **Accent Colors**:
  - Gold / Amber (`#f59e0b`): High-value compensation ceilings, statutory caps, and trade remedies.
  - Cyan / Sky Blue (`#06b6d4`): Air transport, SDR limits, and multimodal cargo indicators.
  - Emerald Green (`#10b981`): Valid claims, timely filings, and compliance passes.
  - Coral / Crimson (`#ef4444`): Expired limitations, fundamental breaches, and dumped imports.

## 2. CLI Experience Principles
- **Immediate Clarity**: Summary panels present the exact payable liability, applicable statutory ceiling, and legal basis up front.
- **Comparative Breakdown**: Tables show raw claimed loss vs statutory limitation ceiling side-by-side.
- **Machine-Readability**: All commands support `--json` for seamless scripting and integration into automated dispatch workflows.
- **Statutory Notice**: Clear indicators when claims exceed statutory limitation windows (e.g., 9 months for MTO, 2 years for Aviation).

## 3. Web Dashboard / Wireframe Specs
- Interactive tabs for:
  1. Multimodal Transport (MTO) Liability Calculator
  2. Montreal 1999 Air Carrier Compensation Matrix
  3. CISG 1980 Contract Breach & Incoterms 2020 Explorer
  4. Trade Remedies & Anti-Dumping Margin Evaluator
