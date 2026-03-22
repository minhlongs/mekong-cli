-- Migration: Mission Resource Allocation
-- Tracks resource allocations per mission and resource pools per tenant

CREATE TABLE IF NOT EXISTS mission_resource_allocations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  allocated_amount REAL NOT NULL,
  used_amount REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'allocated',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_resource_allocations_tenant ON mission_resource_allocations(tenant_id);

CREATE TABLE IF NOT EXISTS mission_resource_pools (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  pool_name TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  total_capacity REAL NOT NULL,
  available_capacity REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_resource_pools_tenant ON mission_resource_pools(tenant_id);
