-- Migration 0019: Coupon system for promotional credit codes
CREATE TABLE IF NOT EXISTS coupons (
  id TEXT PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  discount_percent INTEGER DEFAULT 0,
  bonus_credits INTEGER DEFAULT 0,
  max_uses INTEGER DEFAULT 100,
  current_uses INTEGER DEFAULT 0,
  valid_from TEXT DEFAULT (datetime('now')),
  valid_until TEXT,
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS coupon_redemptions (
  id TEXT PRIMARY KEY,
  coupon_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (coupon_id) REFERENCES coupons(id),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Prevent duplicate redemptions per tenant per coupon
CREATE UNIQUE INDEX IF NOT EXISTS idx_coupon_tenant ON coupon_redemptions(coupon_id, tenant_id);
