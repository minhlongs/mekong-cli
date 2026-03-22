-- Migration: 0174_platform_resource_pools
-- Created: 2026-03-22
-- Description: Platform resource pools for capacity management across tenants

CREATE TABLE IF NOT EXISTS resource_pools (
  id TEXT PRIMARY KEY,
  pool_name TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  total_capacity INTEGER NOT NULL,
  allocated INTEGER NOT NULL DEFAULT 0,
  available INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pool_allocations (
  id TEXT PRIMARY KEY,
  pool_id TEXT NOT NULL REFERENCES resource_pools(id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  amount INTEGER NOT NULL,
  allocated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  released_at TEXT
);

-- Indexes for resource_pools
CREATE INDEX IF NOT EXISTS idx_resource_pools_pool_name ON resource_pools(pool_name);

-- Indexes for pool_allocations
CREATE INDEX IF NOT EXISTS idx_pool_allocations_pool_id ON pool_allocations(pool_id);
