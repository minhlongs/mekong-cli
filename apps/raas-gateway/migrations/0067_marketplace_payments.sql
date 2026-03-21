-- Migration 0067: Marketplace Payments — revenue share for template sellers
-- 70% seller / 30% platform commission split

CREATE TABLE IF NOT EXISTS marketplace_sellers (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  display_name TEXT NOT NULL,
  payout_email TEXT,
  commission_rate REAL DEFAULT 0.70, -- 70% to seller, 30% platform
  total_earnings REAL DEFAULT 0,
  total_payouts REAL DEFAULT 0,
  status TEXT DEFAULT 'active' CHECK(status IN ('active','suspended','pending_review')),
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX idx_marketplace_sellers_tenant ON marketplace_sellers(tenant_id);

CREATE TABLE IF NOT EXISTS marketplace_transactions (
  id TEXT PRIMARY KEY,
  seller_id TEXT NOT NULL,
  buyer_tenant_id TEXT NOT NULL,
  template_id TEXT NOT NULL,
  amount REAL NOT NULL,
  seller_share REAL NOT NULL,
  platform_share REAL NOT NULL,
  currency TEXT DEFAULT 'USD',
  status TEXT DEFAULT 'completed' CHECK(status IN ('pending','completed','refunded')),
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_mp_transactions_seller ON marketplace_transactions(seller_id);
CREATE INDEX idx_mp_transactions_buyer ON marketplace_transactions(buyer_tenant_id);

CREATE TABLE IF NOT EXISTS marketplace_payouts (
  id TEXT PRIMARY KEY,
  seller_id TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT DEFAULT 'USD',
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending','processing','completed','failed')),
  payout_method TEXT DEFAULT 'polar',
  reference TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  completed_at TEXT
);
CREATE INDEX idx_mp_payouts_seller ON marketplace_payouts(seller_id);
