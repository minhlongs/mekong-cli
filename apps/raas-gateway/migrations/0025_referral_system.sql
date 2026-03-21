-- Migration 0025: Referral system
-- Adds referral tracking columns to tenants and a referrals table

-- Add referral columns to tenants
ALTER TABLE tenants ADD COLUMN referral_code TEXT;
ALTER TABLE tenants ADD COLUMN referred_by TEXT;
ALTER TABLE tenants ADD COLUMN referral_count INTEGER DEFAULT 0;

-- Referral tracking table
CREATE TABLE IF NOT EXISTS referrals (
  id TEXT PRIMARY KEY,
  referrer_id TEXT NOT NULL,
  referred_id TEXT NOT NULL,
  bonus_credits INTEGER DEFAULT 5,
  status TEXT DEFAULT 'completed',
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (referrer_id) REFERENCES tenants(id),
  FOREIGN KEY (referred_id) REFERENCES tenants(id)
);
