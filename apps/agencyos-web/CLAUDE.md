# AgencyOS Web — 第六篇 虛實 (Xu Shi) — Dashboard & Command Center

> **Inherits**: `../../CLAUDE.md` (Root Constitution)
> **Domain**: RaaS Dashboard & Admin Panel — full visibility into ecosystem operations
> **Binh Phap**: 虛實 — Exploit strengths, expose weaknesses: the dashboard reveals ALL system state
> **Stack**: Next.js + TypeScript + Tailwind CSS

## Project Overview

AgencyOS Web is the main dashboard/admin interface for the RaaS (Revenue-as-a-Service) ecosystem. It provides unified visibility into all sub-projects, agent operations, and revenue metrics.

## Tech Stack

| Component     | Technology   |
| ------------- | ------------ |
| **Framework** | Next.js      |
| **Language**  | TypeScript   |
| **Styling**   | Tailwind CSS |
| **State**     | React Context / Zustand |

## Architecture

```
src/
├── components/     # Reusable UI components
│   ├── network/    # Network visualization (tree, list, cards)
│   └── withdrawal/ # Financial operations
├── pages/          # Route pages
└── lib/            # Utilities and API clients
```

## Quality Standards

- All components: WCAG 2.1 AA accessible
- Semantic HTML + ARIA labels mandatory
- Type safety: zero `any` types
- File size: < 200 lines per file
- Responsive: mobile-first design

## Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| NetworkPage | `src/pages/NetworkPage.tsx` | Network visualization |
| WithdrawalPage | `src/pages/WithdrawalPage.tsx` | Financial operations |
| NodeCard | `src/components/network/node-card.tsx` | Agent node display |

## Development Rules

- Follow root CLAUDE.md Binh Phap quality gates
- Run `npm run build` before commit — 0 TypeScript errors
- Use kebab-case for all file names
- Components must handle loading, error, and empty states
