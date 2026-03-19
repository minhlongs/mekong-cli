-- Equity tracking — cap table, share classes, SAFE, vesting
CREATE TABLE IF NOT EXISTS equity_entities (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  entity_type TEXT NOT NULL DEFAULT 'portfolio_company' CHECK (entity_type IN ('studio', 'portfolio_company', 'spv')),
  total_authorized_shares INTEGER NOT NULL DEFAULT 10000000,
  incorporation_date TEXT,
  jurisdiction TEXT DEFAULT 'VN',
  metadata JSON DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS share_classes (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES equity_entities(id) ON DELETE CASCADE,
  name TEXT NOT NULL DEFAULT 'Common',
  class_type TEXT NOT NULL DEFAULT 'common' CHECK (class_type IN ('common', 'preferred_a', 'preferred_b', 'advisory')),
  votes_per_share REAL NOT NULL DEFAULT 1.0,
  liquidation_preference REAL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS equity_grants (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES equity_entities(id) ON DELETE CASCADE,
  stakeholder_id TEXT NOT NULL REFERENCES stakeholders(id),
  share_class_id TEXT NOT NULL REFERENCES share_classes(id),
  grant_type TEXT NOT NULL DEFAULT 'grant' CHECK (grant_type IN ('grant', 'exercise', 'transfer', 'conversion', 'cancellation')),
  shares INTEGER NOT NULL,
  price_per_share REAL DEFAULT 0,
  vesting_months INTEGER DEFAULT 0,
  cliff_months INTEGER DEFAULT 0,
  vesting_start_date TEXT,
  effective_date TEXT NOT NULL DEFAULT (datetime('now')),
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_grant_entity ON equity_grants(entity_id);
CREATE INDEX IF NOT EXISTS idx_grant_stakeholder ON equity_grants(stakeholder_id);

CREATE TABLE IF NOT EXISTS safe_notes (
  id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL REFERENCES equity_entities(id) ON DELETE CASCADE,
  investor_stakeholder_id TEXT NOT NULL REFERENCES stakeholders(id),
  principal_amount REAL NOT NULL,
  valuation_cap REAL,
  discount_rate REAL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'outstanding' CHECK (status IN ('outstanding', 'converted', 'cancelled')),
  investment_date TEXT NOT NULL DEFAULT (datetime('now')),
  conversion_date TEXT,
  converted_shares INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
