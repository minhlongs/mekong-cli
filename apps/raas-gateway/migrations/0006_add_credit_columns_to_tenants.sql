-- Migration: 0006_add_credit_columns_to_tenants
-- Created: 2026-03-19
-- Description: Add balance, total_earned, total_spent columns to tenants table

-- Add credit balance columns
ALTER TABLE tenants ADD COLUMN balance INTEGER DEFAULT 0;
ALTER TABLE tenants ADD COLUMN total_earned INTEGER DEFAULT 0;
ALTER TABLE tenants ADD COLUMN total_spent INTEGER DEFAULT 0;

-- Migrate existing used_credits to total_spent (if any)
UPDATE tenants SET total_spent = used_credits WHERE used_credits > 0;

-- Note: balance and total_earned start at 0
-- New tenants will get welcome credits via the onboarding flow
