-- Migration 0045: Affiliate Wiring
-- Adds payout tracking and tenant referral linkage tables
-- Supports: processSignupReferral, processPaymentCommission, processCommissionPayout

CREATE TABLE IF NOT EXISTS affiliate_payouts (
  id TEXT PRIMARY KEY,
  partner_id TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT DEFAULT 'USD',
  payout_method TEXT DEFAULT 'polar',
  status TEXT DEFAULT 'pending',
  processed_at TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_payouts_partner ON affiliate_payouts(partner_id);
CREATE INDEX IF NOT EXISTS idx_payouts_status ON affiliate_payouts(status);

-- Track which referral code was used at signup, per tenant (unique constraint prevents double-referral)
CREATE TABLE IF NOT EXISTS tenant_referrals (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  partner_id TEXT NOT NULL,
  referral_code TEXT NOT NULL,
  signed_up_at TEXT DEFAULT (datetime('now')),
  first_payment_at TEXT,
  lifetime_value REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_tenant_referrals_tenant ON tenant_referrals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_referrals_partner ON tenant_referrals(partner_id);
