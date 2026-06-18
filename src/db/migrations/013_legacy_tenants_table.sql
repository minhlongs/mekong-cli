-- Migration 013: Legacy Tenants Table for RaaS Compatibility
-- Created: 2026-06-18
-- Description: Create tenants table for Vietnam RaaS integration
-- Purpose: Support legacy Tenant model while transitioning to economic_particles

CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Indexes for tenant lookups
CREATE INDEX IF NOT EXISTS idx_tenants_api_key_hash ON tenants(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_tenants_is_active ON tenants(is_active);
CREATE INDEX IF NOT EXISTS idx_tenants_created_at ON tenants(created_at DESC);

-- Trigger to update timestamp (for consistency, though tenants rarely updated)
CREATE OR REPLACE FUNCTION update_tenants_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at column if not exists (for future compatibility)
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE TRIGGER trigger_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_tenants_updated_at();
