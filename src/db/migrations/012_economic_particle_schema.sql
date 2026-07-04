-- Migration 012: Economic Particle Schema
-- Created: 2026-06-18
-- Description: Atomic economic units for usage tracking, credits, and financial events
-- Purpose: Replace legacy raas/tenant.py SQLite with unified PostgreSQL particle system

-- ============================================================================
-- ECONOMIC PARTICLES - Atomic economic units (usage, credits, adjustments)
-- ============================================================================
-- Each row represents an immutable economic event that affects balance.
-- Particles are append-only for audit trail integrity.

CREATE TABLE IF NOT EXISTS economic_particles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Legacy RaaS compatibility (kept for Vietnam integration)
    tenant_id VARCHAR(255), -- Nullable: new systems use key_id, legacy uses tenant reference

    -- Modern identification (preferred)
    key_id VARCHAR(50) NOT NULL, -- License key identifier (e.g., 'opc_001_xxx')

    -- Particle classification
    particle_type VARCHAR(50) NOT NULL CHECK (
        particle_type IN (
            'usage',          -- API/command consumption
            'credit',         -- Credit addition (purchase, grant, refund)
            'adjustment',     -- Manual balance adjustment
            'payment',        -- External payment recorded
            'refund',         -- Payment reversal/credit return
            'fee',            -- Platform/stripe fee
            'subscription',   -- Subscription cycle charge
            'adjustment_positive', -- Positive adjustment (credit)
            'adjustment_negative'  -- Negative adjustment (debit)
        )
    ),

    -- Economic values (signed: positive = credit in, negative = consumption)
    amount DECIMAL(14,6) NOT NULL,

    -- Currency handling (for multi-currency support, Vietnam: VND/USD)
    currency VARCHAR(10) DEFAULT 'USD' CHECK (currency IN ('USD', 'VND', 'EUR')),

    -- Balance snapshot after this particle (for efficient balance lookup)
    balance_after DECIMAL(14,6),

    -- Flexible data payload (rate card, usage details, webhook payloads)
    metadata JSONB DEFAULT '{}',

    -- Origin tracking
    source VARCHAR(100) NOT NULL DEFAULT 'api' CHECK (
        source IN ('api', 'manual', 'webhook', 'cron', 'admin', 'migration', 'reconciliation')
    ),

    -- External reference linkage (payment tx, Stripe PI, invoice number)
    reference_id VARCHAR(255),

    -- Timestamps (UTC throughout)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Vietnam-specific: store original tenant identifier for legacy integration
    tenant_reference_id VARCHAR(255) -- Alias for tenant_id, kept separate for clarity
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_economic_particles_tenant_id ON economic_particles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_economic_particles_key_id ON economic_particles(key_id);
CREATE INDEX IF NOT EXISTS idx_economic_particles_particle_type ON economic_particles(particle_type);
CREATE INDEX IF NOT EXISTS idx_economic_particles_created_at ON economic_particles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_economic_particles_source ON economic_particles(source);
CREATE INDEX IF NOT EXISTS idx_economic_particles_reference_id ON economic_particles(reference_id) WHERE reference_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_economic_particles_tenant_ref ON economic_particles(tenant_reference_id) WHERE tenant_reference_id IS NOT NULL;

-- Composite indexes for balance queries (most critical for real-time balance lookup)
CREATE INDEX IF NOT EXISTS idx_economic_particles_key_id_created_at ON economic_particles(key_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_economic_particles_key_id_type_created ON economic_particles(key_id, particle_type, created_at DESC);

-- GIN index for JSONB metadata queries (rate card lookups, usage details)
CREATE INDEX IF NOT EXISTS idx_economic_particles_metadata ON economic_particles USING GIN (metadata);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_economic_particles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_economic_particles_updated_at
    BEFORE UPDATE ON economic_particles
    FOR EACH ROW
    EXECUTE FUNCTION update_economic_particles_updated_at();
