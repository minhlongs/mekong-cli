-- Affiliate partners
CREATE TABLE IF NOT EXISTS affiliate_partners (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  partner_code TEXT UNIQUE NOT NULL,
  commission_rate REAL DEFAULT 0.20,
  status TEXT DEFAULT 'active' CHECK(status IN ('active','suspended','terminated')),
  total_referrals INTEGER DEFAULT 0,
  total_earned REAL DEFAULT 0,
  total_paid REAL DEFAULT 0,
  payout_method TEXT DEFAULT 'polar',
  payout_details TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Affiliate commissions (per referred tenant payment)
CREATE TABLE IF NOT EXISTS affiliate_commissions (
  id TEXT PRIMARY KEY,
  partner_id TEXT NOT NULL REFERENCES affiliate_partners(id),
  referred_tenant_id TEXT NOT NULL,
  payment_amount REAL NOT NULL,
  commission_amount REAL NOT NULL,
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','paid','rejected')),
  period TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Track which tenants were referred by which partner
CREATE TABLE IF NOT EXISTS affiliate_referrals (
  id TEXT PRIMARY KEY,
  partner_id TEXT NOT NULL REFERENCES affiliate_partners(id),
  referred_tenant_id TEXT UNIQUE NOT NULL,
  signup_at TEXT DEFAULT (datetime('now')),
  first_payment_at TEXT,
  lifetime_value REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_affiliate_partners_tenant ON affiliate_partners(tenant_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_partners_code ON affiliate_partners(partner_code);
CREATE INDEX IF NOT EXISTS idx_affiliate_commissions_partner ON affiliate_commissions(partner_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_referrals_partner ON affiliate_referrals(partner_id);
