# AgencyOS API — Backend Service Layer

> **第四篇 軍形 (Jun Xing)** — Military disposition: defense before offense
>
> This file governs CC CLI behavior ONLY when working inside `apps/api/`.
> Inherits from root `CLAUDE.md` (Constitution) and `~/.claude/CLAUDE.md` (Global).

## Identity

**Role:** Core backend API service for the AgencyOS ecosystem
**Function:** Business logic, data access, external integrations

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Node.js |
| Language | TypeScript |
| Framework | TBD (Express/Fastify/Hono) |

## Development Rules (Domain-Specific)

### API Standards
- All endpoints must validate input (zod or similar)
- RESTful conventions: proper HTTP methods and status codes
- API versioning: `/v1/` prefix
- Error response format: `{ error: string, code: string, details?: any }`

### Security (軍形 Priority)
- Input validation on EVERY endpoint — no trust from external
- Rate limiting on all public endpoints
- Authentication required for non-public routes
- No secrets in codebase — environment variables only
- SQL injection prevention (parameterized queries)
- CORS whitelist (no wildcard in production)

### Code Standards
- TypeScript strict mode
- Zero `:any` types
- kebab-case file naming
- Files < 200 lines

## Quality Gates

- `npm run build` — 0 TypeScript errors
- `npm test` — all tests pass
- `npm audit --audit-level=high` — 0 high/critical vulnerabilities
- No hardcoded secrets or API keys
