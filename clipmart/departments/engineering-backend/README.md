# Backend Engineering Department as a Service

> Replace a backend team with AI agents that build APIs, manage databases, and ship features end-to-end.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| 2 Backend Engineers ($160k each) | $320,000/yr | $49/mo floor |
| GitHub Copilot Enterprise | $4,800/yr | Included |
| **Total replaced** | **$324,800/yr** | **~$3,600/yr** |

## What This Department Does

1. **API Development** — REST/GraphQL endpoints, auth, rate limiting, validation
2. **Database Management** — Schema design, migrations, optimization, RLS
3. **Feature Implementation** — Full backend feature from spec to tested code
4. **Code Review** — PR reviews with security, performance, and maintainability checks
5. **Performance Optimization** — Query profiling, caching, load testing

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| REST API endpoint built + tested | $15 |
| Database migration | $10 |
| Backend feature complete (spec→code) | $25 |
| Code review (PR) | $8 |
| Performance optimization | $20 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong backend-api-build    # Build API endpoint from spec
mekong backend-db-task      # Database task execution
mekong cook                 # Full feature implementation
mekong code                 # Code generation
mekong review               # Code review
mekong test                 # Test generation + execution
```

## Install

```bash
mekong install dept-engineering-backend
```

## Configuration

```bash
# .mekong/.env.dept-engineering-backend
DEPT_BE_LANGUAGE=typescript  # typescript|python|go
DEPT_BE_FRAMEWORK=hono       # hono|express|fastapi
DEPT_BE_DATABASE=postgres
DEPT_BE_DB_URL=postgres://user:pass@localhost:5432/db
DEPT_BE_TEST_FRAMEWORK=vitest
DEPT_BE_REPO_URL=https://github.com/org/repo
```
