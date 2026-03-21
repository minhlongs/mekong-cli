-- Migration 0079: Revenue Analytics V2
-- Cohort analysis, expansion/contraction MRR, NRR

CREATE TABLE IF NOT EXISTS revenue_snapshots (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  period TEXT NOT NULL,
  mrr REAL DEFAULT 0,
  arr REAL DEFAULT 0,
  credits_purchased INTEGER DEFAULT 0,
  credits_used INTEGER DEFAULT 0,
  plan_tier TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cohort_assignments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  cohort_month TEXT NOT NULL,
  signup_source TEXT,
  first_payment_at TEXT,
  current_plan TEXT,
  lifetime_revenue REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rev_snap_tenant ON revenue_snapshots(tenant_id, period);
CREATE INDEX IF NOT EXISTS idx_rev_snap_period ON revenue_snapshots(period);
CREATE INDEX IF NOT EXISTS idx_cohort_month ON cohort_assignments(cohort_month);
