---
title: "Phase 8 — Database Migration"
description: "Create SQL migration for idempotency_keys table"
status: pending
priority: P2
effort: 0.5h
parent_plan: 260306-2301-usage-metering-phase4
---

# Phase 8 — Database Migration

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- Database: `src/db/database.py`

## Migration SQL

### File: docs/migrations/add_idempotency_keys_table.sql

```sql
-- Migration: Add usage_idempotency_keys table
-- Date: 2026-03-06
-- Purpose: Prevent double-counting of CLI commands with idempotency keys

-- Create idempotency keys table
CREATE TABLE IF NOT EXISTS usage_idempotency_keys (
    id SERIAL PRIMARY KEY,
    key_id TEXT NOT NULL,
    command_hash TEXT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint prevents duplicates
    CONSTRAINT unique_idempotency_key
        UNIQUE (key_id, command_hash, date)
);

-- Index for efficient cleanup queries
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_date
    ON usage_idempotency_keys(date);

-- Index for lookups
CREATE INDEX IF NOT EXISTS idx_idempotency_keys_lookup
    ON usage_idempotency_keys(key_id, command_hash, date);

-- Add comment
COMMENT ON TABLE usage_idempotency_keys IS
'Prevents double-counting of CLI commands. TTL: 24 hours (lazy cleanup).';

COMMENT ON COLUMN usage_idempotency_keys.command_hash IS
'SHA256 hash of command (first 16 chars)';

COMMENT ON COLUMN usage_idempotency_keys.date IS
'Date in UTC (YYYY-MM-DD). Keys auto-expired after 24h.';

-- Grant permissions (adjust as needed)
GRANT SELECT, INSERT, DELETE ON usage_idempotency_keys TO mekong_user;
GRANT USAGE ON SEQUENCE usage_idempotency_keys_id_seq TO mekong_user;

-- Verification query
-- SELECT COUNT(*) FROM usage_idempotency_keys;
```

## Run Migration

```bash
# Option 1: Via Supabase CLI (if using Supabase)
psql "$(npx supabase db url)" -f docs/migrations/add_idempotency_keys_table.sql

# Option 2: Via psql directly
psql "$DATABASE_URL" -f docs/migrations/add_idempotency_keys_table.sql

# Option 3: Via Python script
python3 -c "
from src.db.database import init_database
import asyncio

async def run():
    db = await init_database()
    with open('docs/migrations/add_idempotency_keys_table.sql') as f:
        sql = f.read()
    # Split by semicolons and run each
    for stmt in sql.split(';'):
        if stmt.strip():
            await db.execute(stmt)
    print('Migration complete')

asyncio.run(run())
"
```

## Verification

```sql
-- Check table exists
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'usage_idempotency_keys';

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'usage_idempotency_keys';

-- Insert test row
INSERT INTO usage_idempotency_keys (key_id, command_hash, date)
VALUES ('test123', 'abc123', CURRENT_DATE);

-- Verify
SELECT * FROM usage_idempotency_keys;

-- Cleanup test
DELETE FROM usage_idempotency_keys WHERE key_id = 'test123';
```

## Success Criteria

- [ ] SQL migration file created
- [ ] Migration runs without errors
- [ ] Table exists after migration
- [ ] Indexes created
- [ ] Permissions granted

## Todo List

- [ ] Create `docs/migrations/add_idempotency_keys_table.sql`
- [ ] Run migration on database
- [ ] Verify table and indexes
- [ ] Document in `docs/usage-metering.md`
