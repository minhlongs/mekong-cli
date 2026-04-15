# PostgreSQL Migration Plan — Billing Layer

## Current State
- SQLite WAL mode for MCU billing, license storage, audit logs
- Single-writer limitation, no connection pooling
- Acceptable for <100 concurrent tenants

## Migration Triggers
- >100 concurrent tenants
- >1000 MCU transactions/minute
- Multi-region deployment needed

## Migration Steps
1. Add `asyncpg` / `psycopg[binary]` to requirements
2. Create `src/db/postgres_adapter.py` implementing same interface as SQLite adapter
3. Add connection pooling (min=5, max=20)
4. Migrate schema with Alembic
5. Dual-write period: SQLite + PostgreSQL for 2 weeks
6. Cut over to PostgreSQL-only
7. Remove SQLite adapter

## Connection String
```
DATABASE_URL=postgresql://user:pass@host:5432/mekong_billing
```

## Estimated Effort
- 2-3 days for adapter + tests
- 1 week for dual-write validation
- Does not block current operations
