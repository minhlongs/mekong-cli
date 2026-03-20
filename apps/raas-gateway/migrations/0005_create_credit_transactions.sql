-- Migration: 0005_create_credit_transactions
-- Created: 2026-03-19
-- Description: Create credit transactions table for billing history

CREATE TABLE IF NOT EXISTS credit_transactions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  amount INTEGER NOT NULL,
  type TEXT NOT NULL CHECK(type IN (
    'purchase', 'mission', 'refund', 'rollover', 'adjustment', 'webhook'
  )),
  mission_id TEXT REFERENCES missions(id) ON DELETE SET NULL,
  description TEXT,
  metadata TEXT DEFAULT '{}',  -- JSON metadata (e.g., Polar order ID)
  created_at TEXT DEFAULT (datetime('now'))
);

-- Index for tenant transactions
CREATE INDEX IF NOT EXISTS idx_transactions_tenant ON credit_transactions(tenant_id, created_at DESC);

-- Index for transaction type
CREATE INDEX IF NOT EXISTS idx_transactions_type ON credit_transactions(type);

-- Index for purchase transactions (billing)
CREATE INDEX IF NOT EXISTS idx_transactions_purchase ON credit_transactions(tenant_id, type)
WHERE type = 'purchase';
