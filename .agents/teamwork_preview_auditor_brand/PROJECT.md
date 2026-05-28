# Project: Nhịp Điệu Xanh Brand Audit
# Scope: Forensic Audit

## Architecture
- Brand identity directory: `/Users/macbook/nhipdieuxanh-agent/brand`
- Artifacts to check: `brand_tokens.json`, `logos/` SVGs, `guidelines.html`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | JSON Audit | Parse brand_tokens.json for schema & genuineness | none | DONE |
| 2 | SVG Audit | Parse SVG logos and check stroke outlines | none | DONE |
| 3 | HTML Audit | Verify guidelines.html features | none | DONE |
| 4 | Keyword Audit | Scan for forbidden keywords | none | DONE |
| 5 | Integrity Audit | Check for dummy code / bypasses / cheats | none | DONE |
| 6 | Aggregated Handoff | Synthesize findings, produce verdict and write handoff.md | all | DONE |

## Interface Contracts
### Forensic Auditor ↔ Brand Directory
- Path: `/Users/macbook/nhipdieuxanh-agent/brand`
- Verifiers: Valid JSON parsing, SVG XML validation, HTML structural validation, keyword regex scans.
