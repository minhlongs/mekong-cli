-- Migration: 0010_add_telegram_chat_id
-- Created: 2026-03-21
-- Description: Add telegram_chat_id and referral_code to tenants

ALTER TABLE tenants ADD COLUMN telegram_chat_id TEXT;
ALTER TABLE tenants ADD COLUMN referral_code TEXT;
ALTER TABLE tenants ADD COLUMN referred_by TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_tenants_referral ON tenants(referral_code) WHERE referral_code IS NOT NULL;
