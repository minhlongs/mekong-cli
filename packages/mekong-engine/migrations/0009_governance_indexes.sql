-- Migration 0009: Add missing indexes for governance tables
-- Addresses performance gaps identified in 0007_governance.sql

-- Index on votes(stakeholder_id) for stakeholder vote lookups
CREATE INDEX IF NOT EXISTS idx_vote_stakeholder ON votes(stakeholder_id);

-- Index on treasury(tenant_id) for tenant treasury queries
CREATE INDEX IF NOT EXISTS idx_treasury_tenant ON treasury(tenant_id);

-- Compound index for UNIQUE constraint lookups on votes
CREATE INDEX IF NOT EXISTS idx_vote_proposal_stakeholder ON votes(proposal_id, stakeholder_id);
