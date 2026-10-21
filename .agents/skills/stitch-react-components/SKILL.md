---
name: stitch-react-components
description: >-
  Component synthesis and transformation engine. Translates Stitch Tailwind HTML prototypes into production React 18/TypeScript components with dual-mode API integration and Web Crypto fallback.
---

# /stitch-react-components — React & Vite Architecture

Transforms static Stitch screens into responsive, interactive React components with TypeScript and Tailwind CSS.

## Architecture
- `src/components/CyberNavbar.tsx`: Global glass navigation & status beacon.
- `src/components/CommandPalette.tsx`: Filterable Cmd+K modal for all screens.
- `src/components/VietQRModal.tsx`: Real-time VietQR modal with HMAC-SHA256 simulation.
- `src/components/BentoCard.tsx`: Modular Bento containers with flexible column spans.
- `src/components/ScreenViewer.tsx`: Responsive multi-viewport screen viewer (Desktop / Tablet / Mobile).
- `src/services/api.ts`: Dual-mode backend API client with Web Crypto subtle fallback.

## Execution
```bash
npm --prefix site/react-app run build
```
