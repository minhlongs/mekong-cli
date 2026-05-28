# Project: Nhịp Điệu Xanh Brand Identity System

## Architecture
This project defines the branding visual language, style guide tokens, logos, and HTML-based guidelines for the "Nhịp Điệu Xanh" green-energy and real-estate platform.
Target Directory: `/Users/macbook/nhipdieuxanh-agent/brand`
All assets must be valid, well-structured, and non-cheating.

## Code Layout
- `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json` — Color palette and typography tokens.
- `/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-primary.svg` — Primary brand logo.
- `/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-monochrome.svg` — Monochrome version.
- `/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-symbol.svg` — Icon-only/symbol version.
- `/Users/macbook/nhipdieuxanh-agent/brand/logos/favicon.svg` — Favicon SVG.
- `/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html` — Brand Style Guide & Guidelines HTML.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Strategic Planning & Setup | Plan architecture, create plan.md, define subagent strategy | None | DONE |
| 2 | Color and Typography Tokens | Define brand_tokens.json containing Emerald-based palette and typography scale | M1 | DONE |
| 3 | SVG Logo Assets | Design and output logo-primary.svg, logo-monochrome.svg, logo-symbol.svg, and favicon.svg | M2 | DONE |
| 4 | Brand Guidelines HTML | Design guidelines.html rendering style tokens, logo assets, and rules | M3 | DONE |
| 5 | Verification & Audit | Verify correctness and integrity | M4 | DONE |

## Interface Contracts
- `brand_tokens.json` format:
  ```json
  {
    "colors": {
      "primary": { "light": "...", "medium": "...", "dark": "..." },
      "neutral": { "light": "...", "dark": "..." },
      "semantic": { "success": "...", "warning": "...", "error": "..." }
    },
    "typography": {
      "headings": { "family": "Outfit", "weights": [500, 600, 700], "scale": { ... } },
      "body": { "family": "Inter", "weights": [400, 500], "scale": { ... } }
    }
  }
  ```
