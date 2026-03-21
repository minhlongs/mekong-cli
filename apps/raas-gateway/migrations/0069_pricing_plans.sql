-- Migration 0069: Custom Pricing Plans for RaaS Gateway
-- Admin-defined pricing plans with feature gates and tenant subscriptions

CREATE TABLE IF NOT EXISTS pricing_plans (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  description TEXT,
  price_monthly REAL NOT NULL,
  price_yearly REAL,
  currency TEXT DEFAULT 'USD',
  features TEXT NOT NULL DEFAULT '{}', -- JSON: feature gates
  limits TEXT NOT NULL DEFAULT '{}',   -- JSON: { missions_per_month, api_calls_per_day, team_members, storage_mb }
  is_active BOOLEAN DEFAULT TRUE,
  is_public BOOLEAN DEFAULT TRUE,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_pricing_plans_active ON pricing_plans(is_active, is_public);

CREATE TABLE IF NOT EXISTS plan_subscriptions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  status TEXT DEFAULT 'active' CHECK(status IN ('active','canceled','past_due','trialing')),
  billing_cycle TEXT DEFAULT 'monthly' CHECK(billing_cycle IN ('monthly','yearly')),
  current_period_start TEXT,
  current_period_end TEXT,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX idx_plan_subs_tenant ON plan_subscriptions(tenant_id);
CREATE INDEX idx_plan_subs_plan ON plan_subscriptions(plan_id);
