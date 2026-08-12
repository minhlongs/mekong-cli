# Mekong CLI v6.0 Tech Stack Research Report

## Recommended Tech Stack

### Core Runtime
| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **CLI** | Python + Typer | 3.11+ / 0.12+ | Rich CLI, async support, auto-completion |
| **API Gateway** | TypeScript + Hono | 4.x / 4.x | Edge-native, Cloudflare Workers optimized |
| **Workers** | Cloudflare Workers | Latest | Zero cold start, global distribution |
| **Database** | D1 (SQLite) + Supabase | - | Edge-compatible, Postgres for complex queries |
| **Cache/Rate Limit** | Cloudflare KV | - | Global, low-latency |

### Language & Framework Choices
- **Python**: Primary for CLI, billing, tax logic, orchestration
- **TypeScript**: API Gateway, Dashboard, Landing pages
- **Shared Types**: JSON Schema / OpenAPI for cross-language contracts

### Three Funnels Stack

#### 1. Zalo OA Funnel
```
┌─────────────────────────────────────────────┐
│  Python (src/seed/telegram/)                │
│  ├── Webhook Handler (FastAPI on Workers)   │
│  ├── Message Template Engine (Jinja2)       │
│  ├── Automation Rules Engine                │
│  └── Rate Limiter (Redis/KV)                │
└─────────────────────────────────────────────┘
```
- Zalo OA Official API (REST + Webhook)
- Message templates with VN/EN i18n
- Webhook verification (HMAC-SHA256)

#### 2. Tax & Accounting Funnel
```
┌─────────────────────────────────────────────┐
│  Python (src/seed/tax/)                     │
│  ├── TNCN/TNDN/GTGT Calculator              │
│  ├── TT78 Invoice Generator (PDF)           │
│  ├── Compliance Report Generator            │
│  └── MISA/ERP Export Adapters               │
└─────────────────────────────────────────────┘
```
- Decimal arithmetic for currency (no float)
- Config-driven tax rates (annual updates)
- PDF generation via ReportLab/WeasyPrint
- Digital signature for e-invoices

#### 3. Sophia AI Video Factory
```
┌─────────────────────────────────────────────┐
│  TypeScript (apps/sophia-ai-factory/)       │
│  ├── CF Worker Entry (Hono)                 │
│  ├── D-ID / ElevenLabs / OpenRouter SDKs    │
│  ├── MCU Credit Tracker (Durable Objects)   │
│  └── Video Pipeline Orchestrator            │
└─────────────────────────────────────────────┘
```
- Cloudflare Workers + Durable Objects for stateful pipelines
- D-ID for avatar video, ElevenLabs for TTS, OpenRouter for LLM
- MCU billing integration (1 MCU = 1 credit)
- Webhook callbacks for async video completion

### Billing & Payment Stack
- **Polar.sh**: Subscription management, checkout, webhooks
- **MCU System**: Custom credit ledger (src/billing/mcu.py)
- **Tier Gates**: Middleware on all premium routes
- **Webhook Idempotency**: Event deduplication via event_id

### Quality & Observability
| Tool | Purpose |
|------|---------|
| Ruff + MyPy | Python linting + type checking |
| ESLint + TypeScript | TS linting + type checking |
| Pytest + Vitest | Unit + integration tests |
| Sentry | Error tracking (all layers) |
| PostHog | Product analytics |
| GitHub Actions | CI/CD |

### Deployment Architecture
```
┌────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Python   │ │ TypeScript│ │ Tests    │ │ Build/Deploy │  │
│  │ Lint/Type│ │ Lint/Type │ │ (Real!)  │ │ Workers/Pages│  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ CLI PyPI │    │ API CF   │    │ Dashboard│
    │ Package  │    │ Workers  │    │ CF Pages │
    └──────────┘    └──────────┘    └──────────┘
```

### Key Integration Patterns
1. **Shared Contracts**: `contracts/` directory with JSON Schema
2. **Environment Sync**: `.env.example` → `.env` via setup wizard
3. **Cross-Language Types**: Generate TS types from Python Pydantic models
4. **Webhook Contracts**: Zod schemas for all incoming webhooks